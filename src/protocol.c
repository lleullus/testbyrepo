#include <ctype.h>
#include <errno.h>
#include <json.h>
#include <libwebsockets.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pty.h"
#include "server.h"
#include "utils.h"

// initial message list
static char initial_cmds[] = {SET_WINDOW_TITLE, SET_PREFERENCES, SET_SESSION_STATE};

#define SESSION_ID_LENGTH 32
#define SESSION_BACKLOG_MAX (8 * 1024 * 1024)
#define SESSION_REPLAY_CHUNK (64 * 1024)
#define SESSION_GRACE_MAX_SECONDS (9 * 60 * 60)
#define SESSION_GRACE_DEFAULT_MS (SESSION_GRACE_MAX_SECONDS * 1000ULL)

struct tty_session {
  char id[SESSION_ID_LENGTH + 1];
  bool resumable;
  pty_process *process;
  struct pss_tty *client;
  uv_timer_t *expiry_timer;
  char *output_buf;
  size_t output_len;
  size_t output_offset;
  size_t output_cap;
  bool needs_redraw;
  struct tty_session *next;
  uint64_t diagnostic_id;
  uint64_t pty_read_count;
  uint64_t pty_output_bytes;
  uint64_t pty_zero_read_count;
  uint64_t pty_write_count;
  uint64_t ws_input_bytes;
  uint64_t ws_output_bytes;
  uint64_t dropped_output_bytes;
};

static struct tty_session *session_list = NULL;
static uint64_t next_session_diagnostic_id = 0;
static uint64_t next_connection_generation = 0;

static bool diagnostics_enabled(void) {
  static int enabled = -1;
  if (enabled < 0) {
    const char *value = getenv("TTYD_DIAGNOSTICS");
    enabled = value != NULL && *value != '\0' && strcmp(value, "0") != 0;
  }
  return enabled != 0;
}

static void schedule_writable(struct pss_tty *pss) {
  if (pss == NULL || pss->wsi == NULL || pss->writable_pending) return;
  pss->writable_pending = true;
  lws_callback_on_writable(pss->wsi);
}

static void session_diagnostic(struct tty_session *session, struct pss_tty *pss, const char *event) {
  if (!diagnostics_enabled() || session == NULL) return;
  const int pid = session->process == NULL ? -1 : session->process->pid;
  const unsigned long long connection = pss == NULL ? 0 : (unsigned long long)pss->connection_generation;
  const size_t pending = session->output_len >= session->output_offset
                             ? session->output_len - session->output_offset
                             : 0;
  lwsl_notice(
      "diag event=%s monotonic_ms=%llu session=%llu connection=%llu pid=%d initialized=%d client_paused=%d "
      "pty_paused=%d output=%zu/%zu pending_output=%zu needs_redraw=%d reads=%llu zero_reads=%llu "
      "pty_output_bytes=%llu writes=%llu ws_input_bytes=%llu ws_output_bytes=%llu dropped_output_bytes=%llu\n",
      event, (unsigned long long)(uv_hrtime() / 1000000ULL), (unsigned long long)session->diagnostic_id, connection,
      pid, pss != NULL && pss->initialized, pss != NULL && pss->client_flow_paused,
      session->process != NULL && session->process->paused, session->output_offset, session->output_len, pending,
      session->needs_redraw, (unsigned long long)session->pty_read_count,
      (unsigned long long)session->pty_zero_read_count, (unsigned long long)session->pty_output_bytes,
      (unsigned long long)session->pty_write_count, (unsigned long long)session->ws_input_bytes,
      (unsigned long long)session->ws_output_bytes, (unsigned long long)session->dropped_output_bytes);
}

static bool session_output_pending(const struct tty_session *session) {
  return session != NULL && session->output_len > session->output_offset;
}

static void session_output_append(struct tty_session *session, const char *data, size_t len) {
  if (session == NULL || data == NULL || len == 0) return;
  if (session->needs_redraw) {
    session->dropped_output_bytes += len;
    return;
  }

  size_t unconsumed = session->output_len - session->output_offset;
  if (len > SESSION_BACKLOG_MAX - unconsumed) {
    session->dropped_output_bytes += unconsumed + len;
    free(session->output_buf);
    session->output_buf = NULL;
    session->output_len = 0;
    session->output_offset = 0;
    session->output_cap = 0;
    session->needs_redraw = true;
    const int pid = session->process == NULL ? -1 : session->process->pid;
    lwsl_warn("session output exceeded %d bytes; session=%llu pid=%d redraw required\n", SESSION_BACKLOG_MAX,
              (unsigned long long)session->diagnostic_id, pid);
    session_diagnostic(session, session->client, "output-overflow");
    return;
  }

  if (session->output_offset > 0) {
    if (unconsumed > 0) memmove(session->output_buf, session->output_buf + session->output_offset, unconsumed);
    session->output_len = unconsumed;
    session->output_offset = 0;
  }

  size_t needed = session->output_len + len;
  if (needed > session->output_cap) {
    size_t cap = session->output_cap == 0 ? 64 * 1024 : session->output_cap;
    while (cap < needed) cap *= 2;
    if (cap > SESSION_BACKLOG_MAX) cap = SESSION_BACKLOG_MAX;
    session->output_buf = xrealloc(session->output_buf, cap);
    session->output_cap = cap;
  }
  memcpy(session->output_buf + session->output_len, data, len);
  session->output_len += len;
}
static bool session_discard_and_redraw(struct tty_session *session, struct pss_tty *pss) {
  if (session == NULL || session->process == NULL) return false;
  free(session->output_buf);
  session->output_buf = NULL;
  session->output_len = 0;
  session->output_offset = 0;
  session->output_cap = 0;

  if (!pty_signal_foreground(session->process, SIGWINCH)) {
    session_diagnostic(session, pss, "redraw-failed");
    return false;
  }
  session->needs_redraw = false;
  session_diagnostic(session, pss, "redraw-complete");
  return true;
}

static uint64_t session_grace_ms(void) {
  const char *value = getenv("TTYD_RECONNECT_GRACE");
  if (value == NULL || *value == '\0') return SESSION_GRACE_DEFAULT_MS;
  char *end = NULL;
  long seconds = strtol(value, &end, 10);
  if (end == value || *end != '\0' || seconds < 1 || seconds > SESSION_GRACE_MAX_SECONDS)
    return SESSION_GRACE_DEFAULT_MS;
  return (uint64_t)seconds * 1000;
}

static bool resume_id_valid(const char *id) {
  if (id == NULL || strlen(id) != SESSION_ID_LENGTH) return false;
  for (size_t i = 0; i < SESSION_ID_LENGTH; i++) {
    if (!isxdigit((unsigned char)id[i])) return false;
  }
  return true;
}

static struct tty_session *session_find(const char *id) {
  for (struct tty_session *session = session_list; session != NULL; session = session->next) {
    if (!strcmp(session->id, id)) return session;
  }
  return NULL;
}

static void session_unlink(struct tty_session *session) {
  if (!session->resumable) return;
  struct tty_session **cursor = &session_list;
  while (*cursor != NULL) {
    if (*cursor == session) {
      *cursor = session->next;
      return;
    }
    cursor = &(*cursor)->next;
  }
}

static void expiry_timer_close_cb(uv_handle_t *handle) { free(handle); }

static void session_cancel_expiry(struct tty_session *session) {
  if (session->expiry_timer == NULL) return;
  uv_timer_t *timer = session->expiry_timer;
  session->expiry_timer = NULL;
  timer->data = NULL;
  uv_timer_stop(timer);
  uv_close((uv_handle_t *)timer, expiry_timer_close_cb);
}

static void session_release(struct tty_session *session) {
  if (session == NULL) return;
  session_diagnostic(session, session->client, "release");
  session_cancel_expiry(session);
  session_unlink(session);
  free(session->output_buf);
  free(session);
}

static struct tty_session *session_create(const char *id, bool resumable) {
  struct tty_session *session = xmalloc(sizeof(struct tty_session));
  memset(session, 0, sizeof(struct tty_session));
  session->diagnostic_id = ++next_session_diagnostic_id;
  session->resumable = resumable;
  if (resumable) {
    memcpy(session->id, id, SESSION_ID_LENGTH);
    session->id[SESSION_ID_LENGTH] = '\0';
    session->next = session_list;
    session_list = session;
  }
  return session;
}

static void session_expire_cb(uv_timer_t *timer) {
  struct tty_session *session = (struct tty_session *)timer->data;
  if (session == NULL) return;
  session->expiry_timer = NULL;
  timer->data = NULL;
  uv_timer_stop(timer);
  uv_close((uv_handle_t *)timer, expiry_timer_close_cb);

  if (session->client != NULL || session->process == NULL) return;
  session_unlink(session);
  if (process_running(session->process)) {
    lwsl_notice("resume grace expired, killing process, pid: %d\n", session->process->pid);
    if (!pty_kill(session->process, server->sig_code))
      lwsl_err("failed to kill expired resumable process, pid: %d\n", session->process->pid);
  }
}

static void session_start_expiry(struct tty_session *session) {
  session_cancel_expiry(session);
  uv_timer_t *timer = xmalloc(sizeof(uv_timer_t));
  if (uv_timer_init(server->loop, timer) != 0) {
    free(timer);
    if (session->process != NULL && process_running(session->process)) pty_kill(session->process, server->sig_code);
    return;
  }
  session->expiry_timer = timer;
  timer->data = session;
  uv_timer_start(timer, session_expire_cb, session_grace_ms(), 0);
}

static const char *session_state(const struct pss_tty *pss) { return pss->resumed ? "resumed" : "fresh"; }

static int send_initial_message(struct pss_tty *pss, int index) {
  char buffer[128] = "";
  const char *state = session_state(pss);
  int n = -1;

  char cmd = initial_cmds[index];
  switch (cmd) {
    case SET_WINDOW_TITLE:
      gethostname(buffer, sizeof(buffer) - 1);
      buffer[sizeof(buffer) - 1] = '\0';
      n = snprintf(NULL, 0, "%c%s (%s)", cmd, server->command, buffer);
      break;
    case SET_PREFERENCES:
      n = snprintf(NULL, 0, "%c%s", cmd, server->prefs_json);
      break;
    case SET_SESSION_STATE:
      n = snprintf(NULL, 0, "%c%s", cmd, state);
      break;
    default:
      return -1;
  }

  if (n < 0) return -1;

  size_t capacity = (size_t)n + 1;
  unsigned char *message = xmalloc(LWS_PRE + capacity);
  unsigned char *p = &message[LWS_PRE];
  int written = -1;

  switch (cmd) {
    case SET_WINDOW_TITLE:
      written = snprintf((char *)p, capacity, "%c%s (%s)", cmd, server->command, buffer);
      break;
    case SET_PREFERENCES:
      written = snprintf((char *)p, capacity, "%c%s", cmd, server->prefs_json);
      break;
    case SET_SESSION_STATE:
      written = snprintf((char *)p, capacity, "%c%s", cmd, state);
      break;
    default:
      break;
  }

  if (written < 0 || written != n || (size_t)written >= capacity) {
    free(message);
    return -1;
  }

  int rc = lws_write(pss->wsi, p, (size_t)written, LWS_WRITE_BINARY);
  free(message);
  return rc;
}

static json_object *parse_window_size(const char *buf, size_t len, uint16_t *cols, uint16_t *rows) {
  json_tokener *tok = json_tokener_new();
  json_object *obj = json_tokener_parse_ex(tok, buf, len);
  struct json_object *o = NULL;

  if (json_object_object_get_ex(obj, "columns", &o)) *cols = (uint16_t)json_object_get_int(o);
  if (json_object_object_get_ex(obj, "rows", &o)) *rows = (uint16_t)json_object_get_int(o);

  json_tokener_free(tok);
  return obj;
}

static void parse_resume_id(struct lws *wsi, struct pss_tty *pss) {
  char arg[128];
  int index = 0;
  pss->resume_id[0] = '\0';
  while (lws_hdr_copy_fragment(wsi, arg, sizeof(arg), WSI_TOKEN_HTTP_URI_ARGS, index++) > 0) {
    if (strncmp(arg, "resume=", 7) != 0) continue;
    const char *id = arg + 7;
    if (!resume_id_valid(id)) continue;
    memcpy(pss->resume_id, id, SESSION_ID_LENGTH);
    pss->resume_id[SESSION_ID_LENGTH] = '\0';
    return;
  }
}

static bool check_host_origin(struct lws *wsi) {
  char buf[256];
  memset(buf, 0, sizeof(buf));
  int len = lws_hdr_copy(wsi, buf, (int)sizeof(buf), WSI_TOKEN_ORIGIN);
  if (len <= 0) return false;

  const char *prot, *address, *path;
  int port;
  if (lws_parse_uri(buf, &prot, &address, &port, &path)) return false;
  char origin_host[256];
  int written;
  if (port == 80 || port == 443) {
    written = snprintf(origin_host, sizeof(origin_host), "%s", address);
  } else {
    written = snprintf(origin_host, sizeof(origin_host), "%s:%d", address, port);
  }
  if (written < 0 || (size_t)written >= sizeof(origin_host)) return false;

  char host_buf[256];
  memset(host_buf, 0, sizeof(host_buf));
  len = lws_hdr_copy(wsi, host_buf, (int)sizeof(host_buf), WSI_TOKEN_HOST);

  return len > 0 && strcasecmp(origin_host, host_buf) == 0;
}

static void process_read_cb(pty_process *process, pty_buf_t *buf, bool eof) {
  struct tty_session *session = (struct tty_session *)process->ctx;
  if (session == NULL) {
    pty_buf_free(buf);
    return;
  }

  if (eof && !process_running(process)) {
    pty_buf_free(buf);
    session_diagnostic(session, session->client, "pty-eof");
    if (session->client != NULL) {
      session->client->lws_close_status = process->exit_code == 0 ? 1000 : 1006;
      schedule_writable(session->client);
    }
    return;
  }
  if (buf == NULL) {
    session->pty_zero_read_count++;
    session_diagnostic(session, session->client, "pty-zero-read");
    return;
  }

  session->pty_read_count++;
  session->pty_output_bytes += buf->len;
  struct pss_tty *pss = session->client;
  session_output_append(session, buf->base, buf->len);
  pty_buf_free(buf);
  if (pss != NULL && pss->initialized && !pss->client_flow_paused) schedule_writable(pss);
}

static void process_exit_cb(pty_process *process) {
  struct tty_session *session = (struct tty_session *)process->ctx;
  if (session == NULL) return;

  if (process->exit_signal)
    lwsl_notice("process killed with signal %d, pid: %d\n", process->exit_signal, process->pid);
  else
    lwsl_notice("process exited with code %d, pid: %d\n", process->exit_code, process->pid);
  session_diagnostic(session, session->client, "process-exit");

  if (session->client != NULL) {
    struct pss_tty *pss = session->client;
    pss->process = NULL;
    pss->session = NULL;
    pss->lws_close_status = process->exit_code == 0 ? 1000 : 1006;
    schedule_writable(pss);
  }

  session->client = NULL;
  session->process = NULL;
  process->ctx = NULL;
  session_release(session);
}

static char **build_args(struct pss_tty *pss) {
  int i, n = 0;
  char **argv = xmalloc((server->argc + pss->argc + 1) * sizeof(char *));

  for (i = 0; i < server->argc; i++) {
    argv[n++] = server->argv[i];
  }

  for (i = 0; i < pss->argc; i++) {
    argv[n++] = pss->args[i];
  }
  argv[n] = NULL;

  return argv;
}

static char **build_env(struct pss_tty *pss) {
  int i = 0, n = 2;
  char **envp = xmalloc(n * sizeof(char *));

  // TERM
  envp[i] = xmalloc(36);
  snprintf(envp[i], 36, "TERM=%s", server->terminal_type);
  i++;

  // TTYD_USER
  if (strlen(pss->user) > 0) {
    envp = xrealloc(envp, (++n) * sizeof(char *));
    envp[i] = xmalloc(40);
    snprintf(envp[i], 40, "TTYD_USER=%s", pss->user);
    i++;
  }

  envp[i] = NULL;

  return envp;
}

static bool spawn_process(struct pss_tty *pss, uint16_t columns, uint16_t rows) {
  bool resumable = resume_id_valid(pss->resume_id);
  struct tty_session *session = session_create(pss->resume_id, resumable);
  pty_process *process = process_init((void *)session, server->loop, build_args(pss), build_env(pss));
  if (server->cwd != NULL) process->cwd = strdup(server->cwd);
  if (columns > 0) process->columns = columns;
  if (rows > 0) process->rows = rows;
  if (pty_spawn(process, process_read_cb, process_exit_cb) != 0) {
    lwsl_err("pty_spawn: %d (%s)\n", errno, strerror(errno));
    process->ctx = NULL;
    if (!process->async_initialized) {
      process_free(process);
      free(process);
    }
    session_release(session);
    return false;
  }
  lwsl_notice("started process, pid: %d%s\n", process->pid, resumable ? " (resumable)" : "");
  session->process = process;
  session->client = pss;
  pss->session = session;
  pss->process = process;
  pss->resumed = false;
  session_diagnostic(session, pss, "spawn");
  schedule_writable(pss);
  return true;
}

static bool attach_process(struct pss_tty *pss, struct tty_session *session, uint16_t columns, uint16_t rows) {
  if (session == NULL || session->process == NULL || !process_running(session->process)) return false;

  session_cancel_expiry(session);

  if (session->client != NULL && session->client != pss) {
    struct pss_tty *old = session->client;
    old->session = NULL;
    old->process = NULL;
    old->lws_close_status = LWS_CLOSE_STATUS_NORMAL;
    schedule_writable(old);
  }

  session->client = pss;
  pss->session = session;
  pss->process = session->process;
  pss->resumed = true;
  pss->client_flow_paused = false;

  if (columns > 0) session->process->columns = columns;
  if (rows > 0) session->process->rows = rows;
  pty_resize(session->process);
  session_diagnostic(session, pss, "attach");
  schedule_writable(pss);
  return true;
}
static void wsi_output_data(struct pss_tty *pss, const char *data, size_t len) {
  if (pss == NULL || data == NULL || len == 0) return;
  char *message = xmalloc(LWS_PRE + 1 + len);
  char *ptr = message + LWS_PRE;
  *ptr = OUTPUT;
  memcpy(ptr + 1, data, len);
  size_t n = len + 1;
  if (lws_write(pss->wsi, (unsigned char *)ptr, n, LWS_WRITE_BINARY) < (int)n) {
    lwsl_err("write OUTPUT to WS\n");
  } else if (pss->session != NULL) {
    pss->session->ws_output_bytes += len;
  }
  free(message);
}

static bool check_auth(struct lws *wsi, struct pss_tty *pss) {
  if (server->auth_header != NULL) {
    return lws_hdr_custom_copy(wsi, pss->user, sizeof(pss->user), server->auth_header, strlen(server->auth_header)) > 0;
  }

  if (server->credential != NULL) {
    char buf[256];
    size_t n = lws_hdr_copy(wsi, buf, sizeof(buf), WSI_TOKEN_HTTP_AUTHORIZATION);
    return n >= 7 && strstr(buf, "Basic ") && !strcmp(buf + 6, server->credential);
  }

  return true;
}

int callback_tty(struct lws *wsi, enum lws_callback_reasons reason, void *user, void *in, size_t len) {
  struct pss_tty *pss = (struct pss_tty *)user;
  char buf[256];
  size_t n = 0;

  switch (reason) {
    case LWS_CALLBACK_FILTER_PROTOCOL_CONNECTION:
      if (server->once && server->client_count > 0) {
        lwsl_warn("refuse to serve WS client due to the --once option.\n");
        return 1;
      }
      if (server->max_clients > 0 && server->client_count == server->max_clients) {
        lwsl_warn("refuse to serve WS client due to the --max-clients option.\n");
        return 1;
      }
      if (!check_auth(wsi, pss)) return 1;

      n = lws_hdr_copy(wsi, pss->path, sizeof(pss->path), WSI_TOKEN_GET_URI);
#if defined(LWS_ROLE_H2)
      if (n <= 0) n = lws_hdr_copy(wsi, pss->path, sizeof(pss->path), WSI_TOKEN_HTTP_COLON_PATH);
#endif
      if (strncmp(pss->path, endpoints.ws, n) != 0) {
        lwsl_warn("refuse to serve WS client for illegal ws path: %s\n", pss->path);
        return 1;
      }

      if (server->check_origin && !check_host_origin(wsi)) {
        lwsl_warn(
            "refuse to serve WS client from different origin due to the "
            "--check-origin option.\n");
        return 1;
      }
      break;

    case LWS_CALLBACK_ESTABLISHED:
      pss->initialized = false;
      pss->initial_cmd_index = 0;
      pss->authenticated = false;
      pss->wsi = wsi;
      pss->lws_close_status = LWS_CLOSE_STATUS_NOSTATUS;
      pss->session = NULL;
      pss->process = NULL;
      pss->resumed = false;
      pss->client_flow_paused = false;
      pss->writable_pending = false;
      pss->connection_generation = ++next_connection_generation;
      parse_resume_id(wsi, pss);

      if (server->url_arg) {
        while (lws_hdr_copy_fragment(wsi, buf, sizeof(buf), WSI_TOKEN_HTTP_URI_ARGS, n++) > 0) {
          if (strncmp(buf, "arg=", 4) == 0) {
            pss->args = xrealloc(pss->args, (pss->argc + 1) * sizeof(char *));
            pss->args[pss->argc] = strdup(&buf[4]);
            pss->argc++;
          }
        }
      }

      server->client_count++;

      lws_get_peer_simple(lws_get_network_wsi(wsi), pss->address, sizeof(pss->address));
      lwsl_notice("WS   %s - %s, clients: %d\n", pss->path, pss->address, server->client_count);
      break;

    case LWS_CALLBACK_SERVER_WRITEABLE:
      pss->writable_pending = false;
      if (pss->lws_close_status > LWS_CLOSE_STATUS_NOSTATUS) {
        lws_close_reason(wsi, pss->lws_close_status, NULL, 0);
        return 1;
      }

      if (!pss->initialized) {
        if (pss->initial_cmd_index == sizeof(initial_cmds)) {
          pss->initialized = true;
          struct tty_session *session = pss->session;
          if (session != NULL && session->needs_redraw) session_discard_and_redraw(session, pss);
          if (!pss->client_flow_paused && session_output_pending(session)) schedule_writable(pss);
          session_diagnostic(session, pss, "initialized");
          break;
        }
        if (send_initial_message(pss, pss->initial_cmd_index) < 0) {
          lwsl_err("failed to send initial message, index: %d\n", pss->initial_cmd_index);
          lws_close_reason(wsi, LWS_CLOSE_STATUS_UNEXPECTED_CONDITION, NULL, 0);
          return -1;
        }
        pss->initial_cmd_index++;
        schedule_writable(pss);
        break;
      }

      if (pss->client_flow_paused) break;
      struct tty_session *session = pss->session;
      if (session == NULL) break;
      if (session->needs_redraw && !session_discard_and_redraw(session, pss)) break;
      if (!session_output_pending(session)) break;

      size_t remaining = session->output_len - session->output_offset;
      size_t chunk = remaining > SESSION_REPLAY_CHUNK ? SESSION_REPLAY_CHUNK : remaining;
      wsi_output_data(pss, session->output_buf + session->output_offset, chunk);
      session->output_offset += chunk;
      if (session_output_pending(session)) {
        schedule_writable(pss);
      } else {
        free(session->output_buf);
        session->output_buf = NULL;
        session->output_len = 0;
        session->output_offset = 0;
        session->output_cap = 0;
        session_diagnostic(session, pss, "output-drained");
      }
      break;

    case LWS_CALLBACK_RECEIVE:
      if (len == 0 && pss->buffer == NULL) {
        if (lws_remaining_packet_payload(wsi) > 0 || !lws_is_final_fragment(wsi)) return 0;
        lwsl_warn("ignored empty WS message\n");
        break;
      }

      if (pss->buffer == NULL) {
        pss->buffer = xmalloc(len);
        pss->len = len;
        memcpy(pss->buffer, in, len);
      } else {
        pss->buffer = xrealloc(pss->buffer, pss->len + len);
        memcpy(pss->buffer + pss->len, in, len);
        pss->len += len;
      }

      const char command = pss->buffer[0];

      // check auth
      if (server->credential != NULL && !pss->authenticated && command != JSON_DATA) {
        lwsl_warn("WS client not authenticated\n");
        return 1;
      }

      // check if there are more fragmented messages
      if (lws_remaining_packet_payload(wsi) > 0 || !lws_is_final_fragment(wsi)) {
        return 0;
      }

      switch (command) {
        case INPUT: {
          if (!server->writable) break;
          const size_t input_len = pss->len - 1;
          int err = pty_write(pss->process, pty_buf_init(pss->buffer + 1, input_len));
          if (err) {
            lwsl_err("uv_write: %s (%s)\n", uv_err_name(err), uv_strerror(err));
            return -1;
          }
          if (pss->session != NULL) {
            pss->session->pty_write_count++;
            pss->session->ws_input_bytes += input_len;
          }
          break;
        }
        case RESIZE_TERMINAL:
          if (pss->process == NULL) break;
          json_object_put(
              parse_window_size(pss->buffer + 1, pss->len - 1, &pss->process->columns, &pss->process->rows));
          pty_resize(pss->process);
          break;
        case PAUSE:
          pss->client_flow_paused = true;
          session_diagnostic(pss->session, pss, "client-pause");
          break;
        case RESUME:
          pss->client_flow_paused = false;
          schedule_writable(pss);
          session_diagnostic(pss->session, pss, "client-resume");
          break;
        case JSON_DATA: {
          if (pss->process != NULL) break;
          uint16_t columns = 0;
          uint16_t rows = 0;
          json_object *obj = parse_window_size(pss->buffer, pss->len, &columns, &rows);
          if (obj == NULL) {
            lws_close_reason(wsi, LWS_CLOSE_STATUS_INVALID_PAYLOAD, NULL, 0);
            return -1;
          }
          if (server->credential != NULL) {
            struct json_object *o = NULL;
            if (json_object_object_get_ex(obj, "AuthToken", &o)) {
              const char *token = json_object_get_string(o);
              if (token != NULL && !strcmp(token, server->credential))
                pss->authenticated = true;
              else
                lwsl_warn("WS authentication failed with token: %s\n", token);
            }
            if (!pss->authenticated) {
              json_object_put(obj);
              lws_close_reason(wsi, LWS_CLOSE_STATUS_POLICY_VIOLATION, NULL, 0);
              return -1;
            }
          }
          json_object_put(obj);
          struct tty_session *session = resume_id_valid(pss->resume_id) ? session_find(pss->resume_id) : NULL;
          if (session != NULL) {
            if (!attach_process(pss, session, columns, rows)) {
              lwsl_warn("resume target is not ready; retry connection\n");
              lws_close_reason(wsi, LWS_CLOSE_STATUS_UNEXPECTED_CONDITION, NULL, 0);
              return -1;
            }
          } else if (!spawn_process(pss, columns, rows)) {
            return 1;
          }
          break;
        }
        default:
          lwsl_warn("ignored unknown message type: %c\n", command);
          break;
      }

      if (pss->buffer != NULL) {
        free(pss->buffer);
        pss->buffer = NULL;
      }
      break;

    case LWS_CALLBACK_CLOSED:
      if (pss->wsi == NULL) break;

      server->client_count--;
      lwsl_notice("WS closed from %s, clients: %d\n", pss->address, server->client_count);
      if (pss->buffer != NULL) free(pss->buffer);
      for (int i = 0; i < pss->argc; i++) free(pss->args[i]);

      struct tty_session *closed_session = pss->session;
      session_diagnostic(closed_session, pss, "connection-close");
      if (closed_session != NULL && closed_session->client == pss && pss->process != NULL) {
        pty_process *process = pss->process;
        closed_session->client = NULL;
        pss->session = NULL;
        pss->process = NULL;

        if (closed_session->resumable && process_running(process)) {
          session_start_expiry(closed_session);
          lwsl_notice("detached resumable process, pid: %d\n", process->pid);
        } else if (process_running(process)) {
          lwsl_notice("killing process, pid: %d\n", process->pid);
          pty_kill(process, server->sig_code);
        }
      }

      if ((server->once || server->exit_no_conn) && server->client_count == 0) {
        lwsl_notice("exiting due to the --once/--exit-no-conn option.\n");
        force_exit = true;
        lws_cancel_service(context);
        exit(0);
      }
      break;

    default:
      break;
  }

  return 0;
}
