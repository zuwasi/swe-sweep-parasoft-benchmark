# HDF5 — Neon bug-hunt vs SWE-Sweep bugs (scored)

Denominator: all 14 SWE-Sweep bugs, including the 1 empty-region bug (hdf5-8b449df9cbdd, not matchable).

## Accepted

- **BUG-108** (Critical) — "H5S__combine_select unconditionally dereferences NULL hslab when result is empty" (H5Shyper.c 10448-10460).
  Bug `hdf5-cd22c0502f29` ("hslab pointer may be null", region 10456-10462, strict 10459).
  Maintainer fix: commit e8760978c93 "Fix segfault in H5Scombine_select (#5296)", which adds
  `if (H5S_SEL_HYPERSLABS == H5S_GET_SELECT_TYPE(new_space))` before the `new_space->select.sel_info.hslab->unlim_dim = -1;`
  write. Same defect, same mechanism (NULL hslab deref on empty selection result). **ACCEPT region + strict.**

- **BUG-139** (Medium) — "... and empty enum/compound bugs" (src/H5T.c 3465-3471 among its spans).
  Bug `hdf5-aa1b6edb1d73` ("datatype not closed on error path", RESOURCE; oracle patch hunks in H5T.c at
  1845/2678/2704/3063/3114/3462/5089 and H5Tcompound.c at 470).
  Maintainer fix: HDF5 "Address memory issues when copying empty enums" (upstream #3088, backported as
  "Brings an enum fix from develop (#3304)", commit bab8acbe823 on the 1.10 line). The fix (a) guards the
  H5T__complete_copy H5T_ENUM case with `if (nalloc > 0)` (memset instead of malloc(0)/memcpy-from-NULL) —
  exactly the lines BUG-139 cites (3465-3471), and (b) adds failure checks for `H5MM_xstrdup`/`H5T_copy`
  in H5T__insert (H5Tcompound.c 473/476) so a failing insert errors out and cleans up instead of leaving a
  half-built member (the "datatype not closed on error path" facet). BUG-139's empty-enum claim
  ("H5Tcopy() unconditionally fails on any empty H5T_ENUM because H5MM_malloc(0) returns NULL") identifies
  the same defect the maintainer fixed at the cited lines. Its other bundled claims (H5T__bit_dec borrow,
  H5Tenum_insert read-only, H5T_decode over-read, H5T_detect_class VL-string) were not part of the fix and
  were not verified. **ACCEPT region + strict** (span 3465-3471 intersects strict 3465-3479).

## Clear misses

The remaining 12 bugs had no Neon finding whose spans reached their regions (matcher output; no candidate
findings to judge). 8b449df9cbdd has an empty region in the oracle patch and is not matchable.

## Final score

| Metric | Neon | Parasoft (published) |
|---|---|---|
| Region | 2/14 = 14.3% | 42.9% |
| Strict | 2/14 = 14.3% | 28.6% |

Novel findings: Neon reported 170 findings across the repo; 168 did not correspond to a SWE-Sweep bug
(the 2 accepted above account for both matched bugs). Not vetted for real-vs-false; counted as unmatched.
