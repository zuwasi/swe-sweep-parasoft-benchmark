# godot · Neon bug-hunt vs SWE-Sweep oracle (scored)

- Neon findings: 160 (`BUG-001`..`BUG-160`), 3 findings matched at least one oracle bug region; 3 matched bug-pairs over 3 distinct bugs (`BUG-038`/ad060d7c9da5, `BUG-058`/16e44a6ee5fd, `BUG-124`/3cec1823b69a).
- Denominator: all 17 SWE-Sweep godot bugs (the 14 bugs with no matched finding are misses by definition).
- Parasoft published: 76.5% region (13/17), 41.2% strict (7/17).

Fix-commit identification notes: `find_fixes4.py` candidates were verified against the oracle hunks. Two data-quality observations discovered during verification, neither of which changes any verdict:

1. For 16e44a6ee5fd and ad060d7c9da5 the oracle hunk positions match the fix's first-parent diff exactly, and the stored pre-images are byte-identical to the fix parent's blobs.
2. For 3cec1823b69a the stored pre-image directory (`abb4a2f215`) holds the fix-parent (cb8cb95, 2025-04-03) version of text_edit.cpp, but the oracle hunk line numbers are in the task-base version's coordinates (master as of bb343ed1c5, 2025-02-07, shifted 69..218 lines earlier). After re-anchoring to the base version, all four oracle hunks align exactly with PR #104776's changes. The oracle patch files under /tmp were already deleted, so this was reconstructed from the recorded hunks plus git history plus the GitHub PR base SHA (1f56d96cf2c7).

## Accepted (1 bug, 1 finding)

Region-only (1; the oracle hunk is insertion-only, so no strict set exists):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| BUG-038 | ad060d7c9da5 | a2b9fc08e31 | "Fix ghost collisions in segment_intersects_convex()" inserts 4 lines exactly at the oracle hunk (@@ -292,6, removed: []): when a plane of the convex is parallel to the segment (`abs(den) <= CMP_EPSILON`) it now returns `false` if `p.is_point_over(p_from)`, instead of unconditionally `continue`-ing past a separating plane. The finding bundles many claims and only the "Geometry2D/3D" one lands at the matched lines: its span `core/math/geometry_3d.h` 291-318 covers the parallel-plane branch, matched region 294-299. The claim is component-level (the title states no mechanism for Geometry2D/3D), so this is the weakest acceptance here; it is credited under the bundled-claims rule (one claim matches at the matched lines, no conflicting mechanism claimed). All other claims in the bundle (PackedDataContainer::_pack, Image::resize mipmaps, StreamPeerGZIP, PList, XMLParser, marshalls, Geometry2D) are not part of this fix. |

## Rejected (2 distinct bugs, 2 findings) — line overlap, different mechanism

- BUG-058 / 16e44a6ee5fd: fix 5836a24a1ce (merge of PR #99488 "[TextServer] Fix some line breaking edge cases", branch 0708048530). Verified: all 17 oracle hunks in servers/text_server.cpp (+ text_server.h 538) match the merge diff vs first parent 2dc30a4c39 exactly (old_starts 827, 840, 850, 867, 880, 889, 905, 919, 980, 996, 1009, 1019, 1036, 1047, 1059, 1083, 1808). The fix is a line-break logic rewrite: aggregate `advance * repeat` over glyphs sharing start/end (`adv` loop), pick the break via `cur_safe_brk` (set to `end_pos` when edge spaces are trimmed), skip same-end glyphs when advancing `prev_safe_break`, and fix the final-line pushes (`last_end` guard, `MAX(last_end, line_start)`). The finding claims a memory-safety defect: heap under-read `l_gl[-1]` and over-read `l_gl[l_size]` in the BREAK_TRIM_EDGE_SPACES trimming. That is a different mechanism: the trailing trim block is guarded by `if (l_size > 0)` (pre-image line 925), so `l_gl[-1]` cannot occur there, and the rewrite keeps the same unguarded `l_gl[start_pos]` reads, adding bounds only to its own new loops; no bounds check is added at either claimed site. The finding's regions and even two strict lines (929, 1086) are oracle-removed lines, but the claimed defect (OOB read) is not what the maintainer changed (wrong break positions). REJECT; 16e44a6ee5fd counted as miss.
- BUG-124 / 3cec1823b69a: fix 9bbda47794e (merge of PR #104776 "Fix TextEdit VScroll max tolerance", base 1f56d96cf2c7). Verified after re-anchoring to the task-base version bb343ed1c5: oracle removed line 786 = `int draw_amount = visible_rows + (smooth_scroll_enabled ? 1 : 0);` in _notification (rewritten to `visible_rows + 1`), 4424 = the same line in get_minimap_line_at_pos, 7851 = `if (scroll_past_end_of_file_enabled && !fit_content_height) {` in _update_scrollbars (gains `|| visible_rows == 0`), 7874 = the blank line after `set_v_scroll(get_v_scroll())`. The finding's TextEdit claim is an infinite loop in `TextEdit::search()` (span scene/gui/text_edit.cpp 4192-4235, which is search()'s find loop in base coordinates; matched region 4204-4210, strict 4207), plus Control focus loops, GraphEdit frame cycles, and a TabContainer null deref. The fix never touches search(), Control, GraphEdit, or TabContainer; its mechanism is scrollbar max-tolerance / draw-amount logic. The finding's own Control/GraphEdit/TabContainer claims are also untouched by the fix. REJECT; 3cec1823b69a counted as miss.

## Final score

- Neon region: 1/17 = 5.9% (Parasoft published: 76.5%)
- Neon strict: 0/17 = 0.0% (Parasoft published: 41.2%)
- Novel findings: 159 of 160 (only BUG-038 accepted at least one bug)
- Unresolved: none. All 3 matched bug-pairs have an identified and verified fix commit; both rejected pairs were rejected on mechanism, so they count as misses.
- Cross-check: this result agrees exactly with the earlier session's recorded reference (Neon godot region 1/17 = 5.9%, strict 0/17). The one accepted pair is the same one (BUG-038/ad060d7c9da5, the only insertion-only oracle, hence region-only), and the same two rejections.
