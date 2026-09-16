#ifndef TTYD_PTY_H
#define TTYD_PTY_H

#include <stdbool.h>
#include <stdint.h>
#include <uv.h>

#ifdef _WIN32
#ifndef HPCON
#define HPCON VOID *
#endif
#ifndef PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE
#define PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE 0x00020016
#endif

bool conpty_init();
#endif

typedef struct {
  char *base;
  size_t len;
} pty_buf_t;

struct pty_process_;
typedef struct pty_process_ pty_process;
typedef void (*pty_read_cb)(pty_process *, pty_buf_t *, bool);
typedef void (*pty_exit_cb)(pty_process *);

struct pty_process_ {
  int pid, exit_code, exit_signal;
  uint16_t columns, rows;
#ifdef _WIN32
  STARTUPINFOEXW si;
  HPCON pty;
  HANDLE handle;
  HANDLE wait;
#else
  pid_t pty;
  uv_thread_t tid;
#endif
  char **argv;
  char **envp;
  char *cwd;

  uv_loop_t *loop;
  uv_async_t async;
  uv_pipe_t *in;
  uv_pipe_t *out;
  bool paused;
  bool async_initialized;
  bool thread_started;
  pty_read_cb read_cb;
  pty_exit_cb exit_cb;
  void *ctx;
};

pty_buf_t *pty_buf_init(char *base, size_t len);
void pty_buf_free(pty_buf_t *buf);
pty_process *process_init(void *ctx, uv_loop_t *loop, char *argv[], char *envp[]);
bool process_running(pty_process *process);
void process_free(pty_process *process);
int pty_spawn(pty_process *process, pty_read_cb read_cb, pty_exit_cb exit_cb);
void pty_pause(pty_process *process);
void pty_resume(pty_process *process);
int pty_write(pty_process *process, pty_buf_t *buf);
bool pty_resize(pty_process *process);
bool pty_kill(pty_process *process, int sig);
bool pty_signal_foreground(pty_process *process, int sig);
typedef struct proc_ident {
  pid_t pid;
  pid_t pgrp;
  unsigned long long starttime;
} proc_ident_t;

bool pty_proc_get_ident(pid_t pid, proc_ident_t *ident_out);
bool pty_proc_ident_alive(const proc_ident_t *ident);
pid_t pty_get_fg_pgid(pty_process *process);
void pty_get_process_tree_idents(pid_t root_pid, pid_t extra_pgid, proc_ident_t **idents_out, size_t *count_out);
void pty_expand_tree_idents(proc_ident_t **idents_inout, size_t *count_inout);
bool pty_tree_idents_alive(const proc_ident_t *idents, size_t count);
bool pty_kill_tree(pty_process *process, int sig);
void pty_get_process_tree(pid_t root_pid, pid_t **pids_out, size_t *count_out);
bool pty_tree_alive(pid_t root_pid);

#endif  // TTYD_PTY_H
