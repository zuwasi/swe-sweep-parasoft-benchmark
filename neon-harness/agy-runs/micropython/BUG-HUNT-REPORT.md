# MicroPython Independent Quality Review — Bug Hunt Report

Commit: `9b486340da22931cde82872f79e1c34db959548b`
Scope: C code under `py/`, `ports/unix/`, and `shared/`.

## Summary Table

| ID | Severity | Subsystem | Title | Status |
|---|---|---|---|---|
| MP-001 | Critical | `ports/unix` (`moduos.c`) | Heap buffer overflow in `uos.urandom()` on negative length via `size_t` wraparound | CONFIRMED |
| MP-002 | Critical | `ports/unix` (`modffi.c`) | Heap buffer overflow in `ffi.callback()` when `paramtypes` lacks `__len__` | CONFIRMED |
| MP-003 | Critical | `ports/unix` (`unix_mphal.c`) | Missing `nlr_pop()` on early returns in `call_dupterm_read()` corrupts NLR exception stack | SUSPECTED |
| MP-004 | High | `ports/unix` (`modusocket.c`) | Stack buffer over-read in `socket.accept()` when peer address exceeds 32 bytes (`AF_UNIX`) | CONFIRMED |
| MP-005 | High | `ports/unix` (`modusocket.c`) | Missing buffer length checks in `usocket.sockaddr()` and `inet_ntop()` cause OOB read and unsigned underflow | CONFIRMED |
| MP-006 | High | `ports/unix` (`main.c`) | Out-of-bounds read past `MICROPYPATH=""` leaks adjacent environment variables into `sys.path` | CONFIRMED |
| MP-007 | High | `ports/unix` (`modtermios.c`) | Missing type and length checks in `termios.tcsetattr()` cause OOB heap read / NULL deref | CONFIRMED |
| MP-008 | High | `ports/unix` (`modtime.c`) | Unchecked NULL return from `gmtime()`/`localtime()` causes SEGFAULT on out-of-range timestamps | CONFIRMED |
| MP-009 | High | `ports/unix` (`modffi.c`) | Unvalidated argument count/kwargs in `ffifunc_call()` aborts (debug) or reads OOB/uninitialized args (release) | CONFIRMED |
| MP-010 | High | `ports/unix` (`alloc.c`) | Pointer-to-pointer bug in `mp_unix_free_exec()` corrupts `mmap_region_head` list; failed `mmap` causes GC NULL deref | SUSPECTED |
| MP-011 | High | `shared/readline` (`readline.c`) | Stack buffer overflow / assertion failure in `mp_hal_move_cursor_back()` for cursor moves >= 1000 chars | CONFIRMED |
| MP-012 | High | `shared/netutils` (`dhcpserver.c`) | Uninitialized stack reads and stack buffer over-reads in DHCP option parsing (`opt_find` / `dhcp_server_process`) | SUSPECTED |
| MP-013 | Medium | `ports/unix` (`modffi.c`) | 64-bit `long` (`'l'`) FFI return values truncated to 32-bit `signed int` on LP64 systems | CONFIRMED |
| MP-014 | Medium | `ports/unix` (`modusocket.c`, `modtime.c`) | Floating-point rounding sets `tv_usec = 1000000`, causing spurious `OSError(EDOM/EINVAL)` | CONFIRMED |
| MP-015 | Medium | `ports/unix` (`main.c`) | Unchecked `malloc()` failure in `-X heapsize=` causes NULL dereference in `gc_init()` | CONFIRMED |
| MP-016 | Medium | `ports/unix` (`mpthreadport.c`) | Unchecked `pthread_kill()` and unretried `EINTR` on `sem_wait()` in `mp_thread_gc_others()` cause GC race/deadlock | SUSPECTED |
| MP-017 | Medium | `shared/readline` (`readline.c`) | `size_t` underflow OOB read (`rl.cursor_pos - 1`) on Tab when cursor is at column 0 of non-empty line | SUSPECTED |
| MP-018 | Medium | `shared/libc` (`string0.c`) | Signed `char` comparisons in `memcmp`/`strcmp`/`strncmp` and mismatched casts in `strchr`/`memchr` violate C99 | SUSPECTED |
| MP-019 | Medium | `shared/memzip` (`memzip.c`) | Prefix-only comparison in `memzip_find_file_header()` matches wrong files sharing a prefix | SUSPECTED |
| MP-020 | Critical | `py/` (`objstr.c`) | Negative width in `str.center()` wraps `size_t` and triggers heap buffer overflow in `memset()` | CONFIRMED |
| MP-021 | Critical | `py/` (`objstr.c`, `objlist.c`, `objtuple.c`) | Missing multiplication overflow check in sequence `*` causes heap/global buffer overflow | CONFIRMED |
| MP-022 | Critical | `py/` (`objarray.c`) | `array_construct()` trusts iterable `__len__` without bounds checks, causing heap overflow or stale length | CONFIRMED |
| MP-023 | Critical | `py/` (`objtype.c`) | Native-type subclass overriding `__new__` via `object.__new__` leaves `subobj[0]` uninitialized (type confusion / SIGSEGV) | CONFIRMED |
| MP-024 | Critical | `py/` (`objlist.c`) | `list.sort(key=...)` holds raw `head`/`tail` pointers across Python callbacks, causing UAF / SIGSEGV on list mutation | CONFIRMED |
| MP-025 | Critical | `py/` (`persistentcode.c`) | `.mpy` loader (`read_uint`, `load_obj`, `load_raw_code`, `mp_native_relocate`) lacks EOF/bounds checks (infinite loop, assert abort, OOB) | CONFIRMED |
| MP-026 | High | `py/` (`modbuiltins.c`) | Exception in `class` body skips `mp_locals_set(old_locals)`, permanently corrupting module `locals()` | CONFIRMED |
| MP-027 | High | `py/` (`objstringio.c`) | `StringIO.seek()` omits open check before dereferencing `o->vstr`, causing NULL dereference / SIGSEGV | CONFIRMED |
| MP-028 | High | `py/` (`mpz.c`, `objint_mpz.c`) | `pow(a, b, 0)` aborts/reads OOB; `0**0` (mpz) and `pow(0, 0, m)` return `0`; negative exponent/modulus bugs | CONFIRMED |
| MP-029 | High | `py/` (`objrange.c`) | `range` truncates 64-bit `mp_int_t` into 63-bit small-int (sign flip) and overflows signed subtraction in `range_len` | CONFIRMED |
| MP-030 | High | `py/` (`modstruct.c`) | `get_fmt_num()` uses unchecked `MP_OBJ_SMALL_INT_VALUE` (pointer bits read as repeat count) and unchecked pointer arithmetic | CONFIRMED |
| MP-031 | High | `py/` (`binary.c`, `modstruct.c`) | `mp_binary_get_size()` missing `case '=':`, breaking all native-order standard-size `ustruct` formats | CONFIRMED |
| MP-032 | High | `py/` (`objarray.c`) | Array/bytearray comparisons confuse signed/unsigned types and compare multi-byte integers via little-endian `memcmp` | CONFIRMED |
| MP-033 | Medium | `py/` (`objlist.c`) | `list.insert()` uses unchecked `MP_OBJ_SMALL_INT_VALUE`, silently misinterpreting non-small-int indices | CONFIRMED |
| MP-034 | Medium | `py/` (`parsenum.c`, `mpz.c`) | Number parser accepts digitless strings (`int("_")`, `float(".")`) and rejects underscored big ints | CONFIRMED |
| MP-035 | Medium | `py/` (`modmath.c`) | `math.pow(2.0, inf)` raises `ValueError` due to missing `!isinf(y)` check; `math.ldexp()` truncates 64-bit exponent to 32-bit `int` | CONFIRMED |
| MP-036 | Medium | `py/` (`modcmath.c`) | `cmath.log(0)` returns `-inf` instead of `ValueError`; `polar`/`log`/`sqrt` overflow for `abs(z) > 1.34e154` | CONFIRMED |
| MP-037 | Medium | `py/` (`objgenerator.c`) | Calling `.throw(exc)` on an exhausted generator returns `StopIteration` instead of raising `exc` | CONFIRMED |
| MP-038 | Medium | `py/` (`modbuiltins.c`) | `round(1, -(1<<62))` overflows small-int negation and raises `ZeroDivisionError` | CONFIRMED |
| MP-039 | Medium | `py/` (`stream.c`) | `stream_unbuffered_readline()` uses unchecked `MP_OBJ_SMALL_INT_VALUE` on optional `size` argument | CONFIRMED |
| MP-040 | Medium | `py/` (`objstr.c`) | `str.rsplit`/`startswith`/`endswith` accept `bytes` on `str`; `'{:c}'.format()` truncates `>= 0x100` and emits invalid UTF-8 | CONFIRMED |
| MP-041 | Medium | `py/` (`objint.c`) | `(-1).to_bytes(10, 'big')` zero-pads high bytes instead of sign-extending or rejecting negative values | CONFIRMED |
| MP-042 | Medium | `py/` (`objdict.c`, `runtime.c`) | Negative `__len__` hint causes unsigned wraparound and multi-gigabyte allocation failure in `dict.fromkeys` and `*` unpacking | CONFIRMED |
| MP-043 | Medium | `py/` (`objexcept.c`) | Unsigned underflow in `decompress_error_text_maybe()` when `emg_buf_size < EMG_BUF_STR_BUF_OFFSET` causes NULL deref under OOM | SUSPECTED |
| MP-044 | Medium | `py/` (`objarray.c`, `objlist.c`, `vstr.c`) | Stale source pointer UAF on self-extend/self-slice-assign reallocation, and 32-bit `ROUND_ALLOC` truncation in `vstr.c` | SUSPECTED |
| MP-045 | Critical | `py/` (`objnamedtuple.c`) | Zero-field `namedtuple` overwrites read-only global `mp_const_empty_tuple.base.type` (SIGSEGV) | CONFIRMED |
| MP-046 | Critical | `py/` (`modio.c`) | `IOBase` passes stack-allocated mutable `bytearray` to Python callbacks (stack UAR, ROM write SIGSEGV, `gc_realloc` abort) | CONFIRMED |
| MP-047 | Critical | `py/` (`map.c`) | Clearing/rehashing `dict` or `set` inside `__eq__` causes division by zero (`SIGFPE`) and dangling `avail_slot` UAF | CONFIRMED |
| MP-048 | Critical | `py/` (`emitbc.c`, `emitnative.c`) | Unchecked 8-bit packing in `unpack_ex`, `call_function`, and closures causes VM stack corruption (`SIGSEGV`) and assertion aborts | CONFIRMED |
| MP-049 | Critical | `py/` (`emitnative.c`, `smallint.c`) | Viper `//` and `%` lack zero-divisor and `INT64_MIN // -1` checks, crashing the interpreter with hardware `SIGFPE` | CONFIRMED |
| MP-050 | Critical | `py/` (`emitnative.c`) | Viper emitter asserts `VTYPE_PYOBJ` / cast arity instead of type-checking (`SIGABRT` in debug; raw-int type confusion in release) | CONFIRMED |
| MP-051 | Critical | `py/` (`gc.c`) | `ATB_GET_KIND(block + n_blocks)` reads/corrupts past end of alloc table; `gc_realloc` `size_t` overflow frees live block and returns it | SUSPECTED |
| MP-052 | High | `py/` (`objstrunicode.c`) | `str_subscr` computes multi-byte length from lead byte without bounds check, reading OOB on malformed UTF-8 `str` | CONFIRMED |
| MP-053 | High | `py/` (`objslice.c`) | `slice.indices()` accepts negative length and truncates 64-bit bounds/step into 63-bit small-int (sign flip) | CONFIRMED |
| MP-054 | High | `py/` (`profile.c`) | `sys.settrace` has `raw_code_lnotab` heap overflow / assert aborts, dangling `frame->code_state` UAF, and stuck `mp_prof_is_executing` | SUSPECTED |
| MP-055 | High | `py/` (`objmodule.c`) | `module_attr_try_delegation()` indexes `map->table[map->alloc - 1]` without checking `map->alloc > 0` (NULL deref on empty dict) | SUSPECTED |
| MP-056 | High | `shared/netutils` (`trace.c`) | `netutils_ethernet_trace()` reads IP/TCP/UDP/DHCP/IPv6 headers without length checks and suffers `size_t` underflow OOB reads | SUSPECTED |
| MP-057 | High | `ports/unix` (`modjni.c`) | Format-string injection in `print_jobject()`, 64-byte stack overflow in `get_jclass_name()`, and unbounded `strprev()` scan | SUSPECTED |
| MP-058 | High | `ports/unix` (`mpbthciport.c`, `mpbtstackport_usb.c`) | Stack buffer overflow via `strcpy` from `MICROPYBTUART`, `pthread_join` on detached threads, and UART fd leak on error | SUSPECTED |
| MP-059 | Medium | `py/` (`lexer.c`) | F-string lexer fails on adjacent f-strings (`f'{1}' f'{2}'`), underflows `nested_bracket_level` on `']'`, and sign-extends `char` | CONFIRMED |
| MP-060 | Medium | `py/` (`builtinimport.c`) | `__import__` uses unchecked `MP_OBJ_SMALL_INT_VALUE` for `level`; non-external weak-link path passes `mp_obj_t` to `strcpy()` | CONFIRMED |
| MP-061 | Medium | `py/` (`objcomplex.c`) | Complex `abs()`, `/`, and `**` compute `real*real + imag*imag` unscaled, overflowing for `abs(z) > 1.34e154` (`0j` / `nan`) | CONFIRMED |
| MP-062 | Medium | `py/` (`modio.c`, `modthread.c`, `reader.c`, `ports/unix/input.c`) | `BufferedWriter` infinite loop on `alloc==0` & flush assert; thread `th_args` GC root race; `EINTR` EOF in `reader.c`; `buf[-1]` in `input.c` | SUSPECTED |
| MP-063 | High | `ports/unix` (`moduselect.c`) | `uselect.poll` has negative/`uint16` `alloc` wrap, `ipoll()` assert abort (`SIGABRT`), stale `revents` on `unregister`, and 32-bit timeout truncation | CONFIRMED |
| MP-064 | Medium | `py/` (`formatfloat.c`) | Float formatting rounds values `< 1.0` prematurely with `while (--e)` underflow (`0.999999999996` -> `1.0`) and omits carry room in `'f'` mode | CONFIRMED |
| MP-065 | High | `shared/runtime` (`pyexec.c`) | Double `reader->close()` on post-parse exception in `parse_compile_execute()` causes double-free for heap-backed readers | SUSPECTED |
| MP-066 | High | `ports/unix` (`modmachine.c`) | Unchecked `mmap()` `MAP_FAILED` return and missing `munmap()` leak in `/dev/mem` mapping; `if (!fd)` mishandles fd `0` | SUSPECTED |
| MP-067 | Medium | `shared/timeutils` (`timeutils.c`) | Unbounded `days_since_jan1[month]` OOB read, 32-bit year-2068 signed wraparound, and pre-2000 unsigned underflow in leap-day math | SUSPECTED |
| MP-068 | Medium | `shared/netutils` (`netutils.c`), `shared/libc` (`printf.c`) | `netutils_parse_ipv4_addr()` accepts non-digits/octets `>255`; internal `vsnprintf(NULL, 0, ...)` calls `memcpy(NULL, ..., 0)` and `putchar(0xff)` returns `-1` | SUSPECTED |

---

## Detailed Findings

### MP-001: Heap buffer overflow in `uos.urandom()` on negative length via `size_t` wraparound
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `ports/unix/moduos.c:91-97`, `ports/unix/unix_mphal.c:246-255`
- **Mechanism**: `mp_uos_urandom()` parses `mp_int_t n = mp_obj_get_int(num)` without verifying `n >= 0`. Passing `-1` converts `n` to `(size_t)-1` in `vstr_init_len(&vstr, n)`. Inside `vstr_init(&vstr, len + 1)`, `len + 1` wraps to `0`, allocating a minimal buffer while setting `vstr.len = (size_t)-1`. `mp_hal_get_random(n, vstr.buf)` then invokes `getrandom(vstr.buf, (size_t)-1, 0)` (or `read`), writing megabytes of random data past the end of the GC heap. Additionally, `mp_hal_get_random()` does not loop on short reads from `getrandom()`/`read()`.
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "import uos; uos.urandom(-1)"
  ```
  ASan output: `ERROR: AddressSanitizer: heap-buffer-overflow ... WRITE of size 10593568 ... in getrandom` at `ports/unix/unix_mphal.c:248` called from `ports/unix/moduos.c:95`.
- **Remediation**: Validate `if (n < 0) { mp_raise_ValueError(...); }` in `mp_uos_urandom()`, and loop in `mp_hal_get_random()` until all `n` bytes are filled.

### MP-002: Heap buffer overflow in `ffi.callback()` when `paramtypes` lacks `__len__`
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `ports/unix/modffi.c:337-351`
- **Mechanism**: `mod_ffi_callback()` computes `mp_int_t nparams = MP_OBJ_SMALL_INT_VALUE(mp_obj_len_maybe(paramtypes_in))` without checking if `mp_obj_len_maybe()` returned `MP_OBJ_NULL` (which happens for generators and other iterables without `__len__`). `MP_OBJ_SMALL_INT_VALUE(MP_OBJ_NULL)` evaluates to `0`, so `mp_obj_malloc_var(mp_obj_fficallback_t, ffi_type *, 0, ...)` allocates zero slots for `o->params[]`. The subsequent iteration loop writes `o->params[i++] = get_ffi_type(item)` out of bounds on the GC heap, corrupting adjacent objects and crashing. (Additionally, `o->clo` allocated via `ffi_closure_alloc()` has no finalizer and leaks on both normal GC and error paths.)
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import ffi; ffi.callback('i', lambda *a: 0, (x for x in 'i'*200))"
  ```
  Result: `Segmentation fault (exit 139)`.
- **Remediation**: Check `mp_obj_t len_obj = mp_obj_len_maybe(paramtypes_in)` (or require a string/sequence via `mp_obj_str_get_data()`), verify `i < nparams` during iteration, and free `o->clo` on error/finalization.

### MP-003: Missing `nlr_pop()` on early returns in `call_dupterm_read()` corrupts NLR exception stack
- **Severity**: Critical
- **Status**: SUSPECTED
- **Location**: `ports/unix/unix_mphal.c:125-144`
- **Mechanism**: Inside `if (nlr_push(&nlr) == 0)`, two early `return` statements — `if (res == mp_const_none) { return -2; }` (line 133) and `if (bufinfo.len == 0) { ... return -1; }` (line 140) — return from `call_dupterm_read()` without calling `nlr_pop()`. This leaves a dangling pointer to the dead stack frame's `nlr_buf_t` at the top of the NLR stack. Worse, `mp_hal_stdin_rx_chr()` immediately loops `do { c = call_dupterm_read(0); } while (c == -2);`, re-entering `call_dupterm_read()` at the same stack address and pushing `&nlr` onto itself (`nlr.prev == &nlr`), creating a cycle in the NLR chain and causing stack corruption / infinite loop on the next exception or `nlr_pop()`.
- **Remediation**: Call `nlr_pop()` before both early returns (lines 133 and 140).

### MP-004: Stack buffer over-read in `socket.accept()` when peer address exceeds 32 bytes (`AF_UNIX`)
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `ports/unix/modusocket.c:249-262`
- **Mechanism**: `socket_accept()` allocates a 32-byte stack buffer `byte addr[32]` and passes `addr_len = sizeof(addr)` to `accept()`. Per POSIX `accept(2)`, when the peer's address (such as an `AF_UNIX` `sockaddr_un` with a path > 30 bytes) exceeds the buffer size, the kernel truncates the written data but updates `addr_len` to the *actual untruncated length* (> 32). Line 262 then passes the unclamped `addr_len` to `mp_obj_new_bytearray(addr_len, &addr)`, reading past `addr` on the stack and exposing stack memory in the returned bytearray.
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "
  import usocket, uos
  p1, p2 = '/tmp/mp_s1_' + 'a'*60, '/tmp/mp_s2_' + 'b'*60
  for p in (p1, p2):
      try: uos.remove(p)
      except: pass
  mk = lambda p: b'\x01\x00' + p.encode() + b'\x00'
  srv = usocket.socket(usocket.AF_UNIX, usocket.SOCK_STREAM); srv.bind(mk(p1)); srv.listen(1)
  cli = usocket.socket(usocket.AF_UNIX, usocket.SOCK_STREAM); cli.bind(mk(p2)); cli.connect(mk(p1))
  c, addr = srv.accept()
  "
  ```
  ASan output: `ERROR: AddressSanitizer: stack-buffer-overflow ... READ of size 83 ... in mp_obj_new_bytearray` from `modusocket.c:262`.
- **Remediation**: Clamp `if (addr_len > sizeof(addr)) { addr_len = sizeof(addr); }` (or use `struct sockaddr_storage`).

### MP-005: Missing buffer length checks in `usocket.sockaddr()` and `inet_ntop()` cause OOB read and unsigned underflow
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `ports/unix/modusocket.c:552-563, 638-669`
- **Mechanism**:
  1. `mod_socket_sockaddr()` dereferences `((struct sockaddr *)bufinfo.buf)->sa_family` (line 641) without checking `bufinfo.len >= sizeof(sa_family_t)`. For `AF_INET` (line 643) and `AF_INET6` (line 651), it reads `struct sockaddr_in` (16 bytes) or `struct sockaddr_in6` (28 bytes) without verifying `bufinfo.len`. In the `default:` branch (line 664), `bufinfo.len - offsetof(struct sockaddr, sa_data)` underflows when `bufinfo.len < 2`, requesting `(size_t)-1` / `(size_t)-2` bytes.
  2. `mod_socket_inet_ntop()` passes `bufinfo.buf` directly to `inet_ntop()` (line 558) without checking `bufinfo.len >= sizeof(struct in_addr)` (4) or `sizeof(struct in6_addr)` (16), reading past the buffer and leaking adjacent heap bytes into the formatted IP string.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import usocket; usocket.sockaddr(b'')"
  ./ports/unix/build-rev-dbg/micropython -c "import usocket; print(usocket.sockaddr(b'\x02\x00'))"
  ./ports/unix/build-rev-dbg/micropython -c "import usocket; print(usocket.inet_ntop(usocket.AF_INET6, b'a'))"
  ```
  Results: `MemoryError: memory allocation failed, allocating 4294967295 bytes` (underflow), `(2, b'\x00\x00\x00\x00', 0)` (OOB read of 6+ bytes), and `6100::` (OOB read of 15 bytes).
- **Remediation**: Validate `bufinfo.len` against the required `sockaddr*` / `in_addr` / `in6_addr` structure sizes before dereferencing or calling `inet_ntop()`.

### MP-006: Out-of-bounds read past `MICROPYPATH=""` leaks adjacent environment variables into `sys.path`
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `ports/unix/main.c:515-549`
- **Mechanism**: When `MICROPYPATH` is set to the empty string `""`, the counting loop at line 519 (`for (char *p = path; p != NULL; p = strchr(p, ':')) { path_num++; if (p != NULL) p++; }`) increments `p` past the terminating NUL byte of `""` into the immediately following environment string in memory. `strchr(p, ':')` then scans out-of-bounds through adjacent environment variables, counting their colons and causing lines 530-548 to populate `sys.path` with out-of-bounds environment data.
- **Repro**:
  ```bash
  env -i MICROPYPATH="" SECRET=foo:bar:baz ./ports/unix/build-rev-dbg/micropython -c "import sys; print(sys.path)"
  ```
  Output: `['', '', 'SECRET=foo', 'bar']` (leaks `SECRET=foo` and `bar` from the adjacent `SECRET` environment variable).
- **Remediation**: Handle empty `path` (`*path == '\0'`) explicitly, or check `if (*p == '\0') break;` before `p++`.

### MP-007: Missing type and length checks in `termios.tcsetattr()` cause OOB heap read / NULL deref
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `ports/unix/modtermios.c:70-107`
- **Mechanism**: `mod_termios_tcsetattr()` only checks `assert(mp_obj_is_type(attrs_in, &mp_type_list))` (no runtime check in release builds) and never checks `attrs->len >= 7`, nor that `attrs->items[6]` is a list with `cc->len >= NCCS`. Passing a short or empty list reads `attrs->items[0..6]` out of bounds (or dereferences `NULL` when `items == NULL`). Additionally, `struct termios term` (line 71) is uninitialized on the stack.
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "import termios; termios.tcsetattr(0, 0, [])"
  ```
  ASan output: `ERROR: AddressSanitizer: SEGV on unknown address 0x000000000000` in `mp_obj_get_int` called from `modtermios.c:85`.
- **Remediation**: Zero-initialize `term`, validate types and exact lengths (`attrs->len == 7`, `cc->len == NCCS`) with `mp_obj_get_array_fixed_n()`, and raise `TypeError`/`ValueError` on invalid inputs.

### MP-008: Unchecked NULL return from `gmtime()`/`localtime()` causes SEGFAULT on out-of-range timestamps
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `ports/unix/modtime.c:141-165`
- **Mechanism**: `mod_time_gm_local_time()` casts `mp_float_t` to `time_t` without range checking (UB on NaN/Inf/overflow) and calls `gmtime(&t)` or `localtime(&t)` without checking for `NULL`. On 64-bit Linux, timestamps whose year overflows 32-bit `tm_year` cause `gmtime()`/`localtime()` to return `NULL` (`EOVERFLOW`), which line 152 immediately dereferences (`tm->tm_year`).
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "import utime; utime.gmtime(1e20)"
  ```
  Output: `modtime.c:152:23: runtime error: member access within null pointer of type 'struct tm'` followed by `AddressSanitizer: SEGV on unknown address 0x000000000014`.
- **Remediation**: Check `if (tm == NULL) { mp_raise_OSError(errno); }` (or `OverflowError`) and validate float bounds before casting to `time_t`.

### MP-009: Unvalidated argument count/kwargs in `ffifunc_call()` aborts (debug) or reads OOB/uninitialized args (release)
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `ports/unix/modffi.c:482-526`
- **Mechanism**: `ffifunc_call()` uses `assert(n_kw == 0); assert(n_args == self->cif.nargs);` instead of raising `TypeError`. In debug builds, calling any FFI function with the wrong number of arguments or with keyword arguments aborts the interpreter. In release builds (`-DNDEBUG`), passing too many arguments walks `argtype++` past `self->argtypes` (OOB read), and passing too few leaves `ffi_call()` reading past the end of `valueptrs[n_args]` (stack buffer over-read).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import ffi; libc = ffi.open('libc.so.6'); f = libc.func('i', 'abs', 'i'); f()"
  ```
  Output: `micropython: modffi.c:486: ffifunc_call: Assertion 'n_args == self->cif.nargs' failed. Aborted`.
- **Remediation**: Replace the `assert()` calls with `mp_arg_check_num(n_args, n_kw, self->cif.nargs, self->cif.nargs, false);`.

### MP-010: Pointer-to-pointer bug in `mp_unix_free_exec()` corrupts `mmap_region_head` list; failed `mmap` causes GC NULL deref
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `ports/unix/alloc.c:52-86`
- **Mechanism**:
  1. In `mp_unix_free_exec()` (line 72), the loop increment is `*rg = (*rg)->next` instead of `rg = &(*rg)->next`. Whenever the first node in `mmap_region_head` is not the region being freed, `*rg = (*rg)->next` overwrites `MP_STATE_VM(mmap_region_head)` itself, permanently unlinking and discarding all preceding live executable regions from GC root scanning (leading to premature collection / use-after-free of objects referenced by native/viper code).
  2. In `mp_unix_alloc_exec()` (lines 56-65), if `mmap()` returns `MAP_FAILED`, `*ptr` is set to `NULL` but a node with `rg->ptr = NULL` and `rg->len = min_size` is still prepended to `mmap_region_head`. On the next GC cycle, `mp_unix_mark_exec()` calls `gc_collect_root(NULL, rg->len / sizeof(mp_uint_t))`, causing a NULL pointer dereference.
- **Remediation**: Fix line 72 to `rg = &(*rg)->next`, and return early without linking when `mmap()` fails.

### MP-011: Stack buffer overflow / assertion failure in `mp_hal_move_cursor_back()` for cursor moves >= 1000 chars
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `shared/readline/readline.c:72-86`
- **Mechanism**: `mp_hal_move_cursor_back()` formats `"\x1b[%u"` into a 6-byte stack buffer `char vt100_command[6]`, leaving room for at most 3 digits (`pos <= 999`). When moving the cursor back by >= 1000 characters (e.g., typing/pasting 1000+ characters in the REPL and pressing Ctrl-A / Home), `snprintf()` returns `n >= 6`. Debug builds abort on `assert((unsigned)n < sizeof(vt100_command))`; release builds (`-DNDEBUG`) write `'D'` out of bounds at `vt100_command[n]` (stack buffer overflow) and transmit `n + 1` bytes from the 6-byte buffer (stack over-read).
- **Repro**:
  Start the REPL (`./ports/unix/build-rev-dbg/micropython -i -c pass` in a PTY), write 1010 `'a'` characters followed by `\x01` (Ctrl-A):
  Output: `micropython: ../../shared/readline/readline.c:81: mp_hal_move_cursor_back: Assertion '(unsigned)n < sizeof(vt100_command)' failed.` (exit status `-6` / SIGABRT).
- **Remediation**: Increase buffer size to `char vt100_command[16]` (enough for `\x1b[4294967295D\0`) and check `(unsigned)n < sizeof(vt100_command)`.

### MP-012: Uninitialized stack reads and stack buffer over-reads in DHCP option parsing
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `shared/netutils/dhcpserver.c:146-154, 190-208, 241-254`
- **Mechanism**:
  1. `dhcp_msg_t dhcp_msg` (line 190) is uninitialized on the stack; `pbuf_copy_partial()` may copy as few as `DHCP_MIN_SIZE` (243) bytes, leaving up to 305 bytes of `dhcp_msg.options` uninitialized.
  2. `opt_find()` (line 147) scans up to fixed bound `308` instead of the actual copied packet length, reading uninitialized stack bytes.
  3. `opt_find()` does not handle 1-byte `DHCP_OPT_PAD` (`0`) options, and at `i == 307` reads `opt[i + 1]` = `opt[308]` (1 byte past `dhcp_msg.options[312]`, since `opt = dhcp_msg.options + 4`).
  4. In `DHCPREQUEST` handling (lines 246, 250), `memcmp(o + 2, &d->ip.addr, 3)` and `o[5]` are read without checking `o[1] >= 4` or that `o + 6` lies within the packet/buffer (up to 5-byte stack buffer over-read).
- **Remediation**: Zero-initialize `dhcp_msg` (or pass the actual `options_len = len - offsetof(dhcp_msg_t, options) - 4` to `opt_find()`), handle `DHCP_OPT_PAD`, and validate option length and remaining bytes before reading option payloads.

### MP-013: 64-bit `long` (`'l'`) FFI return values truncated to 32-bit `signed int` on LP64 systems
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `ports/unix/modffi.c:190-194`
- **Mechanism**: `return_ffi_value()` handles `'b'`, `'h'`, `'i'`, and `'l'` with `return mp_obj_new_int((signed)val->ffi);`. In C, `(signed)` is `signed int` (32 bits on LP64 Linux x86_64/aarch64), silently discarding the upper 32 bits of 64-bit `long` return values.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import ffi; libc = ffi.open('libc.so.6'); f = libc.func('l', 'labs', 'l'); print(hex(f(0x100000001)))"
  ```
  Output: `0x1` (expected `0x100000001`).
- **Remediation**: Cast `'l'` to `(signed long)val->ffi` (or `(ffi_sarg)val->ffi`).

### MP-014: Floating-point rounding sets `tv_usec = 1000000`, causing spurious `OSError(EDOM/EINVAL)`
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `ports/unix/modusocket.c:416-417`, `ports/unix/modtime.c:99-100`
- **Mechanism**: Both `socket_settimeout()` and `mod_time_sleep()` compute `tv.tv_usec = (time_t)round(modf(val, &ipart) * 1000000.0); tv.tv_sec = (suseconds_t)ipart;` (also swapping the `time_t`/`suseconds_t` casts). When the fractional part is >= `0.9999995` (e.g., `0.9999999`), `round()` yields `1000000`, which violates the POSIX `struct timeval` invariant `0 <= tv_usec < 1000000`. On Linux, `setsockopt(SO_RCVTIMEO)` rejects `tv_usec == 1000000` with `EDOM` (errno 33).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import usocket; s = usocket.socket(); s.settimeout(0.9999999)"
  ```
  Output: `OSError: 33` (`EDOM`).
- **Remediation**: Carry `tv_usec >= 1000000` into `tv_sec++` and `tv_usec -= 1000000` (and fix the swapped `time_t`/`suseconds_t` casts).

### MP-015: Unchecked `malloc()` failure in `-X heapsize=` causes NULL dereference in `gc_init()`
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `ports/unix/main.c:373-404, 480-481`
- **Mechanism**: `main_()` calls `char *heap = malloc(heap_size); gc_init(heap, heap + heap_size);` without checking if `heap == NULL`. Passing a very large `-X heapsize=` value causes `malloc()` to return `NULL`, immediately dereferenced via `memset()` inside `gc_init()` (`py/gc.c:142`). (Additionally, `heap_size *= 1024 * 1024` at line 390 can suffer signed `long` overflow.)
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0:allocator_may_return_null=1 ./ports/unix/build-rev-san/micropython -X heapsize=9999999999999999 -c "1"
  ```
  Output: `../../py/gc.c:142:5: runtime error: null pointer passed as argument 1` (SEGFAULT without ASan).
- **Remediation**: Check `if (heap == NULL)` and exit with an error message; guard `heap_size` multiplication against overflow.

### MP-016: Unchecked `pthread_kill()` and unretried `EINTR` on `sem_wait()` in `mp_thread_gc_others()` cause GC race/deadlock
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `ports/unix/mpthreadport.c:166-184, 230-272`
- **Mechanism**:
  1. In `mp_thread_gc_others()`, `pthread_kill(th->id, MP_THREAD_GC_SIGNAL)` return value is ignored. If a thread exits or is cancelled before removing itself in `mp_thread_finish()`, `pthread_kill` returns `ESRCH` and the subsequent `sem_wait(&thread_signal_done)` deadlocks forever.
  2. `sem_wait(&thread_signal_done)` is not retried on `EINTR`. If a signal interrupts `sem_wait`, it returns `-1` prematurely before the target thread finishes scanning its stack, causing a GC race (potentially sweeping live objects) and leaving the semaphore count permanently skewed by +1 for subsequent GCs.
  3. In `mp_thread_create()`, `pthread_attr_destroy(&attr)` is never called, and `malloc()` return value (line 259) is unchecked.
- **Remediation**: Only wait on `sem_wait` if `pthread_kill() == 0`, retry `sem_wait` while `errno == EINTR`, call `pthread_attr_destroy(&attr)`, and check `malloc()`.

### MP-017: `size_t` underflow OOB read (`rl.cursor_pos - 1`) on Tab when cursor is at column 0 of non-empty line
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `shared/readline/readline.c:244`
- **Mechanism**: When Tab (`c == 9`) is pressed, line 244 evaluates `if (vstr_len(rl.line) != 0 && unichar_isspace(vstr_str(rl.line)[rl.cursor_pos - 1]))`. If the line is non-empty (`vstr_len(rl.line) != 0`) and the user moved the cursor to the start of the line (`rl.cursor_pos == 0`, e.g., via Ctrl-A / Home), `rl.cursor_pos - 1` underflows `size_t` to `(size_t)-1`, reading 1 byte before `rl.line->buf` (out-of-bounds heap read).
- **Remediation**: Change the guard to `rl.cursor_pos > 0` (or `rl.cursor_pos > rl.orig_line_len`).

### MP-018: Signed `char` comparisons in `memcmp`/`strcmp`/`strncmp` and mismatched casts in `strchr`/`memchr` violate C99
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `shared/libc/string0.c:112-168, 221-229`
- **Mechanism**:
  1. `memcmp()`, `strcmp()`, and `strncmp()` compare bytes using `char c1`, `char c2` instead of `unsigned char`. On architectures with signed `char`, bytes `>= 0x80` compare less than `0x00..0x7f` (e.g., `memcmp("\x80", "\x7f", 1) == -1`), violating ISO C99 7.21.4 and breaking byte/UTF-8 ordering.
  2. `strchr()` loops with `*s != (char)c` (line 226) but returns `(*s == c) ? (char *)s : 0` (line 228) without casting `c` to `(char)`. On signed-`char` platforms, searching for `c = 0x80` (`128`) stops at `*s == -128` and then fails `-128 == 128`, falsely returning `NULL`.
  3. `memchr()` compares `*p++ == c` (line 129) instead of `(unsigned char)c`, failing whenever `c` is a negative signed `char` or `> 255`.
- **Remediation**: Use `unsigned char` in `memcmp`/`strcmp`/`strncmp`/`memchr`, and compare `*s == (char)c` in `strchr()`.

### MP-019: Prefix-only comparison in `memzip_find_file_header()` matches wrong files sharing a prefix
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `shared/memzip/memzip.c:25`
- **Mechanism**: `memzip_find_file_header()` matches filenames using `!strncmp(file_hdr_filename, filename, file_hdr->filename_len)` without checking that `filename[file_hdr->filename_len] == '\0'`. Any lookup whose path begins with an earlier archive entry's name (such as `"foo.py.bak"` matching `"foo.py"`, or `"dir/file.py"` matching a `"dir/"` entry) erroneously returns the shorter entry.
- **Remediation**: Also check `filename[file_hdr->filename_len] == '\0'` (or compare `strlen(filename) == file_hdr->filename_len`).


### MP-020: Negative width in `str.center()` wraps `size_t` and triggers heap buffer overflow in `memset()`
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/objstr.c:883-895`
- **Mechanism**: `str_center()` reads `mp_uint_t width = mp_obj_get_int(width_in);` without checking for negative values. Passing `-1` wraps `width` to `(mp_uint_t)-1`. `if (len >= width)` is false, so `vstr_init_len(&vstr, width)` computes `width + 1 == 0` in `vstr_init()`, allocating a minimal buffer while setting `vstr.len = (size_t)-1`. Line 892 then executes `memset(vstr.buf, ' ', width)` with `size = (size_t)-1`, overflowing the heap.
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "'a'.center(-1)"
  ```
  ASan output: `ERROR: AddressSanitizer: negative-size-param: (size=-1)` in `memset` called from `str_center` (`py/objstr.c:892`).
- **Remediation**: Store `mp_int_t width = mp_obj_get_int(width_in);` and return `str_in` immediately if `width <= 0 || len >= (size_t)width`.

### MP-021: Missing multiplication overflow check in sequence `*` causes heap/global buffer overflow
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/objstr.c:344-345`, `py/objlist.c:135-136`, `py/objtuple.c:168-169`, `py/sequence.c:32-44`
- **Mechanism**: String/bytes (`mp_obj_str_binary_op`), list (`list_binary_op`), and tuple (`tuple_binary_op`) multiplication compute `self->len * n` in `size_t` without overflow checking. On 64-bit platforms, `len = 16` and `n = 1 << 60` wraps `16 * (1 << 60)` to `0`.
  - For strings and lists, `0` bytes are allocated, then `mp_seq_multiply(src, len, times, dst)` writes `len` bytes/elements starting at `dst` (heap buffer overflow).
  - For tuples, `mp_obj_new_tuple(0, NULL)` returns the static global `mp_const_empty_tuple` (`py/objtuple.c:168`), and `mp_seq_multiply()` writes 128 bytes directly over `mp_const_empty_tuple` and adjacent globals (global buffer overflow).
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "((0,)*16) * (1 << 60)"
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "('a'*16) * (1 << 60)"
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "([0]*16) * (1 << 60)"
  ```
  ASan output for tuple case: `ERROR: AddressSanitizer: global-buffer-overflow ... WRITE of size 128 ... in mp_seq_multiply (py/sequence.c:41) ... 0 bytes to the right of global variable 'mp_const_empty_tuple'`.
- **Remediation**: Check `if (n > 0 && len > SIZE_MAX / n) { mp_raise_msg(&mp_type_MemoryError, NULL); }` (or `OverflowError`) before multiplying in `objstr.c`, `objlist.c`, and `objtuple.c`.

### MP-022: `array_construct()` trusts iterable `__len__` without bounds checks, causing heap overflow or stale length
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/objarray.c:136-154`
- **Mechanism**: When constructing an `array` or `bytearray` from a custom iterable implementing `__len__`, `array_construct()` uses `mp_obj_len_maybe()` to allocate `len` elements and sets `o->len = len`. The iteration loop then writes `mp_binary_set_val_array(typecode, o->items, i++, item)` with **no check** that `i < o->len` and never updates `o->len = i` when iteration ends.
  - If `__len__` returns less than the number of yielded items, `array_construct()` writes out of bounds past `o->items`, corrupting the GC heap.
  - If `__len__` returns more than the number of yielded items, the resulting array retains the inflated length with unpopulated trailing zeros.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  class BadLen:
      def __len__(self): return 1
      def __iter__(self): return iter(range(10000))
  bytearray(BadLen())
  "
  ```
  Result: `Assertion 'type->locals_dict->base.type == &mp_type_dict' failed` at `py/runtime.c:1179` (`SIGABRT`, GC heap corrupted).
- **Remediation**: In `array_construct()`, grow `o->items` dynamically if `i >= o->len` (or check bounds and reallocate), and set `o->len = i` after iteration finishes.

### MP-023: Native-type subclass overriding `__new__` via `object.__new__` leaves `subobj[0]` uninitialized (type confusion / SIGSEGV)
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/objtype.c:291-365`
- **Mechanism**: In `mp_obj_instance_make_new()`, `mp_obj_new_instance()` initializes `o->subobj[0] = MP_OBJ_FROM_PTR(&native_base_init_wrapper_obj)` (a `fun_builtin_var` sentinel). Normally, `mp_obj_instance_make_new()` discovers `native_base` during lookup and replaces `o->subobj[0]` with the native instance returned by `native_base->make_new(...)`. However, if a Python subclass of a native type (such as `uio.StringIO` or `ucollections.deque`) defines `__new__` and delegates to `object.__new__(cls)`, `object_make_new` invokes `mp_obj_new_instance()` directly without invoking the native base's `make_new`. The resulting object retains `&native_base_init_wrapper_obj` in `o->subobj[0]`. Subsequent native method calls unwrap `subobj[0]` via `mp_obj_cast_to_native_base()` (or direct cast) and interpret `mp_obj_fun_builtin_var_t` fields as `mp_obj_stringio_t` / `mp_obj_deque_t` pointers, crashing with SIGSEGV.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  import uio
  class BadSIO(uio.StringIO):
      def __new__(cls): return object.__new__(cls)
  BadSIO().getvalue()
  "
  ./ports/unix/build-rev-dbg/micropython -c "
  import ucollections
  class BadDeque(ucollections.deque):
      def __new__(cls): return object.__new__(cls)
  BadDeque().append(1)
  "
  ```
  Result: Both crash with `Segmentation fault (exit 139)`.
- **Remediation**: Reject `object.__new__(cls)` when `cls` has a native base with its own `make_new` (matching CPython's `TypeError: object.__new__(X) is not safe, use Base.__new__()`), or ensure `subobj[0]` is initialized/type-checked before native dispatch.

### MP-024: `list.sort(key=...)` holds raw `head`/`tail` pointers across Python callbacks, causing UAF / SIGSEGV on list mutation
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/objlist.c:293-348`
- **Mechanism**: `mp_quicksort()` takes raw `mp_obj_t *head, mp_obj_t *tail` pointers into `self->items` and invokes arbitrary Python callbacks (`key_fn` and element `__lt__` via `mp_binary_op`) without locking the list or reloading `self->items` / `self->len`. If `key_fn` (or `__lt__`) mutates the list being sorted — e.g. `a.clear(); a.extend(...)` — `self->items` is freed or reallocated. `mp_quicksort()` continues reading and writing through dangling `head`/`tail` pointers into freed/reused GC heap memory, causing memory corruption and `SIGSEGV`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  a = list(range(20))
  def k(x):
      if x == 10:
          a.clear()
          a.extend([99]*100)
      return x
  a.sort(key=k)
  "
  ```
  Result: `Segmentation fault (exit 139)`.
- **Remediation**: Either temporarily detach/empty the list's `items` buffer while sorting (as CPython does: move `items` to a local temporary array, set `self->items = NULL; self->len = 0;`, restore on completion/exception), or pre-evaluate keys and disallow concurrent mutation during sort.

### MP-025: `.mpy` loader (`read_uint`, `load_obj`, `load_raw_code`, `mp_native_relocate`) lacks EOF/bounds checks (infinite loop, assert abort, OOB)
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/persistentcode.c:83-132, 140-265, 389-433`
- **Mechanism**: The `.mpy` bytecode/native module loader assumes well-formed input and omits EOF and bounds validation throughout:
  1. **Infinite loop on truncated `.mpy` (`read_uint`, lines 146-156)**: `reader->readbyte()` returns `MP_READER_EOF` (`(mp_uint_t)-1`). Casting to `byte b` produces `0xff`, which has bit 7 (`0x80`) set, so `for (;;) { ... if ((b & 0x80) == 0) break; }` spins forever on any truncated `.mpy` file.
  2. **Abort / invalid tag (`load_obj`, line 209)**: Unknown `obj_type` tags hit `assert(obj_type == MP_PERSISTENT_OBJ_FLOAT || obj_type == MP_PERSISTENT_OBJ_COMPLEX)` (SIGABRT in debug builds) or feed arbitrary bytes to `mp_parse_num_decimal`.
  3. **Unchecked offsets and relocation indices (`load_raw_code`, lines 251-253; `mp_native_relocate`, lines 126-130)**: `prelude_offset` is added to `fun_data` without verifying `prelude_offset < fun_data_len`. In `mp_native_relocate()`, `addr` is added to `text` without checking bounds against `fun_data_len`, and `op - 9` indexes `mp_fun_table` without checking `op - 9 < MP_FUN_TABLE_LEN`.
  4. **Resource leak (`mp_raw_code_load`, lines 389-433)**: If an exception is raised (e.g. invalid header at line 396 or OOM), `reader->close(reader->data)` at line 430 is never called, leaking the open file descriptor.
- **Repro**:
  ```bash
  python3 -c 'open("/tmp/trunc_test.mpy", "wb").write(b"M\x06\x00\x1f")'
  timeout 2 ./ports/unix/build-rev-dbg/micropython -c 'import sys; sys.path.insert(0, "/tmp"); import trunc_test'
  echo "exit=$?"
  ```
  Result: Hangs indefinitely until killed by `timeout` (`exit=124`).
- **Remediation**: Check `b == MP_READER_EOF` in `read_byte`/`read_bytes`/`read_uint` and raise `ValueError`; validate `obj_type`, `prelude_offset`, relocation offsets, and `mp_fun_table` indices; ensure `reader->close()` is invoked via `nlr_push` on error paths.

### MP-026: Exception in `class` body skips `mp_locals_set(old_locals)`, permanently corrupting module `locals()`
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/modbuiltins.c:53-61`
- **Mechanism**: `mp_builtin___build_class__()` saves `old_locals = mp_locals_get()`, switches to the temporary `class_locals` dict via `mp_locals_set(class_locals)`, invokes the class body function `mp_call_function_0(args[0])`, and restores `mp_locals_set(old_locals)` on line 61. There is no `nlr_push` guard around the call. If the class body raises an exception that is caught by surrounding code, NLR unwinds past line 61 and `locals()` remains permanently set to the aborted class's temporary dictionary. All subsequent module-level bindings write into the dead class dict instead of `globals()`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  try:
      class Bad:
          leaked = 42
          raise ValueError
  except ValueError:
      pass
  new_var = 99
  print(locals() is globals(), 'new_var' in globals(), 'leaked' in locals())
  "
  ```
  Output: `False False True` (expected: `True True False`).
- **Remediation**: Wrap `mp_call_function_0(args[0])` in `nlr_push(&nlr)` so `mp_locals_set(old_locals)` is always restored before re-raising.

### MP-027: `StringIO.seek()` omits open check before dereferencing `o->vstr`, causing NULL dereference / SIGSEGV
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/objstringio.c:116-142` (and minor UBSan at line 75)
- **Mechanism**: `stringio_close()` sets `o->vstr = NULL`. While `stringio_read()` and `stringio_write()` call `check_stringio_is_open(o)`, `stringio_ioctl()` omits that check in `case MP_STREAM_SEEK:` and immediately dereferences `o->vstr->len` when `whence == SEEK_END` (line 124). Calling `s.seek(0, 2)` on a closed `StringIO` dereferences NULL and crashes with SIGSEGV. (Additionally, in `stringio_copy_on_write()` line 75, writing to `uio.StringIO('')` passes `NULL` from `m_new(char, 0)` to `memcpy(new_buf, ..., 0)`, triggering UBSan.)
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "import uio; s = uio.StringIO('abc'); s.close(); s.seek(0, 2)"
  ```
  Output: `py/objstringio.c:124:31: runtime error: member access within null pointer of type 'vstr_t'` followed by ASan `SEGV on unknown address 0x000000000008`.
- **Remediation**: Call `check_stringio_is_open(o)` at the start of `stringio_ioctl()` (or in `MP_STREAM_SEEK`), and guard `memcpy` with `if (o->vstr->len > 0)` in `stringio_copy_on_write()`.

### MP-028: `pow(a, b, 0)` aborts/reads OOB; `0**0` (mpz) and `pow(0, 0, m)` return `0`; negative exponent/modulus bugs
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/mpz.c:1325, 1359, 1484`, `py/objint_mpz.c:344-369`
- **Mechanism**:
  1. `mp_obj_int_pow3()` and `mpz_pow3_inpl()` never check if the modulus `c` is zero before invoking `mpz_rem_inpl()`, hitting `assert(!mpz_is_zero(rhs))` in debug builds (`SIGABRT`) and reading `den_dig[-1]` out of bounds in release builds (`mpn_div`).
  2. `mpz_pow_inpl()` (line 1325) and `mpz_pow3_inpl()` (line 1359) check `if (mpz_is_zero(lhs)) { mpz_set_from_int(z, 0); return; }` **before** checking `if (mpz_is_zero(rhs))`, so `((1<<70)-(1<<70))**0` and `pow(0, 0, 5)` erroneously return `0` instead of `1`.
  3. `mpz_pow3_inpl()` returns `1` for `pow(2, 0, -5)` (should be `-4` in Python floor-modulo semantics) and silently returns `0` for negative exponents like `pow(2, -3, 5)` instead of raising `ValueError`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "pow(2, 3, 0)"
  ./ports/unix/build-rev-dbg/micropython -c "print(((1<<70)-(1<<70))**0, pow(0, 0, 5), pow(2, 0, -5), pow(2, -3, 5))"
  ```
  Results: First command aborts with `Assertion '!mpz_is_zero(rhs)' failed` (`py/mpz.c:1484`); second prints `0 0 1 0` instead of `1 1 -4` and `ValueError`.
- **Remediation**: Raise `ValueError` when modulus is zero or exponent is negative; check `mpz_is_zero(rhs)` before `mpz_is_zero(lhs)`; reduce `1 % mod` when exponent is 0.

### MP-029: `range` truncates 64-bit `mp_int_t` into 63-bit small-int (sign flip) and overflows signed subtraction in `range_len`
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/objrange.c:45, 117-127, 137, 182`
- **Mechanism**: `range_make_new()` accepts full 64-bit `mp_int_t` bounds via `mp_obj_get_int()`, but `range_len()` (`MP_OBJ_NEW_SMALL_INT(range_len(self))`), `range_subscr()`, and `range_it_iternext()` wrap `mp_int_t` values using `MP_OBJ_NEW_SMALL_INT()` (63-bit signed on 64-bit platforms) instead of `mp_obj_new_int()`. Values `>= 1<<62` silently flip sign when shifted into small-int representation. Furthermore, `range_len()` computes `self->stop - self->start` in signed `mp_int_t`, causing signed integer overflow UB when `stop - start > INT64_MAX`.
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "
  print(range(1<<62, (1<<62)+2)[0], len(range(1<<62)))
  print(len(range(-(1<<62), (1<<62)-1)))
  "
  ```
  Output: `-4611686018427387904 -4611686018427387904`, UBSan `signed integer overflow` at `py/objrange.c:117` and `119`, and `-1`.
- **Remediation**: Use `mp_obj_new_int()` when returning range elements/lengths, and compute `(mp_uint_t)stop - (mp_uint_t)start` in unsigned arithmetic inside `range_len()` (returning `mp_uint_t` / `mp_obj_new_int_from_uint()`).

### MP-030: `get_fmt_num()` uses unchecked `MP_OBJ_SMALL_INT_VALUE` (pointer bits read as repeat count) and unchecked pointer arithmetic
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/modstruct.c:80, 117, 152, 243-244`
- **Mechanism**: `get_fmt_num()` parses a repeat prefix with `mp_parse_num_integer(...)` and immediately applies `MP_OBJ_SMALL_INT_VALUE(...)` without checking `MP_OBJ_IS_SMALL_INT()`. Any numeric prefix larger than `MP_SMALL_INT_MAX` returns a heap `mp_obj_int_t *`, whose pointer address is shifted right by 1 and used as the repeat count `cnt`. Additionally, `calcsize()` returns `MP_OBJ_NEW_SMALL_INT(size)` (truncating/sign-flipping large sizes), and `struct_pack_into()` / `struct_unpack_from()` check `p + total_sz > end_p` without guarding against pointer wraparound.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import ustruct; print(ustruct.calcsize('99999999999999999999s'))"
  ```
  Output: Prints a heap-pointer-derived integer (e.g. `65134917593424`) instead of raising `OverflowError`.
- **Remediation**: Parse the repeat count directly into `mp_uint_t` with overflow checking (raising `OverflowError`), return `mp_obj_new_int_from_uint(size)` in `calcsize`, and check `total_sz > (size_t)(end_p - p)`.

### MP-031: `mp_binary_get_size()` missing `case '=':`, breaking all native-order standard-size `ustruct` formats
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/binary.c:48-85`, `py/modstruct.c:62`
- **Mechanism**: `get_fmt_type()` in `py/modstruct.c` accepts `'='` (native byte order, standard size/no alignment) as a valid format prefix and passes `fmt_type = '='` to `mp_binary_get_size()`. However, `mp_binary_get_size()` in `py/binary.c` only switches on `'<', '>', '!', '@'` and falls into `default:` for `'='`, leaving `size` uninitialized/zero and failing every `ustruct.calcsize`/`pack`/`unpack` call using `'='`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import ustruct; ustruct.calcsize('=I')"
  ```
  Output: `ValueError: bad typecode`.
- **Remediation**: Add `case '=':` alongside `case '<': case '>': case '!':` in `mp_binary_get_size()` (`py/binary.c`).

### MP-032: Array/bytearray comparisons confuse signed/unsigned types and compare multi-byte integers via little-endian `memcmp`
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/objarray.c:348-353`
- **Mechanism**:
  1. `array_binary_op()` checks signedness with a single boolean `is_unsigned` rather than comparing each operand's typecode, so signed `'b'` arrays and unsigned `'B'`/`bytearray` objects compare raw bytes directly (`array('b', [-1]) == bytearray([255])` is `True` and `array('b', [-1]) > bytearray([1])` is `True`).
  2. Ordering comparisons (`<`, `<=`, `>`, `>=`) on multi-byte integer arrays (`'h'`, `'H'`, `'i'`, `'I'`, `'l'`, `'L'`, `'q'`, `'Q'`) fall through to `mp_seq_cmp_bytes()`, which performs raw `memcmp()` on little-endian memory bytes rather than numeric element comparison. Thus `256` (`00 01`) compares less than `1` (`01 00`).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  import uarray
  print(uarray.array('b', [-1]) == bytearray([255]))
  print(uarray.array('H', [256]) < uarray.array('H', [1]))
  "
  ```
  Output: `True` and `True` (expected: `False` and `False`).
- **Remediation**: Only use byte-wise `memcmp` fast paths when both operands have identical 1-byte unsigned typecodes (`'B'`/`BYTEARRAY_TYPECODE`); compare elements numerically otherwise.

### MP-033: `list.insert()` uses unchecked `MP_OBJ_SMALL_INT_VALUE`, silently misinterpreting non-small-int indices
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/objlist.c:383`
- **Mechanism**: `list_insert()` extracts the index with `mp_int_t index = MP_OBJ_SMALL_INT_VALUE(idx);` without checking `mp_obj_is_small_int(idx)` or calling `mp_obj_get_int()`. Passing a string (e.g. `'abc'`) or a big integer (`-(1<<100)`) shifts the heap pointer address right by 1 and treats it as a large positive index, silently appending the item at the end of the list instead of raising `TypeError` or clamping negative big ints to index `0`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "a = [1, 2]; a.insert('abc', 99); a.insert(-(1<<100), 88); print(a)"
  ```
  Output: `[1, 2, 99, 88]` (expected: `TypeError` for `'abc'`, and `88` inserted at index `0`).
- **Remediation**: Use `mp_obj_get_int_truncated(idx)` (or clamp mpz signs to `0` / `self->len` after validating `mp_obj_is_int(idx)`).

### MP-034: Number parser accepts digitless strings (`int("_")`, `float(".")`) and rejects underscored big ints
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/parsenum.c:86, 121, 141, 268-325`, `py/mpz.c:832-848`
- **Mechanism**:
  1. `mp_parse_num_integer()` does not require at least one valid digit before returning `0`, so `int("_")`, `int("___")`, and `int("0x_")` succeed and return `0`.
  2. `mp_parse_num_decimal()` tracks `in` state without requiring any mantissa or exponent digits, accepting `float(".")`, `float("_")`, `float("e0")`, and `float("1e+ ")`.
  3. Conversely, when `mp_parse_num_integer()` falls back to `mpz_set_from_str()` (`py/mpz.c:832`) for integers exceeding small-int range, `mpz_set_from_str()` does not skip `'_'` separators, rejecting valid strings like `int("1_000_000_000_000_000_000_000")`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  print(int('_'), int('0x_'), float('.'), float('_'), float('e0'), float('1e+ '))
  int('1_000_000_000_000_000_000_000')
  "
  ```
  Output: `0 0 0.0 0.0 0.0 1.0`, followed by `ValueError: invalid syntax for integer with base 10`.
- **Remediation**: Track `bool had_digit` in both integer and decimal parsers (and reject invalid underscore placements), and handle `'_'` consistently in `mpz_set_from_str()`.

### MP-035: `math.pow(2.0, inf)` raises `ValueError` due to missing `!isinf(y)` check; `math.ldexp()` truncates 64-bit exponent to 32-bit `int`
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/modmath.c:57, 85`
- **Mechanism**:
  1. `math_generic_2()` raises `ValueError("math domain error")` whenever `(isnan(ans) && !isnan(x) && !isnan(y)) || (isinf(ans) && !isinf(x))`, omitting `&& !isinf(y)`. Thus `math.pow(2.0, float('inf'))` erroneously raises `ValueError` instead of returning `inf`.
  2. `mp_math_ldexp()` passes `(int)mp_obj_get_int(exp_obj)` to `ldexp()`. On 64-bit platforms, exponents like `1 << 32` truncate to `0` (`math.ldexp(1.0, 1<<32) == 1.0`), and `1 << 31` truncates to `INT_MIN` (`math.ldexp(1.0, 1<<31) == 0.0` instead of `OverflowError`).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  import math
  print(math.ldexp(1.0, 1<<32), math.ldexp(1.0, 1<<31))
  math.pow(2.0, float('inf'))
  "
  ```
  Output: `1.0 0.0` followed by `ValueError: math domain error`.
- **Remediation**: Add `&& !isinf(y)` in `math_generic_2()`, and clamp `mp_int_t exp` to `[INT_MIN, INT_MAX]` before casting to `int` in `mp_math_ldexp()`.

### MP-036: `cmath.log(0)` returns `-inf` instead of `ValueError`; `polar`/`log`/`sqrt` overflow for `|z| > 1.34e154`
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/modcmath.c:46, 75, 84, 93`
- **Mechanism**: `cmath_polar()`, `cmath_log()`, and `cmath_sqrt()` compute magnitude via `MICROPY_FLOAT_C_FUN(sqrt)(real * real + imag * imag)` instead of `hypot(real, imag)` or scaled arithmetic. For any complex number with `|real| > ~1.34e154` (well within IEEE-754 double range `1.8e308`), `real * real` overflows to `+inf`, yielding `(inf, 0.0)` for `cmath.polar(1e200)` and `(inf+nanj)` for `cmath.sqrt(1e200)`. Additionally, `cmath_log(0)` does not check for `real == 0 && imag == 0` and returns `(-inf+0j)` instead of raising `ValueError`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import cmath; print(cmath.log(0), cmath.polar(1e200), cmath.sqrt(1e200))"
  ```
  Output: `(-inf+0j) (inf, 0.0) (inf+nanj)`.
- **Remediation**: Check for zero in `cmath_log()` and raise `ValueError`; use `hypot(real, imag)` (or scale by `max(|real|, |imag|)`) in `polar`, `log`, and `sqrt`.

### MP-037: Calling `.throw(exc)` on an exhausted generator returns `StopIteration` instead of raising `exc`
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/objgenerator.c:160-165`
- **Mechanism**: In `mp_obj_gen_resume()`, when `self->code_state.ip == 0` (exhausted generator), the function unconditionally returns `MP_VM_RETURN_NORMAL` with `*value = MP_OBJ_STOP_ITERATION` without inspecting `throw_value`. Per PEP 342 and Python semantics, `gen.throw(exc)` on a finished generator must raise `exc`, not `StopIteration`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  def g(): yield 1
  it = g(); next(it)
  try: next(it)
  except StopIteration: pass
  it.throw(ValueError('boom'))
  "
  ```
  Output: Raises `StopIteration` instead of `ValueError: boom`.
- **Remediation**: If `self->code_state.ip == 0` and `throw_value != MP_OBJ_NULL`, normalize and return `MP_VM_RETURN_EXCEPTION` with `throw_value`.

### MP-038: `round(1, -(1<<62))` overflows small-int negation and raises `ZeroDivisionError`
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/modbuiltins.c:489`
- **Mechanism**: When `num_dig < 0` in `mp_builtin_round()`, line 489 computes `MP_OBJ_NEW_SMALL_INT(-num_dig)`. For `num_dig = -(1 << 62)` (`MP_SMALL_INT_MIN`), `-num_dig = 1 << 62` exceeds `MP_SMALL_INT_MAX` and wraps back to `-(1 << 62)` inside `MP_OBJ_NEW_SMALL_INT()`. `mp_binary_op(MP_BINARY_OP_POWER, 10, -(1<<62))` evaluates to `0.0`, and the subsequent division raises `ZeroDivisionError: divide by zero` instead of returning `0`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "round(1, -(1<<62))"
  ```
  Output: `ZeroDivisionError: divide by zero`.
- **Remediation**: Use `mp_obj_new_int(-num_dig)` (or short-circuit when `-num_dig` exceeds maximum decimal digit count for integer/float arguments).

### MP-039: `stream_unbuffered_readline()` uses unchecked `MP_OBJ_SMALL_INT_VALUE` on optional `size` argument
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/stream.c:349`
- **Mechanism**: When a second argument is passed to `.readline(size)`, line 349 computes `max_size = MP_OBJ_SMALL_INT_VALUE(args[1])` without validating that `args[1]` is an integer or using `mp_obj_get_int()`. Passing a string or big integer silently reinterprets the object's heap pointer bits as a maximum byte count instead of raising `TypeError` (or handling `None`/big ints).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import uio; print(repr(uio.StringIO('hello world').readline('bad')))"
  ```
  Output: `'hello world'` (no `TypeError` raised).
- **Remediation**: Use `mp_obj_get_int(args[1])` (accepting `None` as unlimited, matching CPython).

### MP-040: `str.rsplit`/`startswith`/`endswith` accept `bytes` on `str`; `'{:c}'.format()` truncates `>= 0x100` and emits invalid UTF-8
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/objstr.c:658, 767, 782, 1242, 1536`
- **Mechanism**:
  1. `str_rsplit()` (when `maxsplit > 0`), `str_startswith()`, and `str_endswith()` extract raw bytes with `mp_obj_str_get_data()` without checking that the separator/prefix/suffix matches the receiver's type (`str` vs `bytes`), so `'a,b'.rsplit(b',', 1)` returns `['a', 'b']` and `'abc'.startswith(b'a')` returns `True` (violating Python's strict `str`/`bytes` separation).
  2. In `str_do_format()` (`case 'c':`, line 1536), integer arguments are written via `byte b = mp_obj_get_int(arg)` without checking `0 <= val <= 0x10ffff` or UTF-8 encoding. `'{:c}'.format(0x100)` silently truncates to `'\x00'`, and `'{:c}'.format(0x80)` inserts a raw invalid UTF-8 byte into a `str` object.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  print('a,b'.rsplit(b',', 1), 'abc'.startswith(b'a'))
  print(repr('{:c}'.format(0x100)), '{:c}'.format(0x80).encode())
  "
  ```
  Output: `['a', 'b'] True` and `'\x00' b'\x80'`.
- **Remediation**: Use `check_is_str_or_bytes()` (or compare `mp_obj_get_type()`) in `str_rsplit`/`startswith`/`endswith`; in format `'c'`, validate `0 <= val < 0x110000` and emit UTF-8 via `vstr_add_char()`.

### MP-041: `(-1).to_bytes(10, 'big')` zero-pads high bytes instead of sign-extending or rejecting negative values
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/objint.c:436-447`
- **Mechanism**: `mp_obj_int_to_bytes_impl()` initializes the output buffer with `0x00` and only copies `sizeof(mp_int_t)` (8) bytes for small ints, leaving leading bytes as `0x00` even for negative integers. Thus `(-1).to_bytes(10, 'big')` returns `b'\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff'` (which represents `+2**64 - 1`, neither unsigned-rejected as in CPython nor properly sign-extended two's complement).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "print((-1).to_bytes(10, 'big'))"
  ```
  Output: `b'\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff'`.
- **Remediation**: Reject negative values with `OverflowError` (matching CPython's default `signed=False`) or sign-extend with `0xff` if signed encoding is intended.

### MP-042: Negative `__len__` hint causes unsigned wraparound and multi-gigabyte allocation failure in `dict.fromkeys` and `*` unpacking
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/objdict.c:280`, `py/runtime.c:736-740`
- **Mechanism**: Both `dict_fromkeys()` and `mp_call_function_n_kw` / `*` argument unpacking (`mp_obj_len_maybe()`) cast `MP_OBJ_SMALL_INT_VALUE(len)` directly to `size_t` / `mp_uint_t` without verifying `>= 0`. If a custom iterable's `__len__` returns `-1` (or any negative small int), the value wraps to a huge unsigned allocation size, triggering spurious multi-gigabyte `MemoryError` (or overflow on `alloc * sizeof(mp_obj_t)`).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  class NegLen:
      def __len__(self): return -1
      def __iter__(self): return iter([1])
  dict.fromkeys(NegLen())
  "
  ```
  Output: `MemoryError: memory allocation failed, allocating 4294967280 bytes`.
- **Remediation**: Enforce `len >= 0` in `mp_obj_len_maybe()` (raising `ValueError: __len__() should return >= 0`, as in CPython).

### MP-043: Unsigned underflow in `decompress_error_text_maybe()` when `emg_buf_size < EMG_BUF_STR_BUF_OFFSET` causes NULL deref under OOM
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `py/objexcept.c:133`
- **Mechanism**: In `decompress_error_text_maybe()`, `size_t avail = emg_buf + emg_buf_size - (emg_buf + EMG_BUF_STR_BUF_OFFSET);` subtracts a larger offset from a smaller buffer size whenever `emg_buf_size < EMG_BUF_STR_BUF_OFFSET` (including the default unconfigured state `emg_buf == NULL, emg_buf_size == 0`). `avail` underflows to a huge `size_t`, bypassing `avail >= len` checks and attempting to decompress into `emg_buf + EMG_BUF_STR_BUF_OFFSET` (NULL dereference / heap corruption under out-of-memory conditions when `MICROPY_ROM_TEXT_COMPRESSION` is enabled).
- **Remediation**: Check `if (emg_buf == NULL || emg_buf_size <= EMG_BUF_STR_BUF_OFFSET) { return; }` before computing `avail`.

### MP-044: Stale source pointer UAF on self-extend/self-slice-assign reallocation, and 32-bit `ROUND_ALLOC` truncation in `vstr.c`
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `py/objarray.c:404, 484`, `py/objlist.c:216`, `py/vstr.c:38`
- **Mechanism**:
  1. In `array_extend()` (`py/objarray.c:484`), `mp_get_buffer_raise(arg, &bf, MP_BUFFER_READ)` captures `bf.buf` before `m_renew()` reallocates `self->items`. When `b.extend(b)` causes relocation, `memcpy(self->items + ..., bf.buf, ...)` reads from the just-freed `bf.buf` (use-after-free). The same pattern occurs in `array_subscr()` (`py/objarray.c:404`) and `list_subscr()` (`py/objlist.c:206-220`) when `value` aliases `self` (`a[0:0] = a`) and `m_renew()` relocates `self->items`.
  2. In `py/vstr.c:38`, `#define ROUND_ALLOC(a) (((a) & ((~0U) - 7)) + 8)` uses 32-bit unsigned `~0U` (`0xffffffffU`) instead of `~(size_t)0`, silently truncating any allocation size `>= 4 GiB` on 64-bit platforms to its lower 32 bits.
- **Remediation**: Detect aliasing (`arg == self_in` or `value_items == self->items`) and refresh the source pointer after `m_renew()` (using `memmove` for overlapping copies); change `~0U` to `~(size_t)0` in `py/vstr.c:38`.


### MP-045: Zero-field `namedtuple` overwrites read-only global `mp_const_empty_tuple.base.type` (SIGSEGV)
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/objnamedtuple.c:112-113`
- **Mechanism**: `namedtuple_make_new()` allocates its backing tuple via `mp_obj_new_tuple(num_fields, NULL)` and then unconditionally writes `tuple->base.type = type_in;` (line 113). When `num_fields == 0` (e.g., `namedtuple("E", ())`), `mp_obj_new_tuple(0, NULL)` returns the static `const` global `mp_const_empty_tuple` rather than a newly allocated object. Assigning `tuple->base.type` writes to read-only `.rodata` memory (crashing with `SIGSEGV` on Linux/Unix, or globally corrupting the type of `()` if writable).
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "import ucollections; E = ucollections.namedtuple('E', ()); E()"
  ```
  ASan output: `ERROR: AddressSanitizer: SEGV ... The signal is caused by a WRITE memory access ... in namedtuple_make_new (py/objnamedtuple.c:113)`.
- **Remediation**: Allocate a fresh `mp_obj_tuple_t` via `mp_obj_malloc_var(mp_obj_tuple_t, mp_obj_t, num_fields, type_in)` directly in `namedtuple_make_new()` instead of reusing `mp_obj_new_tuple()`.

### MP-046: `IOBase` passes stack-allocated mutable `bytearray` to Python callbacks (stack UAR, ROM write SIGSEGV, `gc_realloc` abort)
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/modio.c:57-81`
- **Mechanism**: `iobase_read_write()` constructs a stack-allocated `mp_obj_array_t ar = {{&mp_type_bytearray}, BYTEARRAY_TYPECODE, 0, size, buf};` (line 60) and passes `MP_OBJ_FROM_PTR(&ar)` as a mutable Python `bytearray` to user-defined `readinto()` / `write()` methods. This violates object lifetime, mutability, and allocator invariants in three distinct ways:
  1. **Stack Use-After-Return**: If the Python callback saves `buf` (e.g., into a list) and accesses it after `iobase_read_write()` returns, it dereferences a dead C stack frame (confirmed ASan SEGV with corrupted instruction pointer `pc = 0x61`).
  2. **Mutable Alias to `const`/ROM Memory**: `iobase_write()` casts `const void *buf` to `(void *)buf` and wraps it in a mutable `bytearray`. User `write()` code executing `buf[0] = 65` writes directly into immutable `bytes`/`str` or read-only `.rodata` strings (confirmed ASan SEGV WRITE at `py/binary.c:392`).
  3. **Invalid `gc_realloc()` on Non-GC Buffer**: If `readinto()` resizes `buf` (e.g., `buf.append(1)`), `array_extend()` passes the caller's stack/non-GC `buf` pointer to `gc_realloc()`, aborting with `Assertion 'VERIFY_PTR(ptr)' failed` at `py/gc.c:701` (or corrupting the GC heap in release builds).
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "
  import uio, sys
  class MutIO(uio.IOBase):
      def write(self, buf):
          buf[0] = 65
          return len(buf)
  sys.print_exception(ValueError('hi'), MutIO())
  "
  ./ports/unix/build-rev-dbg/micropython -c "
  import uio, ujson
  class BadIO(uio.IOBase):
      def readinto(self, buf):
          buf.append(1)
          return 1
  ujson.load(BadIO())
  "
  ```
  Results: First triggers ASan `SEGV` (WRITE to `.rodata` via `iobase_write`); second triggers `Assertion 'VERIFY_PTR(ptr)' failed` at `py/gc.c:701` (`SIGABRT`). Saving `buf` and printing after return triggers `SEGV` at `pc = 0x61`.
- **Remediation**: Heap-allocate a non-resizable `memoryview` (`MP_OBJ_ARRAY_MEMVIEW`, read-only for `write`) and invalidate its length/pointer (`mv->len = 0; mv->items = NULL;`) on return/exception via `nlr_push`.

### MP-047: Clearing/rehashing `dict` or `set` inside `__eq__` causes division by zero (`SIGFPE`) and dangling `avail_slot` UAF
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/map.c:254-320, 363-418` (also `OrderedDict` at lines 193-221)
- **Mechanism**: Both `mp_map_lookup()` and `mp_set_lookup()` call `mp_obj_equal()` inside their open-addressing probe loops without guarding against re-entrant mutation of `map`/`set`.
  1. If `__eq__` clears the `dict` or `set` (`d.clear()` / `s.clear()`), `map->alloc` (`set->alloc`) becomes `0` and `table` becomes `NULL`. Upon returning from `mp_obj_equal()`, line 296 (`pos = (pos + 1) % map->alloc`) / line 398 (`pos = (pos + 1) % set->alloc`) divides by zero (`SIGFPE`).
  2. If `__eq__` triggers a rehash (`mp_map_rehash` / `mp_set_rehash`), any cached `avail_slot` pointer points into the freed `old_table` (use-after-free write on insertion), and `pos`/`start_pos` become out of bounds or stale.
  3. Similarly, in `OrderedDict` (`py/map.c:218-219`), `map->alloc += 4` happens before `m_renew()`, leaving `map->alloc` inflated if `m_renew()` throws `MemoryError`, and `elem`/`top` pointers are invalidated by re-entrant mutation.
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "
  d = {}
  class Evil:
      def __hash__(self): return 1
      def __eq__(self, other): d.clear(); return False
  d[Evil()] = 1
  print(Evil() in d)
  "
  ```
  Output: `py/map.c:296:25: runtime error: division by zero` followed by ASan `FPE` (`py/map.c:398` for `set`).
- **Remediation**: Save `table`/`alloc` before `mp_obj_equal()`, detect mutation after `mp_obj_equal()` returns (restarting the probe or raising `RuntimeError`), and update `map->alloc` only after `m_renew()` succeeds.

### MP-048: Unchecked 8-bit packing in `unpack_ex`, `call_function`, and closures causes VM stack corruption (`SIGSEGV`) and assertion aborts
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/emitbc.c:355, 630, 730, 747, 759, 762`, `py/emitnative.c:681, 2643, 2734, 2741`
- **Mechanism**: Multiple bytecode and native-emitter encodings pack counts into 8-bit fields without validating `< 256` (or `< 128`):
  1. `mp_emit_bc_unpack_ex()` (line 730) and `emit_native_unpack_ex()` (line 2643) pack `n_left | (n_right << 8)`. With 256 targets before `*rest`, `n_left = 256` overflows into `n_right = 1, n_left = 0`. At runtime `MP_BC_UNPACK_EX` unpacks only 2 values while the generated bytecode executes 257 `STORE_NAME` instructions, underflowing the VM stack and crashing with `SIGSEGV`.
  2. `emit_bc_call_function_method_helper()` (lines 759, 762) and `emit_native_call_function()` (lines 2734, 2741) pack `(n_keyword << 8) | n_positional`. Calling a function with 256 positional arguments encodes `n_positional = 0, n_keyword = 1`, misaligning the VM stack and invoking an argument as the callable (`TypeError: 'int' object isn't callable`).
  3. `mp_emit_bc_end_pass()` (line 355), `emit_native_end_pass()` (line 681), and `mp_emit_bc_make_closure()` (line 747) use `assert(id->local_num <= 255)` / `assert(n_closed_over <= 255)` and write single bytes. Functions with `> 255` locals closing over variable `>= 256` abort with `SIGABRT` in debug builds and silently truncate to `uint8_t` in release builds (corrupting unrelated local slots / VM stack).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  lhs = ','.join([f'a{i}' for i in range(256)]) + ',*r'
  exec(lhs + ' = range(260)')
  "
  ./ports/unix/build-rev-dbg/micropython -c "
  def f(*args): return len(args)
  print(eval('f(' + ','.join(['1']*256) + ')'))
  "
  ./ports/unix/build-rev-dbg/micropython -c "
  lines = ['def outer():'] + [f'    v{i} = {i}' for i in range(260)] + ['    def inner(): return v259', '    return inner()']
  exec('\n'.join(lines) + '\nouter()')
  "
  ```
  Results: `Segmentation fault (exit 139)` for `unpack_ex`, `TypeError: 'int' object isn't callable` for 256-arg call, and `Assertion 'id->local_num <= 255' failed` (`SIGABRT`) for closures (both bytecode and `@micropython.native`).
- **Remediation**: Enforce compile-time limits (raising `SyntaxError` / `RuntimeError`) whenever `n_left`, `n_positional`, `n_closed_over`, `id->local_num`, or `except_depth` exceed their wire-encoding limits, or widen the bytecode encoding.

### MP-049: Viper `//` and `%` lack zero-divisor and `INT64_MIN // -1` checks, crashing the interpreter with hardware `SIGFPE`
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/emitnative.c:2313-2325`, `py/smallint.c:55-75`
- **Mechanism**: In `@micropython.viper` functions, integer `//` and `%` emit direct calls to `mp_small_int_floor_divide()` and `mp_small_int_modulo()`. Those helpers assume their caller already validated `divisor != 0` and that operands are 63-bit small integers (so `INT64_MIN / -1` cannot happen). Viper passes arbitrary 64-bit native `int` values directly:
  - `a // 0` and `a % 0` execute hardware integer division by zero (`SIGFPE`), terminating the entire interpreter process instead of raising `ZeroDivisionError`.
  - `(-2**63) // -1` executes `INT64_MIN / -1`, triggering signed division overflow UB and x86-64 hardware `SIGFPE`.
- **Repro**:
  ```bash
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "
  @micropython.viper
  def f(a: int, b: int) -> int: return a // b
  f(1, 0)
  "
  ASAN_OPTIONS=detect_leaks=0:detect_stack_use_after_return=0 ./ports/unix/build-rev-san/micropython -c "
  @micropython.viper
  def f(a: int, b: int) -> int: return a // b
  f(-(1 << 63), -1)
  "
  ```
  Output: UBSan `division by zero` / `division of -9223372036854775808 by -1` and ASan `ERROR: AddressSanitizer: FPE` at `py/smallint.c:74` (and `py/smallint.c:57` for `%`).
- **Remediation**: Check `denom == 0` (raising `ZeroDivisionError`) and guard `num == MP_INT_MIN && denom == -1` in viper division/modulo helpers (or dedicated `mp_native_floor_divide` / `mp_native_modulo` entry points).

### MP-050: Viper emitter asserts `VTYPE_PYOBJ` / cast arity instead of type-checking (`SIGABRT` in debug; raw-int type confusion in release)
- **Severity**: Critical
- **Status**: CONFIRMED
- **Location**: `py/emitnative.c:1467, 1480, 1698-1699, 1904, 1913-1914, 2078, 2221, 2570-2572, 2583-2592, 2604, 2632, 2641, 2702-2703, 2731`
- **Mechanism**: Numerous operations in `@micropython.viper` code use `assert(vtype == VTYPE_PYOBJ)` or `assert(n_positional == 1 && n_keyword == 0)` instead of emitting a `ViperTypeError` or boxing native values. Because integer literals default to native `VTYPE_INT` in Viper, ordinary Python expressions inside a `@micropython.viper` function abort debug builds with `SIGABRT` — and in release builds (where `assert` compiles out), pass raw unboxed integers directly as `mp_obj_t` pointers to runtime functions (`mp_store_map`, `mp_load_attr`, `mp_obj_subscr`, `mp_obj_new_slice`, `mp_call_function_n_kw`), causing type confusion and `SIGSEGV`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "@micropython.viper
  def f(): return int()"
  ./ports/unix/build-rev-dbg/micropython -c "@micropython.viper
  def f(): return {1: 2}"
  ./ports/unix/build-rev-dbg/micropython -c "@micropython.viper
  def f(a): return a[1:2]"
  ./ports/unix/build-rev-dbg/micropython -c "@micropython.viper
  def f(): x = 1; return x.foo"
  ```
  Results: Each immediately aborts with `SIGABRT` (`Assertion 'n_positional == 1 && n_keyword == 0' failed` at `emitnative.c:2702`, `Assertion 'vtype_key == VTYPE_PYOBJ' failed` at `emitnative.c:2570`, `Assertion 'vtype_start == VTYPE_PYOBJ' failed` at `emitnative.c:2583`, `Assertion 'vtype_base == VTYPE_PYOBJ' failed` at `emitnative.c:1467`).
- **Remediation**: Replace `assert(...)` on user-controlled Viper operand types and cast arities with either automatic boxing (`MP_F_CONVERT_NATIVE_TO_OBJ`) or `EMIT_NATIVE_VIPER_TYPE_ERROR(...)`.

### MP-051: `ATB_GET_KIND(block + n_blocks)` reads/corrupts past end of alloc table; `gc_realloc` `size_t` overflow frees live block and returns it
- **Severity**: Critical
- **Status**: SUSPECTED
- **Location**: `py/gc.c:126-139, 218-221, 618-621, 637-640, 706, 741-759`
- **Mechanism**:
  1. **Out-of-bounds ATB access**: `gc_init()` places `gc_finaliser_table_start` (or `gc_pool_start` when finalisers are disabled) immediately after `gc_alloc_table_start + gc_alloc_table_byte_len` with no trailing sentinel byte. Unlike `gc_realloc()` (which explicitly bounds its loop with `bl < max_block` at line 717), `gc_mark_subtree()` (line 221), `gc_free()` (line 621), and `gc_nbytes()` (line 640) scan `do { ... } while (ATB_GET_KIND(block + n_blocks) == AT_TAIL);` with no upper bound check. When an allocation occupies the final block of the GC pool (`block + n_blocks == max_block`), `ATB_GET_KIND(max_block)` reads the first two bits of `gc_finaliser_table_start[0]` (or `gc_pool_start[0]`). If those bits equal `AT_TAIL` (`0b10`), `gc_mark_subtree()` reads past `gc_pool_end`, `gc_nbytes()` over-reports size, and `gc_free()` overwrites `gc_finaliser_table_start[0]` (or `gc_pool_start[0]`) via `ATB_ANY_TO_FREE(max_block)`.
  2. **`gc_realloc()` integer overflow to UAF**: Line 706 computes `size_t new_blocks = (n_bytes + BYTES_PER_BLOCK - 1) / BYTES_PER_BLOCK;`. When `n_bytes > SIZE_MAX - BYTES_PER_BLOCK + 1`, the addition overflows `size_t` so `new_blocks == 0`. Line 741 (`if (new_blocks < n_blocks)`) then frees **all** blocks of `ptr_in` starting at `block + 0` (including the `AT_HEAD` block) and returns the now-freed `ptr_in` as a valid pointer.
- **Remediation**: Add `block + n_blocks < max_block` checks in `gc_mark_subtree()`, `gc_free()`, and `gc_nbytes()` (or reserve a zeroed sentinel byte at the end of ATB); guard `n_bytes > SIZE_MAX - BYTES_PER_BLOCK + 1` in `gc_alloc()` and `gc_realloc()` (returning `NULL`).

### MP-052: `str_subscr` computes multi-byte length from lead byte without bounds check, reading OOB on malformed UTF-8 `str`
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/objstrunicode.c:214-222`
- **Mechanism**: When indexing a `str`, `str_subscr()` counts leading `1` bits in `*s` (`for (char mask = 0x40; *s & mask; mask >>= 1) { ++len; }`) and passes `(s, len)` to `mp_obj_new_str_via_qstr()` without clamping `len` to `self_data + self_len - s`. Combined with paths that permit non-UTF-8 bytes in `str` (such as `'{:c}'.format(0xfe)`, see MP-040), `len` evaluates to `7`, reading 6 bytes past the end of the 1-byte string buffer.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "s = '{:c}'.format(0xfe); print(repr(s[0]), len(s[0].encode()))"
  ```
  Output: `'\x00\x00\x00\x00\x00\x00\x00' 7` (6 bytes read past the 1-byte string).
- **Remediation**: Clamp `len` to `(size_t)(self_data + self_len - s)` (and enforce valid UTF-8 on all `str` construction paths).

### MP-053: `slice.indices()` accepts negative length and truncates 64-bit bounds/step into 63-bit small-int (sign flip)
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `py/objslice.c:50-61`
- **Mechanism**:
  1. `slice_indices()` parses `length` via `mp_obj_int_get_checked(length_obj)` without checking `length >= 0`, returning invalid negative stop indices (e.g. `(0, -10, 1)`) instead of raising `ValueError`.
  2. Lines 56-58 wrap full 64-bit `mp_int_t` fields `bound_indices.start`, `stop`, and `step` using `MP_OBJ_NEW_SMALL_INT()` (63-bit signed), silently flipping the sign of values `>= 1 << 62`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "
  class S:
      def __getitem__(self, s): return s
  print(S()[:].indices(-10))
  print(S()[::1<<62].indices(10))
  print(S()[:1<<62].indices(1<<62))
  "
  ```
  Output: `(0, -10, 1)`, `(0, 10, -4611686018427387904)`, and `(0, -4611686018427387904, 1)`.
- **Remediation**: Reject `length < 0` with `ValueError`, and construct tuple elements with `mp_obj_new_int()`.

### MP-054: `sys.settrace` has `raw_code_lnotab` heap overflow / assert aborts, dangling `frame->code_state` UAF, and stuck `mp_prof_is_executing`
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `py/profile.c:106-128, 220-242, 269, 291-305`
- **Mechanism**: When `MICROPY_PY_SYS_SETTRACE` is enabled:
  1. **Heap buffer overflow / abort in `raw_code_lnotab()` (lines 106-128)**: `buffer_chunk_size = (stop - start) >> 2` is `0` for `fun_data_len < 4` and `1` for `< 8`. When `buffer_index + 2 > buffer_size`, `m_renew` grows the buffer by only `buffer_chunk_size` (0 or 1 bytes) while the loop immediately writes 2 bytes (`buffer[buffer_index++]` twice), overflowing the heap buffer. Additionally, lines 117-118 `assert(instr_diff < 256)` and `assert(line_diff < 256)` abort whenever a function has `>= 256` blank/comment lines between statements or `>= 256` bytes of bytecode on one line.
  2. **Use-after-free / stack use-after-return on saved frames (lines 220-242, 269)**: `mp_obj_new_frame()` stores raw pointer `o->code_state = code_state`. Because `fun_bc_call()` allocates `code_state` via `alloca()` or frees it on return (`py/objfun.c:276, 338`), accessing `frame.f_globals` or `frame.f_back` on a frame saved by a trace callback after the function returns dereferences freed heap or dead stack memory.
  3. **Stuck `mp_prof_is_executing` on exception (lines 294-299)**: `mp_prof_callback_invoke()` sets `mp_prof_is_executing = true` before invoking the Python callback with no `nlr_push` cleanup. If the trace function raises an exception that is caught, `mp_prof_is_executing` stays `true` forever, aborting on the next traced call (`assert(!mp_prof_is_executing)` at lines 317/380).
- **Remediation**: Use `MAX(buffer_chunk_size, 16)` and split diffs `>= 256` into multiple lnotab entries (per CPython); detach/clear `frame->code_state` when leaving a frame; reset `mp_prof_is_executing = false` inside an `nlr_push` handler.

### MP-055: `module_attr_try_delegation()` indexes `map->table[map->alloc - 1]` without checking `map->alloc > 0` (NULL deref on empty dict)
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `py/objmodule.c:70-77`
- **Mechanism**: When `MICROPY_MODULE_ATTR_DELEGATION` is enabled (the default for `MICROPY_CONFIG_ROM_LEVEL_AT_LEAST_EXTRA_FEATURES`), `module_attr_try_delegation()` unconditionally evaluates `if (map->table[map->alloc - 1].key == MP_OBJ_NEW_QSTR(MP_QSTRnull))` without checking `map->alloc > 0`. If a module's globals dictionary has been cleared via `globals().clear()`, `map->alloc == 0` and `map->table == NULL`, causing `NULL[(size_t)-1].key` to dereference unmapped memory (`SIGSEGV`) on any attribute lookup.
- **Remediation**: Guard with `if (map->is_fixed && map->alloc > 0 && ...)` (since delegation entries only reside in fixed ROM module tables).

### MP-056: `netutils_ethernet_trace()` reads IP/TCP/UDP/DHCP/IPv6 headers without length checks and suffers `size_t` underflow OOB reads
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `shared/netutils/trace.c:58-166`
- **Mechanism**: `netutils_ethernet_trace()` parses incoming raw Ethernet frames without validating `len` against header sizes:
  - Reads Ethernet header `buf[0..13]` without checking `len >= 14` (lines 60-68).
  - For IPv4 (line 74), replaces `len` with packet-supplied `get_be16(buf + 2)` (ignoring actual buffer size), reads `buf[9..19]` without checking `len >= 20`, and computes `len -= 20` (underflowing `size_t` when IP total length < 20).
  - For TCP (lines 83-98), reads 20-byte TCP header without bounds checks and subtracts `opts_len = ((dataoff_flags >> 12) - 5) * 4` without checking `opts_len <= len`.
  - For UDP/DHCP (lines 102-145), overwrites `len = get_be16(buf + 4)`, advances `buf += 8` without subtracting 8 from `len`, dumps 108 bytes, subtracts `n = 236` from `len` without checking `len >= 236`, and reads `buf[6]` OOB.
  - For IPv6 (lines 150-160), reads 40 bytes and subtracts `40` from `len` without checking `len >= 40`.
  - Any `size_t` underflow in `len` causes line 164 (`dump_hex_bytes(print, len, buf)`) to read gigabytes past the packet buffer.
- **Remediation**: Track `const uint8_t *end = buf + len`, clamp header-reported lengths to `(size_t)(end - buf)`, and verify remaining length before every header read and subtraction.

### MP-057: Format-string injection in `print_jobject()`, 64-byte stack overflow in `get_jclass_name()`, and unbounded `strprev()` scan
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `ports/unix/modjni.c:113-118, 235-248, 254, 278, 286, 370-375, 411-412, 491-503`
- **Mechanism**:
  1. **Format string vulnerability (`print_jobject`, line 116)**: Calls `mp_printf(print, str)` directly with the string returned by Java's `Object.toString()`. Any `%` format specifier in a Java string is interpreted by `mp_printf()`, reading arbitrary stack/register values and crashing.
  2. **Stack buffer overflow (`get_jclass_name`, lines 235-247, 411-412)**: Callers pass a fixed `char class_name[64]`, while `get_jclass_name()` calls `GetStringUTFRegion(name, 0, len, buf)` with no check that the UTF-8 byte length fits in 64 bytes (and without ensuring NUL termination). Java class names frequently exceed 64 bytes, overflowing the stack.
  3. **Unbounded backward scan & argument count bug (`strprev`, line 370; `call_method`, line 491)**: `strprev()` scans backwards without a buffer-start bound; `call_method()` loop condition `j < n_args && *arg_types != ')'` accepts calls with excess Python arguments; `jobject_subscr()` hits unconditional `assert(0)` on delete/store.
- **Remediation**: Use `mp_print_str(print, str)` in `print_jobject()`; pass buffer size to `get_jclass_name()` (or use `GetStringUTFChars`/`ReleaseStringUTFChars`); check `j == n_args` after the argument loop; replace `assert(0)` with `mp_raise_NotImplementedError`.

### MP-058: Stack buffer overflow via `strcpy` from `MICROPYBTUART`, `pthread_join` on detached threads, and UART fd leak on error
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `ports/unix/mpbthciport.c:121-124, 175-199, 211`, `ports/unix/mpbtstackport_usb.c:79, 110-113`
- **Mechanism**:
  1. **Stack buffer overflow (`mpbthciport.c:175-180`)**: `mp_bluetooth_hci_uart_init()` copies `getenv("MICROPYBTUART")` into a 256-byte stack buffer `char uart_device_name[256]` using unbounded `strcpy()`.
  2. **Undefined `pthread_join()` on detached threads (`mpbthciport.c:195-198, 211`, `mpbtstackport_usb.c:79, 110-113`)**: Both `hci_poll_thread_id` and `bstack_thread_id` are created with `PTHREAD_CREATE_DETACHED` (and `pthread_attr_destroy(&attr)` is omitted), yet their `deinit()` functions call `pthread_join(...)`. Joining a detached thread fails immediately with `EINVAL` (UB per POSIX), causing `deinit()` to close resources while the background thread is still running.
  3. **FD leak & stuck state (`mpbthciport.c:121-124, 190-192`)**: If `tcgetattr()` fails inside `configure_uart()`, it returns `-1` without closing `uart_fd` or resetting `uart_fd = -1`, leaving `uart_fd` leaked and subsequent `init()` calls falsely succeeding as "already active".
- **Remediation**: Use `snprintf` (or pass `path` directly to `open()`); create the thread joinable (remove `PTHREAD_CREATE_DETACHED`) and call `pthread_attr_destroy(&attr)`; close and reset `uart_fd = -1` on `tcgetattr()` failure.

### MP-059: F-string lexer fails on adjacent f-strings (`f'{1}' f'{2}'`), underflows `nested_bracket_level` on `']'`, and sign-extends `char`
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/lexer.c:156, 180-183, 340, 366-376, 611-675`
- **Mechanism**:
  1. **Broken adjacent f-string concatenation (lines 340, 611-675)**: In `mp_lexer_to_next()`, adjacent string literals are merged in a loop calling `parse_string_literal()`. Every f-string piece unconditionally executes `vstr_add_str(&lex->fstring_args, ".format(")`, producing malformed `.format(1,.format(2,)` and raising `SyntaxError` on valid Python like `f'{1}' f'{2}'`.
  2. **Unsigned underflow in `nested_bracket_level` (lines 366-373)**: Because the loop ignores string quotes inside `{...}` and `nested_bracket_level` is `unsigned int`, encountering `']'` at level 0 (e.g., `f"{'a]b'}"`) decrements `nested_bracket_level` to `0xffffffff`, preventing the loop from ever seeing `'}'` and consuming the entire remainder of the input stream.
  3. **Signed `char` extension & CRLF consumption (lines 156, 182)**: `lex->chr2 = lex->fstring_args.buf[...]` sign-extends signed `char` bytes `>= 0x80` into `unichar` (`uint32_t`); and on `\r\n` inside injected f-string args, line 182 reads from `lex->reader` instead of `lex->fstring_args`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "eval('f\"{1}\" f\"{2}\"')"
  ./ports/unix/build-rev-dbg/micropython -c "eval(\"f\\\"{'a]b'}\\\"\")"
  ```
  Output: Both raise `SyntaxError: invalid syntax` on valid Python f-strings.
- **Remediation**: Only prepend `".format("` once per merged string token (`if (lex->fstring_args.len == 0)`); guard `if (nested_bracket_level > 0) nested_bracket_level--;` and track quotes; cast `fstring_args.buf` bytes to `(byte)`.

### MP-060: `__import__` uses unchecked `MP_OBJ_SMALL_INT_VALUE` for `level`; non-external weak-link path passes `mp_obj_t` to `strcpy()`
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/builtinimport.c:500, 571, 584-586`
- **Mechanism**:
  1. `mp_builtin___import__()` extracts the optional 5th `level` argument with `MP_OBJ_SMALL_INT_VALUE(args[4])` (lines 500 and 571) without checking that `args[4]` is a small int or calling `mp_obj_get_int()`. Passing a non-integer (such as a string) silently interprets its heap pointer bits as a positive relative import depth instead of raising `TypeError`.
  2. In the `#else // MICROPY_ENABLE_EXTERNAL_IMPORT` branch with `MICROPY_MODULE_WEAK_LINKS` enabled (line 586), `strcpy(umodule_buf + 1, args[0]);` passes `mp_obj_t args[0]` directly to `strcpy()` (type bug — should be `qstr_str(module_name_qstr)`) and performs an unbounded copy into `char umodule_buf[MICROPY_ALLOC_PATH_MAX]`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "__import__('sys', None, None, None, 'not_an_int')"
  ```
  Output: `KeyError: __main__` (entered `evaluate_relative_import` with pointer-derived `level` instead of raising `TypeError`).
- **Remediation**: Use `mp_obj_get_int(args[4])`; in the `#else` branch, extract the string length and use bounded `memcpy` after checking `len + 2 <= sizeof(umodule_buf)`.

### MP-061: Complex `abs()`, `/`, and `**` compute `real*real + imag*imag` unscaled, overflowing for `|z| > 1.34e154` (`0j` / `nan`)
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/objcomplex.c:129, 221-225, 235`
- **Mechanism**: `complex_unary_op(MP_UNARY_OP_ABS)`, `mp_obj_complex_binary_op(MP_BINARY_OP_TRUE_DIVIDE)`, and `MP_BINARY_OP_POWER` compute `real * real + imag * imag` directly without scaling or `hypot()`. Whenever `|real|` or `|imag|` exceeds `~1.34e154`, squaring overflows to `+inf`, causing `abs(1e200+0j)` to return `inf`, `(1e200+1e200j) / (1e200+1e200j)` to return `0j`, and `(1e200+0j) ** 0.5` to return `(nan+nanj)`.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "print(abs(1e200+0j), (1e200+1e200j)/(1e200+1e200j), (1e200+0j)**0.5)"
  ```
  Output: `inf 0j (nan+nanj)` (expected: `1e+200 (1+0j) (1e+100+0j)`).
- **Remediation**: Use Smith's algorithm for complex division and `hypot()` (or max-component scaling) for `abs` and `**`.

### MP-062: `BufferedWriter` infinite loop on `alloc==0` & flush assert; thread `th_args` GC root race; `EINTR` EOF in `reader.c`; `buf[-1]` in `input.c`
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `py/modio.c:123-180`, `py/modthread.c:236-271`, `py/reader.c:91-96`, `ports/unix/input.c:50-58`
- **Mechanism**:
  1. **`BufferedWriter` (`py/modio.c:123-180`)**: `bufwriter_make_new()` accepts `alloc <= 0`; with `alloc == 0`, `bufwriter_write()` loops forever (`rem = 0`, `size -= 0`). In `bufwriter_flush()`, `assert(out_sz == self->len)` (line 176) runs *before* checking `if (err != 0)` (line 178), aborting debug builds whenever the underlying stream fails on flush.
  2. **Thread startup GC root race (`py/modthread.c:236-271`)**: `mod_thread_start_new_thread()` allocates `th_args` on the GC heap and passes it to `mp_thread_create()`, returning immediately. On Unix, `mp_thread_create()` does not wait for the new thread to enter `thread_entry()` and register its stack with GC, so a GC cycle before the child thread starts can collect and reuse `th_args` while the child still holds a pointer to it.
  3. **Silent file truncation on `EINTR` (`py/reader.c:91-96`)**: `mp_reader_posix_readbyte()` treats `read() == -1` (including `EINTR`) as EOF (`reader->len = 0; return MP_READER_EOF`), silently truncating `.py`/`.mpy` imports if a signal arrives.
  4. **Underflow read/write on NUL input (`ports/unix/input.c:50-58`)**: When `MICROPY_USE_READLINE == 0`, if `stdin` begins with a NUL byte, `fgets()` succeeds with `strlen(buf) == 0`, and `buf[l - 1]` accesses `buf[-1]` out of bounds; `malloc(l)` is also unchecked.
- **Remediation**: Require `alloc > 0` in `BufferedWriter` and check `err != 0` before asserting `out_sz == self->len`; keep `th_args` rooted (e.g., via a synchronized startup handshake or root list) until `mp_thread_start()`; retry `read()` on `EINTR` in `py/reader.c`; guard `if (l > 0 && buf[l - 1] == '\n')` and check `malloc()` in `ports/unix/input.c`.


### MP-063: `uselect.poll` has negative/`uint16` `alloc` wrap, `ipoll()` assert abort (`SIGABRT`), stale `revents` on `unregister`, and 32-bit timeout truncation
- **Severity**: High
- **Status**: CONFIRMED
- **Location**: `ports/unix/moduselect.c:112-127, 141-150, 185, 250-281, 322-330`
- **Mechanism**:
  1. **Unvalidated `alloc` and `unsigned short` truncation (`select_poll`, lines 322-330; `poll_register`, lines 112-118)**: `select_poll()` does not validate `alloc >= 0`, so `uselect.poll(-1)` attempts to allocate `(size_t)-1 * sizeof(struct pollfd)`. Furthermore, `poll->alloc` is `unsigned short`, truncating `alloc >= 65536` modulo 65536 (and wrapping `self->alloc += 4` once `alloc` exceeds 65532, causing `m_renew` to shrink `self->entries` below `self->len`).
  2. **Assertion abort in `poll_iternext()` (lines 250-281)**: `poll_ipoll()` caches `self->iter_cnt = n_ready`. If a subsequent `poll(0)` updates `revents` to `0` before the iterator finishes, `next(it)` reaches `assert(!"inconsistent number of poll active entries")` and aborts (`SIGABRT`).
  3. **Stale `revents` on `unregister()` (lines 141-150)**: `poll_unregister()` sets `entries->fd = -1` without clearing `entries->revents`. Unregistering an active fd during `ipoll()` iteration causes `poll_iternext()` to yield `(-1, revents)`.
  4. **64-bit timeout truncation (line 185)**: `int timeout = timeout_i;` truncates 64-bit `mp_int_t` milliseconds to 32-bit `int`, turning `1 << 32` into `0` (immediate non-blocking return) and `1 << 31` into `-2147483648` (infinite block).
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "import uselect; uselect.poll(-1)"
  ./ports/unix/build-rev-dbg/micropython -c "
  import uselect, usocket
  s = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
  s.bind(usocket.getaddrinfo('127.0.0.1', 19876)[0][-1])
  c = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
  c.sendto(b'hi', usocket.getaddrinfo('127.0.0.1', 19876)[0][-1])
  p = uselect.poll(); p.register(s, uselect.POLLIN)
  it = p.ipoll(100); s.recv(10); p.poll(0); next(it)
  "
  ./ports/unix/build-rev-dbg/micropython -c "
  import uselect
  p = uselect.poll(); p.register(1, uselect.POLLOUT); p.register(2, uselect.POLLOUT)
  it = p.ipoll(0); print(next(it)); p.unregister(2); print(next(it))
  "
  ```
  Results: First fails with `MemoryError: allocating 4294967288 bytes`; second aborts with `Assertion '!"inconsistent number of poll active entries"' failed` (`SIGABRT`); third prints `(1, 4)` then `(-1, 4)`. `p.poll(1 << 32)` returns in 0 ms.
- **Remediation**: Validate `0 <= alloc <= USHRT_MAX` (or widen `alloc`/`len` to `size_t`); clear `entries->revents = 0` in `poll_unregister()`; reset `self->iter_cnt = 0` inside `poll_poll()` and remove the fatal `assert` in `poll_iternext()`; clamp `timeout_i` to `INT_MAX`.

### MP-064: Float formatting rounds values `< 1.0` prematurely with `while (--e)` underflow (`0.999999999996` -> `1.0`) and omits carry room in `'f'` mode
- **Severity**: Medium
- **Status**: CONFIRMED
- **Location**: `py/formatfloat.c:90, 199-246, 282-290, 380-409`
- **Mechanism**:
  1. For `f < 1.0`, `mp_format_float()` compares `f >= FPROUND_TO_ONE` (`0.999999999995` for double, line 200) regardless of the requested precision `prec`. When `0.999999999995 <= f < 1.0`, `first_dig` is set to `'1'`, `e` remains `0`, and `f` is overwritten with `1.0` (line 213). Then at line 242, `while (--e && num_digits)` decrements `e` from `0` to `-1, -2, ...` until `num_digits` reaches `0`, emitting all zeros instead of the real fractional digits. Thus `"{:.20f}".format(0.999999999996)` prints `1.00000000000000000000`, discarding 5 digits of IEEE-754 double precision.
  2. In `'f'` mode (lines 282-290, 396-409), `prec` is clamped only against `e + prec + 2 <= buf_remaining`, reserving no byte for a carry digit (`9.99...` rounding up to `10.00...`). When rounding carries past the leading digit (`fmt == 'f'`), line 397 increments `s++` and shifts digits right by 1, overflowing `buf` by 1 byte and triggering `assert((size_t)(s + 1 - buf) <= buf_size)` (line 409) for small caller buffers.
- **Repro**:
  ```bash
  ./ports/unix/build-rev-dbg/micropython -c "print('{:.20f}'.format(0.999999999996))"
  ```
  Output: `1.00000000000000000000` (expected: `0.99999999999599997743`).
- **Remediation**: Remove the hardcoded `FPROUND_TO_ONE` early override (let the final rounding loop handle rounding to `prec` digits) and guard `while (e > 1 && num_digits) { e--; ... }`; reserve 1 extra byte in `buf_remaining` for carry expansion in `'f'` mode.

### MP-065: Double `reader->close()` on post-parse exception in `parse_compile_execute()` causes double-free for heap-backed readers
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `shared/runtime/pyexec.c:99-109, 133-136`
- **Mechanism**: When `parse_compile_execute()` is called with `EXEC_FLAG_SOURCE_IS_READER`, line 100 passes `*(mp_reader_t *)source` to `mp_lexer_new()`, and line 108 passes `lex` to `mp_parse()`. Upon successful parsing, `mp_parse()` calls `mp_lexer_free(lex)` (`py/parse.c:1364`), which invokes `reader->close(reader->data)` (closing and freeing the reader's internal state). If `mp_compile()` or `mp_call_function_0(module_fun)` subsequently raises an uncaught exception, the NLR handler at lines 133-136 unconditionally calls `reader->close(reader->data)` a second time. While `mp_reader_stdin_close` happens to be idempotent via `reader->eof`, any heap-backed reader (`mp_reader_mem_close`, `mp_reader_posix_close`) frees `reader->data` on close, causing a double-free / double-`close(fd)`.
- **Remediation**: Track `bool reader_open = (exec_flags & EXEC_FLAG_SOURCE_IS_READER) != 0;` and clear `reader_open = false;` immediately after `mp_parse()` returns (since `mp_parse()` closes the reader on success).

### MP-066: Unchecked `mmap()` `MAP_FAILED` return and missing `munmap()` leak in `/dev/mem` mapping; `if (!fd)` mishandles fd `0`
- **Severity**: High
- **Status**: SUSPECTED
- **Location**: `ports/unix/modmachine.c:57-74`
- **Mechanism**: When `MICROPY_PLAT_DEV_MEM` is enabled, `mod_machine_mem_get_addr()` has three defects:
  1. `mmap()` (line 70) is not checked for `MAP_FAILED` (`(void *)-1`). If `mmap()` fails, `map_page` is set to `(uintptr_t)-1` and cached in `last_base = cur_base`; line 73 returns `(uintptr_t)-1 + (addr & 0xfff)` (wrapping to a low unmapped address such as `0x0000..0xffe`), causing a `SIGSEGV` when the caller reads/writes the address.
  2. When switching pages (`cur_base != last_base`), the previously mapped page is never unmapped with `munmap()`, leaking virtual address space and kernel VMAs on every page transition.
  3. `static int fd;` is initialized to `0` and checked with `if (!fd)`. If stdin is closed so `open("/dev/mem", ...)` returns fd `0`, `/dev/mem` is repeatedly reopened and leaked on every access.
- **Remediation**: Initialize `static int fd = -1;` (`if (fd < 0)`), check `if (p == MAP_FAILED) mp_raise_OSError(errno);` before updating `last_base`/`map_page`, and `munmap()` the previous mapping before replacing it.

### MP-067: Unbounded `days_since_jan1[month]` OOB read, 32-bit year-2068 signed wraparound, and pre-2000 unsigned underflow in leap-day math
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `shared/timeutils/timeutils.c:50-65, 72, 147-215`
- **Mechanism**:
  1. `timeutils_days_in_month()` (line 51) and `timeutils_year_day()` (line 61) index `days_since_jan1[month]` and `days_since_jan1[month - 1]` (13-element array) with no validation that `1 <= month <= 12`. Calling either with `month == 0` underflows `month - 1` to `(mp_uint_t)-1` (OOB read / crash); `month > 12` reads past the array.
  2. `timeutils_seconds_since_2000_to_struct_time()` (line 72) computes `mp_int_t seconds = t - LEAPOCH;` from unsigned `mp_uint_t t`. On 32-bit platforms, valid unsigned timestamps `>= 2068-01-19` overflow `int32_t` to negative values and wrap to the 1930s.
  3. `timeutils_seconds_since_2000()` (lines 154-158) computes `(year - 2000 + 3) / 4` in unsigned `mp_uint_t`, underflowing for `year < 1997` and producing bogus leap-day adjustments; `timeutils_mktime_2000()` uses an O(`|mday| / 30`) loop that can stall on large `mday` values and underflows unsigned `year` below 0.
- **Remediation**: Validate `1 <= month <= 12` in `timeutils_days_in_month`/`year_day`; use `int64_t` / unsigned division for `timeutils_seconds_since_2000_to_struct_time()`; use signed arithmetic for year deltas in `timeutils_seconds_since_2000()`.

### MP-068: `netutils_parse_ipv4_addr()` accepts non-digits/octets `>255`; internal `vsnprintf(NULL, 0, ...)` calls `memcpy(NULL, ..., 0)` and `putchar(0xff)` returns `-1`
- **Severity**: Medium
- **Status**: SUSPECTED
- **Location**: `shared/netutils/netutils.c:57-85`, `shared/libc/printf.c:73-77, 92-123`
- **Mechanism**:
  1. `netutils_parse_ipv4_addr()` (`shared/netutils/netutils.c:69-76`) accumulates `val = val * 10 + *s - '0'` without checking `'0' <= *s && *s <= '9'`, without requiring at least one digit per octet, and without checking `val <= 255`. Invalid strings like `"..."` (`0.0.0.0`), `"256.0.0.1"` (`0.0.0.1`), and `"a.b.c.d"` are silently accepted with truncated/garbage octets.
  2. In `shared/libc/printf.c:97`, `strn_print_strn()` unconditionally calls `memcpy(strn_print_env->cur, str, len)` even when `len == 0` and `cur == NULL`, invoking C99 undefined behavior on standard `vsnprintf(NULL, 0, fmt, ap)` size-query calls.
  3. In `shared/libc/printf.c:74-76`, `putchar(int c)` stores `char chr = c;` and returns `chr`, which on signed-`char` platforms sign-extends `0xff` to `-1` (`EOF`), violating C99 7.19.7.9 (must return `(unsigned char)c`).
- **Remediation**: Validate digits, non-empty octets, and `val <= 255` in `netutils_parse_ipv4_addr()`; guard `if (len > 0) memcpy(...)` in `strn_print_strn()`; return `(unsigned char)chr` in `putchar()`.