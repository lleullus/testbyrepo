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
#define SESSION_GRACE_DEFAULT_MS 3600000

struct tty_session {
  char id[SESSION_ID_LENGTH + 1];
  bool resumable;
  pty_process *process;
  struct pss_tty *client;
  uv_timer_t *expiry_timer;
  char *backlog;
  size_t backlog_len;
  size_t backlog_cap;
  size_t replay_offset;
  bool backlog_overflow;
  struct tty_session *next;
};

static struct tty_session *session_list = NULL;

static uint64_t session_grace_ms(void) {
  const char *value = getenv("TTYD_RECONNECT_GRACE");
  if (value == NULL || *value == '\0') return SESSION_GRACE_DEFAULT_MS;
  char *end = NULL;
  long seconds = strtol(value, &end, 10);
  if (end == value || *end != '\0' || seconds < 1 || seconds > 3600) return SESSION_GRACE_DEFAULT_MS;
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
  session_cancel_expiry(session);
  session_unlink(session);
  free(session->backlog);
  free(session);
}

static struct tty_session *session_create(const char *id, bool resumable) {
  struct tty_session *session = xmalloc(sizeof(struct tty_session));
  memset(session, 0, sizeof(struct tty_session));
  session->resumable = resumable;
  if (resumable) {
    memcpy(session->id, id, SESSION_ID_LENGTH);
    session->id[SESSION_ID_LENGTH] = '\0';
    session->next = session_list;
    session_list = session;
  }
  return session;
}

static void session_buffer_append(struct tty_session *session, const char *data, size_t len) {
  if (session == NULL || len == 0 || session->backlog_overflow) return;
  if (len > SESSION_BACKLOG_MAX - session->backlog_len) {
    free(session->backlog);
    session->backlog = NULL;
    session->backlog_len = 0;
    session->backlog_cap = 0;
    session->replay_offset = 0;
    session->backlog_overflow = true;
    lwsl_warn("detached session output exceeded %d bytes; redraw required on resume\n", SESSION_BACKLOG_MAX);
    return;
  }

  size_t needed = session->backlog_len + len;
  if (needed > session->backlog_cap) {
    size_t cap = session->backlog_cap == 0 ? 65536 : session->backlog_cap;
    while (cap < needed) cap *= 2;
    if (cap > SESSION_BACKLOG_MAX) cap = SESSION_BACKLOG_MAX;
    session->backlog = xrealloc(session->backlog, cap);
    session->backlog_cap = cap;
  }
  memcpy(session->backlog + session->backlog_len, data, len);
  session->backlog_len += len;
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

static int send_initial_message(struct pss_tty *pss, int index) {
  char buffer[128] = "";
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
    case SET_SESSION_STATE: {
      const char *state = pss->resumed ? (pss->resume_reset ? "resumed-reset" : "resumed") : "fresh";
      n = snprintf(NULL, 0, "%c%s", cmd, state);
      break;
    }
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
    case SET_SESSION_STATE: {
      const char *state = pss->resumed ? (pss->resume_reset ? "resumed-reset" : "resumed") : "fresh";
      written = snprintf((char *)p, capacity, "%c%s", cmd, state);
      break;
    }
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
    if (session->client != NULL) {
      session->client->lws_close_status = process->exit_code == 0 ? 1000 : 1006;
      lws_callback_on_writable(session->client->wsi);
    }
    return;
  }
  if (buf == NULL) return;

  struct pss_tty *pss = session->client;
  if (pss != NULL && pss->initialized && session->replay_offset >= session->backlog_len && pss->pty_buf == NULL) {
    pss->pty_buf = buf;
    lws_callback_on_writable(pss->wsi);
    return;
  }

  session_buffer_append(session, buf->base, buf->len);
  pty_buf_free(buf);
  if (session->client == NULL) pty_resume(process);
}

static void process_exit_cb(pty_process *process) {
  struct tty_session *session = (struct tty_session *)process->ctx;
  if (session == NULL) return;

  if (process->exit_signal)
    lwsl_notice("process killed with signal %d, pid: %d\n", process->exit_signal, process->pid);
  else
    lwsl_notice("process exited with code %d, pid: %d\n", process->exit_code, process->pid);

  if (session->client != NULL) {
    struct pss_tty *pss = session->client;
    pss->process = NULL;
    pss->session = NULL;
    pss->lws_close_status = process->exit_code == 0 ? 1000 : 1006;
    lws_callback_on_writable(pss->wsi);
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
    process_free(process);
    session_release(session);
    return false;
  }
  lwsl_notice("started process, pid: %d%s\n", process->pid, resumable ? " (resumable)" : "");
  session->process = process;
  session->client = pss;
  pss->session = session;
  pss->process = process;
  pss->resumed = false;
  pss->resume_reset = false;
  lws_callback_on_writable(pss->wsi);
  return true;
}

static bool attach_process(struct pss_tty *pss, struct tty_session *session, uint16_t columns, uint16_t rows) {
  if (session == NULL || session->process == NULL || !process_running(session->process)) return false;

  pty_pause(session->process);
  session_cancel_expiry(session);

  if (session->client != NULL && session->client != pss) {
    struct pss_tty *old = session->client;
    if (old->pty_buf != NULL) {
      session_buffer_append(session, old->pty_buf->base, old->pty_buf->len);
      pty_buf_free(old->pty_buf);
      old->pty_buf = NULL;
    }
    old->session = NULL;
    old->process = NULL;
    old->lws_close_status = LWS_CLOSE_STATUS_NORMAL;
    lws_callback_on_writable(old->wsi);
  }

  session->client = pss;
  session->replay_offset = 0;
  pss->session = session;
  pss->process = session->process;
  pss->resumed = true;
  pss->resume_reset = session->backlog_overflow;

  if (columns > 0) session->process->columns = columns;
  if (rows > 0) session->process->rows = rows;
  pty_resize(session->process);
  lws_callback_on_writable(pss->wsi);
  return true;
}

static void wsi_output_data(struct lws *wsi, const char *data, size_t len) {
  if (data == NULL || len == 0) return;
  char *message = xmalloc(LWS_PRE + 1 + len);
  char *ptr = message + LWS_PRE;
  *ptr = OUTPUT;
  memcpy(ptr + 1, data, len);
  size_t n = len + 1;
  if (lws_write(wsi, (unsigned char *)ptr, n, LWS_WRITE_BINARY) < (int)n) lwsl_err("write OUTPUT to WS\n");
  free(message);
}

static void wsi_output(struct lws *wsi, pty_buf_t *buf) {
  if (buf == NULL) return;
  wsi_output_data(wsi, buf->base, buf->len);
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
      pss->resume_reset = false;
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
      if (pss->lws_close_status > LWS_CLOSE_STATUS_NOSTATUS) {
        lws_close_reason(wsi, pss->lws_close_status, NULL, 0);
        return 1;
      }

      if (!pss->initialized) {
        if (pss->initial_cmd_index == sizeof(initial_cmds)) {
          pss->initialized = true;
          struct tty_session *session = pss->session;
          if (session != NULL && session->replay_offset < session->backlog_len) {
            lws_callback_on_writable(wsi);
          } else {
            if (pss->resume_reset && pss->process != NULL) {
              session->backlog_overflow = false;
              pty_kill(pss->process, SIGWINCH);
            }
            pty_resume(pss->process);
          }
          break;
        }
        if (send_initial_message(pss, pss->initial_cmd_index) < 0) {
          lwsl_err("failed to send initial message, index: %d\n", pss->initial_cmd_index);
          lws_close_reason(wsi, LWS_CLOSE_STATUS_UNEXPECTED_CONDITION, NULL, 0);
          return -1;
        }
        pss->initial_cmd_index++;
        lws_callback_on_writable(wsi);
        break;
      }

      if (pss->session != NULL && pss->session->replay_offset < pss->session->backlog_len) {
        struct tty_session *session = pss->session;
        size_t remaining = session->backlog_len - session->replay_offset;
        size_t chunk = remaining > SESSION_REPLAY_CHUNK ? SESSION_REPLAY_CHUNK : remaining;
        wsi_output_data(wsi, session->backlog + session->replay_offset, chunk);
        session->replay_offset += chunk;
        if (session->replay_offset < session->backlog_len) {
          lws_callback_on_writable(wsi);
        } else {
          free(session->backlog);
          session->backlog = NULL;
          session->backlog_len = 0;
          session->backlog_cap = 0;
          session->replay_offset = 0;
          pty_resume(pss->process);
        }
        break;
      }

      if (pss->pty_buf != NULL) {
        wsi_output(wsi, pss->pty_buf);
        pty_buf_free(pss->pty_buf);
        pss->pty_buf = NULL;
        pty_resume(pss->process);
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
        case INPUT:
          if (!server->writable) break;
          int err = pty_write(pss->process, pty_buf_init(pss->buffer + 1, pss->len - 1));
          if (err) {
            lwsl_err("uv_write: %s (%s)\n", uv_err_name(err), uv_strerror(err));
            return -1;
          }
          break;
        case RESIZE_TERMINAL:
          if (pss->process == NULL) break;
          json_object_put(
              parse_window_size(pss->buffer + 1, pss->len - 1, &pss->process->columns, &pss->process->rows));
          pty_resize(pss->process);
          break;
        case PAUSE:
          pty_pause(pss->process);
          break;
        case RESUME:
          pty_resume(pss->process);
          break;
        case JSON_DATA:
          if (pss->process != NULL) break;
          uint16_t columns = 0;
          uint16_t rows = 0;
          json_object *obj = parse_window_size(pss->buffer, pss->len, &columns, &rows);
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

      struct tty_session *session = pss->session;
      if (session != NULL && session->client == pss && pss->process != NULL) {
        if (pss->pty_buf != NULL) {
          if (session->resumable) session_buffer_append(session, pss->pty_buf->base, pss->pty_buf->len);
          pty_buf_free(pss->pty_buf);
          pss->pty_buf = NULL;
        }

        pty_process *process = pss->process;
        session->client = NULL;
        pss->session = NULL;
        pss->process = NULL;

        if (session->resumable && process_running(process)) {
          pty_resume(process);
          session_start_expiry(session);
          lwsl_notice("detached resumable process, pid: %d\n", process->pid);
        } else if (process_running(process)) {
          lwsl_notice("killing process, pid: %d\n", process->pid);
          pty_kill(process, server->sig_code);
        }
      } else if (pss->pty_buf != NULL) {
        pty_buf_free(pss->pty_buf);
        pss->pty_buf = NULL;
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
