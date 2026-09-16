#include <ctype.h>
#include <errno.h>
#include <json.h>
#include <libwebsockets.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifndef _WIN32
#include <sys/wait.h>
#endif

#include "pty.h"
#include "server.h"
#include "utils.h"

// initial message list
static char initial_cmds[] = {SET_WINDOW_TITLE, SET_PREFERENCES, SET_SESSION_STATE};

#define SESSION_PROTOCOL_VERSION 3
#define SESSION_ID_LENGTH 32
#define SESSION_BACKLOG_MAX (8 * 1024 * 1024)
#define SESSION_REPLAY_CHUNK (64 * 1024)
#define SESSION_GRACE_MAX_SECONDS (9 * 60 * 60)
#define SESSION_GRACE_DEFAULT_MS (SESSION_GRACE_MAX_SECONDS * 1000ULL)
#define SESSION_TOMBSTONE_MAX 256
#define SESSION_TOMBSTONE_MAX_AGE_MS SESSION_GRACE_DEFAULT_MS
#define OWNER_CHECK_PREPARE_MS 2000
#define OWNER_CHECK_PONG_MS 10000
#define OWNER_CHECK_NONCE_LENGTH 16

struct tty_session {
  char id[SESSION_ID_LENGTH + 1];
  bool resumable;
  pty_process *process;
  struct pss_tty *client;
  uv_timer_t *expiry_timer;
  struct pss_tty *pending_contender;
  struct pss_tty *check_owner;
  uv_timer_t *owner_check_timer;
  uint64_t owner_check_sequence;
  uint64_t owner_check_old_generation;
  uint64_t owner_check_deadline_ms;
  unsigned char owner_check_nonce[OWNER_CHECK_NONCE_LENGTH];
  bool owner_check_sent;
  char *output_buf;
  size_t output_len;
  size_t output_cap;
  uint64_t output_start;
  uint64_t output_end;
  bool needs_redraw;
  bool replay_lost;
  bool expiry_recorded;
  struct tty_session *next;
  uint64_t diagnostic_id;
  uint64_t pty_read_count;
  uint64_t pty_output_bytes;
  uint64_t pty_zero_read_count;
  uint64_t pty_write_count;
  uint64_t ws_input_bytes;
  uint64_t ws_output_bytes;
  uint64_t dropped_output_bytes;
  enum session_state state;
  int exit_code;
  int exit_signal;
  uint64_t exited_at_ms;
  uint64_t disconnect_at_ms;
  uint64_t expiry_deadline_ms;
  bool truncated;
  pid_t saved_root_pid;
};

struct session_tombstone {
  char id[SESSION_ID_LENGTH + 1];
  uint64_t diagnostic_id;
  uint64_t observed_ms;
  char reason[8];
  struct session_tombstone *next;
};

static struct tty_session *session_list = NULL;
static struct session_tombstone *tombstone_list = NULL;
static size_t tombstone_count = 0;
static uint64_t next_session_diagnostic_id = 0;
static uint64_t next_connection_generation = 0;
static uint64_t next_owner_check_sequence = 0;

static void owner_check_clear(struct tty_session *session, const char *event);
static void owner_check_finish(struct tty_session *session, const char *state);
static bool attach_process(struct pss_tty *pss, struct tty_session *session, uint16_t columns, uint16_t rows);
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
  const uint64_t sent = pss == NULL ? session->output_start : pss->send_position;
  const uint64_t pending = session->output_end > sent ? session->output_end - sent : 0;
  const unsigned long long contender = session->pending_contender == NULL
                                           ? 0
                                           : (unsigned long long)session->pending_contender->connection_generation;
  lwsl_notice(
      "diag event=%s monotonic_ms=%llu session=%llu connection=%llu pid=%d initialized=%d accepted=%d "
      "input_ready=%d client_paused=%d pty_paused=%d output=%llu/%llu pending_output=%llu replay_lost=%d "
      "reads=%llu zero_reads=%llu pty_output_bytes=%llu writes=%llu ws_input_bytes=%llu "
      "ws_output_bytes=%llu dropped_output_bytes=%llu check_sent=%d check_deadline_ms=%llu contender=%llu\n",
      event, (unsigned long long)(uv_hrtime() / 1000000ULL), (unsigned long long)session->diagnostic_id, connection,
      pid, pss != NULL && pss->initialized, pss != NULL && pss->session_accepted, pss != NULL && pss->input_ready,
      pss != NULL && pss->client_flow_paused, session->process != NULL && session->process->paused,
      (unsigned long long)sent, (unsigned long long)session->output_end, (unsigned long long)pending,
      session->replay_lost, (unsigned long long)session->pty_read_count,
      (unsigned long long)session->pty_zero_read_count, (unsigned long long)session->pty_output_bytes,
      (unsigned long long)session->pty_write_count, (unsigned long long)session->ws_input_bytes,
      (unsigned long long)session->ws_output_bytes, (unsigned long long)session->dropped_output_bytes,
      session->owner_check_sent, (unsigned long long)session->owner_check_deadline_ms, contender);
}

static bool session_output_pending(const struct tty_session *session, const struct pss_tty *pss) {
  if (session == NULL || pss == NULL || pss->send_position < session->output_start) return false;
  const uint64_t limit = pss->input_ready ? session->output_end : pss->replay_target;
  return pss->send_position < limit;
}

static void session_output_append(struct tty_session *session, const char *data, size_t len) {
  if (session == NULL || data == NULL || len == 0) return;

  if (len >= SESSION_BACKLOG_MAX) {
    const size_t overflow = (session->output_len + len) - SESSION_BACKLOG_MAX;
    session->dropped_output_bytes += overflow;
    session->output_start += overflow;
    session->output_end += len;
    session->replay_lost = true;
    session->truncated = true;

    if (session->output_cap < SESSION_BACKLOG_MAX) {
      session->output_buf = xrealloc(session->output_buf, SESSION_BACKLOG_MAX);
      session->output_cap = SESSION_BACKLOG_MAX;
    }
    const char *tail = data + (len - SESSION_BACKLOG_MAX);
    memcpy(session->output_buf, tail, SESSION_BACKLOG_MAX);
    session->output_len = SESSION_BACKLOG_MAX;
    return;
  }

  if (session->output_len + len > SESSION_BACKLOG_MAX) {
    const size_t overflow = (session->output_len + len) - SESSION_BACKLOG_MAX;
    session->dropped_output_bytes += overflow;
    session->output_start += overflow;
    session->output_end += len;
    session->replay_lost = true;
    session->truncated = true;

    memmove(session->output_buf, session->output_buf + overflow, session->output_len - overflow);
    session->output_len -= overflow;
    memcpy(session->output_buf + session->output_len, data, len);
    session->output_len += len;
    return;
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
  session->output_end += len;
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

static uint64_t monotonic_ms(void) { return uv_hrtime() / 1000000ULL; }

static void tombstone_purge(void) {
  const uint64_t now = monotonic_ms();
  struct session_tombstone **cursor = &tombstone_list;
  while (*cursor != NULL) {
    struct session_tombstone *entry = *cursor;
    if (now - entry->observed_ms <= SESSION_TOMBSTONE_MAX_AGE_MS) {
      cursor = &entry->next;
      continue;
    }
    *cursor = entry->next;
    free(entry);
    tombstone_count--;
  }
}

static struct session_tombstone *tombstone_find(const char *id) {
  tombstone_purge();
  for (struct session_tombstone *entry = tombstone_list; entry != NULL; entry = entry->next) {
    if (!strcmp(entry->id, id)) return entry;
  }
  return NULL;
}

static void tombstone_add(const struct tty_session *session, const char *reason) {
  if (session == NULL || !session->resumable || tombstone_find(session->id) != NULL) return;
  struct session_tombstone *entry = xmalloc(sizeof(struct session_tombstone));
  memset(entry, 0, sizeof(struct session_tombstone));
  memcpy(entry->id, session->id, sizeof(entry->id));
  entry->diagnostic_id = session->diagnostic_id;
  entry->observed_ms = monotonic_ms();
  snprintf(entry->reason, sizeof(entry->reason), "%s", reason);
  entry->next = tombstone_list;
  tombstone_list = entry;
  tombstone_count++;

  if (tombstone_count <= SESSION_TOMBSTONE_MAX) return;
  struct session_tombstone **cursor = &tombstone_list;
  while ((*cursor)->next != NULL) cursor = &(*cursor)->next;
  free(*cursor);
  *cursor = NULL;
  tombstone_count--;
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
  owner_check_clear(session, "owner-check-release");
  session_unlink(session);
  free(session->output_buf);
  free(session);
}

static struct tty_session *session_create(const char *id, bool resumable) {
  struct tty_session *session = xmalloc(sizeof(struct tty_session));
  memset(session, 0, sizeof(struct tty_session));
  session->diagnostic_id = ++next_session_diagnostic_id;
  session->resumable = resumable;
  session->state = SESSION_STATE_ACTIVE;
  if (resumable) {
    memcpy(session->id, id, SESSION_ID_LENGTH);
    session->id[SESSION_ID_LENGTH] = '\0';
    session->next = session_list;
    session_list = session;
  }
  return session;
}

static uint64_t get_reap_grace_ms(void) {
  const char *env = getenv("TTYD_REAP_GRACE_MS");
  if (env != NULL && atoi(env) > 0) return (uint64_t)atoi(env);
  return 3000ULL;
}

struct session_reaper {
  pid_t root_pid;
  struct tty_session *session;
  uv_timer_t timer;
  uint64_t grace_ms;
  int step;
  proc_ident_t *idents;
  size_t idents_count;
};

static void session_reaper_close_cb(uv_handle_t *handle) {
  free(handle);
}

static void session_reaper_timer_cb(uv_timer_t *timer) {
  struct session_reaper *reaper = (struct session_reaper *)timer->data;
  if (reaper == NULL) return;

  if (reaper->step == 1) {
    pty_expand_tree_idents(&reaper->idents, &reaper->idents_count);

    bool any_alive = false;
    for (size_t i = 0; i < reaper->idents_count; i++) {
      if (pty_proc_ident_alive(&reaper->idents[i])) {
        any_alive = true;
        kill(reaper->idents[i].pid, SIGKILL);
        if (reaper->idents[i].pgrp > 1) kill(-reaper->idents[i].pgrp, SIGKILL);
      }
    }

    if (any_alive) {
      reaper->step = 2;
      uv_timer_start(timer, session_reaper_timer_cb, 200, 0);
      return;
    }
  }

  int status;
  while (waitpid(-1, &status, WNOHANG) > 0) {}

  bool remaining_alive = pty_tree_idents_alive(reaper->idents, reaper->idents_count);
  if (reaper->session != NULL) {
    if (remaining_alive) {
      reaper->session->state = SESSION_STATE_TERMINATING;
      lwsl_err("process tree reap incomplete: pid %d remaining in TERMINATING\n", reaper->root_pid);
    } else {
      reaper->session->state = SESSION_STATE_PURGED;
      lwsl_notice("process tree reaped completely: pid %d transitioned to PURGED\n", reaper->root_pid);
      session_release(reaper->session);
      reaper->session = NULL;
    }
  }

  free(reaper->idents);
  reaper->idents = NULL;
  reaper->idents_count = 0;

  uv_timer_stop(timer);
  uv_close((uv_handle_t *)timer, session_reaper_close_cb);
  free(reaper);
}

static void session_reap_tree(struct tty_session *session, uint64_t grace_ms) {
  if (session == NULL) return;
  pid_t root_pid = session->process != NULL ? session->process->pid : session->saved_root_pid;
  session->state = SESSION_STATE_TERMINATING;
  session_unlink(session);

  if (root_pid <= 1) {
    session->state = SESSION_STATE_PURGED;
    session_release(session);
    return;
  }

  pid_t fg_pgid = pty_get_fg_pgid(session->process);
  proc_ident_t *idents = NULL;
  size_t count = 0;
  pty_get_process_tree_idents(root_pid, fg_pgid, &idents, &count);

  for (size_t i = 0; i < count; i++) {
    if (pty_proc_ident_alive(&idents[i])) {
      kill(idents[i].pid, SIGHUP);
      if (idents[i].pgrp > 1) kill(-idents[i].pgrp, SIGHUP);
    }
  }

  struct session_reaper *reaper = xmalloc(sizeof(struct session_reaper));
  memset(reaper, 0, sizeof(struct session_reaper));
  reaper->root_pid = root_pid;
  reaper->session = session;
  reaper->grace_ms = grace_ms;
  reaper->step = 1;
  reaper->idents = idents;
  reaper->idents_count = count;

  if (uv_timer_init(server->loop, &reaper->timer) != 0) {
    free(reaper->idents);
    free(reaper);
    session->state = SESSION_STATE_PURGED;
    session_release(session);
    return;
  }
  reaper->timer.data = reaper;
  uv_timer_start(&reaper->timer, session_reaper_timer_cb, grace_ms, 0);
}

static void session_expire_cb(uv_timer_t *timer) {
  struct tty_session *session = (struct tty_session *)timer->data;
  if (session == NULL) return;
  session->expiry_timer = NULL;
  timer->data = NULL;
  uv_timer_stop(timer);
  uv_close((uv_handle_t *)timer, expiry_timer_close_cb);

  if (session->client != NULL) return;
  session->expiry_recorded = true;
  tombstone_add(session, "expired");

  const uint64_t reap_grace = get_reap_grace_ms();
  session_reap_tree(session, reap_grace);
}

static void session_start_expiry(struct tty_session *session) {
  if (session->expiry_timer != NULL) return;
  uv_timer_t *timer = xmalloc(sizeof(uv_timer_t));
  if (uv_timer_init(server->loop, timer) != 0) {
    free(timer);
    if (session->process != NULL && process_running(session->process))
      session_reap_tree(session, get_reap_grace_ms());
    return;
  }
  session->expiry_timer = timer;
  session->disconnect_at_ms = monotonic_ms();
  session->expiry_deadline_ms = session->disconnect_at_ms + session_grace_ms();
  timer->data = session;
  uv_timer_start(timer, session_expire_cb, session_grace_ms(), 0);
}

static int wsi_send_command(struct pss_tty *pss, char command, const void *data, size_t len) {
  unsigned char *message = xmalloc(LWS_PRE + 1 + len);
  unsigned char *payload = message + LWS_PRE;
  payload[0] = (unsigned char)command;
  if (len > 0) memcpy(payload + 1, data, len);
  const int rc = lws_write(pss->wsi, payload, 1 + len, LWS_WRITE_BINARY);
  free(message);
  return rc;
}

static int send_session_state(struct pss_tty *pss) {
  json_object *obj = json_object_new_object();
  json_object *replay = json_object_new_object();
  json_object_object_add(obj, "version", json_object_new_int(SESSION_PROTOCOL_VERSION));
  json_object_object_add(obj, "state", json_object_new_string(pss->session_state));
  json_object_object_add(obj, "sessionDiagnosticId", json_object_new_int64((int64_t)pss->reported_session_id));
  json_object_object_add(obj, "connectionGeneration", json_object_new_int64((int64_t)pss->connection_generation));
  if (pss->takeover_offered)
    json_object_object_add(obj, "ownerGeneration", json_object_new_int64((int64_t)pss->offered_owner_generation));
  json_object_object_add(replay, "from", json_object_new_int64((int64_t)pss->replay_start));
  json_object_object_add(replay, "to", json_object_new_int64((int64_t)pss->replay_target));
  json_object_object_add(replay, "truncated", json_object_new_boolean(pss->replay_lost));
  if (pss->session != NULL) {
    json_object_object_add(replay, "droppedBytes", json_object_new_int64((int64_t)pss->session->dropped_output_bytes));
    if (pss->session->state == SESSION_STATE_EXITED_RETAINED) {
      json_object_object_add(obj, "exitCode", json_object_new_int(pss->session->exit_code));
      json_object_object_add(obj, "exitSignal", json_object_new_int(pss->session->exit_signal));
    }
  }
  json_object_object_add(obj, "replay", replay);
  json_object_object_add(obj, "inputReady", json_object_new_boolean(pss->input_ready));
  const char *json = json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN);
  const int rc = wsi_send_command(pss, SET_SESSION_STATE, json, strlen(json));
  json_object_put(obj);
  return rc;
}

static int send_initial_message(struct pss_tty *pss, int index) {
  const char command = initial_cmds[index];
  if (command == SET_SESSION_STATE) return send_session_state(pss);
  if (command == SET_PREFERENCES)
    return wsi_send_command(pss, command, server->prefs_json, strlen(server->prefs_json));
  if (command != SET_WINDOW_TITLE) return -1;

  char hostname[128] = "";
  gethostname(hostname, sizeof(hostname) - 1);
  hostname[sizeof(hostname) - 1] = '\0';
  const int size = snprintf(NULL, 0, "%s (%s)", server->command, hostname);
  if (size < 0) return -1;
  char *title = xmalloc((size_t)size + 1);
  snprintf(title, (size_t)size + 1, "%s (%s)", server->command, hostname);
  const int rc = wsi_send_command(pss, command, title, (size_t)size);
  free(title);
  return rc;
}

static json_object *parse_window_size(const char *buf, size_t len, uint16_t *cols, uint16_t *rows) {
  json_tokener *tok = json_tokener_new();
  json_object *obj = json_tokener_parse_ex(tok, buf, len);
  json_tokener_free(tok);
  if (obj == NULL) return NULL;

  json_object *value = NULL;
  if (json_object_object_get_ex(obj, "columns", &value)) {
    const int columns = json_object_get_int(value);
    if (columns > 0 && columns <= UINT16_MAX) *cols = (uint16_t)columns;
  }
  if (json_object_object_get_ex(obj, "rows", &value)) {
    const int row_count = json_object_get_int(value);
    if (row_count > 0 && row_count <= UINT16_MAX) *rows = (uint16_t)row_count;
  }
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
    if (session->state != SESSION_STATE_EXITED_RETAINED && session->client != NULL) {
      session->client->lws_close_status = 1000;
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
  if (pss != NULL && pss->initialized && !pss->client_flow_paused && session_output_pending(session, pss))
    schedule_writable(pss);
}
static void session_counts(int *active_count, int *detached_count, int *retained_count, size_t *total_memory) {
  int act = 0, det = 0, ret = 0;
  size_t mem = 0;
  for (struct tty_session *s = session_list; s != NULL; s = s->next) {
    mem += s->output_len;
    if (s->state == SESSION_STATE_EXITED_RETAINED) {
      ret++;
    } else if (s->client != NULL) {
      act++;
    } else {
      det++;
    }
  }
  if (active_count) *active_count = act;
  if (detached_count) *detached_count = det;
  if (retained_count) *retained_count = ret;
  if (total_memory) *total_memory = mem;
}

static bool check_admission_limits(struct pss_tty *pss) {
  (void)pss;
  int active = 0, detached = 0, retained = 0;
  size_t total_mem = 0;
  session_counts(&active, &detached, &retained, &total_mem);

  int max_active = 8;
  const char *env_max = getenv("TTYD_MAX_SESSIONS");
  if (env_max != NULL && atoi(env_max) > 0) max_active = atoi(env_max);
  if (server->max_clients > 0 && server->max_clients < max_active) max_active = server->max_clients;

  size_t max_mem = 64 * 1024 * 1024;
  const char *env_mem = getenv("TTYD_MAX_TOTAL_BUFFER_BYTES");
  if (env_mem != NULL && atol(env_mem) > 0) max_mem = (size_t)atol(env_mem);

  if (active >= max_active) {
    lwsl_warn("admission refused: active sessions %d >= limit %d\n", active, max_active);
    return false;
  }
  if (total_mem + (8 * 1024 * 1024) > max_mem) {
    lwsl_warn("admission refused: total memory %zu + 8MiB > limit %zu\n", total_mem, max_mem);
    return false;
  }
  return true;
}

static void prune_retained_sessions(int max_retained) {
  int retained = 0;
  for (struct tty_session *s = session_list; s != NULL; s = s->next) {
    if (s->state == SESSION_STATE_EXITED_RETAINED) retained++;
  }
  while (retained >= max_retained && max_retained > 0) {
    struct tty_session *oldest = NULL;
    for (struct tty_session *s = session_list; s != NULL; s = s->next) {
      if (s->state == SESSION_STATE_EXITED_RETAINED) {
        if (oldest == NULL || s->exited_at_ms < oldest->exited_at_ms) {
          oldest = s;
        }
      }
    }
    if (oldest == NULL) break;
    lwsl_notice("pruning oldest retained session %llu (exited at %llu) due to max_retained %d\n",
                (unsigned long long)oldest->diagnostic_id, (unsigned long long)oldest->exited_at_ms, max_retained);
    oldest->state = SESSION_STATE_PURGED;
    tombstone_add(oldest, "expired");
    session_release(oldest);
    retained--;
  }
}


static void process_exit_cb(pty_process *process) {
  struct tty_session *session = (struct tty_session *)process->ctx;
  if (session == NULL) return;

  if (process->exit_signal)
    lwsl_notice("process killed with signal %d, pid: %d\n", process->exit_signal, process->pid);
  else
    lwsl_notice("process exited with code %d, pid: %d\n", process->exit_code, process->pid);
  session_diagnostic(session, session->client, "process-exit");
  if (session->pending_contender != NULL) owner_check_finish(session, "exited");

  session->saved_root_pid = process->pid;
  session->exit_code = process->exit_code;
  session->exit_signal = process->exit_signal;
  session->exited_at_ms = monotonic_ms();

  if (session->resumable && session->state != SESSION_STATE_TERMINATING && session->state != SESSION_STATE_PURGED && !session->expiry_recorded) {
    session->state = SESSION_STATE_EXITED_RETAINED;
    int max_retained = 16;
    const char *env_ret = getenv("TTYD_MAX_RETAINED_SESSIONS");
    if (env_ret != NULL && atoi(env_ret) > 0) max_retained = atoi(env_ret);
    prune_retained_sessions(max_retained);

    if (session->client != NULL) {
      struct pss_tty *pss = session->client;
      pss->process = NULL;
      pss->lws_close_status = 1000;
      schedule_writable(pss);
      session->client = NULL;
    }
    if (session->expiry_timer == NULL) {
      session_start_expiry(session);
    }
    session->process = NULL;
    process->ctx = NULL;
  } else if (!session->resumable) {
    session->state = SESSION_STATE_PURGED;
    tombstone_add(session, "exited");
    if (session->client != NULL) {
      struct pss_tty *pss = session->client;
      pss->process = NULL;
      pss->session = NULL;
      pss->lws_close_status = 1000;
      schedule_writable(pss);
    }
    session->client = NULL;
    session->process = NULL;
    process->ctx = NULL;
    session_release(session);
  } else {
    if (session->client != NULL) {
      struct pss_tty *pss = session->client;
      pss->process = NULL;
      pss->lws_close_status = 1000;
      schedule_writable(pss);
      session->client = NULL;
    }
    session->process = NULL;
    process->ctx = NULL;
  }
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

static void prepare_session_response(struct pss_tty *pss, struct tty_session *session, const char *state) {
  pss->takeover_offered = false;
  pss->takeover_pending = false;
  pss->offered_owner_generation = 0;
  pss->session_accepted = true;
  pss->input_ready = false;
  pss->replay_end_sent = false;
  pss->reported_session_id = session->diagnostic_id;
  snprintf(pss->session_state, sizeof(pss->session_state), "%s", state);

  const bool position_valid = pss->requested_position >= session->output_start &&
                              pss->requested_position <= session->output_end;
  pss->replay_start = position_valid ? pss->requested_position : session->output_start;
  pss->send_position = pss->replay_start;
  pss->replay_target = session->output_end;
  pss->replay_lost = session->replay_lost || !position_valid;
}

static void prepare_unattached_response(struct pss_tty *pss, const char *state, uint64_t diagnostic_id) {
  pss->takeover_offered = false;
  pss->takeover_pending = false;
  pss->offered_owner_generation = 0;
  pss->session_accepted = false;
  pss->input_ready = false;
  pss->reported_session_id = diagnostic_id;
  pss->replay_start = 0;
  pss->replay_target = 0;
  pss->replay_lost = false;
  pss->close_after_state = true;
  if (pss->initialized || pss->initial_cmd_index >= (int)sizeof(initial_cmds)) pss->state_update_pending = true;
  snprintf(pss->session_state, sizeof(pss->session_state), "%s", state);
  schedule_writable(pss);
}

static void prepare_conflict_response(struct pss_tty *pss, struct tty_session *session) {
  pss->session_accepted = false;
  pss->input_ready = false;
  pss->reported_session_id = session->diagnostic_id;
  pss->replay_start = 0;
  pss->replay_target = 0;
  pss->replay_lost = false;
  pss->close_after_state = false;
  pss->takeover_offered = true;
  pss->takeover_pending = false;
  pss->offered_owner_generation = session->client->connection_generation;
  if (pss->initialized || pss->initial_cmd_index >= (int)sizeof(initial_cmds)) pss->state_update_pending = true;
  snprintf(pss->session_state, sizeof(pss->session_state), "conflict");
  schedule_writable(pss);
}

static void prepare_displaced_response(struct pss_tty *pss, uint64_t diagnostic_id) {
  pss->session_accepted = false;
  pss->input_ready = false;
  pss->reported_session_id = diagnostic_id;
  pss->replay_start = 0;
  pss->replay_target = 0;
  pss->replay_lost = false;
  pss->takeover_offered = false;
  pss->takeover_pending = false;
  pss->offered_owner_generation = 0;
  pss->close_after_state = true;
  pss->state_update_pending = true;
  snprintf(pss->session_state, sizeof(pss->session_state), "displaced");
  schedule_writable(pss);
}

static void prepare_checking_response(struct pss_tty *pss, struct tty_session *session) {
  pss->session_accepted = false;
  pss->input_ready = false;
  pss->reported_session_id = session->diagnostic_id;
  pss->replay_start = 0;
  pss->replay_target = 0;
  pss->replay_lost = false;
  pss->close_after_state = false;
  snprintf(pss->session_state, sizeof(pss->session_state), "checking");
  schedule_writable(pss);
}

static bool spawn_process(struct pss_tty *pss, uint16_t columns, uint16_t rows) {
  struct tty_session *session = session_create(pss->resume_id, true);
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
  lwsl_notice("started process, pid: %d (resumable)\n", process->pid);
  session->process = process;
  session->saved_root_pid = process->pid;
  session->client = pss;
  pss->session = session;
  pss->process = process;
  prepare_session_response(pss, session, "created");
  session_diagnostic(session, pss, "spawn");
  schedule_writable(pss);
  return true;
}

static bool attach_process(struct pss_tty *pss, struct tty_session *session, uint16_t columns, uint16_t rows) {
  if (session == NULL || session->process == NULL || !process_running(session->process) || session->client != NULL)
    return false;

  session_cancel_expiry(session);
  session->client = pss;
  session->state = SESSION_STATE_ACTIVE;
  pss->session = session;
  pss->process = session->process;
  pss->client_flow_paused = false;

  if (columns > 0) session->process->columns = columns;
  if (rows > 0) session->process->rows = rows;
  pty_resize(session->process);
  pty_signal_foreground(session->process, SIGWINCH);
  prepare_session_response(pss, session, "attached");
  if (pss->initialized || pss->initial_cmd_index >= (int)sizeof(initial_cmds)) pss->state_update_pending = true;
  session_diagnostic(session, pss, "attach");
  schedule_writable(pss);
  return true;
}
static void owner_check_timer_close_cb(uv_handle_t *handle) { free(handle); }

static void owner_check_clear(struct tty_session *session, const char *event) {
  if (session == NULL) return;
  if (session->pending_contender != NULL || session->owner_check_timer != NULL)
    session_diagnostic(session, session->check_owner, event);

  struct pss_tty *contender = session->pending_contender;
  if (contender != NULL && contender->pending_session == session) {
    contender->pending_session = NULL;
    contender->pending_columns = 0;
    contender->pending_rows = 0;
  }

  uv_timer_t *timer = session->owner_check_timer;
  session->pending_contender = NULL;
  session->check_owner = NULL;
  session->owner_check_timer = NULL;
  session->owner_check_sequence = 0;
  session->owner_check_old_generation = 0;
  session->owner_check_deadline_ms = 0;
  session->owner_check_sent = false;
  memset(session->owner_check_nonce, 0, sizeof(session->owner_check_nonce));
  if (timer != NULL) {
    timer->data = NULL;
    uv_timer_stop(timer);
    uv_close((uv_handle_t *)timer, owner_check_timer_close_cb);
  }
}

static void owner_check_finish(struct tty_session *session, const char *state) {
  if (session == NULL || session->pending_contender == NULL) return;
  struct pss_tty *contender = session->pending_contender;
  const uint64_t diagnostic_id = session->diagnostic_id;
  const bool live_conflict = !strcmp(state, "conflict") && session->client != NULL;
  owner_check_clear(session, live_conflict ? "owner-check-live" : "owner-check-finished");
  if (live_conflict)
    prepare_conflict_response(contender, session);
  else
    prepare_unattached_response(contender, state, diagnostic_id);
}

static void owner_check_detach_and_attach(struct tty_session *session, const char *event, bool kill_old) {
  if (session == NULL || session->pending_contender == NULL) return;
  struct pss_tty *old = session->check_owner;
  struct pss_tty *contender = session->pending_contender;
  const uint16_t columns = contender->pending_columns;
  const uint16_t rows = contender->pending_rows;
  session_diagnostic(session, old, event);
  owner_check_clear(session, "owner-check-detach");

  if (old != NULL && session->client == old) {
    old->input_ready = false;
    old->session_accepted = false;
    old->session = NULL;
    old->process = NULL;
    session->client = NULL;
    if (kill_old && old->wsi != NULL)
      lws_set_timeout(old->wsi, PENDING_TIMEOUT_CLOSE_SEND, LWS_TO_KILL_ASYNC);
  }

  if (session->state == SESSION_STATE_EXITED_RETAINED) {
    contender->session = session;
    contender->process = NULL;
    session->client = contender;
    contender->client_flow_paused = false;
    prepare_session_response(contender, session, "exited_retained");
    if (contender->initialized || contender->initial_cmd_index >= (int)sizeof(initial_cmds))
      contender->state_update_pending = true;
    session_diagnostic(session, contender, "retained-attach");
    schedule_writable(contender);
    return;
  }

  if (session->process != NULL && process_running(session->process) &&
      attach_process(contender, session, columns, rows))
    return;

  prepare_unattached_response(contender, "error", session->diagnostic_id);
  if (session->client == NULL && session->resumable && session->process != NULL && process_running(session->process))
    session_start_expiry(session);
}

static void owner_check_timer_cb(uv_timer_t *timer) {
  struct tty_session *session = (struct tty_session *)timer->data;
  if (session == NULL || session->owner_check_timer != timer || session->pending_contender == NULL) return;
  const uint64_t now = monotonic_ms();
  if (now < session->owner_check_deadline_ms) {
    if (uv_timer_start(timer, owner_check_timer_cb, session->owner_check_deadline_ms - now, 0) != 0)
      owner_check_finish(session, "error");
    return;
  }
  if (!session->owner_check_sent) {
    owner_check_finish(session, "error");
    return;
  }
  if (session->client != session->check_owner || session->check_owner == NULL ||
      session->check_owner->connection_generation != session->owner_check_old_generation) {
    owner_check_finish(session, "error");
    return;
  }
  owner_check_detach_and_attach(session, "owner-check-timeout", true);
}

static bool owner_check_begin(struct pss_tty *contender, struct tty_session *session, uint16_t columns,
                              uint16_t rows) {
  if (session->pending_contender != NULL) {
    prepare_unattached_response(contender, "error", session->diagnostic_id);
    session_diagnostic(session, contender, "owner-check-third-contender");
    return false;
  }

  uv_timer_t *timer = xmalloc(sizeof(uv_timer_t));
  if (uv_timer_init(server->loop, timer) != 0) {
    free(timer);
    prepare_unattached_response(contender, "error", session->diagnostic_id);
    session_diagnostic(session, contender, "owner-check-timer-init-failed");
    return false;
  }

  session->pending_contender = contender;
  session->check_owner = session->client;
  session->owner_check_timer = timer;
  session->owner_check_sequence = ++next_owner_check_sequence;
  session->owner_check_old_generation = session->client->connection_generation;
  session->owner_check_deadline_ms = monotonic_ms() + OWNER_CHECK_PREPARE_MS;
  session->owner_check_sent = false;
  for (int i = 0; i < 8; i++) {
    session->owner_check_nonce[i] = (unsigned char)(session->owner_check_sequence >> (56 - i * 8));
    session->owner_check_nonce[8 + i] = (unsigned char)(session->owner_check_old_generation >> (56 - i * 8));
  }
  contender->pending_session = session;
  contender->pending_columns = columns;
  contender->pending_rows = rows;
  timer->data = session;
  if (uv_timer_start(timer, owner_check_timer_cb, OWNER_CHECK_PREPARE_MS, 0) != 0) {
    owner_check_finish(session, "error");
    return false;
  }

  prepare_checking_response(contender, session);
  session_diagnostic(session, session->client, "owner-check-queued");
  schedule_writable(session->client);
  return true;
}

static int owner_check_send_ping(struct pss_tty *owner) {
  struct tty_session *session = owner->session;
  if (session == NULL || session->client != owner || session->check_owner != owner ||
      session->pending_contender == NULL || session->owner_check_sent)
    return 0;

  unsigned char message[LWS_PRE + OWNER_CHECK_NONCE_LENGTH];
  unsigned char *payload = message + LWS_PRE;
  memcpy(payload, session->owner_check_nonce, OWNER_CHECK_NONCE_LENGTH);
  const int written = lws_write(owner->wsi, payload, OWNER_CHECK_NONCE_LENGTH, LWS_WRITE_PING);
  if (written < OWNER_CHECK_NONCE_LENGTH) {
    lwsl_warn("owner check Ping write returned %d, expected at least %d\n", written, OWNER_CHECK_NONCE_LENGTH);
    session_diagnostic(session, owner, "owner-check-send-failed");
    owner_check_finish(session, "error");
    return -1;
  }

  session->owner_check_sent = true;
  session->owner_check_deadline_ms = monotonic_ms() + OWNER_CHECK_PONG_MS;
  uv_timer_stop(session->owner_check_timer);
  if (uv_timer_start(session->owner_check_timer, owner_check_timer_cb, OWNER_CHECK_PONG_MS, 0) != 0) {
    owner_check_finish(session, "error");
    return 1;
  }
  session_diagnostic(session, owner, "owner-check-sent");
  return 1;
}

static void owner_check_receive_pong(struct pss_tty *owner, const void *payload, size_t len) {
  struct tty_session *session = owner->session;
  if (session == NULL || session->client != owner || session->check_owner != owner ||
      session->pending_contender == NULL || !session->owner_check_sent ||
      owner->connection_generation != session->owner_check_old_generation || len != OWNER_CHECK_NONCE_LENGTH ||
      memcmp(payload, session->owner_check_nonce, OWNER_CHECK_NONCE_LENGTH) != 0)
    return;
  if (monotonic_ms() >= session->owner_check_deadline_ms) {
    session_diagnostic(session, owner, "owner-check-late-pong");
    return;
  }
  owner_check_finish(session, "conflict");
}

static void wsi_output_data(struct pss_tty *pss, const char *data, size_t len) {
  if (pss == NULL || data == NULL || len == 0) return;
  const uint64_t end_position = pss->send_position + len;
  unsigned char *message = xmalloc(LWS_PRE + 9 + len);
  unsigned char *ptr = message + LWS_PRE;
  ptr[0] = OUTPUT;
  for (int i = 0; i < 8; i++) ptr[1 + i] = (unsigned char)(end_position >> (56 - i * 8));
  memcpy(ptr + 9, data, len);
  const size_t size = 9 + len;
  if (lws_write(pss->wsi, ptr, size, LWS_WRITE_BINARY) < (int)size) {
    lwsl_err("write OUTPUT to WS\n");
  } else if (pss->session != NULL) {
    pss->session->ws_output_bytes += len;
  }
  free(message);
}

static int send_replay_end(struct pss_tty *pss) {
  json_object *obj = json_object_new_object();
  json_object_object_add(obj, "version", json_object_new_int(SESSION_PROTOCOL_VERSION));
  json_object_object_add(obj, "position", json_object_new_int64((int64_t)pss->replay_target));
  json_object_object_add(obj, "truncated", json_object_new_boolean(pss->replay_lost));
  if (pss->session != NULL && pss->session->state == SESSION_STATE_EXITED_RETAINED) {
    json_object_object_add(obj, "exitCode", json_object_new_int(pss->session->exit_code));
    json_object_object_add(obj, "exitSignal", json_object_new_int(pss->session->exit_signal));
  }
  const char *json = json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN);
  const int rc = wsi_send_command(pss, REPLAY_END, json, strlen(json));
  json_object_put(obj);
  return rc;
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
      pss->pending_session = NULL;
      pss->pending_columns = 0;
      pss->pending_rows = 0;
      pss->session_accepted = false;
      pss->input_ready = false;
      pss->replay_end_sent = false;
      pss->client_flow_paused = false;
      pss->writable_pending = false;
      pss->heartbeat_pending = false;
      pss->close_after_state = false;
      pss->handshake_received = false;
      pss->state_update_pending = false;
      pss->takeover_offered = false;
      pss->takeover_pending = false;
      pss->requested_position = 0;
      pss->send_position = 0;
      pss->replay_target = 0;
      pss->reported_session_id = 0;
      pss->offered_owner_generation = 0;
      pss->replay_start = 0;
      pss->replay_lost = false;
      pss->heartbeat_len = 0;
      snprintf(pss->session_state, sizeof(pss->session_state), "error");
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

    case LWS_CALLBACK_SERVER_WRITEABLE: {
      pss->writable_pending = false;
      if (pss->lws_close_status > LWS_CLOSE_STATUS_NOSTATUS) {
        lws_close_reason(wsi, pss->lws_close_status, NULL, 0);
        return 1;
      }
      int owner_check_write = owner_check_send_ping(pss);
      if (owner_check_write < 0) return -1;
      if (owner_check_write > 0) break;


      if (!pss->initialized) {
        if (pss->initial_cmd_index == sizeof(initial_cmds)) {
          pss->initialized = true;
          if (pss->close_after_state && !pss->state_update_pending) {
            lws_close_reason(wsi, LWS_CLOSE_STATUS_NORMAL, NULL, 0);
            return 1;
          }
          schedule_writable(pss);
          session_diagnostic(pss->session, pss, "initialized");
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

      if (pss->heartbeat_pending) {
        wsi_send_command(pss, HEARTBEAT_REPLY, pss->heartbeat, pss->heartbeat_len);
        pss->heartbeat_pending = false;
        if (pss->session != NULL) schedule_writable(pss);
        break;
      }

      if (pss->state_update_pending) {
        if (send_session_state(pss) < 0) return -1;
        pss->state_update_pending = false;
        if (pss->close_after_state) {
          lws_close_reason(wsi, LWS_CLOSE_STATUS_NORMAL, NULL, 0);
          return 1;
        }
        if (pss->session != NULL) schedule_writable(pss);
        break;
      }

      struct tty_session *session = pss->session;
      if (session == NULL || session->client != pss) break;
      if (!pss->replay_end_sent && !session_output_pending(session, pss)) {
        if (send_replay_end(pss) < 0) return -1;
        pss->replay_end_sent = true;
        session_diagnostic(session, pss, "replay-end");
        break;
      }
      if (pss->client_flow_paused || !session_output_pending(session, pss)) break;

      const uint64_t limit = pss->input_ready ? session->output_end : pss->replay_target;
      const uint64_t remaining = limit - pss->send_position;
      const size_t chunk = remaining > SESSION_REPLAY_CHUNK ? SESSION_REPLAY_CHUNK : (size_t)remaining;
      const size_t offset = (size_t)(pss->send_position - session->output_start);
      wsi_output_data(pss, session->output_buf + offset, chunk);
      pss->send_position += chunk;
      schedule_writable(pss);
      break;
    }

    case LWS_CALLBACK_RECEIVE_PONG:
      owner_check_receive_pong(pss, in, len);
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
          if (!server->writable || !pss->input_ready || pss->session == NULL || pss->session->client != pss ||
              pss->process == NULL || pss->session->state == SESSION_STATE_EXITED_RETAINED)
            break;
          const size_t input_len = pss->len - 1;
          int err = pty_write(pss->process, pty_buf_init(pss->buffer + 1, input_len));
          if (err) {
            lwsl_err("uv_write: %s (%s)\n", uv_err_name(err), uv_strerror(err));
            return -1;
          }
          pss->session->pty_write_count++;
          pss->session->ws_input_bytes += input_len;
          break;
        }
        case RESIZE_TERMINAL: {
          if (!pss->input_ready || pss->session == NULL || pss->session->client != pss || pss->process == NULL ||
              pss->session->state == SESSION_STATE_EXITED_RETAINED)
            break;
          uint16_t columns = pss->process->columns;
          uint16_t rows = pss->process->rows;
          json_object *obj = parse_window_size(pss->buffer + 1, pss->len - 1, &columns, &rows);
          if (obj != NULL && columns > 0 && rows > 0) {
            pss->process->columns = columns;
            pss->process->rows = rows;
            pty_resize(pss->process);
            pty_signal_foreground(pss->process, SIGWINCH);
          }
          if (obj != NULL) json_object_put(obj);
          break;
        }
        case PAUSE:
          if (pss->session != NULL && pss->session->client == pss) {
            pss->client_flow_paused = true;
            session_diagnostic(pss->session, pss, "client-pause");
          }
          break;
        case RESUME:
          if (pss->session != NULL && pss->session->client == pss) {
            pss->client_flow_paused = false;
            schedule_writable(pss);
            session_diagnostic(pss->session, pss, "client-resume");
          }
          break;
        case HEARTBEAT:
          if (pss->initialized && pss->len > 1 && pss->len - 1 <= sizeof(pss->heartbeat)) {
            pss->heartbeat_len = pss->len - 1;
            memcpy(pss->heartbeat, pss->buffer + 1, pss->heartbeat_len);
            pss->heartbeat_pending = true;
            schedule_writable(pss);
          }
          break;
        case SESSION_READY: {
          if (!pss->replay_end_sent || pss->session == NULL || pss->session->client != pss) break;
          if (pss->session->state == SESSION_STATE_EXITED_RETAINED) {
            break;
          }
          json_tokener *tokener = json_tokener_new();
          json_object *obj = json_tokener_parse_ex(tokener, pss->buffer + 1, pss->len - 1);
          json_object *position_obj = NULL;
          const bool valid = obj != NULL && json_object_object_get_ex(obj, "position", &position_obj) &&
                             json_object_get_int64(position_obj) >= 0 &&
                             (uint64_t)json_object_get_int64(position_obj) == pss->replay_target;
          json_tokener_free(tokener);
          if (obj != NULL) json_object_put(obj);
          if (!valid) break;
          pss->input_ready = true;
          pss->state_update_pending = true;
          schedule_writable(pss);
          session_diagnostic(pss->session, pss, "input-ready");
          break;
        }
        case TAKEOVER: {
          if (!pss->handshake_received || !pss->takeover_offered || pss->takeover_pending ||
              pss->session_accepted)
            break;

          pss->takeover_pending = true;
          uint16_t columns = 0;
          uint16_t rows = 0;
          json_object *obj = parse_window_size(pss->buffer + 1, pss->len - 1, &columns, &rows);
          json_object *owner_obj = NULL;
          const bool valid = obj != NULL && json_object_object_get_ex(obj, "ownerGeneration", &owner_obj) &&
                             json_object_get_int64(owner_obj) > 0 && columns > 0 && rows > 0;
          const uint64_t requested_owner =
              valid ? (uint64_t)json_object_get_int64(owner_obj) : 0;
          struct tty_session *session = session_find(pss->resume_id);

          if (!valid || session == NULL || session->diagnostic_id != pss->reported_session_id) {
            struct session_tombstone *tombstone = session == NULL ? tombstone_find(pss->resume_id) : NULL;
            prepare_unattached_response(pss, tombstone == NULL ? "unknown" : tombstone->reason,
                                        tombstone == NULL ? 0 : tombstone->diagnostic_id);
          } else if (session->state == SESSION_STATE_TERMINATING || session->state == SESSION_STATE_PURGED) {
            prepare_unattached_response(pss, "expired", session->diagnostic_id);
          } else if (session->state == SESSION_STATE_EXITED_RETAINED) {
            if (session->client == NULL) {
              prepare_unattached_response(pss, "stale", session->diagnostic_id);
            } else if (requested_owner != pss->offered_owner_generation ||
                       requested_owner != session->client->connection_generation) {
              prepare_conflict_response(pss, session);
            } else {
              struct pss_tty *old = session->client;
              struct pss_tty *competing = session->pending_contender;
              if (competing != NULL) owner_check_clear(session, "takeover-settle-contender");

              old->input_ready = false;
              old->session_accepted = false;
              old->session = NULL;
              old->process = NULL;
              session->client = NULL;
              prepare_displaced_response(old, session->diagnostic_id);

              pss->session = session;
              pss->process = NULL;
              session->client = pss;
              pss->client_flow_paused = false;
              prepare_session_response(pss, session, "exited_retained");
              if (pss->initialized || pss->initial_cmd_index >= (int)sizeof(initial_cmds))
                pss->state_update_pending = true;
              session_diagnostic(session, pss, "retained-takeover");
              schedule_writable(pss);
            }
          } else if (session->process == NULL || !process_running(session->process)) {
            tombstone_add(session, "exited");
            prepare_unattached_response(pss, "exited", session->diagnostic_id);
          } else if (session->client == NULL) {
            prepare_unattached_response(pss, "stale", session->diagnostic_id);
          } else if (requested_owner != pss->offered_owner_generation ||
                     requested_owner != session->client->connection_generation) {
            prepare_conflict_response(pss, session);
          } else {
            struct pss_tty *old = session->client;
            struct pss_tty *competing = session->pending_contender;
            if (competing != NULL) owner_check_clear(session, "takeover-settle-contender");

            old->input_ready = false;
            old->session_accepted = false;
            old->session = NULL;
            old->process = NULL;
            session->client = NULL;
            prepare_displaced_response(old, session->diagnostic_id);

            if (!attach_process(pss, session, columns, rows)) {
              prepare_unattached_response(pss, "error", session->diagnostic_id);
              if (session->client == NULL && session->resumable && session->process != NULL &&
                  process_running(session->process))
                session_start_expiry(session);
            } else if (competing != NULL && competing != pss && competing->wsi != NULL) {
              prepare_conflict_response(competing, session);
            }
            session_diagnostic(session, pss, "takeover");
          }
          if (obj != NULL) json_object_put(obj);
          break;
        }
        case JSON_DATA: {
          if (pss->handshake_received) break;
          pss->handshake_received = true;
          uint16_t columns = 0;
          uint16_t rows = 0;
          json_object *obj = parse_window_size(pss->buffer, pss->len, &columns, &rows);
          json_object *version_obj = NULL;
          json_object *intent_obj = NULL;
          json_object *position_obj = NULL;
          const char *intent = NULL;
          bool valid = obj != NULL && resume_id_valid(pss->resume_id) &&
                       json_object_object_get_ex(obj, "version", &version_obj) &&
                       json_object_get_int(version_obj) == SESSION_PROTOCOL_VERSION &&
                       json_object_object_get_ex(obj, "intent", &intent_obj) &&
                       (intent = json_object_get_string(intent_obj)) != NULL &&
                       (!strcmp(intent, "create") || !strcmp(intent, "resume")) &&
                       json_object_object_get_ex(obj, "replayPosition", &position_obj) &&
                       json_object_get_int64(position_obj) >= 0;

          if (server->credential != NULL) {
            json_object *auth_obj = NULL;
            const char *token = obj != NULL && json_object_object_get_ex(obj, "AuthToken", &auth_obj)
                                    ? json_object_get_string(auth_obj)
                                    : NULL;
            pss->authenticated = token != NULL && !strcmp(token, server->credential);
            valid = valid && pss->authenticated;
          }

          if (!valid) {
            if (obj != NULL) json_object_put(obj);
            prepare_unattached_response(pss, "error", 0);
            break;
          }

          pss->requested_position = (uint64_t)json_object_get_int64(position_obj);
          struct tty_session *session = session_find(pss->resume_id);
          struct session_tombstone *tombstone = session == NULL ? tombstone_find(pss->resume_id) : NULL;

          if (session != NULL && session->state == SESSION_STATE_EXITED_RETAINED) {
            if (session->client != NULL) {
              owner_check_begin(pss, session, columns, rows);
            } else {
              pss->session = session;
              pss->process = NULL;
              session->client = pss;
              pss->client_flow_paused = false;
              prepare_session_response(pss, session, "exited_retained");
              if (pss->initialized || pss->initial_cmd_index >= (int)sizeof(initial_cmds))
                pss->state_update_pending = true;
              session_diagnostic(session, pss, "retained-attach");
              schedule_writable(pss);
            }
          } else if (session != NULL && (session->state == SESSION_STATE_TERMINATING || session->state == SESSION_STATE_PURGED)) {
            prepare_unattached_response(pss, "expired", session->diagnostic_id);
          } else if (session != NULL && (session->process == NULL || !process_running(session->process))) {
            tombstone_add(session, "exited");
            prepare_unattached_response(pss, "exited", session->diagnostic_id);
          } else if (session != NULL && session->client != NULL) {
            owner_check_begin(pss, session, columns, rows);
          } else if (session != NULL) {
            if (!attach_process(pss, session, columns, rows)) prepare_unattached_response(pss, "error", 0);
          } else if (tombstone != NULL) {
            prepare_unattached_response(pss, tombstone->reason, tombstone->diagnostic_id);
          } else if (!strcmp(intent, "create")) {
            if (!check_admission_limits(pss)) {
              prepare_unattached_response(pss, "rejected_capacity", 0);
            } else if (!spawn_process(pss, columns, rows)) {
              prepare_unattached_response(pss, "error", 0);
            }
          } else {
            prepare_unattached_response(pss, "unknown", 0);
          }
          json_object_put(obj);
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

    case LWS_CALLBACK_CLOSED: {
      if (pss->wsi == NULL) break;

      server->client_count--;
      lwsl_notice("WS closed from %s, clients: %d\n", pss->address, server->client_count);
      if (pss->buffer != NULL) free(pss->buffer);
      for (int i = 0; i < pss->argc; i++) free(pss->args[i]);

      if (pss->pending_session != NULL && pss->pending_session->pending_contender == pss) {
        struct tty_session *pending_session = pss->pending_session;
        session_diagnostic(pending_session, pss, "owner-check-contender-close");
        owner_check_clear(pending_session, "owner-check-cancelled");
      }

      struct tty_session *closed_session = pss->session;
      session_diagnostic(closed_session, pss, "connection-close");
      if (closed_session != NULL && closed_session->pending_contender != NULL &&
          closed_session->check_owner == pss && closed_session->client == pss) {
        owner_check_detach_and_attach(closed_session, "owner-check-old-close", false);
      }

      if (closed_session != NULL && closed_session->client == pss) {
        closed_session->client = NULL;
        pty_process *process = pss->process;
        pss->session = NULL;
        pss->process = NULL;

        if (closed_session->state == SESSION_STATE_EXITED_RETAINED) {
          if (closed_session->expiry_timer == NULL) {
            session_start_expiry(closed_session);
          }
          lwsl_notice("detached viewer from exited_retained session\n");
        } else if (closed_session->resumable && process != NULL && process_running(process)) {
          closed_session->state = SESSION_STATE_DETACHED_GRACE;
          session_start_expiry(closed_session);
          lwsl_notice("detached resumable process, pid: %d\n", process->pid);
        } else if (process != NULL && process_running(process)) {
          lwsl_notice("killing process, pid: %d\n", process->pid);
          session_reap_tree(closed_session, get_reap_grace_ms());
        }
      }
      pss->wsi = NULL;

      if ((server->once || server->exit_no_conn) && server->client_count == 0) {
        lwsl_notice("exiting due to the --once/--exit-no-conn option.\n");
        force_exit = true;
        lws_cancel_service(context);
        exit(0);
      }
      break;
    }

    case LWS_CALLBACK_PROTOCOL_DESTROY:
      for (struct tty_session *session = session_list; session != NULL; session = session->next) {
        owner_check_clear(session, "owner-check-shutdown");
        pid_t root_pid = session->process != NULL ? session->process->pid : session->saved_root_pid;
        if (root_pid > 1) {
          pid_t fg_pgid = pty_get_fg_pgid(session->process);
          proc_ident_t *idents = NULL;
          size_t count = 0;
          pty_get_process_tree_idents(root_pid, fg_pgid, &idents, &count);
          for (size_t i = 0; i < count; i++) {
            if (pty_proc_ident_alive(&idents[i])) {
              kill(idents[i].pid, SIGHUP);
              if (idents[i].pgrp > 1) kill(-idents[i].pgrp, SIGHUP);
            }
          }
          usleep(50000);
          for (size_t i = 0; i < count; i++) {
            if (pty_proc_ident_alive(&idents[i])) {
              kill(idents[i].pid, SIGKILL);
              if (idents[i].pgrp > 1) kill(-idents[i].pgrp, SIGKILL);
            }
          }
          free(idents);
        }
      }
      break;
    default:
      break;
  }

  return 0;
}
