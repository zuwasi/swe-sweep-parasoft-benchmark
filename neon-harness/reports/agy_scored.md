# Antigravity pilot scoring: Gemini 4 Neon in Google Antigravity vs SWE-Sweep oracle

Run: `agy` 1.5.15 headless (`--dangerously-skip-permissions --print`), same base commits as the
Amp arms (libexpat 57c7da69b78e, jerryscript 5fdeb7c1d68e, micropython 9b486340da22), same hunter
prompt with three documented harness adaptations (anti-stall note, incremental report writing,
neutral wording to pass Gemini safety filters). Findings: 41 (libexpat) / 78 (jerryscript) /
68 (micropython). Matcher: `match_findings.py`, then per-pair verdicts against the fix commits
below (same methodology as the Amp-arm scored reports).

## libexpat (9 oracle bugs) - region 6/9 = 66.7%, strict 5/9 = 55.6%

| Finding | Bug | Verdict | Fix commit | Evidence |
|---|---|---|---|---|
| BUG-01 | 8e5c789e8d3b | ACCEPT region-only | 847a645152f (CVE-2022-23852) | Same claim as Amp BUG-01: signed overflow of neededSize in XML_GetBuffer skips reallocation. Insertion-only oracle, no strict set |
| BUG-06 | 44558a21f1b7 | ACCEPT strict | 3f0a0cb6 (CVE-2022-25235) | "UTF-8 validation bypass in XML names" is exactly the missing IS_INVALID_CHAR validation the fix adds to CHECK_NAME_CASES / CHECK_NMSTRT_CASES and prologTok |
| BUG-13 | 0c5dbd0bb0a5 | ACCEPT strict | 5026213864b (PR #842, issue #839) | Finding quotes the exact `countBytesDirect ? ... : 1.0f` fallback in accountingGetCurrentAmplification and derives the countBytesDirect==0 bypass via XML_UseForeignDTD + root-element start; the fix replaces that fallback to count indirect bytes against lenOfShortestInclude, the finding's own remediation. (Bug numbering in the oracle is fix-parent coordinates; base-coordinate removed line is inside the finding's span) |
| BUG-15 | cf1142438f11 | ACCEPT strict | 96a69fe2 | Same claim as Amp BUG-07: unchecked m_groupSize * sizeof(int) in nextScaffoldPart scaffIndex allocation on 32-bit; the fix removes the compiled-out UINT_MAX guard |
| BUG-23 | 30d93b149d3d | ACCEPT strict | 9d26eda6f85 | internalEntityProcessor suspend/resume handling: abandons outer nested entities on resume, continues after suspend. Fix simplifies control flow so tracking runs even when suspended. Same function, same defect class |
| BUG-32 | 4e25524fb119 | ACCEPT strict | eb976a36d01 (PR #645, issue #612) | Bundled finding; claim 3 "uncleared m_tempPool on skipped ATTLIST enum" matches the fix exactly (poolClear moved out of the conditional in doProlog). Base-coordinate removed line 4831 sits inside the finding's 4789-4834 span |
| BUG-41 | f67d952cb3de | REJECT | b1e955449ce | Oracle defect is BOM handling in entityValueInitProcessor ("Always consume BOM bytes when found in prolog"). Finding claims TextDecl version contract, GetUserData(NULL), #define inline. Line overlap only |
| BUG-41 | e567e550f1be | REJECT | 7d7975b0928 | Oracle fix rejects an empty version in the XML declaration (insertion-only, xmltok.c doParseXmlDecl at 1177, inside the finding's span but different mechanism: the finding claims version==NULL TextDecl contract, not empty-version acceptance) |
| (BUG-16, BUG-20, BUG-38 on 44558a21f1b7) | 44558a21f1b7 | REJECT (extra findings, same bug already accepted via BUG-06) | 3f0a0cb6 | MIN_SIZE null function pointer, OOB ptr advance in attributeValueTok/entityValueTok, character-table edge cases: none are the IS_INVALID_CHAR validation the fix adds |

Parasoft published: region 7/9 = 77.8%, strict 3/9 = 33.3%. Amp arm: region 6/9 = 66.7%, strict 4/9 = 44.4%.

## jerryscript (15 oracle bugs) - region 4/15 = 26.7%, strict 3/15 = 20.0%

| Finding | Bug | Verdict | Evidence |
|---|---|---|---|
| BUG-013 | df8c37f98e76 | ACCEPT strict | Exact same defect as Amp BUG-068: jerry_define_own_property checks is_enumerable instead of is_configurable (2468-2475) |
| BUG-048 | 5144355d084f | ACCEPT strict | Same block and mechanism as Amp BUG-058: JSON.stringify NULL deref on boxed String whose toString throws (1174-1196 vs removed 1189-1214) |
| BUG-038 | 662bbee88446 | ACCEPT region-only | Oracle is "missing null check after species create" in the slice fast path, no strict lines. Finding's bundled slice NULL-deref claim (829-888) covers the fast path; same acceptance basis as Amp BUG-018 |
| BUG-056 | 9bf98944df1f | ACCEPT strict | Exact same defect as Amp BUG-088: Date.prototype.get* on Invalid Date returns string "NaN" instead of number NaN (237-243) |
| BUG-065 | 042a8ceedc15 | REJECT | Oracle defect is JSON.stringify property_list_p error-path ownership; finding claims empty replacer array ignored. Line overlap only, different mechanism |

Parasoft published: region 13/15 = 86.7%, strict 12/15 = 80.0%. Amp arm: region 7/15 = 46.7%, strict 6/15 = 40.0%.

## micropython (22 oracle bugs) - region 2/22 = 9.1%, strict 2/22 = 9.1%

| Finding | Bug | Verdict | Fix commit | Evidence |
|---|---|---|---|---|
| MP-035 | 639baaf0eaee | ACCEPT strict | 2e4dda3c207 | "py/modmath: Fix two-argument math function domain check": pow(2.0, inf) no longer raises ValueError, exactly the finding's missing !isinf(y) claim (the bundled ldexp claim is not part of the fix) |
| MP-041 | 85267a3c1ee8 | ACCEPT strict | 908ab1ceca1 (#13041) | Verified the fix content: old code zero-pads high bytes for negative values via MIN(len, sizeof(val)) set; new code sign-extends with 0xFF and raises OverflowError. Finding's "(-1).to_bytes(10,'big') zero-pads instead of sign-extending or rejecting" matches. Removed lines 436/445/446 overlap the finding's objint.c 436-447 span |
| MP-053 | ef93b8337084 | REJECT | f397a3ec318 | Fix validates indices()' argument is an integer (#13007); finding claims negative-length overflow and 64-to-63-bit truncation. Same rejection as Amp MP-095, line overlap only |

Parasoft published: region 15/22 = 68.2%, strict 7/22 = 31.8%. Amp arm: region 9/22 = 40.9%, strict 8/22 = 36.4%.

## Totals (46 oracle bugs across the three repos)

| Arm | Region | Strict |
|---|---|---|
| Parasoft C/C++test static analysis (published) | 35/46 = 76.1% | 22/46 = 47.8% |
| Gemini 4 Neon in Amp | 22/46 = 47.8% | 18/46 = 39.1% |
| Gemini 4 Neon in Google Antigravity (pilot) | 12/46 = 26.1% | 10/46 = 21.7% |

## Verdict notes

- 16 matched pairs total; 12 accepted (11 bugs), 4 rejected pairs. Unresolved: none.
- Rejected pairs are all line-overlap-only mechanism mismatches, consistent with the Amp-arm
  rejections for the same oracle bugs (042a8ceedc15, ef93b8337084, f67d952cb3de were also Amp
  misses or rejections).
- Borderline accepts, documented: BUG-038/662bbee88446 (bundled slice NULL-deref claim, region
  only) and BUG-32/4e25524fb119 (one of three bundled claims matches the fix exactly).
- Antigravity found e567e550f1be's location (doParseXmlDecl version handling) but claimed a
  different mechanism, so it scores as a miss for both arms.
