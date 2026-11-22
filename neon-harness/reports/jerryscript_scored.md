# jerryscript scoring (Gemini 4 Neon in Amp, base 5fdeb7c1d68e8c5209e186e1760bc703a723d588)

Agent report: 97 findings (29 Critical / 38 High / 23 Medium / 7 Low), all SUSPECTED.
Parasoft published: region 13/15 (86.7%), strict 12/15 (80.0%).

## Accepted matches (7 region, 6 strict of 15 benchmark bugs)

| bug_id | defect | Neon finding | verdict | region | strict |
|---|---|---|---|---|---|
| 072dcea299cd | literal decode order and delta wrong (MEMORY, BD-PB-POSSIB) | BUG-001 off-by-one first_byte/encoding handling, cites js-parser.c 1411-1452 covering base 1421-1427 decode block | borderline accept: same decode block, same off-by-one-comparison class, mechanism stated differs | yes | yes |
| 32f5320c7e4d | this.x assignment opcode sequence wrong (BD-PB-POSSIB) | BUG-003 CBC_PUSH_THIS_LITERAL type confusion in assignment parsing | exact same defect: removed 2201-2204/2293-2295 are the CBC_PUSH_THIS_LITERAL branches BUG-003 describes | yes | yes |
| 5144355d084f | result value mishandled, EXP39 | BUG-058 JSON.stringify NULL deref unboxing boxed String (1174-1196 vs removed 1189-1214) | same block, error-path value handling | yes | yes |
| 662bbee88446 | missing null check after species create | BUG-018 slice fast-path NULL deref component (796-891 covers rewritten 855) | accept: same function, NULL deref in slice fast-path; bug has no strict lines | yes | n/a |
| 9bf98944df1f | Date get* wrong return type NaN (OPERAND) | BUG-088 Date.prototype.get* returns string NaN | exact same defect (237-243) | yes | yes |
| df8c37f98e76 | configurable/enumerable swapped, MISRA2004-16_10_a | BUG-068 jerry_define_own_property checks is_enumerable instead of is_configurable | exact same defect (2468-2475) | yes | yes |
| edaaae2dd276 | digits buffer overflow for zero, HIGH, BUFFER_OVERFLOW | BUG-089 toFixed rounding/sign bugs at 688-698 covering rewritten 695 | same statement region of toFixed digits computation; mechanism differs | yes | yes |

## Rejected line-overlaps (mechanism differs)

- 042a8ceedc15 (JSON.stringify property_list_p error-path ownership) vs BUG-059 recursion: different defect.
- 1eb47ad8b475 (array length/property-flags rework, property pointer not initialized) vs BUG-021/053/054: different defect.
- 2b0230207b47 (duplicated label check restructure) vs BUG-030 SCAN_STACK_USE_ASYNC: different defect.

## Clear misses (no overlapping finding)

25396dc4b88b (fmod unchecked), 4afcc94994c8 (unary opcode), 5ca8de954fce (ternary target),
63583f11d059 (scanner compression size), bf72a9ea61e4 (isfinite in parseFloat).

## Score

- Neon: region 7/15 (46.7%), strict 6/15 (40.0%)
- Parasoft: region 13/15 (86.7%), strict 12/15 (80.0%)
- Novel findings: 90 (97 minus the 7 accepted)
