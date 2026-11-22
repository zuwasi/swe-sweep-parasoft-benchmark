# micropython · Neon bug-hunt vs SWE-Sweep oracle (scored)

- Neon findings: 296 (`MP-001`..`MP-296`; 209 confirmed, 87 suspected), 17 findings matched at least one oracle bug; 12 distinct bugs matched.
- Denominator: all 22 SWE-Sweep micropython bugs.
- Parasoft published: 68.2% region (15/22), 31.8% strict (7/22).

## Accepted (9 bugs, 10 findings)

Region+strict (8 bugs):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| MP-015 | ec6689a8cc86 | 6baeded3223 | "py/runtime: Fix crash in star arg unpacking": rewrites the oracle's removed line (`args2_len >= args2_alloc` -> `args2_len + (n_args - i) >= args2_alloc`) in mp_call_prepare_args_n_kw_var; exactly the OOB-write crash the finding claims |
| MP-021 | 85267a3c1ee8 | 908ab1ceca1 | "py/objint: Fix int.to_bytes() buffer size checks" (#13041): the rewrite of mpz_as_bytes removes the write-before-check early returns (`*--b = val; if (b == buf) return;`) that underflow on len == 0, the finding's exact claim |
| MP-081 | b3d62f80e40b | 606ec9bfb1c | "py/compile: Fix async for's stack handling of iterator expression": async for no longer uses the iterator expression's identifier as a storage local; the finding's claim verbatim |
| MP-091 | b53492729a4a | f6234333330 | "py/mpz: Fix 3-arg pow() with zero base and zero exponent": pow(0,0,m) returned 0 instead of 1; matches the finding's lhs==0 wrong-result claim at the oracle's removed line |
| MP-111 | 5c51fb896d80 | cf097932a | "unix/modsocket: Set file descriptor to -1 on close": rewrites exactly the oracle's removed lines (MP_THREAD_GIL_EXIT/close/ENTER) adding the fd >= 0 guard and `self->fd = -1`; the finding's double-close claim verbatim. The fix lives at ports/unix/modsocket.c (renamed from modusocket.c), which is why the path-limited fix search reported NO-HIT |
| MP-178 | b53492729a4a | f6234333330 | The 0**0 claim matches the same zero-base/zero-exponent fix |
| MP-179 | 1010a6f1bf3f | 43b05afdf51 | "py/mpz: Skip separators when running out of digits to print" (#8984): stray separator before the number when the first group is three digits = the finding's spurious leading comma claim |
| MP-190 | 8074d176612b | e0a14806002 | "py/objstr: Fix str % {} edge case": rewrites the oracle's removed line (`if (arg_i != n_args)` -> adds `dict == MP_OBJ_NULL`), i.e. the dict is consumed even when unreferenced; matches the finding's unused-dict claim |
| MP-215 | 639baaf0eaee | 2e4dda3c207 | "py/modmath: Fix two-argument math function domain check": pow(1.5, inf)/pow(2, inf) no longer raise ValueError; matches the finding's pow domain-error claim at the oracle's removed line |

Region+strict via one finding, two bugs:

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| MP-261 | 85267a3c1ee8 | 908ab1ceca1 | The fix's core change is exactly the finding's silent-truncation claim: to_bytes now raises OverflowError instead of silently truncating (mp_obj_int_to_bytes_impl returns bool, mpz_as_bytes gains as_signed and the ok/olen overflow logic). The byteorder-validation claim is not part of the fix |

Region-only (1 bug):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| MP-091 | d4d265304c55 | ff318fa58fa | "py/mpz: Fix 3-arg pow() with zero exponent and negative modulus": matches the finding's rhs==0 claim. MP-178 also matched this bug with the same fix (its negative-modulus claim). Oracle hunk is insertion-only, so no strict set |
| MP-178 | d4d265304c55 | ff318fa58fa | Same fix, negative-modulus claim verbatim |

## Rejected (3 distinct bugs... see below) — line overlap, different mechanism

- MP-041 / 8625d05e0e82: fix 5c4153ea379 adds an OverflowError for out-of-bound memoryview slice start (24/56-bit `free` bitfield limit); the finding claimed use-after-free of a memoryview over a resized bytearray. Different defect in the same file.
- MP-095 / ef93b8337084: fix f397a3ec318 validates that indices()' argument is an integer (#13007); the finding claimed negative-length signed overflow and result truncation. Line overlap only.
- MP-207 / 830236cc7dce: fix 093d0c0a177 validates super() arguments (#12830); the finding claimed type(name, bases, dict) sharing the caller's locals_dict. Different mechanism.
- MP-096 / 85267a3c1ee8: hash(float) consistency/UB claim; the matched strict line is the mpz_as_bytes declaration the fix re-signed. Different defect.
- MP-128 / 85267a3c1ee8: LONGLONG-impl arithmetic claims (dropped minus sign, C-truncation div/mod SIGFPE, shift UB); none touched by the fix (only the to_bytes_impl declaration line overlapped).
- MP-244 / 85267a3c1ee8: mp_classify_fp_as_int subnormal claim; the matched lines are the mpz_as_bytes call the fix re-signed. Different defect.
- MP-260 / 85267a3c1ee8: int('0x10') base-prefix claim; unrelated to the to_bytes fix.

Rejected bugs (distinct): 8625d05e0e82, ef93b8337084, 830236cc7dce, 85267a3c1ee8 (via MP-096/128/244/260).

## Final score

- Neon region: 9/22 = 40.9% (Parasoft published: 68.2%)
- Neon strict: 8/22 = 36.4% (Parasoft published: 31.8%; Neon beats Parasoft on strict here)
- Novel findings: 286 of 296 (10 findings accepted at least one bug)
- Unresolved: none. All 12 matched bugs have verified fix commits.
