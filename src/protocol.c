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

#define SESSION_REPLAY_CHUNK OUTPUT_CHUNK_SIZE
#define SESSION_GRACE_MAX_SECONDS (9 * 60 * 60)
#define SESSION_GRACE_DEFAULT_MS (SESSION_GRACE_MAX_SECONDS * 1000ULL)
#define SESSION_TOMBSTONE_MAX 256
#define SESSION_TOMBSTONE_MAX_AGE_MS SESSION_GRACE_DEFAULT_MS
#define JSON_SAFE_INTEGER_MAX 9007199254740991ULL
#define SESSION_REAPER_MAX_RETRIES 5
#define SESSION_REAPER_RETRY_BASE_MS 200ULL
#define SESSION_REAPER_QUARANTINE_MS 5000ULL

struct approval_record {
  enum approval_kind kind;
  char client_instance_id[CLIENT_INSTANCE_ID_LENGTH + 1];
  uint64_t connect_sequence;
  uint64_t lease_epoch;
  uint8_t credential_hash[SUCCESSOR_TOKEN_BYTES];
  bool has_credential_hash;
};
struct output_chunk {
  unsigned char *data;
};

struct output_ring {
  struct output_chunk chunks[OUTPUT_CHUNK_COUNT];
  uint64_t start;
  uint64_t end;
  size_t allocated_chunks;
};

enum output_send_disposition { OUTPUT_SEND_NONE = 0, OUTPUT_SEND_DATA, OUTPUT_SEND_GAP };

struct tty_session {
  char id[SESSION_ID_LENGTH + 1];
  bool resumable;
  pty_process *process;
  struct pss_tty *client;
  uv_timer_t *expiry_timer;
  uv_timer_t *ready_deadline_timer;
  uint64_t ready_deadline_lease_epoch;
  uint64_t lease_epoch;
  char owner_client_instance_id[CLIENT_INSTANCE_ID_LENGTH + 1];
  uint64_t owner_connect_sequence;
  uint8_t successor_token_hash[SUCCESSOR_TOKEN_BYTES];
  bool successor_token_valid;
  enum owner_phase owner_phase;
  uint64_t last_application_heartbeat_ms;
  uint64_t last_progress_at_ms;
  uint64_t owner_started_at_ms;
  struct approval_record last_approval;
  struct output_ring output;
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
  unsigned ref_count;
  bool registry_ref;
  bool process_ref;
  bool viewer_ref;
  bool reaper_ref;
  bool process_exit_active;
  bool pty_eof_observed;
  bool root_exit_observed;
  bool exit_status_known;
  bool reap_failed;
  bool process_tree_reaped;
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
static bool attach_process(struct pss_tty *pss, struct tty_session *session, uint16_t columns, uint16_t rows);
static void ready_deadline_cancel(struct tty_session *session);
static void session_maybe_finalize_exit(struct tty_session *session, pty_process *process);
static void fence_owner(struct tty_session *session, struct pss_tty *old, const char *state);
static void session_maybe_complete_purge(struct tty_session *session);
static void queue_nack(struct pss_tty *pss, const char *code, const char *detail,
                       uint64_t expected, uint64_t received);
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
  const uint64_t sent = pss == NULL ? session->output.start : pss->send_position;
  const uint64_t pending = session->output.end > sent ? session->output.end - sent : 0;
  const unsigned long long lease = (unsigned long long)session->lease_epoch;
  lwsl_notice(
      "diag event=%s monotonic_ms=%llu session=%llu connection=%llu pid=%d initialized=%d accepted=%d "
      "input_ready=%d client_paused=%d pty_paused=%d output=%llu/%llu pending_output=%llu replay_lost=%d "
      "reads=%llu zero_reads=%llu pty_output_bytes=%llu writes=%llu ws_input_bytes=%llu "
      "ws_output_bytes=%llu dropped_output_bytes=%llu lease_epoch=%llu owner_phase=%d connect_sequence=%llu\n",
      event, (unsigned long long)(uv_hrtime() / 1000000ULL), (unsigned long long)session->diagnostic_id, connection,
      pid, pss != NULL && pss->initialized, pss != NULL && pss->session_accepted, pss != NULL && pss->input_ready,
      pss != NULL && pss->client_flow_paused, session->process != NULL && session->process->paused,
      (unsigned long long)sent, (unsigned long long)session->output.end, (unsigned long long)pending,
      session->replay_lost, (unsigned long long)session->pty_read_count,
      (unsigned long long)session->pty_zero_read_count, (unsigned long long)session->pty_output_bytes,
      (unsigned long long)session->pty_write_count, (unsigned long long)session->ws_input_bytes,
      (unsigned long long)session->ws_output_bytes, (unsigned long long)session->dropped_output_bytes, lease,
      (int)session->owner_phase, (unsigned long long)(pss == NULL ? 0 : pss->connect_sequence));
}

static enum output_send_disposition session_output_disposition(const struct tty_session *session,
                                                               const struct pss_tty *pss) {
  if (session == NULL || pss == NULL) return OUTPUT_SEND_NONE;
  if (pss->send_position < session->output.start) return OUTPUT_SEND_GAP;
  const uint64_t limit = pss->input_ready ? session->output.end : pss->replay_target;
  return pss->send_position < limit ? OUTPUT_SEND_DATA : OUTPUT_SEND_NONE;
}

static unsigned char *output_ring_slot(struct output_ring *ring, uint64_t position, bool allocate) {
  const size_t index = (size_t)((position % OUTPUT_CAPACITY) / OUTPUT_CHUNK_SIZE);
  if (ring->chunks[index].data == NULL && allocate) {
    ring->chunks[index].data = xmalloc(OUTPUT_CHUNK_SIZE);
    ring->allocated_chunks++;
  }
  return ring->chunks[index].data;
}

static void output_ring_append(struct output_ring *ring, const unsigned char *data, size_t len) {
  if (len == 0 || ring->end > UINT64_MAX - len) return;
  if (len > OUTPUT_CAPACITY) {
    data += len - OUTPUT_CAPACITY;
    len = OUTPUT_CAPACITY;
  }
  const uint64_t new_end = ring->end + len;
  size_t copied = 0;
  while (copied < len) {
    const uint64_t position = ring->end + copied;
    const size_t offset = (size_t)(position % OUTPUT_CHUNK_SIZE);
    const size_t count = len - copied < OUTPUT_CHUNK_SIZE - offset ? len - copied : OUTPUT_CHUNK_SIZE - offset;
    memcpy(output_ring_slot(ring, position, true) + offset, data + copied, count);
    copied += count;
  }
  ring->end = new_end;
  if (ring->end - ring->start > OUTPUT_CAPACITY) ring->start = ring->end - OUTPUT_CAPACITY;
}

static size_t output_ring_copy(const struct output_ring *ring, uint64_t position, unsigned char *dst, size_t max) {
  if (position < ring->start || position >= ring->end || max == 0) return 0;
  uint64_t available64 = ring->end - position;
  size_t available = available64 > max ? max : (size_t)available64;
  size_t copied = 0;
  while (copied < available) {
    const uint64_t current = position + copied;
    const size_t index = (size_t)((current % OUTPUT_CAPACITY) / OUTPUT_CHUNK_SIZE);
    const size_t offset = (size_t)(current % OUTPUT_CHUNK_SIZE);
    const size_t count = available - copied < OUTPUT_CHUNK_SIZE - offset ? available - copied : OUTPUT_CHUNK_SIZE - offset;
    if (ring->chunks[index].data == NULL) break;
    memcpy(dst + copied, ring->chunks[index].data + offset, count);
    copied += count;
  }
  return copied;
}

static void output_ring_destroy(struct output_ring *ring) {
  for (size_t i = 0; i < OUTPUT_CHUNK_COUNT; i++) free(ring->chunks[i].data);
  memset(ring, 0, sizeof(*ring));
}

static void session_output_append(struct tty_session *session, const char *data, size_t len) {
  if (session == NULL || data == NULL || len == 0 || session->output.end > UINT64_MAX - len) return;
  const uint64_t old_start = session->output.start;
  output_ring_append(&session->output, (const unsigned char *)data, len);
  if (session->output.start > old_start) {
    session->dropped_output_bytes += session->output.start - old_start;
    session->replay_lost = true;
    session->truncated = true;
  }
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
  if (!session->registry_ref) return;
  if (session->resumable) {
    struct tty_session **cursor = &session_list;
    while (*cursor != NULL) {
      if (*cursor == session) {
        *cursor = session->next;
        break;
      }
      cursor = &(*cursor)->next;
    }
  }
  session->registry_ref = false;
}

static void session_ref(struct tty_session *session) {
  if (session != NULL) session->ref_count++;
}

static void session_unref(struct tty_session *session) {
  if (session == NULL || session->ref_count == 0) return;
  if (--session->ref_count != 0) return;
  output_ring_destroy(&session->output);
  free(session);
}

static void session_viewer_attach(struct tty_session *session, struct pss_tty *pss) {
  if (session == NULL || pss == NULL || pss->session_ref_held) return;
  session_ref(session);
  session->viewer_ref = true;
  pss->session_ref_held = true;
}

static void session_viewer_detach(struct tty_session *session, struct pss_tty *pss) {
  if (session == NULL || pss == NULL || !pss->session_ref_held) return;
  pss->session_ref_held = false;
  session->viewer_ref = false;
  session_unref(session);
}
static void session_drop_registry(struct tty_session *session) {
  if (session == NULL || !session->registry_ref) return;
  session_diagnostic(session, session->client, "registry-release");
  session_unlink(session);
  session_unref(session);
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

static void session_destroy_requested(struct tty_session *session) {
  if (session == NULL) return;
  session_cancel_expiry(session);
  ready_deadline_cancel(session);
  session_drop_registry(session);
}
static void session_maybe_complete_purge(struct tty_session *session) {
  if (session == NULL || session->state != SESSION_STATE_TERMINATING || !session->process_tree_reaped ||
      !session->root_exit_observed || !session->pty_eof_observed || session->process != NULL ||
      session->process_ref || session->client != NULL || session->viewer_ref || session->expiry_timer != NULL ||
      session->ready_deadline_timer != NULL || session->reaper_ref)
    return;
  session->state = SESSION_STATE_PURGED;
  lwsl_notice("session lifecycle complete: transitioned to PURGED\n");
  session_drop_registry(session);
}

static struct tty_session *session_create(const char *id, bool resumable) {
  struct tty_session *session = xmalloc(sizeof(struct tty_session));
  memset(session, 0, sizeof(struct tty_session));
  session->diagnostic_id = ++next_session_diagnostic_id;
  session->resumable = resumable;
  session->state = SESSION_STATE_ACTIVE;
  session->ref_count = 1;
  session->registry_ref = true;
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
  unsigned retries;
  proc_ident_t *idents;
  size_t idents_count;
};

static void session_reaper_close_cb(uv_handle_t *handle) {
  struct session_reaper *reaper = container_of((uv_timer_t *)handle, struct session_reaper, timer);
  struct tty_session *session = reaper->session;
  free(reaper->idents);
  if (session != NULL) {
    session_ref(session);
    session->reaper_ref = false;
    session_unref(session);
    session_maybe_complete_purge(session);
    session_unref(session);
  }
  free(reaper);
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

    reaper->step = 2;
    if (any_alive) {
      if (uv_timer_start(timer, session_reaper_timer_cb, SESSION_REAPER_RETRY_BASE_MS, 0) == 0) return;
      reaper->session->reap_failed = true;
      lwsl_err("failed to schedule process tree reap verification: pid %d\n", reaper->root_pid);
      uv_close((uv_handle_t *)timer, session_reaper_close_cb);
      return;
    }
  }

  const bool remaining_alive = pty_tree_idents_alive(reaper->idents, reaper->idents_count);
  if (remaining_alive) {
    reaper->session->state = SESSION_STATE_TERMINATING;
    uint64_t delay = SESSION_REAPER_QUARANTINE_MS;
    if (reaper->retries < SESSION_REAPER_MAX_RETRIES) {
      reaper->retries++;
      delay = SESSION_REAPER_RETRY_BASE_MS << reaper->retries;
      if (delay > SESSION_REAPER_QUARANTINE_MS) delay = SESSION_REAPER_QUARANTINE_MS;
    } else if (!reaper->session->reap_failed) {
      reaper->session->reap_failed = true;
      lwsl_err("process tree reap delayed: pid %d moved to quarantine checks\n", reaper->root_pid);
    }
    if (uv_timer_start(timer, session_reaper_timer_cb, delay, 0) == 0) return;
    reaper->session->reap_failed = true;
    lwsl_err("failed to schedule process tree quarantine check: pid %d\n", reaper->root_pid);
  } else {
    reaper->session->reap_failed = false;
    reaper->session->process_tree_reaped = true;
    lwsl_notice("process tree reaped completely: pid %d awaiting lifecycle completion\n", reaper->root_pid);
  }

  uv_timer_stop(timer);
  uv_close((uv_handle_t *)timer, session_reaper_close_cb);
}

static void session_reap_tree(struct tty_session *session, uint64_t grace_ms) {
  if (session == NULL) return;
  pid_t root_pid = session->process != NULL ? session->process->pid : session->saved_root_pid;
  session->state = SESSION_STATE_TERMINATING;

  if (root_pid <= 1) {
    session->process_tree_reaped = true;
    session_maybe_complete_purge(session);
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
    session->reap_failed = true;
    session->state = SESSION_STATE_TERMINATING;
    return;
  }
  reaper->timer.data = reaper;
  session_ref(session);
  session->reaper_ref = true;
  if (uv_timer_start(&reaper->timer, session_reaper_timer_cb, grace_ms, 0) != 0) {
    session->reap_failed = true;
    session->state = SESSION_STATE_TERMINATING;
    uv_close((uv_handle_t *)&reaper->timer, session_reaper_close_cb);
  }
}

static void session_expire_cb(uv_timer_t *timer) {
  struct tty_session *session = (struct tty_session *)timer->data;
  if (session == NULL) return;
  session->expiry_timer = NULL;
  timer->data = NULL;
  uv_timer_stop(timer);
  uv_close((uv_handle_t *)timer, expiry_timer_close_cb);

  session->expiry_recorded = true;
  session->state = SESSION_STATE_TERMINATING;
  tombstone_add(session, "expired");
  if (session->client != NULL) fence_owner(session, session->client, "expired");

  const uint64_t reap_grace = get_reap_grace_ms();
  session_reap_tree(session, reap_grace);
}

static void session_start_expiry(struct tty_session *session) {
  if (session->expiry_timer != NULL) return;
  uv_timer_t *timer = xmalloc(sizeof(uv_timer_t));
  if (uv_timer_init(server->loop, timer) != 0) {
    free(timer);
    session->state = SESSION_STATE_TERMINATING;
    session_reap_tree(session, 0);
    return;
  }
  session->expiry_timer = timer;
  session->disconnect_at_ms = monotonic_ms();
  session->expiry_deadline_ms = session->disconnect_at_ms + session_grace_ms();
  timer->data = session;
  if (uv_timer_start(timer, session_expire_cb, session_grace_ms(), 0) != 0) {
    session->expiry_timer = NULL;
    timer->data = NULL;
    session->state = SESSION_STATE_TERMINATING;
    uv_close((uv_handle_t *)timer, expiry_timer_close_cb);
    session_reap_tree(session, 0);
  }
}

static int wsi_send_command(struct pss_tty *pss, char command, const void *data, size_t len) {
  unsigned char *message = xmalloc(LWS_PRE + 1 + len);
  unsigned char *payload = message + LWS_PRE;
  payload[0] = (unsigned char)command;
  if (len > 0) memcpy(payload + 1, data, len);
  const size_t size = 1 + len;
  const int rc = lws_write(pss->wsi, payload, size, LWS_WRITE_BINARY);
  free(message);
  return rc == (int)size ? rc : -1;
}

static const char *owner_phase_name(enum owner_phase phase) {
  return phase == OWNER_READY ? "READY" : phase == OWNER_REPLAYING ? "REPLAYING" : "ATTACHING";
}

static int send_session_state(struct pss_tty *pss) {
  json_object *obj = json_object_new_object();
  json_object *replay = json_object_new_object();
  json_object_object_add(obj, "version", json_object_new_int(SESSION_PROTOCOL_VERSION));
  json_object_object_add(obj, "state", json_object_new_string(pss->session_state));
  json_object_object_add(obj, "sessionDiagnosticId", json_object_new_int64((int64_t)pss->reported_session_id));
  json_object_object_add(obj, "connectionGeneration", json_object_new_int64((int64_t)pss->connection_generation));
  json_object_object_add(obj, "leaseEpoch", json_object_new_int64((int64_t)(pss->session ? pss->session->lease_epoch : pss->observed_lease_epoch)));
  if (!strcmp(pss->session_state, "version_mismatch"))
    json_object_object_add(obj, "expectedVersion", json_object_new_int(SESSION_PROTOCOL_VERSION));
  if (!strcmp(pss->session_state, "owner_check_busy")) {
    json_object_object_add(obj, "retryable", json_object_new_boolean(true));
    json_object_object_add(obj, "retryAfterMs", json_object_new_int(1000));
  }
  if (pss->session != NULL) {
    json_object_object_add(obj, "sessionId", json_object_new_string(pss->session->id));
    json_object_object_add(obj, "ownerPhase", json_object_new_string(owner_phase_name(pss->session->owner_phase)));
  }
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
  json_object_object_add(obj, "inputReady", json_object_new_boolean(false));
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

  if (eof) {
    pty_buf_free(buf);
    session->pty_eof_observed = true;
    session_diagnostic(session, session->client, "pty-eof");
    session_maybe_finalize_exit(session, process);
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
  if (pss != NULL && pss->initialized && !pss->client_flow_paused &&
      session_output_disposition(session, pss) != OUTPUT_SEND_NONE)
    schedule_writable(pss);
}
static void session_counts(int *active_count, int *detached_count, int *retained_count, size_t *total_memory) {
  int act = 0, det = 0, ret = 0;
  size_t mem = 0;
  for (struct tty_session *s = session_list; s != NULL; s = s->next) {
    mem += s->output.allocated_chunks * OUTPUT_CHUNK_SIZE;
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

  int max_sessions = 8;
  const char *env_max = getenv("TTYD_MAX_SESSIONS");
  if (env_max != NULL && atoi(env_max) > 0) max_sessions = atoi(env_max);

  size_t max_mem = 64 * 1024 * 1024;
  const char *env_mem = getenv("TTYD_MAX_TOTAL_BUFFER_BYTES");
  if (env_mem != NULL && atol(env_mem) > 0) max_mem = (size_t)atol(env_mem);

  const int total_sessions = active + detached + retained;
  if (total_sessions >= max_sessions) {
    lwsl_warn("admission refused: total sessions %d >= limit %d\n", total_sessions, max_sessions);
    return false;
  }
  if (total_mem + (8 * 1024 * 1024) > max_mem) {
    lwsl_warn("admission refused: total memory %zu + 8MiB > limit %zu\n", total_mem, max_mem);
    return false;
  }
  return true;
}

static void prune_retained_sessions(int max_retained, struct tty_session *protected_session) {
  int retained = 0;
  for (struct tty_session *s = session_list; s != NULL; s = s->next)
    if (s->state == SESSION_STATE_EXITED_RETAINED) retained++;
  while (retained > max_retained && max_retained >= 0) {
    struct tty_session *oldest = NULL;
    for (struct tty_session *s = session_list; s != NULL; s = s->next) {
      if (s == protected_session || s->state != SESSION_STATE_EXITED_RETAINED || s->process_exit_active ||
          s->client != NULL || !s->expiry_recorded || s->reaper_ref)
        continue;
      if (oldest == NULL || s->exited_at_ms < oldest->exited_at_ms) oldest = s;
    }
    if (oldest == NULL) break;
    oldest->state = SESSION_STATE_PURGED;
    tombstone_add(oldest, "expired");
    session_destroy_requested(oldest);
    retained--;
  }
}

static void session_maybe_finalize_exit(struct tty_session *session, pty_process *process) {
  if (session == NULL || process == NULL || !session->root_exit_observed || !session->pty_eof_observed) return;
  session->process_exit_active = true;
  session->saved_root_pid = process->pid;
  session->exit_code = process->exit_code;
  session->exit_signal = process->exit_signal;
  session->exit_status_known = process->wait_succeeded;
  if (!session->exit_status_known) session->exit_code = -1;
  session->exited_at_ms = monotonic_ms();
  session->process = NULL;
  if (session->client != NULL) session->client->process = NULL;
  process->ctx = NULL;

  if (session->resumable && session->state != SESSION_STATE_TERMINATING && session->state != SESSION_STATE_PURGED &&
      !session->expiry_recorded) {
    session->state = SESSION_STATE_EXITED_RETAINED;
    int max_retained = 16;
    const char *env_ret = getenv("TTYD_MAX_RETAINED_SESSIONS");
    if (env_ret != NULL && atoi(env_ret) >= 0) max_retained = atoi(env_ret);
    if (session->client != NULL) {
      session->client->replay_target = session->output.end;
      snprintf(session->client->session_state, sizeof(session->client->session_state), "exited_retained");
      session->client->replay_end_sent = false;
      session->client->input_ready = false;
      session->client->state_update_pending = true;
      schedule_writable(session->client);
    } else if (session->expiry_timer == NULL) {
      session_start_expiry(session);
    }
    prune_retained_sessions(max_retained, session);
  } else if (!session->resumable) {
    session->state = SESSION_STATE_PURGED;
    tombstone_add(session, "exited");
    if (session->client != NULL) {
      struct pss_tty *viewer = session->client;
      viewer->session = NULL;
      viewer->lws_close_status = 1000;
      schedule_writable(viewer);
      session->client = NULL;
      session_viewer_detach(session, viewer);
    }
    session_drop_registry(session);
  }
  session->process_exit_active = false;
  if (session->process_ref) {
    session_ref(session);
    session->process_ref = false;
    session_unref(session);
    session_maybe_complete_purge(session);
    session_unref(session);
  } else {
    session_maybe_complete_purge(session);
  }
}


static void process_exit_cb(pty_process *process) {
  struct tty_session *session = (struct tty_session *)process->ctx;
  if (session == NULL) return;
  session->root_exit_observed = true;
  session->exit_status_known = process->wait_succeeded;
  if (process->wait_succeeded && process->exit_signal)
    lwsl_notice("process killed with signal %d, pid: %d\n", process->exit_signal, process->pid);
  else if (process->wait_succeeded)
    lwsl_notice("process exited with code %d, pid: %d\n", process->exit_code, process->pid);
  else
    lwsl_err("process wait failed: pid %d errno %d\n", process->pid, process->wait_error);
  ready_deadline_cancel(session);
  if (session->resumable && session->state != SESSION_STATE_TERMINATING &&
      session->state != SESSION_STATE_PURGED && !session->expiry_recorded &&
      session->expiry_timer == NULL && !session->reaper_ref)
    session_start_expiry(session);
  session_diagnostic(session, session->client, "process-exit");
  session_maybe_finalize_exit(session, process);
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

static void timer_close_free(uv_handle_t *handle) { free(handle); }

static void ready_deadline_cancel(struct tty_session *session) {
  if (session == NULL || session->ready_deadline_timer == NULL) return;
  uv_timer_t *timer = session->ready_deadline_timer;
  session->ready_deadline_timer = NULL;
  timer->data = NULL;
  uv_timer_stop(timer);
  uv_close((uv_handle_t *)timer, timer_close_free);
}

static void prepare_unattached_response(struct pss_tty *pss, const char *state, uint64_t diagnostic_id) {
  pss->takeover_offered = false;
  pss->takeover_pending = false;
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

static void prepare_session_response(struct pss_tty *pss, struct tty_session *session, const char *state) {
  pss->takeover_offered = false;
  pss->takeover_pending = false;
  pss->session_accepted = true;
  pss->input_ready = false;
  pss->replay_end_sent = false;
  pss->reported_session_id = session->diagnostic_id;
  pss->lease_epoch = session->lease_epoch;
  snprintf(pss->session_state, sizeof(pss->session_state), "%s", state);
  const bool position_valid = pss->requested_position >= session->output.start &&
                              pss->requested_position <= session->output.end;
  pss->replay_target = session->output.end;
  if (pss->requested_position > session->output.end) {
    pss->replay_start = session->output.end;
    pss->send_position = session->output.end;
    pss->replay_lost = true;
    queue_nack(pss, "POSITION_MISMATCH", "REPLAY_POSITION_AHEAD", session->output.end,
               pss->requested_position);
  } else {
    pss->replay_start = pss->requested_position;
    pss->send_position = pss->requested_position;
    pss->replay_lost = !position_valid;
  }
  pss->gap_pending = false;
  pss->degraded_consent = false;
  session->owner_phase = OWNER_REPLAYING;
  session->last_progress_at_ms = monotonic_ms();
}

static void prepare_conflict_response(struct pss_tty *pss, struct tty_session *session) {
  pss->session_accepted = false;
  pss->input_ready = false;
  pss->reported_session_id = session->diagnostic_id;
  pss->observed_lease_epoch = session->lease_epoch;
  pss->replay_start = pss->replay_target = 0;
  pss->replay_lost = false;
  pss->close_after_state = false;
  if (pss->recovery_only_slot) lws_set_timeout(pss->wsi, PENDING_TIMEOUT_SHUTDOWN_FLUSH, 5);
  pss->takeover_offered = true;
  pss->takeover_pending = false;
  if (pss->initialized || pss->initial_cmd_index >= (int)sizeof(initial_cmds)) pss->state_update_pending = true;
  snprintf(pss->session_state, sizeof(pss->session_state), "%s",
           session->owner_phase == OWNER_READY ? "conflict" : "owner_check_busy");
  schedule_writable(pss);
}

static void prepare_displaced_response(struct pss_tty *pss, uint64_t diagnostic_id) {
  if (pss == NULL) return;
  pss->session_accepted = false;
  pss->input_ready = false;
  pss->reported_session_id = diagnostic_id;
  pss->replay_start = pss->replay_target = 0;
  pss->replay_lost = false;
  pss->takeover_offered = false;
  pss->takeover_pending = false;
  pss->close_after_state = true;
  pss->state_update_pending = true;
  snprintf(pss->session_state, sizeof(pss->session_state), "displaced");
  schedule_writable(pss);
}

static bool hash_bytes(const uint8_t *data, size_t len, uint8_t out[SUCCESSOR_TOKEN_BYTES]) {
  struct lws_genhash_ctx hash;
  if (lws_genhash_init(&hash, LWS_GENHASH_TYPE_SHA256) != 0) return false;
  if (lws_genhash_update(&hash, data, len) != 0) {
    lws_genhash_destroy(&hash, NULL);
    return false;
  }
  return lws_genhash_destroy(&hash, out) == 0;
}

static bool decode_token_hash(const char *hex, uint8_t out[SUCCESSOR_TOKEN_BYTES]) {
  if (hex == NULL || strlen(hex) != SUCCESSOR_TOKEN_HEX_LENGTH) return false;
  uint8_t raw[SUCCESSOR_TOKEN_BYTES];
  for (size_t i = 0; i < SUCCESSOR_TOKEN_BYTES; i++) {
    const char a = hex[i * 2], b = hex[i * 2 + 1];
    if (!isxdigit((unsigned char)a) || !isxdigit((unsigned char)b) || isupper((unsigned char)a) || isupper((unsigned char)b)) {
      memset(raw, 0, sizeof(raw));
      return false;
    }
    const unsigned hi = (unsigned)(a <= '9' ? a - '0' : a - 'a' + 10);
    const unsigned lo = (unsigned)(b <= '9' ? b - '0' : b - 'a' + 10);
    raw[i] = (uint8_t)((hi << 4) | lo);
  }
  const bool ok = hash_bytes(raw, sizeof(raw), out);
  memset(raw, 0, sizeof(raw));
  return ok;
}

static bool generate_successor_token(struct pss_tty *pss) {
  uint8_t raw[SUCCESSOR_TOKEN_BYTES];
  static const char digits[] = "0123456789abcdef";
  if (lws_get_random(context, raw, sizeof(raw)) != sizeof(raw)) return false;
  for (size_t i = 0; i < sizeof(raw); i++) {
    pss->ready_token[i * 2] = digits[raw[i] >> 4];
    pss->ready_token[i * 2 + 1] = digits[raw[i] & 15];
  }
  pss->ready_token[SUCCESSOR_TOKEN_HEX_LENGTH] = '\0';
  const bool ok = hash_bytes(raw, sizeof(raw), pss->ready_token_hash);
  memset(raw, 0, sizeof(raw));
  return ok;
}

static void fence_owner(struct tty_session *session, struct pss_tty *old, const char *state) {
  if (session == NULL || old == NULL || session->client != old) return;
  ready_deadline_cancel(session);
  session->client = NULL;
  old->input_ready = false;
  old->session_accepted = false;
  old->lease_epoch = 0;
  old->session = NULL;
  old->process = NULL;
  prepare_displaced_response(old, session->diagnostic_id);
  snprintf(old->session_state, sizeof(old->session_state), "%s", state);
  session_diagnostic(session, old, state);
  session_viewer_detach(session, old);
}

static void ready_deadline_cb(uv_timer_t *timer) {
  struct tty_session *session = (struct tty_session *)timer->data;
  if (session == NULL || session->ready_deadline_timer != timer) return;
  const uint64_t lease = session->ready_deadline_lease_epoch;
  session->ready_deadline_timer = NULL;
  timer->data = NULL;
  uv_timer_stop(timer);
  uv_close((uv_handle_t *)timer, timer_close_free);
  if (session->client == NULL || session->lease_epoch != lease || session->owner_phase == OWNER_READY) return;
  struct pss_tty *owner = session->client;
  fence_owner(session, owner, "ready_timeout");
  if (session->process != NULL && process_running(session->process)) {
    session->state = SESSION_STATE_DETACHED_GRACE;
    session_start_expiry(session);
  }
}

static uint64_t ready_deadline_ms(void) {
  const char *value = getenv("TTYD_READY_DEADLINE_MS");
  if (value == NULL || *value == '\0') return SESSION_READY_DEADLINE_MS;
  char *end = NULL;
  unsigned long parsed = strtoul(value, &end, 10);
  return end != value && *end == '\0' && parsed > 0 && parsed <= SESSION_READY_DEADLINE_MS
             ? (uint64_t)parsed
             : SESSION_READY_DEADLINE_MS;
}

static bool ready_deadline_arm(struct tty_session *session) {
  ready_deadline_cancel(session);
  uv_timer_t *timer = xmalloc(sizeof(*timer));
  if (uv_timer_init(server->loop, timer) != 0) {
    free(timer);
    return false;
  }
  timer->data = session;
  session->ready_deadline_timer = timer;
  session->ready_deadline_lease_epoch = session->lease_epoch;
  if (uv_timer_start(timer, ready_deadline_cb, ready_deadline_ms(), 0) != 0) {
    session->ready_deadline_timer = NULL;
    timer->data = NULL;
    uv_close((uv_handle_t *)timer, timer_close_free);
    return false;
  }
  return true;
}

static bool grant_owner(struct pss_tty *pss, struct tty_session *session, enum approval_kind kind,
                        uint16_t columns, uint16_t rows, bool increment_epoch) {
  if (session == NULL || (increment_epoch && session->lease_epoch == UINT64_MAX)) return false;
  if (increment_epoch) session->lease_epoch++;
  if (session->lease_epoch == 0) session->lease_epoch = 1;
  session_cancel_expiry(session);
  session->client = pss;
  session->state = SESSION_STATE_ACTIVE;
  session->owner_phase = OWNER_ATTACHING;
  session->owner_started_at_ms = monotonic_ms();
  session->last_progress_at_ms = session->owner_started_at_ms;
  memcpy(session->owner_client_instance_id, pss->client_instance_id, sizeof(session->owner_client_instance_id));
  session->owner_connect_sequence = pss->connect_sequence;
  session->last_approval.kind = kind;
  memcpy(session->last_approval.client_instance_id, pss->client_instance_id,
         sizeof(session->last_approval.client_instance_id));
  session->last_approval.connect_sequence = pss->connect_sequence;
  session->last_approval.lease_epoch = session->lease_epoch;
  pss->approval_kind = kind;
  pss->lease_epoch = session->lease_epoch;
  pss->session = session;
  pss->process = session->process;
  session_viewer_attach(session, pss);
  pss->client_flow_paused = false;
  if (session->process != NULL) {
    session->process->columns = columns;
    session->process->rows = rows;
    pty_resize(session->process);
    pty_signal_foreground(session->process, SIGWINCH);
  }
  if (ready_deadline_arm(session)) return true;
  session->client = NULL;
  pss->session = NULL;
  pss->process = NULL;
  session_viewer_detach(session, pss);
  return false;
}

static bool spawn_process(struct pss_tty *pss, uint16_t columns, uint16_t rows) {
  struct tty_session *session = session_create(pss->resume_id, true);
  pty_process *process = process_init((void *)session, server->loop, build_args(pss), build_env(pss));
  if (server->cwd != NULL) process->cwd = strdup(server->cwd);
  process->columns = columns;
  process->rows = rows;
  if (pty_spawn(process, process_read_cb, process_exit_cb) != 0) {
    process->ctx = NULL;
    if (!process->async_initialized) { process_free(process); free(process); }
    session_destroy_requested(session);
    return false;
  }
  session->process = process;
  session_ref(session);
  session->process_ref = true;
  session->saved_root_pid = process->pid;
  if (!grant_owner(pss, session, APPROVAL_CREATE, columns, rows, true)) {
    pty_kill(process, SIGKILL);
    process->ctx = NULL;
    session->process = NULL;
    session->process_ref = false;
    session_unref(session);
    session_destroy_requested(session);
    return false;
  }
  prepare_session_response(pss, session, "created");
  session_diagnostic(session, pss, "spawn");
  schedule_writable(pss);
  return true;
}

static bool attach_process(struct pss_tty *pss, struct tty_session *session, uint16_t columns, uint16_t rows) {
  if (session == NULL || session->process == NULL || !process_running(session->process) || session->client != NULL)
    return false;
  if (!grant_owner(pss, session, APPROVAL_SUCCESSOR, columns, rows, true)) return false;
  prepare_session_response(pss, session, "attached");
  if (pss->initialized || pss->initial_cmd_index >= (int)sizeof(initial_cmds)) pss->state_update_pending = true;
  session_diagnostic(session, pss, "attach");
  schedule_writable(pss);
  return true;
}

static bool wsi_output_data(struct pss_tty *pss, const char *data, size_t len) {
  if (pss == NULL || data == NULL || len == 0) return false;
  const uint64_t start_position = pss->send_position;
  const uint64_t end_position = start_position + len;
  unsigned char *message = xmalloc(LWS_PRE + V4_OUTPUT_HEADER_SIZE + len);
  unsigned char *ptr = message + LWS_PRE;
  ptr[0] = OUTPUT;
  for (int i = 0; i < 8; i++) {
    ptr[1 + i] = (unsigned char)(pss->lease_epoch >> (56 - i * 8));
    ptr[9 + i] = (unsigned char)(start_position >> (56 - i * 8));
    ptr[17 + i] = (unsigned char)(end_position >> (56 - i * 8));
  }
  memcpy(ptr + V4_OUTPUT_HEADER_SIZE, data, len);
  const size_t size = V4_OUTPUT_HEADER_SIZE + len;
  const int written = lws_write(pss->wsi, ptr, size, LWS_WRITE_BINARY);
  free(message);
  if (written != (int)size) return false;
  pss->send_position = end_position;
  if (pss->session != NULL) pss->session->ws_output_bytes += len;
  return true;
}
static int send_replay_gap(struct pss_tty *pss) {
  json_object *obj = json_object_new_object();
  json_object *lost = json_object_new_object();
  json_object *retained = json_object_new_object();
  json_object_object_add(obj, "version", json_object_new_int(SESSION_PROTOCOL_VERSION));
  json_object_object_add(obj, "sessionId", json_object_new_string(pss->resume_id));
  json_object_object_add(obj, "leaseEpoch", json_object_new_int64((int64_t)pss->lease_epoch));
  json_object_object_add(obj, "syncId", json_object_new_int64((int64_t)pss->sync_id));
  json_object_object_add(obj, "code", json_object_new_string("SYNC_REQUIRED"));
  json_object_object_add(obj, "reason", json_object_new_string("BUFFER_OVERRUN"));
  json_object_object_add(lost, "start", json_object_new_int64((int64_t)pss->gap_lost_start));
  json_object_object_add(lost, "end", json_object_new_int64((int64_t)pss->gap_lost_end));
  json_object_object_add(retained, "start", json_object_new_int64((int64_t)pss->gap_retained_start));
  json_object_object_add(retained, "end", json_object_new_int64((int64_t)pss->gap_retained_end));
  json_object_object_add(obj, "lost", lost);
  json_object_object_add(obj, "retained", retained);
  json_object_object_add(obj, "target", json_object_new_int64((int64_t)pss->gap_target));
  const char *json = json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN);
  const int rc = wsi_send_command(pss, REPLAY_GAP, json, strlen(json));
  json_object_put(obj);
  return rc;
}

static int send_replay_end(struct pss_tty *pss) {
  json_object *obj = json_object_new_object();
  json_object_object_add(obj, "version", json_object_new_int(SESSION_PROTOCOL_VERSION));
  json_object_object_add(obj, "sessionId", json_object_new_string(pss->resume_id));
  json_object_object_add(obj, "leaseEpoch", json_object_new_int64((int64_t)pss->lease_epoch));
  json_object_object_add(obj, "position", json_object_new_int64((int64_t)pss->replay_target));
  json_object_object_add(obj, "truncated", json_object_new_boolean(pss->replay_lost));
  if (pss->session != NULL && pss->session->state == SESSION_STATE_EXITED_RETAINED) {
    json_object_object_add(obj, "exitCode", json_object_new_int(pss->session->exit_code));
    json_object_object_add(obj, "exitSignal", json_object_new_int(pss->session->exit_signal));
    json_object_object_add(obj, "exitStatusKnown", json_object_new_boolean(pss->session->exit_status_known));
  }
  const char *json = json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN);
  const int rc = wsi_send_command(pss, REPLAY_END, json, strlen(json));
  json_object_put(obj);
  return rc;
}

static int send_nack(struct pss_tty *pss) {
  json_object *obj = json_object_new_object();
  json_object_object_add(obj, "version", json_object_new_int(SESSION_PROTOCOL_VERSION));
  json_object_object_add(obj, "sessionId", json_object_new_string(pss->resume_id));
  json_object_object_add(obj, "leaseEpoch", json_object_new_int64((int64_t)pss->lease_epoch));
  json_object_object_add(obj, "code", json_object_new_string(pss->nack_code));
  json_object_object_add(obj, "retryable", json_object_new_boolean(!strcmp(pss->nack_code, "SYNC_REQUIRED")));
  if (pss->nack_expected_position || pss->nack_received_position) {
    json_object_object_add(obj, "expectedPosition", json_object_new_int64((int64_t)pss->nack_expected_position));
    json_object_object_add(obj, "receivedPosition", json_object_new_int64((int64_t)pss->nack_received_position));
  }
  if (pss->nack_detail[0]) json_object_object_add(obj, "detail", json_object_new_string(pss->nack_detail));
  const char *json = json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN);
  const int rc = wsi_send_command(pss, SESSION_NACK, json, strlen(json));
  json_object_put(obj);
  return rc;
}

static int send_ready_ack(struct pss_tty *pss) {
  struct tty_session *session = pss->session;
  if (session == NULL || session->client != pss || session->lease_epoch != pss->lease_epoch) return -1;
  if (!generate_successor_token(pss)) return -1;
  json_object *obj = json_object_new_object();
  json_object_object_add(obj, "version", json_object_new_int(SESSION_PROTOCOL_VERSION));
  json_object_object_add(obj, "sessionId", json_object_new_string(session->id));
  json_object_object_add(obj, "leaseEpoch", json_object_new_int64((int64_t)session->lease_epoch));
  json_object_object_add(obj, "position", json_object_new_int64((int64_t)pss->replay_target));
  json_object_object_add(obj, "successorToken", json_object_new_string(pss->ready_token));
  if (pss->degraded_consent) {
    json_object *gap = json_object_new_object();
    json_object_object_add(obj, "degraded", json_object_new_boolean(true));
    json_object_object_add(obj, "syncId", json_object_new_int64((int64_t)pss->sync_id));
    json_object_object_add(gap, "start", json_object_new_int64((int64_t)pss->gap_lost_start));
    json_object_object_add(gap, "end", json_object_new_int64((int64_t)pss->gap_lost_end));
    json_object_object_add(obj, "gap", gap);
  }
  const char *json = json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN);
  const size_t size = strlen(json) + 1;
  const int rc = wsi_send_command(pss, READY_ACK, json, strlen(json));
  json_object_put(obj);
  if (rc != (int)size) { memset(pss->ready_token, 0, sizeof(pss->ready_token)); return -1; }
  memcpy(session->successor_token_hash, pss->ready_token_hash, sizeof(session->successor_token_hash));
  session->successor_token_valid = true;
  session->owner_phase = OWNER_READY;
  session->last_application_heartbeat_ms = monotonic_ms();
  pss->input_ready = true;
  ready_deadline_cancel(session);
  memset(pss->ready_token, 0, sizeof(pss->ready_token));
  memset(pss->ready_token_hash, 0, sizeof(pss->ready_token_hash));
  session_diagnostic(session, pss, "ready-ack");
  return rc;
}

static void queue_nack(struct pss_tty *pss, const char *code, const char *detail,
                       uint64_t expected, uint64_t received) {
  snprintf(pss->nack_code, sizeof(pss->nack_code), "%s", code);
  snprintf(pss->nack_detail, sizeof(pss->nack_detail), "%s", detail == NULL ? "" : detail);
  pss->nack_expected_position = expected;
  pss->nack_received_position = received;
  pss->nack_pending = true;
  pss->input_ready = false;
  schedule_writable(pss);
}

static bool json_u64(json_object *obj, const char *key, uint64_t *out, bool positive) {
  json_object *value = NULL;
  if (!json_object_object_get_ex(obj, key, &value) || !json_object_is_type(value, json_type_int)) return false;
  const char *text = json_object_get_string(value);
  if (text == NULL || *text == '\0') return false;
  uint64_t number = 0;
  for (const char *cursor = text; *cursor != '\0'; cursor++) {
    if (*cursor < '0' || *cursor > '9') return false;
    const uint64_t digit = (uint64_t)(*cursor - '0');
    if (number > (JSON_SAFE_INTEGER_MAX - digit) / 10) return false;
    number = number * 10 + digit;
  }
  if (positive && number == 0) return false;
  *out = number;
  return true;
}

static const char *json_string(json_object *obj, const char *key) {
  json_object *value = NULL;
  if (!json_object_object_get_ex(obj, key, &value) || !json_object_is_type(value, json_type_string)) return NULL;
  return json_object_get_string(value);
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
      if (server->max_clients > 0 && server->client_count >= server->max_clients + 1) {
        lwsl_warn("refuse to serve WS client: recovery reserve already occupied.\n");
        return 1;
      }
      pss->recovery_only_slot = server->max_clients > 0 && server->client_count == server->max_clients;
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
      pss->ready_ack_pending = false;
      pss->nack_pending = false;
      pss->requested_position = 0;
      pss->send_position = 0;
      pss->replay_target = 0;
      pss->reported_session_id = 0;
      pss->observed_lease_epoch = 0;
      pss->lease_epoch = 0;
      pss->connect_sequence = 0;
      pss->replay_start = 0;
      pss->replay_lost = false;
      snprintf(pss->session_state, sizeof(pss->session_state), "error");
      if (pss->recovery_only_slot) lws_set_timeout(wsi, PENDING_TIMEOUT_AWAITING_SERVER_RESPONSE, 5);
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
        if (wsi_send_command(pss, HEARTBEAT_REPLY, pss->heartbeat, pss->heartbeat_len) < 0) return -1;
        pss->heartbeat_pending = false;
        if (pss->session != NULL) schedule_writable(pss);
        break;
      }


      if (pss->nack_pending) {
        if (send_nack(pss) < 0) return -1;
        pss->nack_pending = false;
        break;
      }

      if (pss->ready_ack_pending) {
        pss->ready_ack_pending = false;
        if (send_ready_ack(pss) < 0) {
          queue_nack(pss, "SYNC_REQUIRED", "READY_ACK_WRITE_FAILED", pss->replay_target, pss->replay_target);
          break;
        }
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
      enum output_send_disposition disposition = session_output_disposition(session, pss);
      if (disposition == OUTPUT_SEND_GAP && !pss->gap_pending) {
        pss->gap_pending = true;
        pss->gap_sent = false;
        pss->input_ready = false;
        pss->replay_end_sent = false;
        pss->sync_id++;
        pss->gap_lost_start = pss->send_position;
        pss->gap_lost_end = session->output.start;
        pss->gap_retained_start = session->output.start;
        pss->gap_retained_end = session->output.end;
        pss->gap_target = session->output.end;
      }
      if (pss->gap_pending) {
        if (!pss->gap_sent) {
          if (send_replay_gap(pss) < 0) return -1;
          pss->gap_sent = true;
          session_diagnostic(session, pss, "replay-gap");
        }
        break;
      }
      if (!pss->replay_end_sent && disposition == OUTPUT_SEND_NONE) {
        if (pss->send_position != pss->replay_target || pss->replay_target < session->output.start) break;
        if (send_replay_end(pss) < 0) return -1;
        pss->replay_end_sent = true;
        session_diagnostic(session, pss, "replay-end");
        break;
      }
      if (pss->client_flow_paused || disposition != OUTPUT_SEND_DATA) break;

      const uint64_t limit = pss->input_ready ? session->output.end : pss->replay_target;
      const uint64_t remaining = limit - pss->send_position;
      const size_t wanted = remaining > SESSION_REPLAY_CHUNK ? SESSION_REPLAY_CHUNK : (size_t)remaining;
      unsigned char chunk[SESSION_REPLAY_CHUNK];
      const size_t copied = output_ring_copy(&session->output, pss->send_position, chunk, wanted);
      if (copied != wanted || !wsi_output_data(pss, (const char *)chunk, copied)) return -1;
      schedule_writable(pss);
      break;
    }
    case LWS_CALLBACK_RECEIVE_PONG:
      if (pss->heartbeat_pending || pss->state_update_pending || pss->nack_pending || pss->ready_ack_pending ||
          (pss->session != NULL && session_output_disposition(pss->session, pss) != OUTPUT_SEND_NONE))
        schedule_writable(pss);
      break;

    case LWS_CALLBACK_RECEIVE:
      if (len == 0 && pss->buffer == NULL) {
        if (lws_remaining_packet_payload(wsi) > 0 || !lws_is_final_fragment(wsi)) return 0;
        lwsl_warn("ignored empty WS message\n");
        break;
      }

      if (pss->fragment_rejected) return 0;
      if (len > CLIENT_MESSAGE_MAX || pss->len > CLIENT_MESSAGE_MAX - len) {
        free(pss->buffer);
        pss->buffer = NULL;
        pss->len = 0;
        pss->fragment_rejected = true;
        if (pss->session_accepted) queue_nack(pss, "MESSAGE_TOO_LARGE", "CLIENT_MESSAGE_MAX", 0, 0);
        pss->lws_close_status = 1009;
        schedule_writable(pss);
        return 0;
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
          if (pss->len < V4_INPUT_HEADER_SIZE) { queue_nack(pss, "SYNC_REQUIRED", "SHORT_INPUT", 0, 0); break; }
          uint64_t lease = 0;
          for (int i = 0; i < 8; i++) lease = (lease << 8) | (uint8_t)pss->buffer[1 + i];
          if (!server->writable || !pss->input_ready || pss->session == NULL || pss->session->client != pss ||
              pss->session->lease_epoch != pss->lease_epoch || pss->session->owner_phase != OWNER_READY ||
              pss->process == NULL || lease != pss->lease_epoch) {
            queue_nack(pss, "STALE_LEASE", "INPUT", 0, 0);
            break;
          }
          const size_t input_len = pss->len - V4_INPUT_HEADER_SIZE;
          int err = pty_write(pss->process, pty_buf_init(pss->buffer + V4_INPUT_HEADER_SIZE, input_len));
          if (err) return -1;
          pss->session->pty_write_count++;
          pss->session->ws_input_bytes += input_len;
          break;
        }
        case RESIZE_TERMINAL:
        case PAUSE:
        case RESUME:
        case HEARTBEAT: {
          json_tokener *tok = json_tokener_new();
          json_object *obj = json_tokener_parse_ex(tok, pss->buffer + 1, pss->len - 1);
          uint64_t lease = 0;
          const bool current = obj != NULL && json_u64(obj, "leaseEpoch", &lease, true) &&
                               pss->session != NULL && pss->session->client == pss &&
                               pss->session->owner_phase == OWNER_READY && lease == pss->lease_epoch &&
                               lease == pss->session->lease_epoch;
          if (!current) {
            queue_nack(pss, "STALE_LEASE", "CONTROL", 0, 0);
          } else if (command == RESIZE_TERMINAL) {
            uint64_t columns = 0, rows = 0;
            if (json_u64(obj, "columns", &columns, true) && json_u64(obj, "rows", &rows, true) &&
                columns <= UINT16_MAX && rows <= UINT16_MAX && pss->process != NULL) {
              pss->process->columns = (uint16_t)columns;
              pss->process->rows = (uint16_t)rows;
              pty_resize(pss->process);
              pty_signal_foreground(pss->process, SIGWINCH);
            } else queue_nack(pss, "SYNC_REQUIRED", "INVALID_GEOMETRY", 0, 0);
          } else if (command == PAUSE) {
            pss->client_flow_paused = true;
          } else if (command == RESUME) {
            pss->client_flow_paused = false;
            schedule_writable(pss);
          } else {
            const char *nonce = json_string(obj, "nonce");
            if (nonce != NULL && strlen(nonce) <= sizeof(pss->heartbeat) - 1) {
              const char *json = json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN);
              pss->heartbeat_len = strlen(json);
              memcpy(pss->heartbeat, json, pss->heartbeat_len);
              pss->heartbeat_pending = true;
              pss->session->last_application_heartbeat_ms = monotonic_ms();
              schedule_writable(pss);
            } else queue_nack(pss, "SYNC_REQUIRED", "INVALID_HEARTBEAT", 0, 0);
          }
          json_tokener_free(tok);
          if (obj != NULL) json_object_put(obj);
          break;
        }
        case REPLAY_APPLIED: {
          json_tokener *tok = json_tokener_new();
          json_object *obj = json_tokener_parse_ex(tok, pss->buffer + 1, pss->len - 1);
          uint64_t lease = 0, position = 0, sync_id = 0;
          const char *session_id = obj == NULL ? NULL : json_string(obj, "sessionId");
          json_object *accept_obj = NULL;
          const bool accept_incomplete = obj != NULL &&
              json_object_object_get_ex(obj, "acceptIncomplete", &accept_obj) &&
              json_object_get_boolean(accept_obj);
          if (obj != NULL) json_u64(obj, "syncId", &sync_id, false);
          if (obj == NULL || session_id == NULL || !json_u64(obj, "leaseEpoch", &lease, true) ||
              !json_u64(obj, "position", &position, false)) {
            queue_nack(pss, "SYNC_REQUIRED", "MALFORMED_REPLAY_APPLIED", 0, 0);
          } else if (pss->session == NULL || strcmp(session_id, pss->resume_id) != 0) {
            queue_nack(pss, "SYNC_REQUIRED", "SESSION_MISMATCH", 0, position);
          } else if (pss->session->state == SESSION_STATE_EXITED_RETAINED) {
            queue_nack(pss, "SESSION_ENDED", "READ_ONLY", pss->replay_target, position);
          } else if (pss->session->client != pss || lease != pss->lease_epoch || lease != pss->session->lease_epoch) {
            queue_nack(pss, "STALE_LEASE", "REPLAY_APPLIED", pss->replay_target, position);
          } else if (!pss->replay_end_sent || pss->session->owner_phase != OWNER_REPLAYING) {
            queue_nack(pss, "SYNC_REQUIRED", "WRONG_PHASE", pss->replay_target, position);
          } else if (position != pss->replay_target) {
            queue_nack(pss, "POSITION_MISMATCH", "REPLAY_TARGET", pss->replay_target, position);
          } else if (pss->sync_id != 0 && (!accept_incomplete || sync_id != pss->sync_id)) {
            queue_nack(pss, "SYNC_REQUIRED", "INCOMPLETE_CONSENT_REQUIRED", pss->sync_id, sync_id);
          } else {
            pss->degraded_consent = accept_incomplete;
            pss->ready_ack_pending = true;
            schedule_writable(pss);
          }
          json_tokener_free(tok);
          if (obj != NULL) json_object_put(obj);
          break;
        }
        case REBASE_ACK: {
          json_tokener *tok = json_tokener_new();
          json_object *obj = json_tokener_parse_ex(tok, pss->buffer + 1, pss->len - 1);
          uint64_t lease = 0, sync_id = 0, rebase = 0;
          const char *session_id = obj == NULL ? NULL : json_string(obj, "sessionId");
          const bool valid = obj != NULL && session_id != NULL &&
              json_u64(obj, "leaseEpoch", &lease, true) && json_u64(obj, "syncId", &sync_id, true) &&
              json_u64(obj, "rebasePosition", &rebase, false);
          if (!valid || pss->session == NULL || strcmp(session_id, pss->resume_id) != 0 ||
              pss->session->client != pss || lease != pss->lease_epoch || sync_id != pss->sync_id ||
              !pss->gap_pending || rebase != pss->gap_retained_start) {
            queue_nack(pss, "SYNC_REQUIRED", "INVALID_REBASE_ACK", pss->gap_retained_start, rebase);
          } else {
            pss->send_position = rebase;
            pss->replay_start = rebase;
            pss->replay_target = pss->session->output.end;
            pss->gap_pending = false;
            pss->gap_sent = false;
            pss->replay_end_sent = false;
            pss->replay_lost = true;
            pss->rebase_generation++;
            pss->session->owner_phase = OWNER_REPLAYING;
            schedule_writable(pss);
          }
          json_tokener_free(tok);
          if (obj != NULL) json_object_put(obj);
          break;
        }
        case TAKEOVER: {
          lws_set_timeout(wsi, NO_PENDING_TIMEOUT, 0);
          json_tokener *tok = json_tokener_new();
          json_object *obj = json_tokener_parse_ex(tok, pss->buffer + 1, pss->len - 1);
          uint64_t observed = 0, sequence = 0, columns = 0, rows = 0;
          const bool valid = obj != NULL && json_u64(obj, "observedLeaseEpoch", &observed, true) &&
                             json_u64(obj, "connectSequence", &sequence, true) &&
                             json_u64(obj, "columns", &columns, true) && json_u64(obj, "rows", &rows, true) &&
                             columns <= UINT16_MAX && rows <= UINT16_MAX;
          struct tty_session *session = session_find(pss->resume_id);
          if (!valid || session == NULL) {
            prepare_unattached_response(pss, "unknown", session == NULL ? 0 : session->diagnostic_id);
          } else if (observed != session->lease_epoch) {
            pss->observed_lease_epoch = session->lease_epoch;
            prepare_unattached_response(pss, "stale", session->diagnostic_id);
          } else if (session->state == SESSION_STATE_EXITED_RETAINED) {
            prepare_unattached_response(pss, "exited", session->diagnostic_id);
          } else {
            pss->connect_sequence = sequence;
            struct pss_tty *old = session->client;
            if (old != NULL) fence_owner(session, old, "displaced");
            if (!grant_owner(pss, session, APPROVAL_TAKEOVER, (uint16_t)columns, (uint16_t)rows, true)) {
              prepare_unattached_response(pss, "error", session->diagnostic_id);
            } else {
              prepare_session_response(pss, session, "attached");
              pss->state_update_pending = true;
              schedule_writable(pss);
            }
          }
          json_tokener_free(tok);
          if (obj != NULL) json_object_put(obj);
          break;
        }
        case JSON_DATA: {
          if (pss->handshake_received) { queue_nack(pss, "SYNC_REQUIRED", "DUPLICATE_HELLO", 0, 0); break; }
          lws_set_timeout(wsi, NO_PENDING_TIMEOUT, 0);
          pss->handshake_received = true;
          json_tokener *tok = json_tokener_new();
          json_object *obj = json_tokener_parse_ex(tok, pss->buffer, pss->len);
          uint64_t version = 0, sequence = 0, replay_position = 0, columns = 0, rows = 0;
          const char *intent = obj == NULL ? NULL : json_string(obj, "intent");
          const char *resume_id = obj == NULL ? NULL : json_string(obj, "resumeId");
          const char *client_id = obj == NULL ? NULL : json_string(obj, "clientInstanceId");
          const char *successor = obj == NULL ? NULL : json_string(obj, "successorToken");
          const bool fields = obj != NULL && json_u64(obj, "version", &version, true) &&
                              json_u64(obj, "connectSequence", &sequence, true) &&
                              json_u64(obj, "replayPosition", &replay_position, false) &&
                              json_u64(obj, "columns", &columns, true) && json_u64(obj, "rows", &rows, true) &&
                              columns <= UINT16_MAX && rows <= UINT16_MAX && resume_id_valid(resume_id) &&
                              resume_id_valid(client_id) && intent != NULL &&
                              (!strcmp(intent, "create") || !strcmp(intent, "resume"));
          if (server->credential != NULL) {
            const char *auth = obj == NULL ? NULL : json_string(obj, "AuthToken");
            pss->authenticated = auth != NULL && !strcmp(auth, server->credential);
          }
          if (version != SESSION_PROTOCOL_VERSION) {
            prepare_unattached_response(pss, "version_mismatch", 0);
          } else if (!fields || (server->credential != NULL && !pss->authenticated)) {
            prepare_unattached_response(pss, "error", 0);
          } else {
            memcpy(pss->resume_id, resume_id, SESSION_ID_LENGTH + 1);
            memcpy(pss->client_instance_id, client_id, CLIENT_INSTANCE_ID_LENGTH + 1);
            pss->connect_sequence = sequence;
            pss->requested_position = replay_position;
            struct tty_session *session = session_find(pss->resume_id);
            struct session_tombstone *tombstone = session == NULL ? tombstone_find(pss->resume_id) : NULL;
            if (session != NULL && session->state == SESSION_STATE_EXITED_RETAINED) {
              if (session->client != NULL) fence_owner(session, session->client, "superseded");
              session->client = pss;
              pss->session = session;
              session_viewer_attach(session, pss);
              pss->lease_epoch = session->lease_epoch;
              prepare_session_response(pss, session, "exited_retained");
              pss->state_update_pending = true;
              schedule_writable(pss);
            } else if (session != NULL && (session->state == SESSION_STATE_TERMINATING || session->state == SESSION_STATE_PURGED)) {
              prepare_unattached_response(pss, "expired", session->diagnostic_id);
            } else if (session != NULL && (session->process == NULL || !process_running(session->process))) {
              prepare_unattached_response(pss, "exited", session->diagnostic_id);
            } else if (session != NULL) {
              uint8_t presented_hash[SUCCESSOR_TOKEN_BYTES] = {0};
              const bool same_client = !strcmp(client_id, session->owner_client_instance_id);
              const bool presented_successor = decode_token_hash(successor, presented_hash);
              const bool exact_retry = same_client && sequence == session->last_approval.connect_sequence;
              const bool newer_create_retry = same_client && !strcmp(intent, "create") &&
                  session->last_approval.kind == APPROVAL_CREATE && session->owner_phase != OWNER_READY &&
                  sequence > session->last_approval.connect_sequence;
              const bool newer_successor_retry = same_client && !strcmp(intent, "resume") &&
                  session->last_approval.kind == APPROVAL_SUCCESSOR && session->owner_phase != OWNER_READY &&
                  session->last_approval.has_credential_hash &&
                  sequence > session->last_approval.connect_sequence && presented_successor &&
                  lws_timingsafe_bcmp(presented_hash, session->last_approval.credential_hash,
                                      SUCCESSOR_TOKEN_BYTES) == 0;
              const bool valid_successor = same_client && sequence > session->owner_connect_sequence &&
                  session->successor_token_valid && presented_successor &&
                  lws_timingsafe_bcmp(presented_hash, session->successor_token_hash, SUCCESSOR_TOKEN_BYTES) == 0;
              if (exact_retry || newer_create_retry || newer_successor_retry) {
                if (session->client != NULL) fence_owner(session, session->client, "superseded");
                if (!grant_owner(pss, session, session->last_approval.kind, (uint16_t)columns, (uint16_t)rows, false))
                  prepare_unattached_response(pss, "error", session->diagnostic_id);
                else { prepare_session_response(pss, session, "attached"); pss->state_update_pending = true; schedule_writable(pss); }
              } else if (valid_successor) {
                session->successor_token_valid = false;
                memcpy(session->last_approval.credential_hash, presented_hash, sizeof(presented_hash));
                session->last_approval.has_credential_hash = true;
                if (session->client != NULL) fence_owner(session, session->client, "superseded");
                if (!grant_owner(pss, session, APPROVAL_SUCCESSOR, (uint16_t)columns, (uint16_t)rows, true))
                  prepare_unattached_response(pss, "error", session->diagnostic_id);
                else { prepare_session_response(pss, session, "attached"); pss->state_update_pending = true; schedule_writable(pss); }
              } else if (!same_client) {
                prepare_conflict_response(pss, session);
              } else {
                prepare_unattached_response(pss, "superseded", session->diagnostic_id);
              }
              memset(presented_hash, 0, sizeof(presented_hash));
            } else if (tombstone != NULL) {
              prepare_unattached_response(pss, tombstone->reason, tombstone->diagnostic_id);
            } else if (!strcmp(intent, "create")) {
              if (pss->recovery_only_slot || !check_admission_limits(pss))
                prepare_unattached_response(pss, "rejected_capacity", 0);
              else if (!spawn_process(pss, (uint16_t)columns, (uint16_t)rows))
                prepare_unattached_response(pss, "error", 0);
            } else {
              prepare_unattached_response(pss, "unknown", 0);
            }
          }
          json_tokener_free(tok);
          if (obj != NULL) json_object_put(obj);
          break;
        }
        default:
          queue_nack(pss, "SYNC_REQUIRED", "UNKNOWN_MESSAGE", 0, 0);
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


      struct tty_session *closed_session = pss->session;
      session_diagnostic(closed_session, pss, "connection-close");

      if (closed_session != NULL && closed_session->client == pss && closed_session->lease_epoch == pss->lease_epoch) {
        closed_session->client = NULL;
        pty_process *process = pss->process;
        pss->session = NULL;
        pss->process = NULL;
        session_viewer_detach(closed_session, pss);

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
        uv_stop(server->loop);
      }
      break;
    }

    case LWS_CALLBACK_PROTOCOL_DESTROY:
      for (struct tty_session *session = session_list; session != NULL; session = session->next) {
        ready_deadline_cancel(session);
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
