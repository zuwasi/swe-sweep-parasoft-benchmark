# tarantool · Neon bug-hunt vs SWE-Sweep oracle (scored)

- Neon findings: 189 (`F-001`..`F-189`), 33 findings matched at least one oracle bug region; 34 matched bug-pairs over 20 distinct bugs (F-183 matches two bugs).
- Denominator: all 40 SWE-Sweep tarantool bugs.
- Parasoft published: 57.5% region (23/40), 45.0% strict (18/40).
- Method: for every (finding, bug) pair the maintainer fix commit was located (find_fixes4.py; for the 5 NO-HIT squashed patches the fix was reconstructed as a commit range via `git log --all --find-object=<pre-state blob>` per file blob), and every oracle removed line was checked against the fix diff before judging mechanism identity.

## Accepted (15 bugs, 15 findings)

Region+strict (14 bugs):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| F-013 | 354f1a67549b | 6e45042473f | "box: fix creation of CK and FK constraints on the same field": `tuple_constraint_def_decode_fkey()` loop bound `*count` (includes old_count) changed to `map_size`, plus `int bytes` -> `size_t`; exactly the finding's OOB MsgPack read when `old_count > 0` |
| F-042 | 8c4fecf8c4f6 | 4205553a84c | "box: fix crash on update with delete by json path": `xrow_update_op_do_nop_delete()` map branch replaced `mp_sizeof_str(key_len)` (minimal-header assumption) with the real `field_key` pointer returned by `tuple_field_go_to_key()`; verbatim the finding's non-minimal MsgPack key header claim |
| F-060 | 40d35b1255f4 | 1f4bb194fff | "sql: fix wrong flag is_res_neg in sql_rem_int()": `*is_res_neg = true` -> `u_res != 0` after negative modulo; the finding's negative-zero invariant claim in `sql_rem_int()` (its `sql_atoi64()` claim is not part of the fix) |
| F-101 | 452a757c1c97 | 66907da2283 | "box: fix thread_id check in box.stat.net.thread[]": `thread_id > iproto_threads_count` -> `>=`; exact off-by-one claim |
| F-030 | 4753065c09ed | 3bc642298df | "lua/merger: fix use-after-free during iteration": `lbox_merge_source_gen()` pushed a new cdata for the source instead of returning the same object (no refcount); oracle removes exactly the `/* Push merge_source, tuple. */` block; matches the finding's `merger:ipairs()/pairs()` UAF claim |
| F-055 | f7aac1b241c3 | 440a0f8cff7 | "sql: fix error with new field in new index": `tarantoolsqlIdxKeyCompare()` now handles `fieldno >= base_len` (absent field) by comparing NULL mem instead of walking past the tuple data; matches the absent-field miscomparison/OOB-read claim |
| F-092 | 067eeb123c0e | 64d87e88df8 | "memtx: fix dirty data written to snapshot for hash index": creates the missing MVCC snapshot cleaner in `memtx_hash_index_create_snapshot_iterator()` and fixes `tuple_data_range(*res, ...)` -> `tuple_data_range(tuple, ...)` in `hash_snapshot_iterator_next()`; both halves of the finding's claim (oracle removed-index drift of 2 lines is a generator artifact; hunk shape matches) |
| F-093 | 78ccf4ee3c7f | 5c0d7117db1 | "memtx: fix HASH index 'GT' iterator `next` method set incorrectly": removed `ptr->next_raw = hash_iterator_ge_raw_base` from `hash_iterator_gt_raw_base` and moved the switch into `WRAP_ITERATOR_METHOD` to the clarifying `hash_iterator_ge_raw`; exactly the finding's bypassed-MVCC-clarification claim |
| F-120 | 3203ce795485 | 268de9694de | "datetime: fix precision overflow": `(int)strtol()` width overflow clamped (`INT_MIN..INT_MAX`, errno, `> 9` -> 9), removing the OOB `pow10[9 - width]` read; matches the finding's `(int)strtol()` pow10 claim (its NUL-terminator claim is not part of the fix) |
| F-137 | e409eec61dc6 | 7c5651afc21 | "sql: always treat NaN as NULL": `port_lua_get_vdbemem()` / `port_c_get_vdbemem()` MP_FLOAT/MP_DOUBLE cases now map NaN to `MEM_TYPE_NULL`; exactly the finding's NaN-to-NULL invariant bypass claim (its mpstream-error leak claim is not part of the fix) |
| F-138 | f4801b8daa83 | 4c216c4ce24 | "sql: do nothing in ROUND() if precision is too big": `func_round_double()` guard `n > 322` and removal of the `MIN(n, INT_MAX)` + `tt_sprintf("%.*lf", precision, d)` rounding path; exactly the finding's unbounded `tt_sprintf` precision claim (its func_unicode/replaceFunc claims are not part of the fix) |
| F-187 | 35044a57ea04 | 086b4dde18a | "fiber: don't skip fiber_obj:info() arguments": `lbox_do_backtrace(L)` -> `lbox_do_backtrace(L, index)`, called with slot 1 from `lbox_fiber_info` and slot 2 from `lbox_fiber_object_info`; exactly the finding's slot-1-vs-slot-2 claim |
| F-065 | a0264983c4a6 | 2705e227fd + 056e26a1f9 | Squashed patch = "sql: throw error on creation of too many indexes" (adds the missing `parse->is_aborted = true;` on the `index_def_is_valid()` failure path in `sql_create_index()`, build.c @2848) + "box: rework index_def_is_valid()" (renames it to `index_def_check()`, moves validation to `index_def_new` callers in alter.cc/index_def.c/index_def.h). The finding's "missing parse->is_aborted" claim matches the first commit exactly (its sqlAddPrimaryKey NULL-deref claim is not part of the fix) |
| F-024 | 46aa6eb83fb9 | 4910976938 + 1c9599bef6 | Squashed patch = "sql: introduce OpenSpace opcode" (gh-7358) + "drop unused opcode IteratorReopen". The maintainer-fixed defect: opcode P4 held a raw `struct space *` captured at parse time that goes stale (truncate() replaces the space object) -> sigfault; the fix drops `P4_SPACEPTR`/`p4.space` entirely and resolves the space by ID at runtime. F-024's strict lines sit on `struct space *space = pOp->p4.space;` in `OP_Update` (vdbe.c 3471-3493), i.e. it identifies the dangling-struct-space-pointer defect at the exact code removed. Borderline accept: the finding's "across yields" trigger and its space_def/index claims are not what the fix addresses; the accepted claim is the UAF of `struct space` held in VDBE opcode arguments |

Region-only (1):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| F-127 | 02d1749c6bfb | 05fc976ebe8 | see table above; oracle hunk `src/lib/core/prbuf.c @206` is insertion-only (`removed: []`), so no strict set exists and the bug can only score region |

## Rejected (7 distinct bugs touched, 19 pairs): line overlap, different mechanism

- F-012 / 77c69aba7b2a: fix range = 5a5e72b94c ("denormalize `ITER_ALL` to `ITER_GE` in TREE index", removes the oracle's `case ITER_ALL:` blocks in memtx_tree.cc) + 7360281e27 ("fix handling of corner cases gap tracking in transaction manager", rewrites `memtx_tx_track_gap_slow()`, oracle memtx_tx.c @1748 removes 38 lines matched 37/38, one blank-line artifact). Fixed mechanism: iterator-type denormalization + gap-write corner cases when the key equals the gap item. F-012 claims heap type confusion / OOB destroying a disabled functional TREE index (read-view cast + disabled-index vtab lines); different mechanism.
- F-014 / 46b0022d552a: fix 22fc1f94b48 "decimal: fix index comparison with Inf, NaN": the defect was unchecked `decimal_from_double()` return on Inf/NaN (assertion/garbage compare); fix checks `rc == NULL` and compares via `decimal_compare_nan()`. F-014 claims shift-count UB `1U << ext_type` in field_def.h, missing MP_EXT payload validation, and a hardcoded UUID offset; none of these is the Inf/NaN mechanism (the fix only adds `assert(rc != NULL)` after `decimal_unpack`). Line overlap only.
- F-016 / 8c4fecf8c4f6: fix 4205553a84c changes the map-key branch of `xrow_update_op_do_nop_delete()`; F-016 claims a 32-bit unsigned wraparound on nested array delete (`index + del.count`). The array branch arithmetic (`index + op->arg.del.count > size`) is only renamed, not changed. Different mechanism.
- F-029 / 8c4fecf8c4f6: F-029 claims `cord_ibuf` UAF/double-put when a Lua `__serialize` metamethod yields (src/box/lua/*); the fix touches tuple path lookup and update ops only. Unrelated.
- F-041 / 8c4fecf8c4f6: F-041 claims a prefix `memcmp` without token boundary check in `xrow_update_route_next()`; the fix's xrow_update_route.c change only passes `/*field_key=*/NULL` to `tuple_field_go_to_key()`. Different mechanism.
- F-136 / 8c4fecf8c4f6: F-136 claims `tuple_validate_raw()`/`tuple_field_map_create()` bypass `exact_field_count` when field count is 0; the fix never touches validation. Unrelated.
- F-020 / 46aa6eb83fb9: F-020 claims heap/region overflow in `vdbe_field_ref_create()` on tuples exceeding declared field_count; the OpenSpace patch only reworks opcode space arguments. Unrelated.
- F-022 / 46aa6eb83fb9: F-022 claims a format-string vulnerability in `OP_SetDiag` via `box_error_set()`; the OpenSpace patch does not touch error formatting. Unrelated.
- F-067 / 46aa6eb83fb9: F-067 claims unconditional `p->ignoreRaised++` and premature `p->nChange++` in `OP_Update`; the patch only removes `pOp->p4.space` acquisition from `OP_Update` (and reworks SInsert/SDelete space lookup). Change-counting semantics untouched. Different mechanism.
- F-068 / 46aa6eb83fb9: F-068 claims uninitialized `pSrcIdx`, dead NULL check, missing ROLLBACK in `xferOptimization()`; the patch's insert.c changes there only rework the `OP_IdxInsert` emission (space pointer -> space ID). Different mechanism.
- F-141 / 46aa6eb83fb9: F-141 claims deterministic leaks in `sqlVXPrintf()`, `vdbe_emit_halt_with_presence_test()`, `vdbe_emit_ck_constraint()`; the OpenSpace patch changes no allocation ownership. Unrelated.
- F-166 / 46aa6eb83fb9: F-166 claims a Lua stack-indexing bug in `lbox_trigger_reset()` (src/lua/trigger.c); the bug's files are all `src/box/sql/*` and the match is a coincidental line-number overlap with `sql/trigger.c` oracle hunks (@193, @227). Completely different file and mechanism.
- F-021 / f3e2922c14ee: fix 5eefa06f04c "sql: reset autoincrement IDs before execution" (rewrites the `sql_unbind` comment in execute.c @219 and inserts `sql_reset_autoinc_id_list()` + its declaration, the oracle's insertion-only hunks). F-021 claims missing `vdbeUnbind()` in `sql_bind_*_static()`; the fix changes no bind/unbind behavior. Different mechanism.
- F-078 / f3e2922c14ee: F-078 claims UAF of prepared `struct sql_stmt` across fiber yield; the fix is the autoinc-ID reset above. Different mechanism.
- F-081 / fc35d5a6cfe7: fix range = fda38e663f ("fix reverse iterators gap tracking": replaces the naive `memtx_tree_lower_bound_elem(it->current, NULL)` recovery with `tree_iterator_prev_reposition()` using exact match) + 837e052434 ("remove `tree_iterator_set_current_tuple` on clarified tuples", removes the oracle's @565/@708 lines). F-081 claims UAF/double-free on OOM in `memtx_tx_track_gap_slow()`; the fix never touches that function. Different mechanism.
- F-083 / fc35d5a6cfe7: F-083 claims a dangling fiber `txn` pointer on `txn_begin()` OOM; not touched by the fix range. Unrelated.
- F-094 / fc35d5a6cfe7: F-094 claims a multikey TREE iterator dereferences an invalidated `tree_iterator` after the MVCC story GC bound; the fixed defect (gh-7409) is that reverse iterators clarify the successor early so the gap item must be attached to the story currently present in index, fixed by reusing the check logic to set the current tuple. Different mechanism.
- F-183 / 7530007077a3: fix range = 07c0d3a68a ("refactor `index_def_new`": removes the redundant `unique_part_count = part_count` assignment for non-unique indexes, oracle index_def.c @97) + bfcd8ca7ef ("fix TREE index `get` check for part count": `part_count == cmp_def->part_count` -> `assert(part_count == cmp_def->unique_part_count)`, memtx_tree.cc @905). Fixed mechanism: unique_part_count semantics. F-183 claims `memtx_tree_data_is_equal()` ignores hints, skipping entries on position recovery. Different mechanism.
- F-183 / fc35d5a6cfe7: the oracle removes the `memtx_tree_data_is_equal()`-based position-recovery blocks (fda38e663f, matched 4/4 twice), but the maintainer's stated defect is reverse-iterator gap tracking after early clarification, not hint-ignoring equality; the replacement still compares data without hints. Line overlap, different mechanism.

## Final score

- Neon region: 15/40 = 37.5% (Parasoft published: 57.5% = 23/40)
- Neon strict: 14/40 = 35.0% (Parasoft published: 45.0% = 18/40)
- Novel findings: 174 of 189 (15 findings accepted at least one bug)
- Unresolved: none. All 34 matched bug-pairs have a verdict; every oracle hunk of every fix range is accounted for (remaining per-line mismatches are the generator's small line-drift artifact, verified by hunk shape).

### Disagreement with the cross-check reference

The earlier session recorded Neon tarantool region 14/40 (35.0%), strict 12/40 (30.0%). This scoring finds 15/40 region and 14/40 strict, i.e. +1 region and +2 strict. The difference is evidence-based, not a rule change:

- F-127 / 02d1749c6bfb (region-only): the fix `05fc976ebe8` adds exactly the empty-buffer early return in `prbuf_check()` that the finding's first bundled claim describes; per the bundling rule this is an accept, scored region-only because the oracle hunk is insertion-only.
- F-065 / a0264983c4a6: commit `2705e227fd` adds the missing `parse->is_aborted = true;` at build.c @2848, which is the finding's first claim verbatim; the fix was only findable via `--find-object` on the build.c pre-state blob after the path-based search reported NO-HIT.
- F-024 / 46aa6eb83fb9: borderline accept documented above; if one rejects it, the counts become 14/40 region (35.0%) and 13/40 strict (32.5%).
