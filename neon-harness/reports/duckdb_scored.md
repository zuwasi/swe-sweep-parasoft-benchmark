# duckdb · Neon bug-hunt vs SWE-Sweep oracle (scored)

- Neon findings: 170 (`BUG-001`..`BUG-170`), 25 findings matched at least one oracle bug region; 26 matched bug-pairs over 25 distinct bugs.
- Denominator: all 109 SWE-Sweep duckdb bugs (6 have an empty region: 1e81c42dd1a4, 21cff7c1d5c6, 85e3b88d8300, 95c312388f7b, 99482115caaa, ef0ded97b22b; they can never be matched).
- Parasoft published: 68.8% region (75/109), 32.1% strict (35/109).

## Accepted (18 bugs, 17 findings)

Region+strict (14 bugs):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| BUG-084 | 165dc49e8f37 | df86a0fdf5c | bit.cpp `size > 2` changed to `>= 2`; exact match |
| BUG-053 | 16912ea8773c | a319dd7e0bf | RLE off-by-one (issue #14020); exact match |
| BUG-165 | 2380f9735ed0 | 04b65da7138 | excel day-of-week modulo (issue #11319); matches the nf_calendar off-by-one-Sunday claim |
| BUG-075 | 37580a29144b | 0e567f18efd | hugeint exponent bounds check = POWERS_OF_TEN[40] over-read claim (region-only: insertion-only oracle) |
| BUG-091 | 43b086a35dd5 | c8c543aa1cf | array child slice offset*array_size; exact match |
| BUG-106 | 4fc939834090 | e54cc2e8b49 | list_zip requires one list = OOM claim; exact match |
| BUG-162 | 5e618dfa2d4f | d0276b11de0 | fts quote escaping (issue #13866) = unescaped interpolation claim |
| BUG-081 | 61c3cfc37903 | ac530fea663 | hashes.Flatten = flatten-hashes claim (region-only: insertion-only oracle) |
| BUG-058 | 663c7d842c69 | c85641d2f98 | unset deleted[] on conflict; exact match |
| BUG-099 | 6f234f9c4978 | e520cd2df32 | dictionary vector slice in map reinterpret; exact match |
| BUG-150 | 8a3e974e8727 | 14d2111d23d | cast map keys to string before JSON = type-confusion claim |
| BUG-061 | 9dda7601a697 | c85f5e9ce36 | INVALID_CATALOG replaced by db.GetName() in FK lookup; exact match |
| BUG-008 | a36a17c4de98 | 0035bdc6653 | reversed CastIsInvertible args (issue #13380); exact match |
| BUG-083 | 4f2d8e8eaf2f | add0346b92d | row_radix_scatter.cpp line 128: `width - 1` -> `width - 2` = the finding's width claim verbatim ("Fix ordering issue with nested list type") |

Region+strict via one finding, two bugs:

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| BUG-103 | 824a50418841 | ed91d18d478 | "Empty list for enum_range": empty-enum guard in EnumRangeFunction; matches the EnumRangeBoundaryFunction claim |
| BUG-103 | 1b72fe675ead | d1865c5a13e | "handle empty enums in enum_first and enum_last": rewrites exactly the oracle's removed lines 9 and 18 (`GetValue(0)`, `GetValue(enum_size - 1)`); matches the EnumLastFunction underflow claim. The fix lives under extension/core_functions/ after the file move, which is why the path-limited fix search reported NO-HIT |

Region-only (2):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| BUG-007 | 282d562aa395 | b7c4d955bd9 | "Fix move constants optimization": returns nullptr instead of folding to a NULL constant exactly for COMPARE_(NOT_)DISTINCT_FROM when a constant is NULL = the finding's "folds IS [NOT] DISTINCT FROM NULL to NULL" claim. Oracle hunk is insertion-only, so no strict set |
| BUG-002 | 3f3cf4083ba4 | 3d5cf647e9e | deliminator guard for semi/anti joins with inequality conditions; the finding's RemoveInequalityJoinWithDelimGet NULL-semantics claim aligns with the fix's COMPARE_NOTEQUAL/DISTINCT_FROM guard. Borderline |

## Rejected (7 distinct bugs, 8 findings) — line overlap, different mechanism

- BUG-097 / 685162621323: fix 222a2f23992 is validity-vector/null handling in list cast try-catch; finding claimed OOB read.
- BUG-055 / c9112165759d: fix c04319541c3 resets segment tree next pointers / data race (issue #14077); finding claimed merge_count miscompute.
- BUG-149 / dbd78f790c07: fix ac559087325 adds NULL_IF_NULL executor param for json_type; finding claimed type confusion in json_keys.
- BUG-022 / e5c74941dc92: fix 83b0363a4cc escapes USING columns in JoinRef::ToString; finding claimed parens/CROSS JOIN precedence.
- BUG-022 / 025b1abedd19: NO-HIT fix ("cross product transform tree built wrongly"); unresolvable, counted as miss.
- BUG-070 / 24278e9ffd28: NO-HIT fix ("append initialization count bookkeeping wrong"); finding claimed a wrong-lock-target race in ALTER COLUMN TYPE, a different mechanism. Counted as miss.
- BUG-006, BUG-010, BUG-011 / 55543d201747: the oracle patch is the whole refactor commit bea48309b5a ("refactor compressed materialization to be inside of statistics propagation", 50+ files). Its only semantic defect fix is the guard `if (aggregate.grouping_sets.size() > 1) return;` in CompressAggregate ("FIXME: ... the NULL statistics ain't right"), which is also the bug's only insertion-only hunk. None of the three findings identify that defect: BUG-006 claims ANTI/RIGHT_ANTI join empty-result replacement (propagate_join.cpp overlap only), BUG-010 claims max_cardinality underestimation for GROUPING SETS overflowing in sum_no_overflow (closest in symptom, but the fix changes no cardinality computation and no sum helper; it disables the pass), BUG-011 claims a missing TIMESTAMP->TIME monotonicity case in propagate_cast. All three rejected; 55543d201747 counted as miss.

## Final score

- Neon region: 18/109 = 16.5% (Parasoft published: 68.8%)
- Neon strict: 14/109 = 12.8% (Parasoft published: 32.1%)
- Novel findings: 153 of 170 (17 findings accepted at least one bug)
- Unresolved: none. All 26 matched bug-pairs have a verdict; 2 bugs (025b1abedd19, 24278e9ffd28) have no findable fix commit and their matched findings were rejected on mechanism, so they count as misses.
