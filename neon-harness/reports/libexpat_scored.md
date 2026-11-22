# libexpat · Neon bug-hunt vs SWE-Sweep oracle (scored)

- Neon findings: 12 findings matched at least one oracle bug; 7 distinct bugs matched.
- Denominator: all 9 SWE-Sweep libexpat bugs.
- Parasoft published: 77.8% region (7/9), 33.3% strict (3/9).

## Accepted (6 bugs, 9 findings)

Region+strict (4 bugs):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| BUG-07 | cf1142438f11 | 96a69fe2 (upstream "lib: use a size_t for group sizes") | Bug reason: "overflow guard compiled out, realloc overflow". The #if UINT_MAX >= SIZE_MAX guard around the scaffIndex overflow check in doProlog/nextScaffoldPart compiles out on LP64, leaving the scaffIndex realloc unchecked; BUG-07's "missing size_t overflow check in nextScaffoldPart scaffIndex alloc, OOB write" claim identifies exactly this defect. Verified upstream change removes the compiled-out guard at both sites |
| BUG-08 | 44558a21f1b7 | 3f0a0cb6 (CVE-2022-25235, "Add missing validation of encoding") | Rewrites exactly the oracle's removed lines in xmltok_impl.c (69-72, 98-101: CHECK_NAME_CASES / CHECK_NMSTRT_CASES gain IS_INVALID_CHAR validation) plus the insertion-only prologTok hunk at 1142; the finding's "missing UTF-8 validity checks utf8_isName2/3 utf8_isNmstrt2/3" claim matches the added validation |
| BUG-10 | 44558a21f1b7 | 3f0a0cb6 | Same fix, insertion-only prologTok hunk: the added IS_INVALID_CHAR check validates multi-byte chars before use, matching the unknown-encoding over-read claim (borderline; strict empty) |
| BUG-12 | 0c5dbd0bb0a5 | 5026213864b (merge PR #842, issue #839) | The merge's xmlparse.c diff rewrites accountingGetCurrentAmplification's countBytesDirect == 0 fallback from `: 1.0f;` to count indirect bytes against lenOfShortestInclude; BUG-12's "Billion Laughs bypass when countBytesDirect==0" claim matches exactly |
| BUG-15 | 30d93b149d3d | 9d26eda6f85 ("Simplify control flow in internalEntityProcessor") | Bug reason: "suspend condition precedence". The diff removes the `else if (... XML_SUSPENDED)` precedence so entity close/tracking runs even when suspended, fixing the suspend-during-CDATA state corruption BUG-15 describes |

Region-only (2 bugs):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| BUG-01 | 8e5c789e8d3b | 847a645152f (CVE-2022-23852) | "Detect and prevent integer overflow in XML_GetBuffer": the exact neededSize signed-overflow guard the finding claims (insertion-only oracle, no strict set) |
| BUG-05 | 69f40cffb664 | 5290462a7ea | "Fix overeager DTD destruction in XML_ExternalEntityParserCreate": matches the UAF/double-free of parent m_dtd claim (insertion-only oracle, no strict set) |

## Rejected — line overlap, different mechanism

- BUG-39 / f67d952cb3de: the bug's oracle patch is commit b1e955449ce "Always consume BOM bytes when found in prolog" (hunk shapes 6/15/7 and removed-line patterns match exactly, with old_start drift); its defect is BOM handling in entityValueInitProcessor, not the finding's processXmlDecl minBytesPerChar==1 claim. Rejected.
- BUG-09 / 44558a21f1b7: surrogate-boundary claim in DEFINE_UTF16_TO_UTF16; the fix's changes are the name/nmstrt IS_INVALID_CHAR validation and prologTok check, not UTF-16 conversion. Rejected.
- BUG-11 / 44558a21f1b7: null-vtable-deref claim on UTF-16 surrogates; not the validation the fix adds. Rejected.
- BUG-16 / 30d93b149d3d: allowClosingDoctype claim; the control-flow fix does not touch it. Rejected.
- BUG-38 / cf1142438f11: XML_ParserReset OOM and groupSize rollback claims; the bug's defect is the compiled-out scaffIndex overflow guard. Rejected.

## Final score

- Neon region: 6/9 = 66.7% (Parasoft published: 77.8%)
- Neon strict: 4/9 = 44.4% (Parasoft published: 33.3%; Neon beats Parasoft on strict here)
- Novel findings: total findings minus the 9 matched ones (accepted findings: BUG-01, BUG-05, BUG-07, BUG-08, BUG-10, BUG-12, BUG-15)
- Unresolved: none. Every matched bug has a verified fix commit or verified upstream change. Note: this re-derivation revises the earlier session's tally (7/9 region, 5/9 strict) down by one bug: the BUG-39 pairing is a mechanism mismatch, verified against the oracle's hunk shapes.
