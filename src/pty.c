#include <errno.h>
#include <fcntl.h>
#include <stdbool.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef _WIN32
#include <sys/ioctl.h>
#include <sys/wait.h>
#include <dirent.h>
#include <ctype.h>

#if defined(__OpenBSD__) || defined(__APPLE__)
#include <util.h>
#elif defined(__FreeBSD__)
#include <libutil.h>
#else
#include <pty.h>
#endif

#if defined(__APPLE__)
#include <crt_externs.h>
#define environ (*_NSGetEnviron())
#else
extern char **environ;
#endif
#endif

#include "pty.h"
#include "utils.h"

#ifdef _WIN32
HRESULT (WINAPI *pCreatePseudoConsole)(COORD, HANDLE, HANDLE, DWORD, HPCON *);
HRESULT (WINAPI *pResizePseudoConsole)(HPCON, COORD);
void (WINAPI *pClosePseudoConsole)(HPCON);
#endif

static void alloc_cb(uv_handle_t *unused, size_t suggested_size, uv_buf_t *buf) {
  buf->base = xmalloc(suggested_size);
  buf->len = suggested_size;
}

static void close_cb(uv_handle_t *handle) { free(handle); }

static void async_free_cb(uv_handle_t *handle) {
  pty_process *process = container_of((uv_async_t *)handle, pty_process, async);
  process_free(process);
  free(process);
}

static void process_maybe_close(pty_process *process) {
  if (process == NULL || process->close_started || !process->pty_eof_observed || !process->exit_callback_delivered)
    return;
  process->close_started = true;
  uv_close((uv_handle_t *)&process->async, async_free_cb);
}

pty_buf_t *pty_buf_init(char *base, size_t len) {
  pty_buf_t *buf = xmalloc(sizeof(pty_buf_t));
  buf->base = xmalloc(len);
  memcpy(buf->base, base, len);
  buf->len = len;
  return buf;
}

void pty_buf_free(pty_buf_t *buf) {
  if (buf == NULL) return;
  if (buf->base != NULL) free(buf->base);
  free(buf);
}

static void read_cb(uv_stream_t *stream, ssize_t n, const uv_buf_t *buf) {
  pty_process *process = (pty_process *)stream->data;
  if (n == 0) {
    free(buf->base);
    return;
  }
  if (n < 0) {
    uv_read_stop(stream);
    process->paused = true;
    process->pty_eof_observed = true;
    if (n != UV_EOF) {
      fprintf(stderr, "pty read: %s (%s)\n", uv_err_name((int)n), uv_strerror((int)n));
      if (process_running(process)) pty_kill(process, SIGTERM);
    }
    process->read_cb(process, NULL, true);
    process_maybe_close(process);
    free(buf->base);
    return;
  }
  process->read_cb(process, pty_buf_init(buf->base, (size_t)n), false);
  free(buf->base);
}

static void write_cb(uv_write_t *req, int status) {
  if (status < 0) fprintf(stderr, "pty write completion: %s (%s)\n", uv_err_name(status), uv_strerror(status));
  pty_buf_t *buf = (pty_buf_t *)req->data;
  pty_buf_free(buf);
  free(req);
}

pty_process *process_init(void *ctx, uv_loop_t *loop, char *argv[], char *envp[]) {
  pty_process *process = xmalloc(sizeof(pty_process));
  memset(process, 0, sizeof(pty_process));
  process->ctx = ctx;
  process->loop = loop;
  process->argv = argv;
  process->envp = envp;
  process->columns = 80;
  process->rows = 24;
  process->exit_code = -1;
  process->pid = -1;
#ifdef _WIN32
  process->pty = NULL;
#else
  process->pty = -1;
#endif
  process->async_initialized = false;
  process->thread_started = false;
  return process;
}

bool process_running(pty_process *process) {
  return process != NULL && process->pid > 0 && uv_kill(process->pid, 0) == 0;
}

void process_free(pty_process *process) {
  if (process == NULL) return;
#ifdef _WIN32
  if (process->si.lpAttributeList != NULL) {
    DeleteProcThreadAttributeList(process->si.lpAttributeList);
    free(process->si.lpAttributeList);
    process->si.lpAttributeList = NULL;
  }
  if (process->pty != NULL) {
    pClosePseudoConsole(process->pty);
    process->pty = NULL;
  }
  if (process->handle != NULL) {
    CloseHandle(process->handle);
    process->handle = NULL;
  }
#else
  if (process->pty >= 0) {
    close(process->pty);
    process->pty = -1;
  }
  if (process->thread_started) {
    uv_thread_join(&process->tid);
    process->thread_started = false;
  }
#endif
  if (process->in != NULL) {
    uv_close((uv_handle_t *)process->in, close_cb);
    process->in = NULL;
  }
  if (process->out != NULL) {
    uv_close((uv_handle_t *)process->out, close_cb);
    process->out = NULL;
  }
  if (process->argv != NULL) {
    free(process->argv);
    process->argv = NULL;
  }
  if (process->cwd != NULL) {
    free(process->cwd);
    process->cwd = NULL;
  }
  if (process->envp != NULL) {
    char **p = process->envp;
    for (; *p; p++) free(*p);
    free(process->envp);
    process->envp = NULL;
  }
}
void pty_pause(pty_process *process) {
  if (process == NULL || process->paused) return;
  uv_read_stop((uv_stream_t *)process->out);
  process->paused = true;
}

void pty_resume(pty_process *process) {
  if (process == NULL || !process->paused) return;
  process->out->data = process;
  if (uv_read_start((uv_stream_t *)process->out, alloc_cb, read_cb) == 0) process->paused = false;
}


int pty_write(pty_process *process, pty_buf_t *buf) {
  if (process == NULL) {
    pty_buf_free(buf);
    return UV_ESRCH;
  }
  uv_buf_t b = uv_buf_init(buf->base, buf->len);
  uv_write_t *req = xmalloc(sizeof(uv_write_t));
  req->data = buf;
  int status = uv_write(req, (uv_stream_t *)process->in, &b, 1, write_cb);
  if (status < 0) {
    pty_buf_free(buf);
    free(req);
  }
  return status;
}

bool pty_resize(pty_process *process) {
  if (process == NULL) return false;
  if (process->columns <= 0 || process->rows <= 0) return false;
#ifdef _WIN32
  COORD size = {(int16_t) process->columns, (int16_t) process->rows};
  return pResizePseudoConsole(process->pty, size) == S_OK;
#else
  struct winsize size = {process->rows, process->columns, 0, 0};
  return ioctl(process->pty, TIOCSWINSZ, &size) == 0;
#endif
}

bool pty_kill(pty_process *process, int sig) {
  if (process == NULL) return false;
#ifdef _WIN32
  return TerminateProcess(process->handle, 1) != 0;
#else
  return uv_kill(-process->pid, sig) == 0;
#endif
}

pid_t pty_get_fg_pgid(pty_process *process) {
#ifdef _WIN32
  (void)process;
  return 0;
#else
  if (process == NULL || process->pty < 0) return 0;
  pid_t pgid = 0;
  if (ioctl(process->pty, TIOCGPGRP, &pgid) < 0 || pgid <= 1) return 0;
  return pgid;
#endif
}

bool pty_signal_foreground(pty_process *process, int sig) {
#ifdef _WIN32
  (void)process;
  (void)sig;
  return false;
#else
  if (process == NULL || process->pty < 0) return false;
  pid_t pgid = pty_get_fg_pgid(process);
  if (pgid <= 1) {
    if (process_running(process)) return kill(process->pid, sig) == 0;
    return false;
  }
  if (kill(-pgid, sig) == 0) return true;
  if (errno != ESRCH) return false;
  pid_t retry = pty_get_fg_pgid(process);
  if (retry <= 1) {
    if (process_running(process)) return kill(process->pid, sig) == 0;
    return false;
  }
  if (kill(-retry, sig) == 0) return true;
  if (process_running(process)) return kill(process->pid, sig) == 0;
  return false;
#endif
}

bool pty_proc_get_ident(pid_t pid, proc_ident_t *ident_out) {
  if (pid <= 1 || ident_out == NULL) return false;
  memset(ident_out, 0, sizeof(*ident_out));
  ident_out->pid = pid;

#ifdef __linux__
  char path[64];
  snprintf(path, sizeof(path), "/proc/%d/stat", pid);
  FILE *f = fopen(path, "r");
  if (f == NULL) return false;
  char buf[1024];
  if (fgets(buf, sizeof(buf), f) == NULL) {
    fclose(f);
    return false;
  }
  fclose(f);

  char *closing = strrchr(buf, ')');
  if (closing == NULL || closing[1] != ' ') return false;

  char *p = closing + 2;
  int token_idx = 0;
  while (*p != '\0') {
    while (*p == ' ') p++;
    if (*p == '\0') break;
    char *token_start = p;
    while (*p != '\0' && *p != ' ') p++;
    if (token_idx == 2) {
      ident_out->pgrp = (pid_t)atoi(token_start);
    } else if (token_idx == 19) {
      ident_out->starttime = strtoull(token_start, NULL, 10);
      return true;
    }
    token_idx++;
  }
  return false;
#else
  ident_out->pgrp = getpgid(pid);
  ident_out->starttime = 0;
  return (kill(pid, 0) == 0 || errno == EPERM);
#endif
}

bool pty_proc_ident_alive(const proc_ident_t *ident) {
  if (ident == NULL || ident->pid <= 1) return false;
  if (kill(ident->pid, 0) != 0 && errno == ESRCH) return false;
#ifdef __linux__
  char path[64];
  snprintf(path, sizeof(path), "/proc/%d/stat", ident->pid);
  FILE *f = fopen(path, "r");
  if (f == NULL) return false;
  char buf[1024];
  if (fgets(buf, sizeof(buf), f) == NULL) {
    fclose(f);
    return false;
  }
  fclose(f);

  char *closing = strrchr(buf, ')');
  if (closing == NULL || closing[1] != ' ') return false;

  char *p = closing + 2;
  int token_idx = 0;
  char state = 0;
  unsigned long long starttime = 0;
  while (*p != '\0') {
    while (*p == ' ') p++;
    if (*p == '\0') break;
    char *token_start = p;
    while (*p != '\0' && *p != ' ') p++;
    if (token_idx == 0) {
      state = *token_start;
    } else if (token_idx == 19) {
      starttime = strtoull(token_start, NULL, 10);
      break;
    }
    token_idx++;
  }
  if (state == 'Z') return false;
  if (ident->starttime != 0 && starttime != ident->starttime) return false;
  return true;
#else
  return (kill(ident->pid, 0) == 0 || errno == EPERM);
#endif
}

void pty_get_process_tree_idents(pid_t root_pid, pid_t extra_pgid, proc_ident_t **idents_out, size_t *count_out) {
  if (root_pid <= 1 && extra_pgid <= 1) {
    *idents_out = NULL;
    *count_out = 0;
    return;
  }
  size_t cap = 32;
  size_t count = 0;
  proc_ident_t *idents = xmalloc(cap * sizeof(proc_ident_t));

  if (root_pid > 1) {
    proc_ident_t root_ident;
    if (pty_proc_get_ident(root_pid, &root_ident)) {
      idents[count++] = root_ident;
    } else {
      idents[count].pid = root_pid;
      idents[count].pgrp = (extra_pgid > 1 ? extra_pgid : root_pid);
      idents[count].starttime = 0;
      count++;
    }
  }

#ifdef __linux__
  bool added = true;
  while (added) {
    added = false;
    DIR *dir = opendir("/proc");
    if (dir == NULL) break;
    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL) {
      if (!isdigit((unsigned char)ent->d_name[0])) continue;
      pid_t pid = (pid_t)atoi(ent->d_name);
      if (pid <= 1) continue;

      bool already = false;
      for (size_t i = 0; i < count; i++) {
        if (idents[i].pid == pid) { already = true; break; }
      }
      if (already) continue;

      char stat_path[64];
      snprintf(stat_path, sizeof(stat_path), "/proc/%d/stat", pid);
      FILE *f = fopen(stat_path, "r");
      if (f == NULL) continue;
      char buf[1024];
      if (fgets(buf, sizeof(buf), f) != NULL) {
        char *closing = strrchr(buf, ')');
        if (closing != NULL && closing[1] == ' ') {
          char *p = closing + 2;
          char state = 0;
          int ppid = 0, pgrp = 0, session_id = 0;
          unsigned long long starttime = 0;
          int token_idx = 0;
          while (*p != '\0') {
            while (*p == ' ') p++;
            if (*p == '\0') break;
            char *token_start = p;
            while (*p != '\0' && *p != ' ') p++;
            if (token_idx == 0) state = *token_start;
            else if (token_idx == 1) ppid = atoi(token_start);
            else if (token_idx == 2) pgrp = atoi(token_start);
            else if (token_idx == 3) session_id = atoi(token_start);
            else if (token_idx == 19) {
              starttime = strtoull(token_start, NULL, 10);
              break;
            }
            token_idx++;
          }

          if (state != 'Z') {
            bool matches = false;
            if ((pid_t)session_id == root_pid) matches = true;
            for (size_t i = 0; i < count; i++) {
              if (idents[i].pid == (pid_t)ppid) {
                matches = true;
                break;
              }
            }
            if (!matches) {
              if (extra_pgid > 1 && (pid_t)pgrp == extra_pgid) {
                matches = true;
              } else {
                for (size_t i = 0; i < count; i++) {
                  if (idents[i].pgrp > 1 && idents[i].pgrp == (pid_t)pgrp) {
                    matches = true;
                    break;
                  }
                }
              }
            }

            if (matches) {
              if (count >= cap) {
                cap *= 2;
                idents = xrealloc(idents, cap * sizeof(proc_ident_t));
              }
              idents[count].pid = pid;
              idents[count].pgrp = (pid_t)pgrp;
              idents[count].starttime = starttime;
              count++;
              added = true;
            }
          }
        }
      }
      fclose(f);
    }
    closedir(dir);
  }
#endif

  *idents_out = idents;
  *count_out = count;
}

void pty_expand_tree_idents(proc_ident_t **idents_inout, size_t *count_inout) {
  if (idents_inout == NULL || *idents_inout == NULL || count_inout == NULL || *count_inout == 0) return;

#ifdef __linux__
  proc_ident_t *idents = *idents_inout;
  size_t count = *count_inout;
  const pid_t root_pid = idents[0].pid;
  size_t cap = count + 32;
  idents = xrealloc(idents, cap * sizeof(proc_ident_t));

  bool added = true;
  while (added) {
    added = false;
    DIR *dir = opendir("/proc");
    if (dir == NULL) break;
    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL) {
      if (!isdigit((unsigned char)ent->d_name[0])) continue;
      pid_t pid = (pid_t)atoi(ent->d_name);
      if (pid <= 1) continue;

      bool already = false;
      for (size_t i = 0; i < count; i++) {
        if (idents[i].pid == pid) { already = true; break; }
      }
      if (already) continue;

      char stat_path[64];
      snprintf(stat_path, sizeof(stat_path), "/proc/%d/stat", pid);
      FILE *f = fopen(stat_path, "r");
      if (f == NULL) continue;
      char buf[1024];
      if (fgets(buf, sizeof(buf), f) != NULL) {
        char *closing = strrchr(buf, ')');
        if (closing != NULL && closing[1] == ' ') {
          char *p = closing + 2;
          char state = 0;
          int ppid = 0, pgrp = 0, session_id = 0;
          unsigned long long starttime = 0;
          int token_idx = 0;
          while (*p != '\0') {
            while (*p == ' ') p++;
            if (*p == '\0') break;
            char *token_start = p;
            while (*p != '\0' && *p != ' ') p++;
            if (token_idx == 0) state = *token_start;
            else if (token_idx == 1) ppid = atoi(token_start);
            else if (token_idx == 2) pgrp = atoi(token_start);
            else if (token_idx == 3) session_id = atoi(token_start);
            else if (token_idx == 19) {
              starttime = strtoull(token_start, NULL, 10);
              break;
            }
            token_idx++;
          }

          if (state != 'Z') {
            bool matches = false;
            if ((pid_t)session_id == root_pid) matches = true;
            for (size_t i = 0; i < count; i++) {
              if (idents[i].pid == (pid_t)ppid && pty_proc_ident_alive(&idents[i])) {
                matches = true;
                break;
              }
            }
            if (!matches) {
              for (size_t i = 0; i < count; i++) {
                if (idents[i].pgrp > 1 && idents[i].pgrp == (pid_t)pgrp && pty_proc_ident_alive(&idents[i])) {
                  matches = true;
                  break;
                }
              }
            }

            if (matches) {
              if (count >= cap) {
                cap *= 2;
                idents = xrealloc(idents, cap * sizeof(proc_ident_t));
              }
              idents[count].pid = pid;
              idents[count].pgrp = (pid_t)pgrp;
              idents[count].starttime = starttime;
              count++;
              added = true;
            }
          }
        }
      }
      fclose(f);
    }
    closedir(dir);
  }

  *idents_inout = idents;
  *count_inout = count;
#endif
}

bool pty_tree_idents_alive(const proc_ident_t *idents, size_t count) {
  if (idents == NULL || count == 0) return false;
  for (size_t i = 0; i < count; i++) {
    if (pty_proc_ident_alive(&idents[i])) return true;
  }
  return false;
}

void pty_get_process_tree(pid_t root_pid, pid_t **pids_out, size_t *count_out) {
  proc_ident_t *idents = NULL;
  size_t count = 0;
  pty_get_process_tree_idents(root_pid, 0, &idents, &count);
  if (count == 0 || idents == NULL) {
    *pids_out = NULL;
    *count_out = 0;
    return;
  }
  pid_t *pids = xmalloc(count * sizeof(pid_t));
  for (size_t i = 0; i < count; i++) {
    pids[i] = idents[i].pid;
  }
  free(idents);
  *pids_out = pids;
  *count_out = count;
}

bool pty_tree_alive(pid_t root_pid) {
  proc_ident_t *idents = NULL;
  size_t count = 0;
  pty_get_process_tree_idents(root_pid, 0, &idents, &count);
  bool alive = pty_tree_idents_alive(idents, count);
  free(idents);
  return alive;
}

bool pty_kill_tree(pty_process *process, int sig) {
  if (process == NULL) return false;
#ifdef _WIN32
  return pty_kill(process, sig);
#else
  pid_t root_pid = process->pid;
  if (root_pid <= 1) return false;

  pid_t fg_pgid = pty_get_fg_pgid(process);
  proc_ident_t *idents = NULL;
  size_t count = 0;
  pty_get_process_tree_idents(root_pid, fg_pgid, &idents, &count);
  for (size_t i = 0; i < count; i++) {
    if (pty_proc_ident_alive(&idents[i])) {
      kill(idents[i].pid, sig);
      if (idents[i].pgrp > 1) kill(-idents[i].pgrp, sig);
    }
  }
  free(idents);
  return true;
#endif
}

#ifdef _WIN32
bool conpty_init() {
  uv_lib_t kernel;
  if (uv_dlopen("kernel32.dll", &kernel)) {
    uv_dlclose(&kernel);
    return false;
  }
  static struct {
    char *name;
    FARPROC *ptr;
  } conpty_entry[] = {{"CreatePseudoConsole", (FARPROC *) &pCreatePseudoConsole},
                      {"ResizePseudoConsole", (FARPROC *) &pResizePseudoConsole},
                      {"ClosePseudoConsole", (FARPROC *) &pClosePseudoConsole},
                      {NULL, NULL}};
  for (int i = 0; conpty_entry[i].name != NULL && conpty_entry[i].ptr != NULL; i++) {
    if (uv_dlsym(&kernel, conpty_entry[i].name, (void **) conpty_entry[i].ptr)) {
      uv_dlclose(&kernel);
      return false;
    }
  }
  return true;
}

static WCHAR *to_utf16(char *str) {
  int len = MultiByteToWideChar(CP_UTF8, 0, str, -1, NULL, 0);
  if (len <= 0) return NULL;
  WCHAR *wstr = xmalloc((len + 1) * sizeof(WCHAR));
  if (len != MultiByteToWideChar(CP_UTF8, 0, str, -1, wstr, len)) {
    free(wstr);
    return NULL;
  }
  wstr[len] = L'\0';
  return wstr;
}

// convert argv to cmdline for CreateProcessW
static WCHAR *join_args(char **argv) {
  char args[256] = {0};
  char **ptr = argv;
  for (; *ptr; ptr++) {
    char *quoted = (char *) quote_arg(*ptr);
    size_t arg_len = strlen(args) + 1;
    size_t quoted_len = strlen(quoted);
    if (arg_len == 1) memset(args, 0, 2);
    if (arg_len != 1) strcat(args, " ");
    strncat(args, quoted, quoted_len);
    if (quoted != *ptr) free(quoted);
  }
  if (args[255] != '\0') args[255] = '\0';  // truncate
  return to_utf16(args);
}

static bool conpty_setup(HPCON *hnd, COORD size, STARTUPINFOEXW *si_ex, char **in_name, char **out_name) {
  static int count = 0;
  char buf[256];
  HPCON pty = INVALID_HANDLE_VALUE;
  SECURITY_ATTRIBUTES sa = {0};
  HANDLE in_pipe = INVALID_HANDLE_VALUE;
  HANDLE out_pipe = INVALID_HANDLE_VALUE;
  const DWORD open_mode = PIPE_ACCESS_INBOUND | PIPE_ACCESS_OUTBOUND | FILE_FLAG_FIRST_PIPE_INSTANCE;
  const DWORD pipe_mode = PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_WAIT;
  DWORD pid = GetCurrentProcessId();
  bool ret = false;

  sa.nLength = sizeof(sa);
  snprintf(buf, sizeof(buf), "\\\\.\\pipe\\ttyd-term-in-%d-%d", pid, count);
  *in_name = strdup(buf);
  snprintf(buf, sizeof(buf), "\\\\.\\pipe\\ttyd-term-out-%d-%d", pid, count);
  *out_name = strdup(buf);
  in_pipe = CreateNamedPipeA(*in_name, open_mode, pipe_mode, 1, 0, 0, 30000, &sa);
  out_pipe = CreateNamedPipeA(*out_name, open_mode, pipe_mode, 1, 0, 0, 30000, &sa);
  if (in_pipe == INVALID_HANDLE_VALUE || out_pipe == INVALID_HANDLE_VALUE) {
    print_error("CreateNamedPipeA");
    goto failed;
  }

  HRESULT hr = pCreatePseudoConsole(size, in_pipe, out_pipe, 0, &pty);
  if (FAILED(hr)) {
    print_error("CreatePseudoConsole");
    goto failed;
  }

  si_ex->StartupInfo.cb = sizeof(STARTUPINFOEXW);
  si_ex->StartupInfo.dwFlags |= STARTF_USESTDHANDLES;
  si_ex->StartupInfo.hStdError = NULL;
  si_ex->StartupInfo.hStdInput = NULL;
  si_ex->StartupInfo.hStdOutput = NULL;
  size_t bytes_required;
  InitializeProcThreadAttributeList(NULL, 1, 0, &bytes_required);
  si_ex->lpAttributeList = (PPROC_THREAD_ATTRIBUTE_LIST) xmalloc(bytes_required);
  if (!InitializeProcThreadAttributeList(si_ex->lpAttributeList, 1, 0, &bytes_required)) {
    print_error("InitializeProcThreadAttributeList");
    goto failed;
  }
  if (!UpdateProcThreadAttribute(si_ex->lpAttributeList, 0, PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE, pty, sizeof(HPCON),
                                 NULL, NULL)) {
    print_error("UpdateProcThreadAttribute");
    goto failed;
  }
  count++;
  *hnd = pty;
  ret = true;
  goto done;

failed:
  ret = false;
  free(*in_name);
  *in_name = NULL;
  free(*out_name);
  *out_name = NULL;
done:
  if (in_pipe != INVALID_HANDLE_VALUE) CloseHandle(in_pipe);
  if (out_pipe != INVALID_HANDLE_VALUE) CloseHandle(out_pipe);
  return ret;
}

static void connect_cb(uv_connect_t *req, int status) { free(req); }

static void CALLBACK conpty_exit(void *context, BOOLEAN unused) {
  pty_process *process = (pty_process *) context;
  uv_async_send(&process->async);
}

static void async_cb(uv_async_t *async) {
  pty_process *process = (pty_process *) async->data;
  UnregisterWait(process->wait);

  DWORD exit_code;
  GetExitCodeProcess(process->handle, &exit_code);
  process->exit_code = (int) exit_code;
  process->exit_signal = 1;
  process->exit_cb(process);

  uv_close((uv_handle_t *) async, async_free_cb);
  process_free(process);
}

int pty_spawn(pty_process *process, pty_read_cb read_cb, pty_exit_cb exit_cb) {
  char *in_name = NULL;
  char *out_name = NULL;
  DWORD flags = EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT;
  COORD size = {(int16_t) process->columns, (int16_t) process->rows};

  if (!conpty_setup(&process->pty, size, &process->si, &in_name, &out_name)) return 1;

  SetConsoleCtrlHandler(NULL, FALSE);

  int status = 1;
  process->in = xmalloc(sizeof(uv_pipe_t));
  process->out = xmalloc(sizeof(uv_pipe_t));
  uv_pipe_init(process->loop, process->in, 0);
  uv_pipe_init(process->loop, process->out, 0);

  uv_connect_t *in_req = xmalloc(sizeof(uv_connect_t));
  uv_connect_t *out_req = xmalloc(sizeof(uv_connect_t));
  uv_pipe_connect(in_req, process->in, in_name, connect_cb);
  uv_pipe_connect(out_req, process->out, out_name, connect_cb);

  PROCESS_INFORMATION pi = {0};
  WCHAR *cmdline, *cwd;
  cmdline = join_args(process->argv);
  if (cmdline == NULL) goto cleanup;
  if (process->envp != NULL) {
    char **p = process->envp;
    for (; *p; p++) {
      WCHAR *env = to_utf16(*p);
      if (env == NULL) goto cleanup;
      _wputenv(env);
      free(env);
    }
  }
  if (process->cwd != NULL) {
    cwd = to_utf16(process->cwd);
    if (cwd == NULL) goto cleanup;
  }

  if (!CreateProcessW(NULL, cmdline, NULL, NULL, FALSE, flags, NULL, cwd, &process->si.StartupInfo, &pi)) {
    print_error("CreateProcessW");
    DWORD exitCode = 0;
    if (GetExitCodeProcess(pi.hProcess, &exitCode)) printf("== exit code: %d\n", exitCode);
    goto cleanup;
  }

  process->pid = pi.dwProcessId;
  process->handle = pi.hProcess;
  process->paused = true;
  process->read_cb = read_cb;
  process->exit_cb = exit_cb;
  process->async.data = process;
  uv_async_init(process->loop, &process->async, async_cb);

  if (!RegisterWaitForSingleObject(&process->wait, pi.hProcess, conpty_exit, process, INFINITE, WT_EXECUTEONLYONCE)) {
    print_error("RegisterWaitForSingleObject");
    goto cleanup;
  }

  status = 0;

cleanup:
  if (in_name != NULL) free(in_name);
  if (out_name != NULL) free(out_name);
  if (cmdline != NULL) free(cmdline);
  if (cwd != NULL) free(cwd);
  return status;
}
#else
static bool fd_set_cloexec(const int fd) {
  int flags = fcntl(fd, F_GETFD);
  if (flags < 0) return false;
  return (flags & FD_CLOEXEC) == 0 || fcntl(fd, F_SETFD, flags | FD_CLOEXEC) != -1;
}

static bool fd_duplicate(int fd, uv_pipe_t *pipe) {
  int fd_dup = dup(fd);
  if (fd_dup < 0) return false;

  if (!fd_set_cloexec(fd_dup)) {
    close(fd_dup);
    return false;
  }

  int status = uv_pipe_open(pipe, fd_dup);
  if (status) close(fd_dup);
  return status == 0;
}

static void wait_cb(void *arg) {
  pty_process *process = (pty_process *)arg;
  int stat = 0;
  pid_t pid;
  do
    pid = waitpid(process->pid, &stat, 0);
  while (pid < 0 && errno == EINTR);

  process->wait_complete = true;
  process->wait_succeeded = pid == process->pid;
  process->wait_error = process->wait_succeeded ? 0 : errno;
  if (process->wait_succeeded && WIFEXITED(stat)) {
    process->exit_code = WEXITSTATUS(stat);
  } else if (process->wait_succeeded && WIFSIGNALED(stat)) {
    int sig = WTERMSIG(stat);
    process->exit_code = 128 + sig;
    process->exit_signal = sig;
  }
  uv_async_send(&process->async);
}

static void async_cb(uv_async_t *async) {
  pty_process *process = (pty_process *)async->data;
  process->exit_callback_delivered = true;
  process->exit_cb(process);
  process_maybe_close(process);
}

int pty_spawn(pty_process *process, pty_read_cb on_read_cb, pty_exit_cb on_exit_cb) {
  int status = 0;

  uv_disable_stdio_inheritance();

  int master = -1;
  pid_t pid;
  struct winsize size = {process->rows, process->columns, 0, 0};
  pid = forkpty(&master, NULL, NULL, &size);
  if (pid < 0) return -errno;
  if (pid == 0) {
    setsid();
    if (process->cwd != NULL && chdir(process->cwd) != 0) _exit(-errno);
    if (process->envp != NULL) {
      char **p = process->envp;
      for (; *p; p++) putenv(*p);
    }
    int ret = execvp(process->argv[0], process->argv);
    if (ret < 0) {
      perror("execvp failed\n");
      _exit(-errno);
    }
  }

  process->pty = master;
  process->pid = pid;
  process->async_initialized = false;
  process->thread_started = false;

  int flags = fcntl(master, F_GETFL);
  if (flags == -1) {
    status = -errno;
    goto error_master;
  }
  if (fcntl(master, F_SETFL, flags | O_NONBLOCK) == -1) {
    status = -errno;
    goto error_master;
  }
  if (!fd_set_cloexec(master)) {
    status = -errno;
    goto error_master;
  }

  process->in = xmalloc(sizeof(uv_pipe_t));
  process->out = xmalloc(sizeof(uv_pipe_t));
  uv_pipe_init(process->loop, process->in, 0);
  uv_pipe_init(process->loop, process->out, 0);

  if (!fd_duplicate(master, process->in) || !fd_duplicate(master, process->out)) {
    status = -errno;
    goto error_pipes;
  }

  process->read_cb = on_read_cb;
  process->exit_cb = on_exit_cb;
  process->out->data = process;
  process->paused = true;

  // Stage 1: start the continuous PTY read before creating exit machinery.
  status = uv_read_start((uv_stream_t *)process->out, alloc_cb, read_cb);
  if (status != 0) goto error_pipes;
  process->paused = false;

  // Stage 2: initialize the event-loop exit notification handle.
  process->async.data = process;
  status = uv_async_init(process->loop, &process->async, async_cb);
  if (status != 0) {
    uv_read_stop((uv_stream_t *)process->out);
    goto error_pipes;
  }
  process->async_initialized = true;

  // Stage 3: commit only after the wait thread has started successfully.
  status = uv_thread_create(&process->tid, wait_cb, process);
  if (status != 0) {
    uv_read_stop((uv_stream_t *)process->out);
    uv_kill(pid, SIGKILL);
    waitpid(pid, NULL, 0);
    process->pid = -1;
    uv_close((uv_handle_t *)&process->async, async_free_cb);
    process_free(process);
    return status;
  }
  process->thread_started = true;
  return 0;

error_pipes:
  if (process->in != NULL) {
    uv_close((uv_handle_t *)process->in, close_cb);
    process->in = NULL;
  }
  if (process->out != NULL) {
    uv_close((uv_handle_t *)process->out, close_cb);
    process->out = NULL;
  }

error_master:
  if (process->pty >= 0) {
    close(process->pty);
    process->pty = -1;
  }
  if (process->pid > 0) {
    uv_kill(process->pid, SIGKILL);
    waitpid(process->pid, NULL, 0);
    process->pid = -1;
  }
  return status;
}
#endif
