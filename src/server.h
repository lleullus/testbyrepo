#include <libwebsockets.h>
#include <stdbool.h>
#include <uv.h>

#include "pty.h"

// client message
#define INPUT '0'
#define RESIZE_TERMINAL '1'
#define PAUSE '2'
#define RESUME '3'
#define HEARTBEAT '4'
#define SESSION_READY '5'
#define TAKEOVER '6'
#define JSON_DATA '{'

// server message
#define OUTPUT '0'
#define SET_WINDOW_TITLE '1'
#define SET_PREFERENCES '2'
#define SET_SESSION_STATE '3'
#define REPLAY_END '4'
#define HEARTBEAT_REPLY '5'

// url paths
struct endpoints {
  char *ws;
  char *index;
  char *token;
  char *parent;
};

extern volatile bool force_exit;
extern struct lws_context *context;
extern struct server *server;
extern struct endpoints endpoints;

struct tty_session;
enum session_state {
  SESSION_STATE_ACTIVE = 0,
  SESSION_STATE_DETACHED_GRACE,
  SESSION_STATE_EXITED_RETAINED,
  SESSION_STATE_TERMINATING,
  SESSION_STATE_PURGED
};


struct pss_http {
  char path[128];
  char *buffer;
  char *ptr;
  size_t len;
};

struct pss_tty {
  bool initialized;
  int initial_cmd_index;
  bool authenticated;
  char user[30];
  char address[50];
  char path[128];
  char resume_id[33];
  bool session_accepted;
  bool input_ready;
  bool replay_end_sent;
  bool client_flow_paused;
  bool writable_pending;
  bool heartbeat_pending;
  bool close_after_state;
  bool handshake_received;
  bool state_update_pending;
  bool takeover_offered;
  bool takeover_pending;
  uint64_t connection_generation;
  uint64_t requested_position;
  uint64_t send_position;
  uint64_t replay_target;
  uint64_t reported_session_id;
  uint64_t offered_owner_generation;
  uint64_t replay_start;
  bool replay_lost;
  char session_state[32];
  char heartbeat[65];
  size_t heartbeat_len;
  char **args;
  int argc;

  struct lws *wsi;
  char *buffer;
  size_t len;

  pty_process *process;
  struct tty_session *session;

  struct tty_session *pending_session;
  uint16_t pending_columns;
  uint16_t pending_rows;
  int lws_close_status;
};

struct server {
  int client_count;        // client count
  char *prefs_json;        // client preferences
  char *credential;        // encoded basic auth credential
  char *auth_header;       // header name used for auth proxy
  char *index;             // custom index.html
  char *command;           // full command line
  char **argv;             // command with arguments
  int argc;                // command + arguments count
  char *cwd;               // working directory
  int sig_code;            // close signal
  char sig_name[20];       // human readable signal string
  bool url_arg;            // allow client to send cli arguments in URL
  bool writable;           // whether clients to write to the TTY
  bool check_origin;       // whether allow websocket connection from different origin
  int max_clients;         // maximum clients to support
  bool once;               // whether accept only one client and exit on disconnection
  bool exit_no_conn;       // whether exit on all clients disconnection
  char socket_path[255];   // UNIX domain socket path
  char terminal_type[30];  // terminal type to report

  uv_loop_t *loop;         // the libuv event loop
};
