# libexpat Bug-Hunt Code Review Report

- **Target Repository:** `libexpat` (`expat/lib/`)
- **Commit:** `57c7da69b78e3698e112a6b5da19d5109b8232d1` (2.4.3+ / pre-2.4.4)
- **Scope:** Full static code review of C sources and headers under `expat/lib/` (`xmlparse.c`, `xmltok.c`, `xmltok_impl.c`, `xmltok_ns.c`, `xmlrole.c`, `xmlrole.h`, `xmltok.h`, `xmltok_impl.h`, `utf8tab.h`, `asciitab.h`, `iasciitab.h`, `latin1tab.h`, `nametab.h`, `siphash.h`, `internal.h`, `expat.h`, `expat_external.h`, `libexpat.def`, `libexpatw.def`).
- **Methodology Note:** All findings below were established via line-by-line static source code auditing, caller/precondition verification, and control-flow/arithmetic invariant analysis without generating functional crash PoCs or exploit payloads. Accordingly, all statuses are recorded as `SUSPECTED (argued from code)`.

---

## Summary Table

| ID | Severity | Subsystem | Title | Status |
| :--- | :--- | :--- | :--- | :--- |
| BUG-01 | Critical | `xmlparse.c` / Buffer Management | Signed integer overflow in `XML_GetBuffer` (`neededSize += keep`) skips reallocation and causes heap buffer overflow | SUSPECTED (argued from code) |
| BUG-02 | Critical | `xmlparse.c` / Tag Storage | Integer overflow in `storeRawNames` (`bufSize`) skips `REALLOC` and causes heap buffer overflow (plus signed shift overflow in `doContent`) | SUSPECTED (argued from code) |
| BUG-03 | Critical | `xmlparse.c` / Content Model | Unchecked `unsigned` overflow in `dtd->contentStringLen` causes undersized allocation in `build_model` and heap buffer overflow in `build_node` | SUSPECTED (argued from code) |
| BUG-04 | Critical | `xmlparse.c` / Shared DTD | Heap buffer overflow on `dtd->scaffIndex` via capacity desynchronization and shrinking between root and external PE parsers | SUSPECTED (argued from code) |
| BUG-05 | Critical | `xmlparse.c` / Parser Lifecycle | Use-after-free and double-free of parent parser's shared `m_dtd` on OOM in `parserCreate` via `XML_ExternalEntityParserCreate` | SUSPECTED (argued from code) |
| BUG-06 | Critical | `xmltok.c` / `xmltok_impl.c` / `utf8tab.h` | UTF-8 validation bypass in XML names accepts overlong sequences, non-continuation bytes, embedded NULs, and delimiter-swallowing bytes | SUSPECTED (argued from code) |
| BUG-07 | High | `xmlparse.c` / Entity Resume | Heap use-after-free in `internalEntityProcessor` due to missing `storeRawNames(parser)` (plus wrong `m_processor` for external general entities) | SUSPECTED (argued from code) |
| BUG-08 | High | `xmlparse.c` / Entity Resume | `allowClosingDoctype` guard bypassed in `internalEntityProcessor`, allowing DOCTYPE closure and encoding/processor confusion from resumed internal PE | SUSPECTED (argued from code) |
| BUG-09 | High | `xmlparse.c` / Recursion | Unbounded C-stack recursion (stack overflow crash) in `build_node` and non-cyclic entity expansion chains | SUSPECTED (argued from code) |
| BUG-10 | High | `xmlparse.c` / Namespaces | Namespace separator injection in `addBinding` and expanded attribute name collisions / incomplete duplicate check in `storeAtts` | SUSPECTED (argued from code) |
| BUG-11 | High | `xmlparse.c` / Public Buffer API | Missing `len` bounds validation (`len < 0` / OOB) and unchecked signed `m_parseEndByteIndex` overflow in `XML_ParseBuffer` | SUSPECTED (argued from code) |
| BUG-12 | High | `xmlparse.c` / Threading & External Entities | Unsynchronized shared parent-parser access in `XML_ExternalEntityParserCreate` child parsers causes data races and UAF, violating documented thread-safety contract | SUSPECTED (argued from code) |
| BUG-13 | High | `xmlparse.c` / Billion Laughs Protection | Complete bypass of amplification protection under `XML_UseForeignDTD` when document begins directly with root element | SUSPECTED (argued from code) |
| BUG-14 | High | `xmlparse.c` / Epilog & Accounting | Undefined behavior (`NULL - s`) and accounting counter corruption in `epilogProcessor` on negative prolog tokens | SUSPECTED (argued from code) |
| BUG-15 | High | `xmlparse.c` / Content Model (32-bit) | Unchecked `parser->m_groupSize * sizeof(int)` overflow on 32-bit platforms in `nextScaffoldPart` initial `dtd->scaffIndex` allocation | SUSPECTED (argued from code) |
| BUG-16 | High | `xmltok.c` / `xmltok_impl.c` (`XML_MIN_SIZE`) | NULL function pointer dereference in `XML_MIN_SIZE` builds when a UTF-16 high surrogate appears in any XML name | SUSPECTED (argued from code) |
| BUG-17 | High | `xmltok.c` / UTF-16 Conversion | `DEFINE_UTF16_TO_UTF16` (`little2_toUtf16`/`big2_toUtf16`) wrong bitmask and boundary check drops low surrogates and splits surrogate pairs | SUSPECTED (argued from code) |
| BUG-18 | High | `xmltok.c` / `xmltok_impl.c` / UTF-16 | Missing UTF-16 surrogate pair validation (`IS_INVALID_CHAR` always `0`) accepts unpaired high surrogates paired with arbitrary code units | SUSPECTED (argued from code) |
| BUG-19 | High | `xmltok.c` / Unknown Encoding | Out-of-bounds read and unbounded loop past `fromLim` in `unknown_toUtf8` / `unknown_toUtf16`, reachable via `parsePseudoAttribute` step desync | SUSPECTED (argued from code) |
| BUG-20 | Medium | `xmltok_impl.c` / Literal Scanners | Out-of-bounds pointer advance (`ptr += n` past `end`) in `attributeValueTok`, `entityValueTok`, and `updatePosition` | SUSPECTED (argued from code) |
| BUG-21 | Medium | `xmlrole.c` / Conditional Sections | `externalSubset1` rejects all valid internal PE references inside `<![INCLUDE[ ... ]]>` and allows a PE to close an outer `INCLUDE` section | SUSPECTED (argued from code) |
| BUG-22 | Medium | `xmltok_impl.c` / Conditional Sections | `ignoreSectionTok` fails to recognize `]]>` after odd runs of `]` (e.g., `]]]>`) and omits `ptr >= end` guard | SUSPECTED (argued from code) |
| BUG-23 | Medium | `xmlparse.c` / Entity Resume | `internalEntityProcessor` abandons outer nested internal entities on resume and continues parsing after suspend on final entity token | SUSPECTED (argued from code) |
| BUG-24 | Medium | `xmlparse.c` / DTD Prolog | `XML_ROLE_ENTITY_VALUE` commits entity value and invokes `m_entityDeclHandler` (potentially with `value == NULL`) before checking `storeEntityValue` error | SUSPECTED (argued from code) |
| BUG-25 | Medium | `xmlparse.c` / Context & OOM | `setContext` leaves `prefix->name == NULL` in `dtd->prefixes` on OOM; retrying `XML_Parse` causes NULL dereference in `keyeq` | SUSPECTED (argued from code) |
| BUG-26 | Medium | `xmlparse.c` / Attributes & OOM | Unchecked `lookup()` failure in `getAttributeId` for `xmlns:*` silently drops namespace binding and leaks raw attribute | SUSPECTED (argued from code) |
| BUG-27 | Medium | `xmlparse.c` / Handlers | NULL function pointer dereferences if `m_startDoctypeDeclHandler` (`XML_ROLE_DOCTYPE_CLOSE`) or `m_defaultHandler` (`reportDefault`) is cleared dynamically | SUSPECTED (argued from code) |
| BUG-28 | Medium | `xmlparse.c` / Position Tracking | Use-after-free in `XML_Parse` (`#ifndef XML_CONTEXT_BYTES`) when querying line/column after error or final chunk | SUSPECTED (argued from code) |
| BUG-29 | Medium | `xmlparse.c` / Initialization & Pool | Uninitialized heap reads in `XML_GetIdAttributeIndex` (`m_idAttIndex`), `XML_GetParsingStatus` (`finalBuffer`), and `poolGrow` (`freeBlocks` copy) | SUSPECTED (argued from code) |
| BUG-30 | Medium | `xmlparse.c` / `XML_ATTR_INFO` | Unrelated pointer subtraction UB and heap-distance leak in `storeAtts` (`XML_ATTR_INFO`) during internal entity expansion | SUSPECTED (argued from code) |
| BUG-31 | Medium | `xmlparse.c` / State Machine & Reset | Multiple processor state bugs in `cdataSectionProcessor`, `externalEntityInitProcessor3`, `entityValueInitProcessor`, `XML_ParserReset`, and `XML_StopParser` | SUSPECTED (argued from code) |
| BUG-32 | Medium | `xmlparse.c` / DTD Prolog Conformance | Dead `!dtd->hasParamEntityRefs` WFC check, self-referential PE `NULL + 0` UB, and uncleared `m_tempPool` on skipped ATTLIST enum | SUSPECTED (argued from code) |
| BUG-33 | Medium | `internal.h` / `expat.h` / `libexpat.def` | Wrong `EXPAT_FMT_*` format specifiers on MinGW-w64 / 32-bit platforms, and `#ifdef XML_DTD` guard hiding `XML_SetBillionLaughsAttackProtection*` declarations | SUSPECTED (argued from code) |
| BUG-34 | Low | `xmlparse.c` / Namespaces | Memory leak of `BINDING` struct on integer-overflow error paths in `addBinding` | SUSPECTED (argued from code) |
| BUG-35 | Low | `xmlparse.c` / Billion Laughs Accounting | Double-counting of direct bytes for non-empty start-tag attributes (`XML_TOK_START_TAG_WITH_ATTS`) weakens amplification limit | SUSPECTED (argued from code) |
| BUG-36 | Low | `xmltok_impl.c` / `xmltok.c` / UTF-16 | `prologTok` shrinks odd UTF-16 `end` locally causing `doProlog` to swallow stray trailing bytes; `DEFINE_UTF16_TO_UTF8` returns `COMPLETED` on odd input | SUSPECTED (argued from code) |
| BUG-37 | Low | `xmltok_impl.c` / Prolog Tokenizer | `prologTok` `BT_COLON` accepts `NameChar` instead of `NameStartChar` after `:`, and `BT_RPAR` rejects `)` followed by `%` | SUSPECTED (argued from code) |
| BUG-38 | Low | `latin1tab.h` / `xmltok.c` / `xmltok_impl.c` | `latin1tab.h` misclassifies `0xAA`/`0xB5`/`0xBA` as `BT_NMSTRT`; `doParseXmlDecl` accepts `version=""`; `isPublicId` checks raw bytes for unknown encodings; `_INTERNAL_trim_to_complete_utf8_characters` off-by-one on malformed bytes | SUSPECTED (argued from code) |
| BUG-39 | Low | `xmlparse.c` / Entropy & Edge Cases | Short-read early exit / stale `errno` loop bug in `writeRandomBytes_*`; `XML_GetBuffer(p, 0)` returns `NULL` with `XML_ERROR_NONE`; `copyString` uses signed `int` | SUSPECTED (argued from code) |
| BUG-40 | Low | `xmlparse.c` / `xmlrole.c` / Large-Scale Overflows | Signed `attIndex` / `nPrefixes << 1` / `int j` overflows in `storeAtts` at `>= 2^29` attributes; unchecked `state->includeLevel += 1` wrap in `condSect1` | SUSPECTED (argued from code) |
| BUG-41 | Low | `expat.h` / `internal.h` / API Hygiene | `XML_XmlDeclHandler` `version == NULL` doc mismatch for TextDecls; `XML_GetUserData(NULL)` dereference; `#define inline` macro issues in `internal.h` | SUSPECTED (argued from code) |

---

## Detailed Findings

### BUG-01: Signed integer overflow in `XML_GetBuffer` (`neededSize += keep`) skips reallocation and causes heap buffer overflow
- **Severity:** Critical
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:2054-2086` (specifically lines 2059–2073)
- **Defect Mechanism:**
  When `XML_CONTEXT_BYTES` is defined (default build, `1024`), `XML_GetBuffer` computes `neededSize` in unsigned arithmetic and checks `if (neededSize < 0)` at line 2062. Immediately afterward, lines 2067–2070 compute `keep = min(m_bufferPtr - m_buffer, XML_CONTEXT_BYTES)` and execute `neededSize += keep;` with **no overflow check**:
  ```c
  int neededSize = (int)((unsigned)len
                         + (unsigned)EXPAT_SAFE_PTR_DIFF(
                             parser->m_bufferEnd, parser->m_bufferPtr));
  if (neededSize < 0) {
    parser->m_errorCode = XML_ERROR_NO_MEMORY;
    return NULL;
  }
  #ifdef XML_CONTEXT_BYTES
  keep = (int)EXPAT_SAFE_PTR_DIFF(parser->m_bufferPtr, parser->m_buffer);
  if (keep > XML_CONTEXT_BYTES)
    keep = XML_CONTEXT_BYTES;
  neededSize += keep;
  #endif
  if (neededSize
      <= EXPAT_SAFE_PTR_DIFF(parser->m_bufferLim, parser->m_buffer)) {
  ```
- **Argument:**
  Once at least 1 byte has been parsed into `m_buffer` (`keep >= 1`, e.g., `m_buffer` allocated at 2048 bytes), a subsequent call to `XML_GetBuffer(parser, len)` (or `XML_Parse(parser, s, len, isFinal)` which delegates to `XML_GetBuffer` + `memcpy` at lines 1961–1965) with `len` satisfying `len + leftover <= INT_MAX` and `len + leftover + keep > INT_MAX` passes line 2062, overflows signed `int` at line 2070 (UB), and wraps `neededSize` to a large negative number. Line 2072 (`neededSize <= m_bufferLim - m_buffer`) evaluates to **true** because a negative integer is less than any positive buffer capacity. Reallocation (`else`, line 2096) is bypassed completely, and `XML_GetBuffer` returns `parser->m_bufferEnd` inside the small existing allocation as if `len` (~2 GiB) bytes were available. Any write of `len` bytes (including `XML_Parse`'s `memcpy` at line 1965) causes a massive heap buffer overflow.
- **Remediation:** Check `if (keep > INT_MAX - neededSize)` (or compute `neededSize` in `size_t` / unsigned and check against `INT_MAX` after adding `keep`) and fail with `XML_ERROR_NO_MEMORY`.

---

### BUG-02: Integer overflow in `storeRawNames` (`bufSize`) skips `REALLOC` and causes heap buffer overflow (plus signed shift overflow in `doContent`)
- **Severity:** Critical
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:2554-2595` (`storeRawNames`: lines 2558–2559, 2571–2573, 2591) and `expat/lib/xmlparse.c:2927-2934` (`doContent`)
- **Defect Mechanism:**
  In `storeRawNames`:
  ```c
  int bufSize;
  int nameLen = sizeof(XML_Char) * (tag->name.strLen + 1);
  char *rawNameBuf = tag->buf + nameLen;
  ...
  bufSize = nameLen + ROUND_UP(tag->rawNameLength, sizeof(XML_Char));
  if (bufSize > tag->bufEnd - tag->buf) {
    char *temp = (char *)REALLOC(parser, tag->buf, bufSize);
    ...
  }
  memcpy(rawNameBuf, tag->rawName, tag->rawNameLength);
  ```
  Neither `nameLen` nor `bufSize` has overflow checking before narrowing to signed `int`.
- **Argument:**
  1. `XML_GetBuffer` allows buffer sizes up to `~INT_MAX` (~2 GiB) because line 2099 seeds `bufferSize` from `m_bufferLim - m_bufferPtr` (not necessarily a power of two).
  2. When an open element spans a chunk boundary, `nameLen + ROUND_UP(tag->rawNameLength, sizeof(XML_Char))` can exceed `INT_MAX` (for example: in UTF-8 Expat reading UTF-16 input with a 750M-character element name, `rawNameLength = 1.5e9`, `nameLen = 7.5e8 + 1`, sum `= 2.25e9 > INT_MAX`; or in pure UTF-8 via `m_freeTagList` reuse where an earlier tag expanded `tag->buf` to 1.5 GB and a subsequent 1.1 GB tag name yields sum `2.2e9 > INT_MAX`).
  3. Truncation into signed `int bufSize` yields a negative value, making `bufSize > tag->bufEnd - tag->buf` evaluate to **false**. `REALLOC` is skipped, and line 2591 executes `memcpy(rawNameBuf, tag->rawName, tag->rawNameLength)` past `tag->bufEnd`, causing a heap buffer overflow write.
  4. Relatedly, in `doContent` line 2927, `bufSize = (int)(tag->bufEnd - tag->buf) << 1;` performs an unchecked signed left shift, overflowing to `INT_MIN` (UB) once `tag->buf` reaches `0x40000000` (1 GiB).
- **Remediation:** Perform all length and rounding calculations in `size_t` with explicit overflow checks against `INT_MAX` / `SIZE_MAX` in both `storeRawNames` and `doContent` line 2927.

---

### BUG-03: Unchecked `unsigned` overflow in `dtd->contentStringLen` causes undersized allocation in `build_model` and heap buffer overflow in `build_node`
- **Severity:** Critical
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:385`, `5383-5386` (`doProlog`), `7351-7375` (`build_model`), `7314-7323` (`build_node`)
- **Defect Mechanism:**
  `DTD::contentStringLen` is a 32-bit `unsigned` (`xmlparse.c:385`). In `doProlog` (`XML_ROLE_CONTENT_ELEMENT*`, line 5386), each element name reference in an `<!ELEMENT>` content model adds `nameLen` to `dtd->contentStringLen` with **no overflow check**:
  ```c
  nameLen = 0;
  for (; name[nameLen++];)
    ;
  dtd->contentStringLen += nameLen;
  ```
  When the element declaration closes, `build_model` allocates `dtd->scaffCount * sizeof(XML_Content) + dtd->contentStringLen * sizeof(XML_Char)` (lines 7364–7367) and calls `build_node`, which copies every scaffold node's `name` string sequentially into `*strpos` starting at `&ret[dtd->scaffCount]`.
- **Argument:**
  Because `getElementType` deduplicates names in `dtd->elementTypes`, repeating a single long element name (e.g., 1 MiB) 4,096 times inside an `<!ELEMENT>` content model stores the string once in `dtd->pool` and creates only 4,097 scaffold nodes, while `dtd->contentStringLen` wraps modulo `2^32` to a tiny number (e.g., 4,096). Because direct input has amplification factor `1.0f`, Billion Laughs protection does not trigger. `build_model`'s overflow guards (lines 7355–7362) inspect the already-wrapped value, allocate a small buffer, and `build_node` writes >4 GiB of name bytes past the end of `ret` (heap buffer overflow).
- **Remediation:** Change `contentStringLen` to `size_t` and guard `dtd->contentStringLen += (size_t)nameLen` against overflow (and check `nameLen` using `size_t` instead of `int`).

---

### BUG-04: Heap buffer overflow on `dtd->scaffIndex` via capacity desynchronization and shrinking between root and external PE parsers
- **Severity:** Critical
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:1048`, `1336-1337`, `5134-5185` (`doProlog`), `6595` (`dtdReset`), `7253-7258` (`nextScaffoldPart`)
- **Defect Mechanism:**
  `dtd->scaffIndex` is stored in the `DTD` struct, which is **shared** between a root parser `P` and any external parameter entity child parser `C` created with `XML_ExternalEntityParserCreate(P, NULL, ...)` (line 1337). However, `dtd->scaffIndex` has no capacity field of its own; its size is tracked solely via each parser's private `parser->m_groupSize` (initialized to `0` in `parserCreate`, line 1048):
  ```c
  if (parser->m_prologState.level >= parser->m_groupSize) {
    if (parser->m_groupSize) {
      ...
      char *const new_connector = (char *)REALLOC(
          parser, parser->m_groupConnector, parser->m_groupSize *= 2);
      ...
      if (dtd->scaffIndex) {
        int *const new_scaff_index = (int *)REALLOC(
            parser, dtd->scaffIndex, parser->m_groupSize * sizeof(int));
        ...
        dtd->scaffIndex = new_scaff_index;
      }
    } ...
  }
  ...
  dtd->scaffIndex[dtd->scaffLevel] = myindex;
  ```
- **Argument:**
  - **Path 1 (Shrinking):** Root parser `P` parses an `<!ELEMENT>` with >=64 nested groups, growing `P->m_groupSize` to `128` and `dtd->scaffIndex` to `128 * sizeof(int)`. `P` then opens an external PE parser `C` (`C->m_dtd == P->m_dtd`, `C->m_groupSize == 0`). `C` parses an `<!ELEMENT>` with 32 nested groups: `C->m_groupSize` grows `0 -> 32 -> 64`, and line 5162 executes `REALLOC(C, dtd->scaffIndex, 64 * sizeof(int))`, **shrinking `dtd->scaffIndex` from 128 to 64 ints**. After `C` is freed, `P->m_groupSize` is still `128`, so when `P` parses an `<!ELEMENT>` with depth 65..127, `level < P->m_groupSize` skips reallocation and line 5183 writes `dtd->scaffIndex[64..126] = myindex` out of bounds on the heap.
  - **Path 2 (Post-`XML_ParserReset`):** `XML_ParserReset(P, ...)` calls `dtdReset` freeing `dtd->scaffIndex` (`NULL`) while preserving `P->m_groupSize` (e.g., `64`). If an external PE `C` then parses even a depth-1 `<!ELEMENT>`, `nextScaffoldPart(C)` allocates `dtd->scaffIndex` with `C->m_groupSize = 32` ints, causing `P` to overflow `dtd->scaffIndex[32..63]` on its next deep element declaration.
- **Remediation:** Track `scaffIndexSize` directly in `DTD` (or ensure `dtd->scaffIndex` only ever grows to `max(dtd->scaffIndexSize, parser->m_groupSize)` and reset/sync capacity cleanly in `dtdReset`).

---

### BUG-05: Use-after-free and double-free of parent parser's shared `m_dtd` on OOM in `parserCreate` via `XML_ExternalEntityParserCreate`
- **Severity:** Critical
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:1029-1030, 1066-1071` (`parserCreate`), `1146, 1149` (`parserInit`), `1336-1354, 1408` (`XML_ExternalEntityParserCreate`), `1474-1479` (`XML_ParserFree`)
- **Defect Mechanism:**
  When `XML_ExternalEntityParserCreate(oldParser, NULL, encodingName)` creates an external PE parser (`context == NULL`), it passes `newDtd = oldParser->m_dtd` into `parserCreate`. Inside `parserCreate`:
  1. Line 1030 sets `parser->m_dtd = dtd` (`oldParser->m_dtd`).
  2. Line 1066 calls `parserInit(parser, encodingName)`, which sets `parser->m_parentParser = NULL` (line 1146), `parser->m_isParamEntity = XML_FALSE` (line 1149), and calls `copyString(encodingName, &parser->m_mem)` (line 1089).
  3. If `copyString` fails (OOM), line 1069 calls `XML_ParserFree(parser)`.
  4. `XML_ParserFree` checks `if (! parser->m_isParamEntity && parser->m_dtd)` (line 1474) — which is **true** because `m_isParamEntity` is not set to `XML_TRUE` until line 1408 in `XML_ExternalEntityParserCreate` — and calls `dtdDestroy(oldParser->m_dtd, XML_TRUE, &parser->m_mem)`.
- **Argument:**
  The parent parser's entire active `DTD` (including all pools, hash tables, `scaffold`, `scaffIndex`, and the `DTD` object itself) is freed while `oldParser->m_dtd` retains a dangling pointer. Immediately upon return from `m_externalEntityRefHandler` (in `doProlog` lines 4691/5294 or `storeEntityValue` line 5988), `oldParser` dereferences freed `DTD` memory (**use-after-free**), and `XML_ParserFree(oldParser)` later calls `dtdDestroy` on the same pointer (**double-free**).
- **Remediation:** On the `parserCreate` error cleanup path (line 1068), clear `parser->m_dtd = NULL` when `dtd != NULL` (caller-owned shared DTD) before calling `XML_ParserFree(parser)` (or initialize `m_isParamEntity` / ownership flag inside `parserCreate`).

---

### BUG-06: UTF-8 validation bypass in XML names accepts overlong sequences, non-continuation bytes, embedded NULs, and delimiter-swallowing bytes
- **Severity:** Critical
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok.c:84-99, 143-167`, `expat/lib/xmltok_impl.c:68-77, 97-106, 1141-1160`, `expat/lib/utf8tab.h:51`
- **Defect Mechanism:**
  In `xmltok_impl.c`, `CHECK_NAME_CASE`, `CHECK_NMSTRT_CASE`, and `prologTok`'s `LEAD_CASE` handle `BT_LEAD2`/`BT_LEAD3` by calling `IS_NAME_CHAR` / `IS_NMSTRT_CHAR` (`utf8_isName2/3`, `utf8_isNmstrt2/3`) **without** calling `IS_INVALID_CHAR` (`UTF8_INVALID2`/`UTF8_INVALID3`). Meanwhile:
  1. `utf8tab.h:51` maps `0xC0` and `0xC1` to `BT_LEAD2` rather than `BT_MALFORM`.
  2. `UTF8_GET_NAMING2` and `UTF8_GET_NAMING3` (`xmltok.c:84-99`) mask out the top two bits of continuation bytes (`byte[1]`, `byte[2]`) and perform no overlong-sequence check.
- **Argument:**
  No secondary UTF-8 validation is applied to XML names in `xmlparse.c` (`utf8_toUtf8` performs `memcpy`; `utf8_toUtf16` masks with `& 0x3f`). Verified directly against `nametab.h` (`nmstrtPages[0] = 0x02`, `namingBitmap[16..23]`):
  - Overlong 2-byte ASCII (`{0xC1, 0x81}` for `'A'`, `{0xC0, 0xBA}` for `':'`) and overlong 3-byte ASCII (`{0xE0, 0x81, 0x81}`) match set bits in `namingBitmap` and are accepted as valid `NMSTRT`/`NAME` characters. `{0xC0, 0xBA}` also bypasses `BT_COLON` checks in `XML_NS` mode and decodes to `':'` in `XML_UNICODE` mode.
  - Non-continuation second bytes such as `{0xC3, 0x00}` (embedded NUL), `{0xC3, 0x3E}` (`>`), `{0xC3, 0x3C}` (`<`), and `{0xC3, 0x0A}` (`\n`) map to valid Latin-1 bits in `namingBitmap[22..23]`. In UTF-8 mode, raw `{0xC3, 0x00}` injects an embedded NUL byte into element/attribute/PI/entity/DOCTYPE names (truncating C strings in callbacks and colliding in `lookup()`/`keyeq()`), while `{0xC3, 0x3E}`/`{0xC3, 0x3C}` swallow XML delimiters and `{0xC3, 0x0A}` desynchronizes `updatePosition` line counting.
- **Remediation:** Reject invalid UTF-8 sequences inside `utf8_isName2/3` and `utf8_isNmstrt2/3` (using `UTF8_INVALID2`/`UTF8_INVALID3`), and classify `0xC0`/`0xC1` as `BT_MALFORM` in `utf8tab.h`.

---

### BUG-07: Heap use-after-free in `internalEntityProcessor` due to missing `storeRawNames(parser)` (plus wrong `m_processor` for external general entities)
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:5674-5680` (`internalEntityProcessor`); compare `2604-2607` (`contentProcessor`) and `2720-2723` (`externalEntityContentProcessor`)
- **Defect Mechanism:**
  When `internalEntityProcessor` finishes a resumed internal general entity, lines 5674–5680 switch `parser->m_processor = contentProcessor` and invoke `doContent(...)` directly, returning its result **without calling `storeRawNames(parser)`**:
  ```c
  parser->m_processor = contentProcessor;
  return doContent(parser, parser->m_parentParser ? 1 : 0, parser->m_encoding,
                   s, end, nextPtr,
                   (XML_Bool)! parser->m_parsingStatus.finalBuffer,
                   XML_ACCOUNT_DIRECT);
  ```
- **Argument:**
  1. **Use-after-free:** If parsing suspends (`XML_StopParser(p, XML_TRUE)`) inside an internal entity during a non-final chunk that also contains an unclosed start tag after the entity reference, `XML_ResumeParser` finishes the entity and executes `doContent` on the start tag, pushing a `TAG` whose `tag->rawName` points directly into `parser->m_buffer` (line 2908). Because `storeRawNames` is not called before returning, a subsequent `XML_GetBuffer` reallocation (lines 2121/2137) frees `m_buffer` (or `memmove`s over it at line 2081), leaving `tag->rawName` dangling. On the matching end tag (`doContent` line 3009 `memcmp`) or next `storeRawNames` (`memcpy` at line 2591), Expat performs a heap use-after-free read.
  2. **Wrong processor for external general entities:** Line 5674 unconditionally sets `parser->m_processor = contentProcessor` even when `parser->m_parentParser != NULL` (should be `externalEntityContentProcessor`), causing subsequent chunks to run with `startTagLevel = 0` and `XML_ACCOUNT_DIRECT` instead of `1` and `XML_ACCOUNT_ENTITY_EXPANSION`, breaking EOF/async-entity checks and accounting.
- **Remediation:** Route post-entity resumption through `contentProcessor` / `externalEntityContentProcessor` (based on `parser->m_parentParser`) so `storeRawNames(parser)`, `startTagLevel`, and accounting are always handled consistently.

---

### BUG-08: `allowClosingDoctype` guard bypassed in `internalEntityProcessor`, allowing DOCTYPE closure and encoding/processor confusion from resumed internal PE
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:5634-5640` (`internalEntityProcessor`); compare `5586-5592` (`processInternalEntity`) and `4651-4655, 4745-4746` (`doProlog`)
- **Defect Mechanism:**
  `processInternalEntity` calls `doProlog` with `allowClosingDoctype = XML_FALSE` (line 5590) to prevent an internal parameter entity from closing the `<!DOCTYPE>` declaration (enforced at line 4652). However, `internalEntityProcessor` (line 5638) resumes an internal parameter entity with `allowClosingDoctype = XML_TRUE`.
- **Argument:**
  `XML_StopParser(parser, XML_TRUE)` only blocks suspension when `parser->m_isParamEntity` is true (external PE parsers), so suspending inside an internal PE in the root parser succeeds and installs `internalEntityProcessor`. Upon `XML_ResumeParser`, `allowClosingDoctype = XML_TRUE` permits the internal PE to emit `XML_ROLE_DOCTYPE_CLOSE` (`]>`) and even `XML_ROLE_INSTANCE_START` (`<root>`). At `XML_ROLE_INSTANCE_START` (line 4745–4746), `doProlog` invokes `contentProcessor(parser, s, end, nextPtr)` where `s..end` lies in `entity->textPtr` (`m_internalEncoding`) while `contentProcessor` tokenizes it with `parser->m_encoding` (encoding confusion and out-of-buffer `m_eventPtr`), and if `contentProcessor` returns `XML_ERROR_NONE`, `internalEntityProcessor` line 5666 overwrites `parser->m_processor` back to `prologProcessor`!
- **Remediation:** Pass `XML_FALSE` for `allowClosingDoctype` in `internalEntityProcessor` at line 5638 (or disallow resuming/suspending inside internal parameter entities as well).

---

### BUG-09: Unbounded C-stack recursion (stack overflow crash) in `build_node` and non-cyclic entity expansion chains
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:7309-7338` (`build_node`), `5995` (`storeEntityValue`), `5873` (`appendAttributeValue`), `2864 -> 5594` (`doContent` <-> `processInternalEntity`), `5274 -> 5589` (`doProlog` <-> `processInternalEntity`)
- **Defect Mechanism:**
  1. `doProlog` parses arbitrarily deep nested content model groups `(` in `<!ELEMENT>` iteratively on the heap (`m_groupConnector`, `dtd->scaffIndex`), but `build_model` converts the scaffold into an `XML_Content` tree via recursive `build_node` (line 7334) with no depth bound.
  2. Internal entity expansion (`storeEntityValue`, `appendAttributeValue`, `doContent`/`doProlog` -> `processInternalEntity`) recurses on the C call stack once per nesting level; `entityTrackingOnOpen` (lines 7593–7605) records `currentDepth` solely for debug output and enforces no depth limit.
- **Argument:**
  1. When `XML_SetElementDeclHandler` is registered, deeply nested parentheses in an `<!ELEMENT>` declaration (a few hundred KB of input, amplification factor `1.0f`) exhausts the C call stack in `build_node` and crashes with stack overflow (SIGSEGV).
  2. A non-cyclic linear chain of entities `e_N -> e_{N-1} -> ... -> e_1` (each referencing the next once) triggers neither `XML_ERROR_RECURSIVE_ENTITY_REF` nor Billion Laughs amplification protection (amplification ~1–2x), yet exhausts the C call stack via `N` nested calls.
- **Remediation:** Convert `build_node` to an explicit heap-allocated iterative stack (or enforce a configurable maximum nesting depth), and enforce a configurable maximum entity expansion nesting depth in `entityTrackingOnOpen` / entity expansion paths.

---

### BUG-10: Namespace separator injection in `addBinding` and expanded attribute name collisions / incomplete duplicate check in `storeAtts`
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:3746-3765, 3820-3822` (`addBinding`) and `3546-3587` (`storeAtts`)
- **Defect Mechanism:**
  1. `addBinding` copies the namespace URI `uri` and appends `parser->m_namespaceSeparator` without validating that `uri` does not contain `parser->m_namespaceSeparator` (or RFC 3986 invalid characters).
  2. `storeAtts` builds expanded attribute names by concatenating `b->uri` (which ends with `m_namespaceSeparator` only if non-NUL) directly with `localPart`, hashing the concatenation without length delimiting, and comparing on hash match using:
     ```c
     /* s1 is null terminated, but not s2 */
     for (; *s1 == *s2 && *s1 != 0; s1++, s2++)
       ;
     if (*s1 == 0)
       return XML_ERROR_DUPLICATE_ATTRIBUTE;
     ```
- **Argument:**
  1. **Namespace separator injection:** When an application uses a separator character that can appear in a namespace URI (e.g., `':'`, `'!'`, `'|'`, `' '`), a namespace declaration whose URI contains that separator injects extra delimiters into the expanded names delivered to `startElementHandler`/`endElementHandler`, allowing namespace/local-name/prefix spoofing in downstream consumers that split on the separator.
  2. **False duplicate-attribute errors:** When `m_namespaceSeparator == '\0'` (documented as supported in `expat.h:236`) or when the separator is a valid XML `NameChar` (e.g., `'-'`, `'.'`, `'_'`), distinct attributes with different `(URI, localPart)` pairs can concatenate to the identical string (e.g., `("http://u", "xy")` vs `("http://ux", "y")`) and be falsely rejected with `XML_ERROR_DUPLICATE_ATTRIBUTE`.
  3. **Prefix collision bug (lines 3578–3581):** The duplicate check stops as soon as `*s1 == 0` without checking `*s2 == 0` (or `*s2 == m_namespaceSeparator` in triplet mode). On a `uriHash` collision (32-bit `unsigned long` on 32-bit/LLP64 platforms), any attribute whose expanded name is a proper prefix of a previously stored attribute's expanded name is falsely rejected as a duplicate.
- **Remediation:** Reject namespace URIs containing `parser->m_namespaceSeparator` (or validate URI syntax per RFC 3986); delimit URI and localPart in SipHash and verify `*s2 == '\0' || (parser->m_ns_triplets && *s2 == parser->m_namespaceSeparator)` in `storeAtts`.

---

### BUG-11: Missing `len` bounds validation (`len < 0` / OOB) and unchecked signed `m_parseEndByteIndex` overflow in `XML_ParseBuffer`
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:1971-2034` (lines 1976, 2003–2005)
- **Defect Mechanism:**
  Unlike `XML_Parse` (line 1819) and `XML_GetBuffer` (line 2040), `XML_ParseBuffer` performs **no** check on `len`:
  ```c
  start = parser->m_bufferPtr;
  parser->m_positionPtr = start;
  parser->m_bufferEnd += len;
  parser->m_parseEndPtr = parser->m_bufferEnd;
  parser->m_parseEndByteIndex += len;
  ```
- **Argument:**
  1. **Negative `len` -> heap buffer underflow:** Passing `len < 0` moves `m_bufferEnd` backward before `m_bufferPtr` (and potentially before `m_buffer`, UB). Because tokenizers return `XML_TOK_NONE` when `ptr >= end`, `XML_ParseBuffer` returns `XML_STATUS_OK` with `m_bufferEnd < m_buffer`. A subsequent `XML_GetBuffer` call either returns `m_bufferEnd` pointing **before** the heap allocation (heap buffer underflow write) or computes a negative `m_bufferEnd - m_bufferPtr` passed as a massive `size_t` to `memcpy`/`memmove`.
  2. **Oversized `len` -> heap OOB read:** Passing `len > parser->m_bufferLim - parser->m_bufferEnd` sets `m_parseEndPtr` past the end of `m_buffer`, causing an out-of-bounds heap read during tokenization.
  3. **Unchecked `m_parseEndByteIndex` overflow:** The overflow guard at line 1894 exists only under `#ifndef XML_CONTEXT_BYTES`. In default builds (`XML_CONTEXT_BYTES` defined), `XML_Parse` delegates to `XML_ParseBuffer` (line 1966), where `m_parseEndByteIndex += len` overflows signed `XML_Index` (`long` on 32-bit and Win64 LLP64) after 2 GiB of streamed input (signed overflow UB, corrupting `XML_GetCurrentByteIndex` and `XML_AttrInfo`).
- **Remediation:** Validate `len >= 0` and `len <= parser->m_bufferLim - parser->m_bufferEnd` in `XML_ParseBuffer` (returning `XML_ERROR_INVALID_ARGUMENT`), and apply the `m_parseEndByteIndex` overflow check unconditionally in `XML_ParseBuffer`.

---

### BUG-12: Unsynchronized shared parent-parser access in `XML_ExternalEntityParserCreate` child parsers causes data races and UAF, violating documented thread-safety contract
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/expat.h:850-854`, `expat/lib/xmlparse.c:941-946`, `1387`, `7424-7552` (`accounting*`), `7569-7629` (`entityTracking*`)
- **Defect Mechanism:**
  `expat.h:852-853` explicitly promises for external general entity parsers (`context != NULL`): *"The new parser is completely independent and may safely be used in a separate thread."*
  However, `XML_ExternalEntityParserCreate` sets `parser->m_parentParser = oldParser` (line 1387), and during parsing the child parser accesses `oldParser` unsynchronized:
  - Every token calls `accountingDiffTolerated` -> `getRootParserOf` -> non-atomic read-modify-write of `rootParser->m_accounting.countBytesIndirect` (line 7533) and reads `countBytesDirect` (line 7427/7536).
  - Every internal entity open/close mutates `rootParser->m_entity_stats` non-atomically (lines 7597–7601, 7613).
  - Every hash lookup calls `get_hash_secret_salt(parser)` walking `m_parentParser` up to `rootParser->m_hash_secret_salt` (lines 943–945).
- **Argument:**
  1. Running the child parser on a separate thread concurrently with the parent (or with a sibling external entity parser) produces **C data races** (UB) on `m_accounting` and `m_entity_stats`.
  2. Freeing `oldParser` before the "completely independent" child parser finishes causes **heap use-after-free** on every token and hash lookup in the child parser.
- **Remediation:** Either make external general entity parsers genuinely independent (copying accounting/salt configuration or using atomic refcounted shared state with atomic counters) or explicitly synchronize/revise the API contract.

---

### BUG-13: Complete bypass of amplification protection under `XML_UseForeignDTD` when document begins directly with root element
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:4555-4565`, `4711-4744` (`doProlog`), `7424-7436` (`accountingGetCurrentAmplification`), `7522-7543` (`accountingDiffTolerated`)
- **Defect Mechanism:**
  ```c
  // accountingGetCurrentAmplification (lines 7429-7433):
  const float amplificationFactor
      = rootParser->m_accounting.countBytesDirect
            ? (countBytesOutput
               / (float)(rootParser->m_accounting.countBytesDirect))
            : 1.0f;
  ```
- **Argument:**
  When `XML_UseForeignDTD(parser, XML_TRUE)` and parameter entity parsing are enabled and the document starts immediately with the root element (no XML declaration, DOCTYPE, or leading whitespace):
  1. `doProlog` receives `XML_ROLE_INSTANCE_START` and intentionally skips accounting it (lines 4555–4559), leaving `rootParser->m_accounting.countBytesDirect == 0`.
  2. Line 4727 calls `m_externalEntityRefHandler` to parse the foreign DTD in a child parser (`originParser != rootParser`).
  3. Because `originParser != rootParser`, `isDirect` (line 7523) is `0`, so all foreign DTD bytes and entity expansions accumulate in `countBytesIndirect` while `countBytesDirect` remains `0`.
  4. `accountingGetCurrentAmplification` returns `1.0f` whenever `countBytesDirect == 0`. Since `maximumAmplificationFactor >= 1.0f` (enforced at line 2531), `amplificationFactor <= maximumAmplificationFactor` is **always true**, completely bypassing Billion Laughs attack protection for the entire foreign DTD.
- **Remediation:** Treat `countBytesDirect == 0 && countBytesIndirect > 0` as exceeding any finite amplification limit (e.g., return `INFINITY` or `(float)countBytesOutput`), or account foreign DTD direct bytes properly.

---

### BUG-14: Undefined behavior (`NULL - s`) and accounting counter corruption in `epilogProcessor` on negative prolog tokens
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:5487-5495` (`epilogProcessor`), `7500-7534` (`accountingDiffTolerated`), `expat/lib/xmltok_impl.c:977, 993, 1094, 1110, 1251`
- **Defect Mechanism:**
  `epilogProcessor` initializes `const char *next = NULL;`, calls `XmlPrologTok(parser->m_encoding, s, end, &next)`, and immediately invokes `accountingDiffTolerated(parser, tok, s, next, __LINE__, XML_ACCOUNT_DIRECT)` before checking `tok`.
- **Argument:**
  When trailing junk at the end of a document causes `XmlPrologTok` to return a negative token (`-XML_TOK_CLOSE_BRACKET`, `-XML_TOK_CLOSE_PAREN`, `-XML_TOK_NAME`, `-XML_TOK_LITERAL`, `-XML_TOK_POUND_NAME`), `XmlPrologTok` does **not** set `*nextTokPtr`, leaving `next == NULL`. `accountingDiffTolerated` only filters `XML_TOK_INVALID` (`0`), `XML_TOK_PARTIAL` (`-1`), `XML_TOK_PARTIAL_CHAR` (`-2`), and `XML_TOK_NONE` (`-4`), not `tok < -4`. Line 7524 then evaluates `after - before = NULL - s` (**undefined behavior in C**), yielding a huge negative `ptrdiff_t` that corrupts `countBytesDirect` via unsigned wraparound (leaking address bits of `s` into accounting stats/logs and potentially triggering a spurious `XML_ERROR_AMPLIFICATION_LIMIT_BREACH` on 32-bit platforms instead of `XML_ERROR_JUNK_AFTER_DOC_ELEMENT`).
- **Remediation:** Initialize `next = s` (or pass `tok < 0 ? end : next` / filter all `tok <= 0` except `-XML_TOK_PROLOG_S` in `accountingDiffTolerated` / `epilogProcessor`).

---

### BUG-15: Unchecked `parser->m_groupSize * sizeof(int)` overflow on 32-bit platforms in `nextScaffoldPart` initial `dtd->scaffIndex` allocation
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:7253-7258` (`nextScaffoldPart`)
- **Defect Mechanism:**
  ```c
  if (! dtd->scaffIndex) {
    dtd->scaffIndex = (int *)MALLOC(parser, parser->m_groupSize * sizeof(int));
    if (! dtd->scaffIndex)
      return -1;
    dtd->scaffIndex[0] = 0;
  }
  ```
- **Argument:**
  While `doProlog` (lines 5156–5160) guards `parser->m_groupSize > (size_t)(-1) / sizeof(int)` when growing an existing `dtd->scaffIndex`, `nextScaffoldPart` lacks this check when allocating `dtd->scaffIndex` for the first time. On 32-bit platforms (`UINT_MAX == SIZE_MAX`), if `m_groupSize` reached `0x40000000` (1 GiB `m_groupConnector`) while `m_elementDeclHandler == NULL` (leaving `dtd->scaffIndex == NULL`), and `m_elementDeclHandler` is later installed, `0x40000000u * 4u` wraps to `0`. `MALLOC(parser, 0)` may return a non-NULL zero-byte block, causing `dtd->scaffIndex[0] = 0` to write out of bounds on the heap.
- **Remediation:** Add the same `#if UINT_MAX >= SIZE_MAX` overflow check (`parser->m_groupSize > (size_t)(-1) / sizeof(int)`) before `MALLOC` in `nextScaffoldPart`.

---

### BUG-16: NULL function pointer dereference in `XML_MIN_SIZE` builds when a UTF-16 high surrogate appears in any XML name
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok.c:227-230, 273-282, 601-606, 820-874, 955-1009`, `expat/lib/xmltok_impl.c:68-77, 97-106, 1141-1160`
- **Defect Mechanism:**
  Under `XML_MIN_SIZE`, all UTF-16 encodings (`little2_*`, `big2_*`, `internal_little2_*`, `internal_big2_*`) reuse `normal_*` tokenizers and initialize `isName2..4`, `isNmstrt2..4`, `isInvalid2..4` to `NULL` via `NULL_VTABLE`. While `IS_INVALID_CHAR` (lines 276–278) guards against a `NULL` function pointer, `IS_NAME_CHAR` and `IS_NMSTRT_CHAR` (lines 273–274) do **not**:
  ```c
  #define IS_NAME_CHAR(enc, p, n) (AS_NORMAL_ENCODING(enc)->isName##n(enc, p))
  #define IS_NMSTRT_CHAR(enc, p, n) (AS_NORMAL_ENCODING(enc)->isNmstrt##n(enc, p))
  ```
- **Argument:**
  `little2_byteType`/`big2_byteType` call `unicode_byte_type`, which returns `BT_LEAD4` for high surrogates `0xD800..0xDBFF`. Whenever a UTF-16 document contains a high surrogate (with `end - ptr >= 4`) in any name position (`scanLt`, `scanEndTag`, `scanAtts`, `scanPi`, `scanRef`, `scanPercent`, `scanPoundName`, `prologTok`), `CHECK_NMSTRT_CASE(4)` / `CHECK_NAME_CASE(4)` / `prologTok` `LEAD_CASE(4)` calls `NULL(enc, ptr)` -> immediate NULL function pointer dereference crash.
- **Remediation:** Guard `IS_NAME_CHAR` and `IS_NMSTRT_CHAR` with non-NULL checks under `XML_MIN_SIZE` (or populate `isName4`/`isNmstrt4` with `isNever`).

---

### BUG-17: `DEFINE_UTF16_TO_UTF16` (`little2_toUtf16`/`big2_toUtf16`) wrong bitmask and boundary check drops low surrogates and splits surrogate pairs
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok.c:701-720`
- **Defect Mechanism:**
  ```c
  fromLim = *fromP + (((fromLim - *fromP) >> 1) << 1); /* shrink to even */
  /* Avoid copying first half only of surrogate */
  if (fromLim - *fromP > ((toLim - *toP) << 1)
      && (GET_HI(fromLim - 2) & 0xF8) == 0xD8) {
    fromLim -= 2;
    res = XML_CONVERT_INPUT_INCOMPLETE;
  }
  for (; *fromP < fromLim && *toP < toLim; *fromP += 2)
    *(*toP)++ = (GET_HI(*fromP) << 8) | GET_LO(*fromP);
  if ((*toP == toLim) && (*fromP < fromLim))
    return XML_CONVERT_OUTPUT_EXHAUSTED;
  else
    return res;
  ```
- **Argument:**
  1. **Wrong bitmask `& 0xF8` + silent loss of trailing low surrogate:** `& 0xF8 == 0xD8` matches `0xD8..0xDF` (both high **and** low surrogates; high surrogates alone require `& 0xFC == 0xD8`). In `XML_UNICODE` mode converting opposite-endian UTF-16 where input has `N + 1` code units (`N = toLim - *toP`) ending in a valid surrogate pair `[0xD8xx, 0xDCxx]`, `GET_HI(fromLim - 2)` is `0xDC..0xDF` which matches `& 0xF8 == 0xD8`. `fromLim -= 2` shrinks `fromLim` to `*fromP + 2N` and sets `res = XML_CONVERT_INPUT_INCOMPLETE`. The loop copies `N` units ending with the unpaired high surrogate `0xD8xx`, exits with `*fromP == fromLim`, and returns `XML_CONVERT_INPUT_INCOMPLETE`. All `xmlparse.c` callers (`doContent:3152`, `doCdataSection:3932`, `reportDefault:6200`, `poolAppend:7049`, tag-name loop `2922`) stop on `XML_CONVERT_INPUT_INCOMPLETE`, **silently dropping the low surrogate** and leaving an unpaired high surrogate (which in `storeEntityValue` later triggers an OOB read in BUG-20).
  2. **Wrong pointer checked:** Checking `fromLim - 2` instead of the output boundary `*fromP + ((toLim - *toP) << 1) - 2` fails to prevent splitting a surrogate pair that straddles the output buffer boundary when followed by non-surrogate data, and fails to catch a trailing lone high surrogate when `fromLim - *fromP <= ((toLim - *toP) << 1)`.
  3. **Odd input length:** Line 707 shrinks `fromLim` without marking `res = XML_CONVERT_INPUT_INCOMPLETE`, falsely returning `XML_CONVERT_COMPLETED`.
- **Remediation:** Clamp the effective copy limit to `min(even_fromLim, *fromP + 2*(toLim - *toP))`, check `(GET_HI(copyLim - 2) & 0xFC) == 0xD8` at `copyLim`, distinguish output exhaustion (`XML_CONVERT_OUTPUT_EXHAUSTED`) from trailing incomplete input (`XML_CONVERT_INPUT_INCOMPLETE`), and preserve odd-byte detection.

---

### BUG-18: Missing UTF-16 surrogate pair validation (`IS_INVALID_CHAR` always `0`) accepts unpaired high surrogates paired with arbitrary code units
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok.c:598-622, 671-691, 790-815, 925-950`, `expat/lib/xmltok_impl.c:43-56, 397-408, 872-883`
- **Defect Mechanism:**
  `unicode_byte_type` returns `BT_LEAD4` for high surrogates `0xD800..0xDBFF`, but `IS_INVALID_CHAR(enc, ptr, 4)` evaluates to `0` for `little2_*` and `big2_*` in all builds (`xmltok_impl.c:43-45` defaults it to `(0)`, and under `XML_MIN_SIZE` `isInvalid4` is `NULL`).
- **Argument:**
  In UTF-16 content, CDATA, comments, PIs, attribute values, DTD literals, and ignore sections, `INVALID_LEAD_CASE(4)` and `LEAD_CASE(4)` advance `ptr += 4` without verifying that the second 16-bit code unit is a low surrogate (`0xDC00..0xDFFF`). An unpaired high surrogate followed by **any** 16-bit unit (including `0x0000` NUL, `0xFFFF`, `'<'`, `'"'`, `'\n'`, or another high surrogate) is accepted as valid:
  - Following markup delimiters are swallowed and `\n` is skipped by `updatePosition` without incrementing `lineNumber`.
  - `DEFINE_UTF16_TO_UTF8` (`xmltok.c:671-691`) masks the non-surrogate second unit with `GET_HI(from) & 0x3` and encodes a bogus supplementary-plane UTF-8 character.
  - In `XML_UNICODE` mode, the unpaired surrogate and illegal XML character (e.g., NUL/`0xFFFF`) are emitted directly to callbacks.
- **Remediation:** Define `IS_INVALID_CHAR` / `isInvalid4` for `little2_*` and `big2_*` to verify that the second 16-bit unit lies in `0xDC00..0xDFFF` (high byte `0xDC..0xDF`).

---

### BUG-19: Out-of-bounds read and unbounded loop past `fromLim` in `unknown_toUtf8` / `unknown_toUtf16`, reachable via `parsePseudoAttribute` step desync
- **Severity:** High
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok.c:1358-1407` (`unknown_toUtf8`, `unknown_toUtf16`), `1043-1144` (`toAscii`, `parsePseudoAttribute`)
- **Defect Mechanism:**
  Neither `unknown_toUtf8` nor `unknown_toUtf16` checks whether `fromLim - *fromP >= seqLen` before invoking `uenc->convert(uenc->userData, *fromP)` and advancing `*fromP += seqLen` (2, 3, or 4).
- **Argument:**
  1. When `fromLim - *fromP < seqLen`, `uenc->convert` reads past `fromLim` (OOB read), and `*fromP` becomes strictly greater than `fromLim`.
  2. In `unknown_toUtf8`, line 1366 terminates only on exact equality `if (*fromP == fromLim)`, which is now skipped — causing an **unbounded OOB read loop** past `fromLim`. Worse, if `uenc->convert` returns `< 0` on OOB bytes, `XmlUtf8Encode` returns `n = 0`, so `if (n > toLim - *toP)` (line 1373) fails to stop the loop even when the output buffer is full.
  3. **In-library reachability:** In `doParseXmlDecl` -> `parsePseudoAttribute` -> `toAscii`, if a multi-byte unknown encoding's `convert` maps a 2-byte sequence to an ASCII whitespace/syntax character, `scanPi` accepts it as valid, `toAscii` returns the ASCII byte, and `parsePseudoAttribute` advances `ptr += enc->minBytesPerChar` (`+1` instead of `+2`), landing `ptr` on the trailing byte at `end - 1`. If that byte is itself a lead byte, the next `toAscii` invokes `unknown_toUtf8` with `fromLim - *fromP == 1 < seqLen`, triggering the OOB read and loop.
- **Remediation:** Check `seqLen > fromLim - *fromP` (returning `XML_CONVERT_INPUT_INCOMPLETE`) in both `unknown_toUtf8` and `unknown_toUtf16`, use `if (*fromP >= fromLim)` in `unknown_toUtf8`, and reject `n == 0` from `XmlUtf8Encode`.

---

### BUG-20: Out-of-bounds pointer advance (`ptr += n` past `end`) in `attributeValueTok`, `entityValueTok`, and `updatePosition`
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok_impl.c:1271-1278, 1319` (`attributeValueTok`), `1340-1347, 1384` (`entityValueTok`), `1776-1784` (`updatePosition`)
- **Defect Mechanism:**
  All three functions check only `HAS_CHAR(enc, ptr, end)` (`>= MINBPC(enc)`) and execute `ptr += n` for `BT_LEAD2`/`BT_LEAD3`/`BT_LEAD4` without verifying `end - ptr >= n`.
- **Argument:**
  In `attributeValueTok` and `entityValueTok`, if input ends with a truncated multi-byte sequence (`end - ptr < n`), `*nextTokPtr` is returned pointing past `end` with `XML_TOK_DATA_CHARS`; callers (`appendAttributeValue:5765`, `storeEntityValue:6017`) pass `(ptr, next)` to `poolAppend`, causing a heap out-of-bounds read. This is concretely reachable in `XML_UNICODE` mode when BUG-17 leaves an unpaired high surrogate (`BT_LEAD4`) at `end - 2` of a stored entity value and that entity is later expanded in an attribute or entity value. In `updatePosition`, `ptr += n` past `end` triggers pointer-arithmetic UB and corrupts `columnNumber` (reachable via `parsePseudoAttribute` desync or `initUpdatePosition` on a truncated UTF-8 lead byte).
- **Remediation:** Check `if (end - ptr < n)` in `LEAD_CASE(n)` in `attributeValueTok`, `entityValueTok` (returning `XML_TOK_PARTIAL_CHAR` or stopping before `ptr`), and `updatePosition` (breaking out of the loop).

---

### BUG-21: `externalSubset1` rejects all valid internal PE references inside `<![INCLUDE[ ... ]]>` and allows a PE to close an outer `INCLUDE` section
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlrole.c:388-411` (`externalSubset1`), `1150-1153` (`condSect1`), `expat/lib/xmlrole.h:124`, `expat/lib/xmlparse.c:4526-4545`
- **Defect Mechanism:**
  `PROLOG_STATE` keeps a single flat `includeLevel` counter shared between the external subset/PE parser and internal parameter entities expanded via `processInternalEntity`. Inside `<![INCLUDE[ ... ]]>`, `state->includeLevel` is `>= 1`.
- **Argument:**
  1. When a valid internal PE `%pe;` is referenced between declarations inside an `INCLUDE` section, `doProlog` calls `processInternalEntity` with `betweenDecl = XML_TRUE`. At the end of `%pe;`, `doProlog` (line 4539) calls `XmlTokenRole(&parser->m_prologState, XML_TOK_NONE, ...)`. `externalSubset1` (line 404) sees `state->includeLevel != 0` and returns `XML_ROLE_ERROR`, causing `doProlog` to fail with `XML_ERROR_INCOMPLETE_PE` on every valid internal PE reference inside `INCLUDE`.
  2. Symmetrically, an internal PE containing an unmatched `]]>` inside an outer `INCLUDE` section decrements the outer section's `includeLevel` to `0`, allowing it to close the outer conditional section without error.
- **Remediation:** Save/track per-entity `includeLevel` baseline in `OPEN_INTERNAL_ENTITY` (checking `state->includeLevel != openEntity->includeLevel` on `XML_TOK_NONE` and preventing `XML_TOK_COND_SECT_CLOSE` from decrementing below the current entity's baseline).

---

### BUG-22: `ignoreSectionTok` fails to recognize `]]>` after odd runs of `]` (e.g., `]]]>`) and omits `ptr >= end` guard
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok_impl.c:1390-1438` (specifically lines 1394–1400, 1416–1431)
- **Defect Mechanism:**
  In `case BT_RSQB:`, after matching two `]` characters, if the third character is not `>` (e.g., a third `]` in `]]]>`), `ignoreSectionTok` breaks **without** decrementing `ptr -= MINBPC(enc)` (contrast `cdataSectionTok:375` and `contentTok:860`, which both step back).
- **Argument:**
  1. On `"]]]>"`, iteration 1 consumes the 1st and 2nd `]`, inspects the 3rd `]` (not `>`), and leaves `ptr` at the 3rd `]`. Iteration 2 sees the 3rd `]` followed by `>` (not `]`), completely missing the `]]>` closing delimiter. Every odd run of `]` before `>` (`3, 5, 7, ...`) fails to close the IGNORE section, causing valid DTDs to error with `XML_ERROR_SYNTAX` or silently swallow subsequent DTD declarations until a later `]]>`.
  2. Unlike `prologTok`, `contentTok`, and `cdataSectionTok`, `ignoreSectionTok` omits `if (ptr >= end) return XML_TOK_NONE;` before `size_t n = end - ptr;`.
- **Remediation:** Add `ptr -= MINBPC(enc);` in the non-`>` branch of `case BT_RSQB:` and add `if (ptr >= end) return XML_TOK_NONE;` at the top of `ignoreSectionTok`.

---

### BUG-23: `internalEntityProcessor` abandons outer nested internal entities on resume and continues parsing after suspend on final entity token
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:5646-5681` (`internalEntityProcessor`)
- **Defect Mechanism:**
  After finishing and popping `openEntity` from `parser->m_openInternalEntities` (line 5657), `internalEntityProcessor` never checks whether `parser->m_openInternalEntities` still has an enclosing open entity, and immediately switches `m_processor` back to `contentProcessor`/`prologProcessor` on the outer document buffer `s..end`. Furthermore, line 5648 checks `textEnd != next && parsing == XML_SUSPENDED`, skipping suspension if the handler suspended on the last token of the entity (`textEnd == next`).
- **Argument:**
  1. When `&e1;` expands `&e2;` and parsing suspends inside `&e2;`, resuming finishes `&e2;` and silently **discards the remainder of `&e1;`**, leaves `e1->open == XML_TRUE` permanently (triggering false `XML_ERROR_RECURSIVE_ENTITY_REF` on subsequent references to `&e1;`), and leaves `m_openInternalEntities` non-NULL (corrupting `XML_DefaultCurrent` and entity depth tracking).
  2. If a callback calls `XML_StopParser(parser, XML_TRUE)` on the final token of a resumed internal entity (`textEnd == next`), `internalEntityProcessor` falls through into `doProlog`/`doContent` and continues firing callbacks while suspended.
- **Remediation:** Loop over `parser->m_openInternalEntities` until empty (returning immediately if `parser->m_parsingStatus.parsing == XML_SUSPENDED`, even when `textEnd == next`).

---

### BUG-24: `XML_ROLE_ENTITY_VALUE` commits entity value and invokes `m_entityDeclHandler` (potentially with `value == NULL`) before checking `storeEntityValue` error
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:4874-4897` (`doProlog`), `5920-5926` (`storeEntityValue`)
- **Defect Mechanism:**
  In `doProlog` (`XML_ROLE_ENTITY_VALUE`), `if (result != XML_ERROR_NONE) return result;` is at line 4894 — **after** committing `textPtr`/`textLen` to `m_declEntity` and calling `parser->m_entityDeclHandler` (lines 4879–4891).
- **Argument:**
  1. If `storeEntityValue` fails on any error (`XML_ERROR_NO_MEMORY`, `XML_ERROR_BAD_CHAR_REF`, `XML_ERROR_PARAM_ENTITY_REF`, `XML_ERROR_AMPLIFICATION_LIMIT_BREACH`, etc.), `m_entityDeclHandler` is erroneously invoked with truncated/corrupted data before the error is returned.
  2. If OOM occurs at `storeEntityValue` line 5924 (`!pool->blocks && !poolGrow(pool)`), `poolStart(&dtd->entityValuePool)` is `NULL` (and `inEntityValue` is left stuck at `1`). `m_entityDeclHandler` is then called with `value == NULL, systemId == NULL, publicId == NULL`, violating the `expat.h:330-337` API contract (which distinguishes internal vs external entities via `value != NULL`).
- **Remediation:** Check `if (result != XML_ERROR_NONE)` immediately after `storeEntityValue`, discarding `dtd->entityValuePool` and returning `result` before committing or invoking `m_entityDeclHandler`; restore `inEntityValue` on the line 5925 OOM return (`goto endEntityValue`).

---

### BUG-25: `setContext` leaves `prefix->name == NULL` in `dtd->prefixes` on OOM; retrying `XML_Parse` causes NULL dereference in `keyeq`
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:1831-1835` (`XML_Parse`), `1992-1995` (`XML_ParseBuffer`), `6481-6503` (`setContext`), `6888, 6833` (`lookup` -> `keyeq`)
- **Defect Mechanism:**
  In `setContext` (lines 6481–6490), `lookup` inserts a `PREFIX` into `dtd->prefixes` pointing into `m_tempPool`, and line 6487 overwrites `prefix->name = poolCopyString(&dtd->pool, prefix->name)`. On OOM, `prefix->name` becomes `NULL` while remaining in `dtd->prefixes`. Meanwhile, when `startParsing(parser)` fails in `XML_Parse` (line 1832) or `XML_ParseBuffer` (line 1992), `m_parsingStatus.parsing` stays `XML_INITIALIZED` and `m_processor` is not set to `errorProcessor`.
- **Argument:**
  A subsequent call to `XML_Parse`/`XML_ParseBuffer` re-enters `startParsing` -> `setContext` -> `lookup(parser, &dtd->prefixes, "xml", ...)`, which hits the slot containing `prefix->name == NULL` and calls `keyeq(name, NULL)` -> immediate NULL pointer dereference. (Also, OOM at lines 6496/6498/6502 leaves un-discarded bytes in `m_tempPool`.)
- **Remediation:** Copy the prefix string into `dtd->pool` *before* calling `lookup` (or preserve the old pointer until `poolCopyString` succeeds), discard `m_tempPool` on all error exits in `setContext`, and set `m_processor = errorProcessor` on `startParsing` failure.

---

### BUG-26: Unchecked `lookup()` failure in `getAttributeId` for `xmlns:*` silently drops namespace binding and leaks raw attribute
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:6326-6329` (`getAttributeId`)
- **Defect Mechanism:**
  ```c
  if (name[5] == XML_T('\0'))
    id->prefix = &dtd->defaultPrefix;
  else
    id->prefix = (PREFIX *)lookup(parser, &dtd->prefixes, name + 6,
                                  sizeof(PREFIX));
  id->xmlns = XML_TRUE;
  ```
- **Argument:**
  Unlike line 6344 right below (`if (! id->prefix) return NULL;`), line 6327 omits the `NULL` check on `lookup()`. On OOM when allocating a new `xmlns:foo` prefix, `getAttributeId` returns `id` with `id->xmlns == XML_TRUE` and `id->prefix == NULL` permanently cached in `dtd->attributeIds`. `storeAtts` (line 3393 `if (attId->prefix)`) silently skips binding the namespace and reports `xmlns:foo` as a plain attribute instead of returning `XML_ERROR_NO_MEMORY`.
- **Remediation:** Check `if (! id->prefix) return NULL;` after line 6328 (and avoid leaving a half-initialized cached `ATTRIBUTE_ID` entry).

---

### BUG-27: NULL function pointer dereferences if `m_startDoctypeDeclHandler` (`XML_ROLE_DOCTYPE_CLOSE`) or `m_defaultHandler` (`reportDefault`) is cleared dynamically
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:4657-4663` (`doProlog`), `6192-6201` (`reportDefault`)
- **Defect Mechanism:**
  1. In `doProlog` (`XML_ROLE_DOCTYPE_CLOSE`, lines 4657–4660): `if (parser->m_doctypeName)` invokes `parser->m_startDoctypeDeclHandler(...)` without checking `&& parser->m_startDoctypeDeclHandler` (unlike lines 4588, 5083, 5098).
  2. In `reportDefault` (lines 6192–6201): the multi-chunk conversion `do { ... parser->m_defaultHandler(...); } while (...)` reloads `parser->m_defaultHandler` on each iteration without checking for `NULL` (contrast `doContent` line 3142, which caches `charDataHandler` locally).
- **Argument:**
  1. Because `XML_SetStartDoctypeDeclHandler` does not block during parsing, if `m_notStandaloneHandler` (line 4923) or `m_defaultHandler` clears `m_startDoctypeDeclHandler` between `<!DOCTYPE name` and `>`, line 4658 calls `NULL`.
  2. If `m_defaultHandler` unregisters itself via `XML_SetDefaultHandler(parser, NULL)` during a converted token spanning >1024 `XML_Char`s (e.g., UTF-16/Latin-1), the next iteration of `reportDefault` calls `NULL`.
- **Remediation:** Add `&& parser->m_startDoctypeDeclHandler` at line 4657, and cache `XML_DefaultHandler defaultHandler = parser->m_defaultHandler` (or recheck `!= NULL` and `m_parsingStatus.parsing`) inside `reportDefault`.

---

### BUG-28: Use-after-free in `XML_Parse` (`#ifndef XML_CONTEXT_BYTES`) when querying line/column after error or final chunk
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:1901-1925` (`XML_Parse` under `#ifndef XML_CONTEXT_BYTES`), `2278-2300` (`XML_GetCurrentLineNumber`, `XML_GetCurrentColumnNumber`)
- **Defect Mechanism:**
  When `XML_CONTEXT_BYTES` is not defined and `m_bufferPtr == m_bufferEnd`, `XML_Parse` parses directly from the caller's buffer `s` (setting `m_positionPtr = s` and `m_eventPtr` into `s`). On the error path (lines 1907–1910) and `isFinal` completion path (lines 1918–1921), `XML_Parse` returns immediately **without** calling `XmlUpdatePosition` and without clearing `m_positionPtr`/`m_eventPtr`.
- **Argument:**
  If the caller frees buffer `s` after `XML_Parse` returns and then calls `XML_GetErrorLineNumber` / `XML_GetCurrentLineNumber` / `XML_GetCurrentColumnNumber` (standard post-error reporting), `XmlUpdatePosition` dereferences `m_positionPtr..m_eventPtr` inside the freed caller buffer (**use-after-free**).
- **Remediation:** Call `XmlUpdatePosition` and set `m_positionPtr = m_eventPtr = m_eventEndPtr = NULL` (or synchronize position before returning) on both the error and `isFinal` paths under `#ifndef XML_CONTEXT_BYTES`.

---

### BUG-29: Uninitialized heap reads in `XML_GetIdAttributeIndex` (`m_idAttIndex`), `XML_GetParsingStatus` (`finalBuffer`), and `poolGrow` (`freeBlocks` copy)
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:986, 1085-1166` (`parserInit`), `1567-1571`, `2225-2230`, `7155-7165` (`poolGrow`)
- **Defect Mechanism:**
  1. `struct XML_ParserStruct` is allocated with `malloc` (uninitialized), and neither `parserCreate` nor `parserInit` initializes `parser->m_idAttIndex` (despite initializing `m_nSpecifiedAtts = 0` at line 1142) or `parser->m_parsingStatus.finalBuffer` (despite initializing `m_parsingStatus.parsing` at line 1147).
  2. In `poolGrow` (line 7160–7161), the `freeBlocks` reuse path copies `(pool->end - pool->start) * sizeof(XML_Char)` bytes instead of `(pool->ptr - pool->start) * sizeof(XML_Char)` (compare line 7239 in the `else` branch).
- **Argument:**
  1. Calling `XML_GetIdAttributeIndex` or `XML_GetParsingStatus` prior to the first start tag / `XML_Parse` reads uninitialized heap memory (UB / info leak), and after `XML_ParserReset` returns stale values from the previous document.
  2. Whenever `poolGrow` is invoked from `poolAppend` on `XML_CONVERT_OUTPUT_EXHAUSTED` with a multi-byte character leaving 1–3 unused bytes between `pool->ptr` and `pool->end`, line 7160 reads uninitialized heap bytes in `[pool->ptr, pool->end)`.
- **Remediation:** Initialize `parser->m_idAttIndex = -1;` and `parser->m_parsingStatus.finalBuffer = XML_FALSE;` in `parserInit`, and copy `(pool->ptr - pool->start) * sizeof(XML_Char)` at line 7161.

---

### BUG-30: Unrelated pointer subtraction UB and heap-distance leak in `storeAtts` (`XML_ATTR_INFO`) during internal entity expansion
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:3339-3348` (`storeAtts`, `#ifdef XML_ATTR_INFO`)
- **Defect Mechanism:**
  ```c
  currAttInfo->nameStart
      = parser->m_parseEndByteIndex - (parser->m_parseEndPtr - currAtt->name);
  ```
- **Argument:**
  When `storeAtts` runs while expanding an internal entity (`enc == parser->m_internalEncoding != parser->m_encoding`), `currAtt->name`, `currAtt->valuePtr`, and `currAtt->valueEnd` point into `dtd->entityValuePool`, whereas `parser->m_parseEndPtr` points into `parser->m_buffer` (an unrelated heap allocation). Subtracting pointers into distinct objects is C undefined behavior and exposes the heap distance between the two allocations via `XML_GetAttributeInfo()`. (Line 3354 properly guards `if (enc == parser->m_encoding)` for `m_eventPtr`, but lines 3339–3348 do not.)
- **Remediation:** Guard `XML_ATTR_INFO` offset calculation with `if (enc == parser->m_encoding)` and populate sentinel/entity-ref offsets otherwise.

---

### BUG-31: Multiple processor state bugs in `cdataSectionProcessor`, `externalEntityInitProcessor3`, `entityValueInitProcessor`, `XML_ParserReset`, and `XML_StopParser`
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:1215-1217`, `2158-2181`, `2218-2219`, `2680-2710`, `3843-3861`, `4286-4359`
- **Defect Mechanism & Argument:**
  1. **`cdataSectionProcessor` ignores `XML_SUSPENDED` (lines 3851–3859):** If `m_endCdataSectionHandler` calls `XML_StopParser(parser, XML_TRUE)` on `]]>`, `doCdataSection` returns `XML_ERROR_NONE` with `*startPtr = next`. `cdataSectionProcessor` checks `if (start)` without checking `m_parsingStatus.parsing == XML_SUSPENDED` and immediately invokes `contentProcessor`/`externalEntityContentProcessor`, continuing to parse while suspended.
  2. **`externalEntityInitProcessor3` fails to advance `m_processor` on suspend (lines 2685–2688):** If `m_xmlDeclHandler` suspends on an external entity's text declaration, `externalEntityInitProcessor3` returns without advancing `m_processor` to `externalEntityContentProcessor` and `m_tagLevel = 1`. On `XML_ResumeParser`, `externalEntityInitProcessor3` runs again and illegally accepts additional `<?xml ...?>` declarations mid-entity.
  3. **`entityValueInitProcessor` TextDecl / BOM / prefix bugs (lines 4286–4359):**
     - Line 4314 passes `isGeneralTextEntity = 0` instead of `1` to `processXmlDecl`, rejecting valid TextDecls without `version` and allowing `standalone="yes"` inside an external PE to mutate `parser->m_dtd->standalone` and disable `m_paramEntityParsing`.
     - Looping over `XmlPrologTok` allows `<?xml ...?>` mid-stream (silently discarding `s..start`), leaves a leading BOM in `s` when followed by non-XMLDecl tokens in the same chunk (storing raw U+FEFF in the entity value), and rejects `<tag>` (`XML_TOK_INSTANCE_START`) inside an external PE referenced in a general entity value.
  4. **`XML_ParserReset` ignores `copyString` OOM (lines 1215–1217):** Unlike `parserCreate:1068`, `XML_ParserReset` does not check `if (encodingName && !parser->m_protocolEncodingName)`, silently dropping the caller's encoding and returning `XML_TRUE`.
  5. **`XML_StopParser` allows suspending in `XML_INITIALIZED` (lines 2158–2181, 2218–2219):** Suspending before parsing (when `m_buffer != NULL` from `XML_GetBuffer` or `XML_ParserReset`) and calling `XML_ResumeParser` reaches line 2218 with `m_positionPtr == NULL` and `m_bufferPtr == m_buffer`, invoking `XmlUpdatePosition(enc, NULL, m_buffer, &m_position)` -> NULL pointer dereference.
- **Remediation:** Check `XML_SUSPENDED` before chaining in `cdataSectionProcessor`; update `m_processor` and `m_tagLevel` before returning on suspend in `externalEntityInitProcessor3`; pass `1` to `processXmlDecl` and check XMLDecl only at start (after optional BOM) in `entityValueInitProcessor`; check `copyString` failure in `XML_ParserReset`; reject `XML_StopParser` when `parsing == XML_INITIALIZED` (or guard `m_positionPtr != NULL` in `XML_ResumeParser`).

---

### BUG-32: Dead `!dtd->hasParamEntityRefs` WFC check, self-referential PE `NULL + 0` UB, and uncleared `m_tempPool` on skipped ATTLIST enum
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:4789-4834`, `5021-5045`, `5213-5234`, `5259`, `5955-6003` (`doProlog`, `storeEntityValue`)
- **Defect Mechanism & Argument:**
  1. **Dead WFC check (lines 5214, 5232):** `doProlog` (`XML_ROLE_PARAM_ENTITY_REF`) sets `dtd->hasParamEntityRefs = XML_TRUE` at line 5214 *before* line 5232 tests `! dtd->hasParamEntityRefs`. For non-standalone documents, `! dtd->hasParamEntityRefs` is always false, silently skipping undeclared parameter entities in the internal subset (with no external subset) instead of reporting `XML_ERROR_UNDEFINED_ENTITY` per XML 1.0 WFC "Entity Declared".
  2. **Incomplete PE self-reference (`NULL + 0` UB & spurious callback, lines 5027, 5995–5997, 5280–5286):** `XML_ROLE_PARAM_ENTITY_NAME` inserts the entity into `dtd->paramEntities` with `open = XML_FALSE, textPtr = NULL, textLen = 0, systemId = NULL` before its value is parsed. In an external DTD/PE, `<!ENTITY % pe "%pe;">` reaches `storeEntityValue(..., (const char *)entity->textPtr, (const char *)(entity->textPtr + entity->textLen), ...)` with `NULL + 0` (C UB) and expands `%pe;` to `""` instead of `XML_ERROR_RECURSIVE_ENTITY_REF`. Similarly, `<!ENTITY % pe %pe; "val">` triggers `m_externalEntityRefHandler(arg, 0, NULL, NULL, NULL)` (mimicking a foreign DTD).
  3. **Uncleared `m_tempPool` data corruption (lines 4791–4834, 5259):** When `m_attlistDeclHandler` is set and an external DTD parses an enumerated attribute list `<!ATTLIST e a (x %undef; | y) #IMPLIED>`, `XML_ROLE_ATTRIBUTE_ENUM_VALUE` appends `"(x"` to `m_tempPool`, then `%undef;` sets `dtd->keepProcessing = XML_FALSE` (line 5259), causing `XML_ROLE_IMPLIED_ATTRIBUTE_VALUE` (line 4809 `if (dtd->keepProcessing)`) to skip `poolClear(&parser->m_tempPool)`. The leftover `"(x"` remains in `m_tempPool` and is prepended to the next string built in `m_tempPool` (such as a comment, PI, notation name, or `<empty/>` element name).
- **Remediation:** Capture `hadParamEntityRefs` before setting `dtd->hasParamEntityRefs = XML_TRUE`; mark `m_declEntity->open = XML_TRUE` (or defer insertion) until the entity declaration completes; discard/clear `m_tempPool` when `dtd->keepProcessing` transitions to `XML_FALSE` (or unconditionally at ATTLIST value completion).

---

### BUG-33: Wrong `EXPAT_FMT_*` format specifiers on MinGW-w64 / 32-bit platforms, and `#ifdef XML_DTD` guard hiding `XML_SetBillionLaughsAttackProtection*` declarations
- **Severity:** Medium
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/internal.h:110-130`, `expat/lib/expat.h:1027-1037`, `expat/lib/libexpat.def:79-80`, `expat/lib/libexpatw.def:79-80`
- **Defect Mechanism & Argument:**
  1. **`internal.h:110-130` (`EXPAT_FMT_*`):** Line 110 tests `#if defined(_WIN32) && ! defined(__USE_MINGW_ANSI_STDIO)`. On 64-bit MinGW-w64 (LLP64, where `ULONG_MAX` is `2^32 - 1` while `size_t`/`ptrdiff_t` are 64-bit), `<_mingw.h>` defines `__USE_MINGW_ANSI_STDIO` (to `1` under C99/POSIX or `0` otherwise), forcing compilation into the `#else` branch where `ULONG_MAX != 2^64 - 1` selects 32-bit `"%d"`/`"%u"` for 64-bit `ptrdiff_t`/`size_t` (format-string UB in `xmlparse.c:7469` and `runtests.c:11508`), and emits `"%llu"` even when `__USE_MINGW_ANSI_STDIO == 0`. Similarly, 32-bit non-Windows platforms where `size_t` is `unsigned long` get `"%u"`/`"%d"` instead of `"%lu"`/`"%ld"`.
  2. **`expat.h:1027-1037` (`#ifdef XML_DTD`):** `expat.h` never includes `expat_config.h` and never defines `XML_DTD`, yet guards `XML_SetBillionLaughsAttackProtectionMaximumAmplification` and `XML_SetBillionLaughsAttackProtectionActivationThreshold` under `#ifdef XML_DTD` (unlike `XML_UseForeignDTD` and `XML_SetParamEntityParsing`, which are unconditional). Consumers including `<expat.h>` fail to compile in C++/strict C, or in permissive C suffer implicit-declaration ABI corruption (promoting `float` to `double`). Conversely, builds without `XML_DTD` fail MSVC `.def` linking because `libexpat.def:79-80` unconditionally exports both symbols.
- **Remediation:** Check `(! defined(__USE_MINGW_ANSI_STDIO) || (__USE_MINGW_ANSI_STDIO == 0))` and use `"%td"`/`"%zu"` (or `"%lld"`/`"%llu"` for `_WIN64`) in `internal.h`; remove `#ifdef XML_DTD` around the declarations in `expat.h` (and provide stub definitions returning `XML_FALSE` when `XML_DTD` is disabled).

---

### BUG-34: Memory leak of `BINDING` struct on integer-overflow error paths in `addBinding`
- **Severity:** Low
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:3793-3816` (`addBinding`)
- **Defect Mechanism & Argument:**
  `b = (BINDING *)MALLOC(parser, sizeof(BINDING))` is allocated at line 3793 before the overflow guards at lines 3798–3800 (`len > INT_MAX - EXPAND_SPARE`) and lines 3806–3808 (`#if UINT_MAX >= SIZE_MAX`). Both early returns exit with `XML_ERROR_NO_MEMORY` without calling `FREE(parser, b)` (unlike line 3814 when `b->uri` allocation fails).
- **Remediation:** Perform both overflow checks before allocating `b` (or call `FREE(parser, b)` before returning).

---

### BUG-35: Double-counting of direct bytes for non-empty start-tag attributes (`XML_TOK_START_TAG_WITH_ATTS`) weakens amplification limit
- **Severity:** Low
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:2753, 2940-2941` vs `2965-2966` (`doContent`), `3376-3378` (`storeAtts`)
- **Defect Mechanism & Argument:**
  `doContent` already accounts the full start-tag token `s..next` at line 2753. For `XML_TOK_EMPTY_ELEMENT_WITH_ATTS` (line 2966), it properly passes `XML_ACCOUNT_NONE` to `storeAtts`, whereas for `XML_TOK_START_TAG_WITH_ATTS` (line 2941) it passes `account` (`XML_ACCOUNT_DIRECT`). Any non-normalized attribute value in a non-empty start tag is therefore counted twice in `countBytesDirect`, inflating the denominator of the amplification ratio by up to ~2x.
- **Remediation:** Pass `XML_ACCOUNT_NONE` to `storeAtts` at line 2941 (matching line 2966).

---

### BUG-36: `prologTok` shrinks odd UTF-16 `end` locally causing `doProlog` to swallow stray trailing bytes; `DEFINE_UTF16_TO_UTF8` returns `COMPLETED` on odd input
- **Severity:** Low
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok_impl.c:1020-1028`, `expat/lib/xmlparse.c:4547-4550`, `expat/lib/xmltok.c:630, 694-698`
- **Defect Mechanism & Argument:**
  1. When `MINBPC(enc) == 2` and `end - ptr` is odd (`2k + 1`, `k >= 1`), `prologTok` shrinks its local `end` to `ptr + 2k`. If the token returns a negative code (`-XML_TOK_CLOSE_PAREN`, `-XML_TOK_LITERAL`, `-XML_TOK_NAME`, etc.) without setting `*nextTokPtr`, `doProlog` (`isFinal == 1`, line 4549) sets `next = end` using the **unshrunk** odd `end`, silently swallowing the stray trailing byte (or feeding an odd slice into `storeEntityValue`).
  2. In `DEFINE_UTF16_TO_UTF8` (`xmltok.c:630, 695`), overwriting `fromLim` with the even-shrunk pointer makes `if (from < fromLim)` dead code, returning `XML_CONVERT_COMPLETED` instead of `XML_CONVERT_INPUT_INCOMPLETE` when an odd byte remains.
- **Remediation:** In `doProlog` line 4549, align `next` down to a multiple of `enc->minBytesPerChar` (or report `XML_TOK_PARTIAL_CHAR` on trailing odd byte); in `DEFINE_UTF16_TO_UTF8`, save original `fromLim` and return `XML_CONVERT_INPUT_INCOMPLETE` if `from < origFromLim`.

---

### BUG-37: `prologTok` `BT_COLON` accepts `NameChar` instead of `NameStartChar` after `:`, and `BT_RPAR` rejects `)` followed by `%`
- **Severity:** Low
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmltok_impl.c:1121-1132, 1206-1224`
- **Defect Mechanism & Argument:**
  1. In `prologTok` (`XML_NS` mode, lines 1212–1217), `case BT_COLON:` uses `CHECK_NAME_CASES` instead of `CHECK_NMSTRT_CASES` (compare `scanLt:767` and `scanAtts:588`). Consequently, `prologTok` emits `XML_TOK_PREFIXED_NAME` for invalid QNames whose local part starts with a digit, `-`, `.`, or combining character (e.g., `<!DOCTYPE a:1>`, `<!ELEMENT a:1 EMPTY>`, `<!ATTLIST a:1 b:- CDATA #IMPLIED>`).
  2. In `prologTok` (`case BT_RPAR:`, lines 1121–1132), `case BT_PERCNT:` is omitted (unlike `Name:1199`, `scanPoundName:968`, `scanLit:1000`), causing valid external DTD declarations like `<!ELEMENT a (b)%pe;>` to fail with `XML_TOK_INVALID`.
- **Remediation:** Use `CHECK_NMSTRT_CASES` after `BT_COLON` in `prologTok`, and add `case BT_PERCNT:` to `case BT_RPAR:`.

---

### BUG-38: Character-table and declaration edge-case defects (`latin1tab.h`, `doParseXmlDecl`, `isPublicId`, `_INTERNAL_trim_to_complete_utf8_characters`)
- **Severity:** Low
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/latin1tab.h:45, 48, 49`, `expat/lib/xmltok.c:334-364, 1131-1143, 1177-1199`, `expat/lib/xmltok_impl.c:1477-1491`
- **Defect Mechanism & Argument:**
  1. **`latin1tab.h:45, 48, 49`:** Classifies `0xAA` (`ª`), `0xB5` (`µ`), and `0xBA` (`º`) as `BT_NMSTRT`, violating XML 1.0 (1st–5th ed.) and contradicting Expat's own `nametab.h` (`namingBitmap[21] == 0`), so ISO-8859-1 and UTF-16 accept names that UTF-8 rejects.
  2. **`doParseXmlDecl` (`xmltok.c:1131-1143, 1177-1199`):** `parsePseudoAttribute` allows empty quoted values, and `doParseXmlDecl` never verifies `version` is non-empty, accepting `<?xml version=""?>` (contrary to XML 1.0 `VersionNum`).
  3. **`isPublicId` (`xmltok_impl.c:1477-1491`):** Uses `BYTE_TO_ASCII(enc, ptr)` (raw `*ptr`) instead of decoded code points for unknown encodings; remapping ASCII `BT_OTHER` bytes (like `0x24`/`0x5C`) to non-PubidChars or remapping `>= 0x80` to `$`/`@` yields wrong Public ID validation.
  4. **`_INTERNAL_trim_to_complete_utf8_characters` (`xmltok.c:334-364`):** Resetting `walked = 0` inside the `for (...; walked++)` loop immediately increments `walked` to `1` on the next iteration, miscounting consecutive truncated lead bytes (e.g., `{0xC3, 0xC3}`) as continuation bytes.
- **Remediation:** Change `0xAA`/`0xB5`/`0xBA` to `BT_OTHER` in `latin1tab.h`; require `val != ptr - enc->minBytesPerChar` for `version` in `doParseXmlDecl`; consult decoded characters for unknown encodings in `isPublicId`; use `continue` or avoid incrementing `walked` when resetting on a truncated lead byte.

---

### BUG-39: Short-read / stale-`errno` loop bug in `writeRandomBytes_*`, `XML_GetBuffer(p, 0)` API inconsistency, and signed `int` length in `copyString`
- **Severity:** Low
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:743-767, 775-799`, `1987, 2054, 2151`, `7402-7418`
- **Defect Mechanism & Argument:**
  1. **`writeRandomBytes_getrandom_nonblock` & `writeRandomBytes_dev_urandom` (lines 743–799):** Neither resets `errno = 0` and both loop on `while (! success && (errno == EINTR))`. A short successful read (`0 < bytesWrittenMore < count`) does not set `errno = EINTR`, causing premature exit with `success = 0` (falling back to weak time/PID entropy); conversely, stale `errno == EINTR` with EOF (`0`) loops infinitely.
  2. **`XML_GetBuffer(parser, 0)` (lines 2054, 2151, 1987):** On a fresh parser (`m_bufferEnd == NULL`), `0 > 0` is false, so `XML_GetBuffer(parser, 0)` returns `NULL` (indicating failure) while leaving `m_errorCode == XML_ERROR_NONE`, and a subsequent `XML_ParseBuffer(parser, 0, 1)` fails with `XML_ERROR_NO_BUFFER`.
  3. **`copyString` (lines 7402–7418):** Uses signed `int charsRequired` with unchecked `charsRequired++` and `charsRequired * sizeof(XML_Char)` (32-bit overflow risk for oversized caller-supplied `encodingName`).
- **Remediation:** Loop while `!success && (bytesWrittenMore > 0 || (bytesWrittenMore == -1 && errno == EINTR))` in `writeRandomBytes_*`; allocate or handle `len == 0` cleanly in `XML_GetBuffer`/`XML_ParseBuffer`; use `size_t` with overflow checks in `copyString`.

---

### BUG-40: Signed `attIndex` / `nPrefixes << 1` / `int j` overflows in `storeAtts` at `>= 2^29` attributes; unchecked `state->includeLevel += 1` wrap in `condSect1`
- **Severity:** Low
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/xmlparse.c:3266-3283, 3435-3445, 3451, 3462, 3505-3506`, `expat/lib/xmlrole.c:1150-1153`
- **Defect Mechanism & Argument:**
  1. `storeAtts` caps `n + nDefaultAtts` at `INT_MAX - INIT_ATTS_SIZE`, yet `appAtts` consumes 2 indices per attribute (`attIndex += 2`). At `>= 2^30` attributes (permitted by `defineAttribute` line 6234), `attIndex` overflows signed `int` to `INT_MIN` (negative OOB write in `appAtts[attIndex]`), `nPrefixes << 1` (line 3462) triggers signed overflow UB, and at `nPrefixes == 2^29`, `nsAttsSize = 0x80000000u` assigns `INT_MIN` to signed `int j` followed by `--j` (signed underflow UB, line 3506).
  2. `condSect1` (`xmlrole.c:1152`) increments `unsigned includeLevel += 1` with no overflow guard and O(1) heap usage; streaming `2^32` `<![INCLUDE[` openings (~40 GiB) wraps `includeLevel` to `0`, accepting unclosed sections at EOF and rejecting valid closing `]]>`.
- **Remediation:** Bound `n + nDefaultAtts <= (INT_MAX - 1) / 2`, use `unsigned int` for `j` and `nPrefixes` shifts in `storeAtts`, and check `state->includeLevel == UINT_MAX` in `condSect1`.

---

### BUG-41: `XML_XmlDeclHandler` `version == NULL` contract mismatch for TextDecls, `XML_GetUserData(NULL)` dereference, and `#define inline` issues in `internal.h`
- **Severity:** Low
- **Status:** SUSPECTED (argued from code)
- **Location:** `expat/lib/expat.h:202-209, 664`, `expat/lib/internal.h:100-106, 133`, `expat/lib/xmltok.c:1177-1199`
- **Defect Mechanism & Argument:**
  1. `expat.h:203-204` documents that `XML_XmlDeclHandler`'s `version` argument *"will be NULL for text declarations"*, but `doParseXmlDecl` (`xmltok.c:1182-1186`) and `processXmlDecl` (`xmlparse.c:4164-4172`) pass a non-NULL `version` string whenever an XML 1.0 TextDecl includes its optional `VersionInfo`.
  2. `XML_GetUserData(parser)` (`expat.h:664`) expands to `(*(void **)(parser))`, dereferencing `NULL` if `parser == NULL` (unlike all other `XML_Get*` APIs) and exposing a modifiable lvalue that bypasses `XML_SetUserData`'s `m_handlerArg` sync.
  3. `internal.h:100-106` defines `#define inline inline` in C++ (UB under `[macro.names]` when standard headers follow on lines 108/146) and `#define inline` (empty) on non-GCC C99 compilers; `internal.h` also lacks an include guard and omits parentheses in `#define UNUSED_P(p) (void)p`.
- **Remediation:** Clarify the `expat.h` comment for `XML_XmlDeclHandler`; make `XML_GetUserData` NULL-safe (`(parser) ? *(void **)(parser) : NULL` or non-lvalue); remove the C++ `#define inline inline` / fix C99 detection and add an include guard in `internal.h`.
