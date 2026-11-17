# DuckDB Bug Hunt Report

**Target:** DuckDB source tree at commit `20b1486d11` (v0.10.0-dev, 2024-02-13)
**Method:** manual code review of the riskiest subsystems, with runtime checks on an ASan+UBSan `RelWithDebInfo` build of the CLI (`/tmp/cbh-build/duckdb`, with `D_ASSERT` enabled).
**Scope rule:** read-only. No source files were changed. Scratch files are in `/tmp/cbh-scratch-*`.

**Status labels:**
- **CONFIRMED**: reproduced on the sanitizer build; the repro is shown.
- **SUSPECTED**: argued from the code, not reproduced.

Each repro can be run with `duckdb -csv -c "<sql>"` unless noted otherwise.

Findings are grouped by subsystem. Severity scale:
- **Critical**: silent data corruption with default settings.
- **High**: memory-unsafe behaviour on untrusted input, wrong query results, or loss of DB integrity.
- **Medium**: wrong results in edge cases, hangs, or denial of service.
- **Low**: minor correctness issues or latent defects.

---

## Summary table

| # | Sev | Area | Short title | Status |
|---|-----|------|-------------|--------|
| S1 | Critical | storage/rle | RLE writes a zero-length run after 65535 repeats; later values shift by one row | CONFIRMED |
| S2 | High | storage/alp | ALP/ALPRD/Patas `Skip` underflow → near-infinite loop | CONFIRMED |
| S3 | Medium | storage | -0.0/0.0 sign lost on checkpoint (RLE / constant segments) | CONFIRMED |
| S4 | Low | storage/bitpacking | Signed overflow (UB) decoding CONSTANT_DELTA groups | CONFIRMED (UBSan) |
| S5 | Low | storage/buffer | Temp-file capacity check inverted | SUSPECTED |
| S6 | Low | storage/metadata | `D_ASSERT(a && b)` should be `a & b` | CONFIRMED (code) |
| F1 | High | common/gzip | Heap over-read parsing the header of a concatenated gzip member | CONFIRMED (ASan) |
| F2 | Medium | common/gzip | Valid gzip files with FTEXT flag rejected | CONFIRMED |
| F3 | High | read_text/read_blob | Files of 2–4 GiB are silently truncated; the tail is uninitialized | CONFIRMED |
| F4 | Low | storage/magic_bytes | Short file → uninitialized stack bytes compared | SUSPECTED |
| F5 | Medium | COPY TO csv | `QUOTE ''` plus a NUL byte in the data → infinite loop | CONFIRMED |
| F6 | Medium | COPY TO partitioned | Hive partition values not escaped → writes outside target dir | CONFIRMED |
| P1 | High | parquet | DELTA_LENGTH_BYTE_ARRAY memcpy with unchecked length | CONFIRMED (ASan) |
| P2 | High | parquet | DELTA_BYTE_ARRAY suffix memcpy with unchecked length | CONFIRMED (ASan) |
| P3 | High | parquet | Dictionary index not bounds-checked | CONFIRMED (ASan) |
| P4 | Medium | parquet | Division by zero in DELTA_BINARY_PACKED header | CONFIRMED (assert) |
| M1 | Medium | pragma | `PRAGMA storage_info` SQL injection | CONFIRMED |
| M2 | Medium | import | IMPORT DATABASE with a non-COPY statement in load.sql invalidates the DB | CONFIRMED |
| M3 | Medium | config | `memory_limit` overflow wraps to 0 bytes | CONFIRMED |
| M4 | Low | config | Missing format argument in memory_limit unit error | CONFIRMED |
| M5 | Medium | CLI | Exception during duckbox rendering → `std::terminate` | CONFIRMED |
| M6 | Medium | export | EXPORT DATABASE emits unquoted/unqualified identifiers; output can't be imported | CONFIRMED |
| M7 | Medium | strings | String results > 4 GiB silently truncated to uint32 length | CONFIRMED |
| C1 | High | catalog | `CREATE … IF NOT EXISTS` no-op leaves stale dependency → DROP cascades to wrong objects | CONFIRMED |
| C2 | High | catalog | Cascaded DROP bypasses foreign-key bookkeeping | CONFIRMED (by reviewer) |
| C3 | Medium | relation API | `Relation::Insert(values)` inserts into the wrong schema | CONFIRMED (by reviewer) |
| C4 | Low | transaction | Uninitialized `UndoBuffer::IteratorState`; row-count drift on failed commit | CONFIRMED (by reviewer) |
| C5 | Low | catalog | COMMENT ON fails for tables with dependents | CONFIRMED (by reviewer) |
| A1–A13 | High/Med | C API | Exceptions escaping `extern "C"`, NULL derefs, missing bounds checks (see section) | CONFIRMED (by reviewer) |
| E1 | High | window | EXCLUDE sub-frames not clipped to the frame | CONFIRMED |
| E2 | High | window | FIRST/LAST/NTH_VALUE + EXCLUDE: mask not reset after empty frame | CONFIRMED |
| E3 | High | window | Streaming FIRST_VALUE ignores frame | CONFIRMED |
| E4 | High | asof join | NULL inequality key not filtered when an equality condition exists | CONFIRMED |
| E5 | High | optimizer | ANTI join with always-true condition folded to empty | CONFIRMED |
| E6 | High | optimizer | MoveConstants folds `x * -1 > -128` to FALSE | CONFIRMED |
| E7 | Medium | optimizer | Comparison/IN simplification strips TRY_CAST | CONFIRMED |
| E8 | High | optimizer | VARCHAR→TIMESTAMP treated as invertible cast | CONFIRMED |
| E9 | High | range/stats | `range()` cardinality underestimates → SUM overflow path chosen | CONFIRMED |
| E10 | Medium | optimizer | Regex→LIKE rewrite: `.` vs UTF-8, mid-pattern anchors dropped | CONFIRMED |
| E11 | Medium | window | NULL LEAD/LAG offset or NULL ROWS offset read as garbage | CONFIRMED |
| E12 | Low | binder | Negative OFFSET with LIMIT % / negative RANGE offsets accepted | CONFIRMED |
| E13 | Medium | optimizer | Cast statistics ignore session-dependent (ICU) casts | SUSPECTED |
| T1–T17 | High/Med/Low | casts/types | Cast rounding, hugeint parse, interval bugs, bit functions, UB negations, strptime OOB (see section) | 16 CONFIRMED, 1 SUSPECTED |
| FN1 | High | list fns / Vector | `list_resize` huge size → size overflow in `Vector::Resize` → heap-buffer-overflow WRITE | CONFIRMED (ASan) |
| FN2 | Medium | aggregates | `sum`/`avg` over HUGEINT / DECIMAL(38) wraps silently on overflow (UB) | CONFIRMED (UBSan) |
| FN3 | Medium | table fn | `repeat(value, <negative>)` produces ~2^64 rows | CONFIRMED |
| FN4 | Medium | math | `bit_count(HUGEINT)` returns TINYINT → 128 shows as -128 | CONFIRMED |
| FN5 | Medium | list fns | `list_cosine_similarity` with a zero vector returns -1.0 (NaN clamped) | CONFIRMED |
| FN6 | Low | list fns | `list_select` / `repeat()` scalar: signed overflow (UB) with INT64_MIN | CONFIRMED (UBSan) |
| FN7 | Low | list fns | `list_inner_product` on empty constant lists hits a D_ASSERT (INTERNAL in debug builds) | CONFIRMED |
| FN8 | Low | aggregates | `fsum`/`favg` return NaN where plain `sum` gives inf | CONFIRMED |

---

## 1. Storage / compression

### S1 — RLE writes a zero-count run after the maximum run length; later rows shift by one (Critical, CONFIRMED)
- **File:** `src/storage/compression/rle.cpp`
  - `RLEState::Update`: lines ~56–77.
  - `Finalize`: ~207.
- **Defect:**
  - When a run reaches 65535 (the `uint16_t` count limit), the state is flushed and `last_seen_count = 0`, but `last_value` is kept.
  - If the next value is different, the "values are different" branch calls `Flush()` again. That writes an entry with count 0.
  - Scan and fetch assume every run has at least one row. So the zero-count entry still emits one row, and every later value in the segment is shifted one row; the last value is lost.
  - `Finalize` can write a trailing zero-count run in the same way.
- **Impact:** silent data corruption with **default settings**. The compression analyzer chooses RLE for long constant runs. Scans, filters and index lookups are all affected.
- **Repro:**
  ```sql
  -- on a persistent database
  CREATE TABLE t AS SELECT CASE WHEN i < 65535 THEN 1.5 ELSE 2.5 END::DOUBLE AS v FROM range(70000) r(i);
  CHECKPOINT;
  SELECT DISTINCT compression FROM pragma_storage_info('t') WHERE segment_type='DOUBLE';  -- RLE
  SELECT v, count(*) FROM t GROUP BY v ORDER BY v;
  -- got: 1.5|65536, 2.5|4464   expected: 1.5|65535, 2.5|4465
  ```
- **Fix:**
  - In the "values are different" branch, call `Flush` only when `last_seen_count > 0`.
  - In `Finalize`, skip the final flush when `last_seen_count == 0`.
  - Optionally make the scan skip zero-count entries defensively.

### S2 — ALP / ALPRD / Patas `Skip` underflows → near-infinite loop (High, CONFIRMED)
- **Files:**
  - `src/include/duckdb/storage/compression/alp/alp_scan.hpp:181-185`
  - `src/include/duckdb/storage/compression/alprd/alprd_scan.hpp:188-192`
  - `src/include/duckdb/storage/compression/patas/patas_scan.hpp:179-183`
- **Defect:**
  - When the scan is in the middle of a vector, `skip_count -= LeftInVector()` runs without checking `skip_count >= LeftInVector()`.
  - The unsigned value wraps, `vectors_to_skip` becomes about 1.8e16, and the `SkipVector()` loop practically never ends.
  - This is reachable through LIST child columns, where `ListColumnData::Skip` skips arbitrary child counts when filter pushdown rejects a whole parent vector.
- **Repro:**
  ```sql
  PRAGMA force_compression='alp';
  CREATE TABLE t AS SELECT CASE WHEN i>=2048 AND i<4096 THEN 0 ELSE 1 END AS f,
    CASE WHEN i=0 THEN list_transform(range(101), x->x*0.5) WHEN i=2048 THEN list_transform(range(10), x->x*0.5)
         WHEN i>2048 AND i<4096 THEN []::DOUBLE[] ELSE [i*0.5] END AS l FROM range(6144) r(i);
  CHECKPOINT;
  SELECT sum(list_sum(l)), count(*) FROM t WHERE f = 1;   -- hangs (100% CPU)
  ```
- **Fix:** if `skip_count <= LeftInVector()`, skip within the current vector and return. Otherwise subtract. Apply the same change in all three scan states.

### S3 — Sign of zero lost on checkpoint (Medium, CONFIRMED)
- **Files:**
  - `src/storage/compression/rle.cpp:56`: RLE compares with `last_value == data[idx]`.
  - Constant-segment detection: float stats consider min == max because `-0.0 == 0.0`.
- **Impact:** after `CHECKPOINT`, `-0.0` becomes `0.0` or the reverse. This changes `1/v`, `atan2`, and `v::VARCHAR`. Also, NaNs never compare equal, so each NaN starts its own run.
- **Repro:**
  ```sql
  CREATE TABLE a AS SELECT i, CASE WHEN i%2=0 THEN '0.0'::DOUBLE ELSE '-0.0'::DOUBLE END v FROM range(10) r(i);
  CHECKPOINT;
  SELECT count(*) FROM a WHERE v::VARCHAR='-0.0';   -- before checkpoint: 5, after: 0
  ```
- **Fix:** compare floats bit-wise in RLE and in constant-segment detection.

### S4 — Signed overflow in bitpacking CONSTANT_DELTA decode (Low, CONFIRMED by UBSan)
- **File:** `src/storage/compression/bitpacking.cpp:807` (scan) and `:901` (fetch).
- **Defect:** `current_group_offset * current_constant` is computed in signed `T` and can overflow even when the final value fits.
- **Repro:**
  ```sql
  PRAGMA force_compression='bitpacking';
  CREATE TABLE t AS SELECT (-4611686018427387904::HUGEINT + i::HUGEINT*4611686018427387904::HUGEINT)::BIGINT v FROM range(3) r(i);
  CHECKPOINT;
  SELECT * FROM t;
  -- UBSan: bitpacking.cpp:807:74 signed integer overflow
  ```
- **Fix:** do the arithmetic in the unsigned counterpart type, then cast back.

### S5 — Temp-file capacity check inverted (Low, SUSPECTED)
- **File:** `src/storage/standard_buffer_manager.cpp:367`
- **Defect:** the check is `if (GetMaxIndex() >= max_allowed_index && HasFreeBlocks())`. A file that still has free slots is reported as full, while a file with no free slots grows without bound.
- **Related:** `RemoveTempBlockIndex` truncates to `GetPositionInFile(max_index + 1)`, which keeps one extra block.
- **Fix:** use `&& !HasFreeBlocks()`, and truncate to `GetPositionInFile(max_index)`.

### S6 — Assertion that can never fail (Low)
- **File:** `src/storage/metadata/metadata_manager.cpp:295`
- **Defect:** `D_ASSERT(modified_list && (1ULL << block_index))` is always true.
- **Fix:** use bitwise `&`.

---

## 2. File systems, I/O and COPY

### F1 — Heap buffer over-read parsing the header of a concatenated gzip member (High, CONFIRMED by ASan)
- **File:** `src/common/gzip_file_system.cpp:151-175` (`MiniZStreamWrapper::Read`, `sd.refresh` branch).
- **Defect:** when a second gzip member follows, its header is parsed straight from the input buffer:
  - `memcpy(gzip_hdr, body_ptr, 10)` runs without checking that 10 bytes are available.
  - The FEXTRA length `xlen` (up to 65535) advances `body_ptr` without checking it against `sd.in_buff_end`. The only check compares `xlen` to `GZIP_HEADER_MAXSIZE` (32 KiB), not to the data actually present.
  - The FNAME `do { c = *body_ptr; body_ptr++; } while (...)` reads at least one byte *before* checking the bound. After a large `xlen`, that read is past the 32 KiB heap buffer.
  - If FNAME is not set, a too-large `xlen` instead truncates the stream silently.
- **Impact:** reading an attacker-supplied `.gz` (CSV/JSON) causes a heap out-of-bounds read: a crash or information leak.
- **Repro:**
  - Generator: `/tmp/cbh-scratch-main/mkgz.py`. It writes one valid member of about 3 KB, followed by a truncated header with flags FEXTRA|FNAME and `xlen=32000`.
  - Run:
    ```sql
    SELECT count(*) FROM read_csv('poc.csv.gz', header=false, columns={'a':'varchar'}, auto_detect=false);
    ```
  - ASan output:
    ```
    ERROR: AddressSanitizer: heap-buffer-overflow ... READ of size 1
      #0 duckdb::MiniZStreamWrapper::Read(duckdb::StreamData&) src/common/gzip_file_system.cpp:172
      #1 duckdb::CompressedFile::ReadData compressed_file_system.cpp:90
    ```
- **Fix:**
  - Before each header field, check `body_ptr + N <= sd.in_buff_end`, or refill the buffer.
  - Turn the FNAME loop into a `while (body_ptr < end && *body_ptr++ != '\0')`.
  - Throw `IOException` on a truncated header instead of `Close(); return true`.
  - Also handle FCOMMENT and FHCRC in both the initial and the concatenated path.

### F2 — Gzip files with the FTEXT flag are rejected (Medium, CONFIRMED)
- **File:** `src/include/duckdb/common/gzip_file_system.hpp:50-51`
- **Defect:** `GZIP_FLAG_UNSUPPORTED` includes `GZIP_FLAG_ASCII` (0x01, FTEXT). FTEXT is only a hint and has no effect on decoding. Bit 0x02 is FHCRC in RFC 1952, not "multipart".
- **Repro:**
  - Create a valid gzip file with the FTEXT bit set: `python3 -c "import gzip; d=bytearray(gzip.compress(b'a\n1\n')); d[3]|=1; open('ftext.csv.gz','wb').write(d)"`.
  - `gzip -dc` decodes it fine.
  - `SELECT * FROM 'ftext.csv.gz'` fails with `IO Error: Unsupported GZIP archive`.
- **Fix:** remove FTEXT from the unsupported mask. Support FHCRC by skipping 2 bytes and FCOMMENT by skipping a zero-terminated string.

### F3 — `read_text` / `read_blob` silently truncate files larger than ~2 GiB (High, CONFIRMED)
- **Files:**
  - `src/function/table/read_file.cpp:154`
  - `src/common/local_file_system.cpp:404-412`
- **Defect:**
  - `read_file.cpp` calls `file_handle->Read(ptr, file_size)` and ignores the returned count.
  - `LocalFileSystem::Read(handle, buf, n)` does a single `read()` call. On Linux one `read()` returns at most 0x7FFFF000 bytes.
  - `AssertMaxFileSize` allows files up to 4 GiB. So for files between 2 and 4 GiB, the rest of the result buffer is never written: it holds uninitialized heap memory, or zero pages for fresh mmaps.
  - Short reads from pipes or concurrently truncated files cause the same problem.
- **Repro:**
  ```sh
  truncate -s 2500000000 big.txt; printf XYZ | dd of=big.txt bs=1 seek=2500000000 conv=notrunc
  duckdb -csv -c "SELECT length(content), hex(content[-3:]), strpos(content,'XYZ') FROM read_text('big.txt')"
  # got: 2500000003,000000,0   (marker 'XYZ' missing; tail is zero/uninitialized)
  ```
- **Fix:** loop until `file_size` bytes are read, or use the positional `Read(buffer, n, location)`, which loops and throws on short reads. Apply the same change wherever the return value of `FileHandle::Read(void*, idx_t)` is ignored:
  - `src/main/extension/extension_install.cpp:268`
  - `src/storage/magic_bytes.cpp:18` (see F4)
  - `CSVBuffer::Reload` in `csv_buffer.cpp:65`

### F4 — Magic-byte detection compares uninitialized stack memory (Low, SUSPECTED)
- **File:** `src/storage/magic_bytes.cpp:15-27`
- **Defect:** `handle->Read(buffer, 16)` ignores the returned count. For files shorter than 16 bytes, `memcmp` reads uninitialized stack bytes, so the file type detected for ATTACH auto-detection depends on garbage.
- **Fix:** zero-initialize `buffer` and compare only up to the number of bytes actually read.

### F5 — `COPY … TO (QUOTE '')` hangs forever on a value containing NUL (Medium, CONFIRMED)
- **File:** `src/function/table/copy_csv.cpp:167-187` (`AddEscapes`), together with lines 49-50 and 105-110.
- **Defect:**
  - With `QUOTE ''` the quote character becomes `'\0'`. The escape defaults to the quote, so it is `'\0'` as well, and `requires_quotes['\0']` is set.
  - A value containing `chr(0)` takes the escape path, which calls `AddEscapes('\0', '\0', val)`.
  - Inside `AddEscapes`, `found` is advanced only when `escape != '\0'`. So `while (found != npos)` never terminates.
- **Repro:**
  ```sql
  COPY (SELECT 'a' || chr(0) || 'b' AS s) TO 'nul.csv' (QUOTE '');   -- never returns (timeout 20 → exit 124)
  ```
- **Fix:** in `AddEscapes`, always advance `found = val.find(to_be_escaped, found + 1)`. When escape is `'\0'`, either skip the escaping or reject `QUOTE ''` combined with quoting.

### F6 — Hive-partitioned COPY doesn't escape partition values → path traversal outside the target directory (Medium, CONFIRMED)
- **File:** `src/execution/operator/persistent/physical_copy_to_file.cpp:195` and `:206`
- **Defect:**
  - Directory names are built as `col + "=" + value.ToString()` and joined into the path. Characters like `/`, `\` and `..` in the value are not escaped.
  - A value with `/` makes the write fail.
  - Worse, a row with an empty value first creates the directory `p=`. A later value `/../../x` then resolves to a path outside the COPY target.
- **Repro:**
  ```sql
  COPY (SELECT * FROM (VALUES ('',1),('/../../escaped_dir',2)) t(p,v)) TO 'part' (FORMAT csv, PARTITION_BY (p));
  -- creates ./escaped_dir/data_0.csv (outside 'part/')
  COPY (SELECT 'a/b' p, 1 v) TO 'part2' (FORMAT csv, PARTITION_BY (p));
  -- IO Error: Failed to create directory "part2/p=a/b"
  ```
- **Impact:** partitioning untrusted data can create or overwrite files anywhere the process can write.
- **Fix:** percent-encode partition values, as Hive and Spark do (`/`, `\`, `=`, `%`, `:`, control characters, and leading `.`). Decode them when reading hive partitions.

---

## 3. Parquet reader (untrusted input)

Crafted files are in `/tmp/cbh-scratch-pq/files/`.

### P1 — DELTA_LENGTH_BYTE_ARRAY: memcpy with an attacker-controlled length (High, CONFIRMED by ASan)
- **File:** `extension/parquet/column_reader.cpp:680-681` (`PrepareDeltaLengthByteArray`)
- **Defect:** `memcpy(result_data, buffer.ptr, length_data[i]);` runs before `buffer.inc()`, so the bounds check happens after the copy.
- **Repro:** `SELECT * FROM 'd_50000000.parquet'` → ASan `READ of size 50000000 … memcpy`, then SIGSEGV.
- **Fix:** call `buffer.available(length_data[i])` before the memcpy.

### P2 — DELTA_BYTE_ARRAY: suffix memcpy with an unchecked length (High, CONFIRMED by ASan)
- **File:** `extension/parquet/column_reader.cpp:714-715` (`PrepareDeltaByteArray`)
- **Repro:** `SELECT * FROM 'dba.parquet'` → ASan memcpy over-read.
- **Fix:** call `buffer.available(suffix_data[i])` before the memcpy.

### P3 — Dictionary index not bounds-checked (High, CONFIRMED by ASan)
- **File:** `extension/parquet/column_reader.cpp:766` (`StringParquetValueConversion::DictRead`: `return dict_strings[offset];`)
- **Same pattern elsewhere,** where only a `D_ASSERT` guards the index, so these are latent in release builds:
  - `templated_column_reader.hpp:19`
  - `column_reader.cpp:1124` (decimal)
  - `column_reader.cpp:1239` (UUID)
  - `column_reader.cpp:1299` (interval)
- **Repro:** `SELECT * FROM 'dict_oob.parquet'` (1-entry dictionary, index 100):
  ```
  AddressSanitizer: heap-buffer-overflow ... column_reader.cpp:766 in StringParquetValueConversion::DictRead
  ```
- **Fix:** validate each decoded index against the dictionary entry count (once per batch in `Offsets()`), and throw `InvalidInputException`.

### P4 — DELTA_BINARY_PACKED: `miniblocks_per_block == 0` → integer division by zero (Medium, CONFIRMED with assertions enabled)
- **File:** `extension/parquet/include/parquet_dbp_decoder.hpp:16-17`
- **Defect:** only a `D_ASSERT` protects `block_value_count / miniblocks_per_block`. Release builds raise SIGFPE.
- **Repro:** `SELECT * FROM 'dbp0.parquet'` → `INTERNAL Error: Assertion … miniblocks_per_block > 0`.
- **Fix:** throw `InvalidInputException` when the value is 0, or when `block_value_count % miniblocks_per_block != 0`.

---

## 4. Main / pragma / config / CLI / export

### M1 — `PRAGMA storage_info` builds SQL with an unescaped argument → SQL injection (Medium, CONFIRMED)
- **File:** `src/function/pragma/pragma_queries.cpp:184`
- **Defect:**
  - `StringUtil::Format("SELECT * FROM pragma_storage_info('%s');", value.ToString())`. Siblings such as `PragmaTableInfo` and `PragmaShow` use `KeywordHelper::WriteQuoted`.
  - A table named `a'b` can't be inspected.
  - A crafted argument runs arbitrary extra statements.
- **Repro:**
  ```sql
  CREATE TABLE t(i INT);
  PRAGMA storage_info('t''); CREATE TABLE pwned(i INT); --');
  SELECT table_name FROM duckdb_tables();   -- pwned, t
  CREATE TABLE "a'b"(i INT); PRAGMA storage_info('a''b');   -- Parser Error
  ```
- **Fix:** `StringUtil::Format("SELECT * FROM pragma_storage_info(%s);", KeywordHelper::WriteQuoted(name, '\''))`.

### M2 — IMPORT DATABASE invalidates the whole database if load.sql contains a non-COPY statement (Medium, CONFIRMED)
- **File:** `src/function/pragma/pragma_queries.cpp:153-156`
- **Defect:**
  - Each statement in load.sql is assumed to be a COPY: `D_ASSERT(type == COPY_STATEMENT)` followed by `Cast<CopyStatement>()`.
  - Release builds throw `InternalException` from `Cast`. `Exception::InvalidatesDatabase(INTERNAL)` is true, so the whole instance becomes unusable.
  - A malformed or hostile export directory is enough to cause this denial of service.
- **Repro:** create `imp/schema.sql` containing `CREATE TABLE t(i INT);` and `imp/load.sql` containing `SELECT 42;`, then run `IMPORT DATABASE 'imp';` → `INTERNAL Error: Assertion triggered … pragma_queries.cpp line 155`.
- **Fix:** check `statement_p->type` and throw a user-facing `InvalidInputException("load.sql may only contain COPY statements")`.

### M3 — `memory_limit` / `max_temp_directory_size` parse overflow wraps to 0 bytes (Medium, CONFIRMED)
- **File:** `src/main/config.cpp:399` (`return (idx_t)multiplier * limit;`)
- **Defect:** the product is a `double`. Converting a value ≥ 2^64 (or `inf`) to `idx_t` is undefined behaviour; on x86 it yields 0. A memory limit of 0 makes every allocation fail.
- **Repro:**
  ```sql
  SET memory_limit='1e300TB'; SELECT current_setting('memory_limit');                 -- "0 bytes"
  SET memory_limit='18446744073709551616B'; SELECT current_setting('memory_limit');   -- "0 bytes"
  ```
  After this, the CLI aborts on the next query (see M5).
- **Fix:** if `limit * multiplier >= 2^64` (or the value is not finite), throw or clamp to `NumericLimits<idx_t>::Maximum()`.

### M4 — Unknown-unit error message never shows the unit (Low, CONFIRMED)
- **File:** `src/main/config.cpp:396`
- **Defect:** `ParserException("Unknown unit for memory_limit: %s …")` is called without the `unit` argument, so the user sees a literal `%s`. The message also says "unites" instead of "units".
- **Fix:** pass `unit` as the format argument.

### M5 — CLI duckbox rendering doesn't catch exceptions → process abort (Medium, CONFIRMED)
- **File:** `tools/sqlite3_api_wrapper/sqlite3_api_wrapper.cpp:270-284` (`duckdb_shell_sqlite3_print_duckbox`)
- **Defect:** `BoxRenderer::ToString` allocates a `ColumnDataCollection` through the buffer manager. Any exception it throws (out-of-memory, interrupt, …) crosses into the C shell, causing `std::terminate` and `abort()`.
- **Repro:**
  ```sh
  duckdb -c "SET memory_limit='0B'; SELECT 1;"
  # terminate called after throwing an instance of 'duckdb::OutOfMemoryException'
  ```
  gdb backtrace: `EvictBlocksOrThrow` ← `ColumnDataAllocator::AllocateBlock` ← `BoxRenderer::FetchRenderCollections` ← `duckdb_shell_sqlite3_print_duckbox`.
- **Fix:** wrap the body in `try { … } catch (std::exception &ex) { store the error; return nullptr; }`, and handle `nullptr` in `shell.c`.

### M6 — EXPORT DATABASE generates SQL that can't be imported (Medium, CONFIRMED)
- **Files:**
  - `src/include/duckdb/parser/parsed_data/create_schema_info.hpp:29-47`. The schema name is not quoted. `"CREATE SCHEMA x IF NOT EXISTS;"` and `"… ON CONFLICT INSERT OR REPLACE;"` are not valid SQL.
  - `src/catalog/catalog_entry/sequence_catalog_entry.cpp:110`. `ss << name;` is unquoted and has no schema.
  - `src/catalog/catalog_entry/type_catalog_entry.cpp:39`. No schema qualification.
  - Table columns whose type is a user ENUM type are exported as anonymous `ENUM(...)`, so the link to the type is lost.
- **Repro:**
  ```sql
  CREATE SCHEMA "s'x"; CREATE TABLE "s'x"."t'1"(i INT); EXPORT DATABASE 'exp';
  -- schema.sql contains: CREATE SCHEMA s'x;
  IMPORT DATABASE 'exp';   -- Parser Error: syntax error at or near "'x; ..."

  CREATE SCHEMA s; CREATE TYPE s.mood AS ENUM('a'); CREATE SEQUENCE s.seq; EXPORT DATABASE 'exp3';
  -- schema.sql: "CREATE TYPE mood ..." / "CREATE SEQUENCE seq ..."; after IMPORT, mood lives in schema main
  ```
- **Fix:**
  - Use `KeywordHelper::WriteOptionallyQuoted` and qualify every name with its schema.
  - Emit `CREATE SCHEMA IF NOT EXISTS <name>`.
  - Export column types by type name when the type is a catalog type.

### M7 — String results longer than 4 GiB are silently truncated (Medium, CONFIRMED)
- **Files:**
  - `src/include/duckdb/common/types/string_type.hpp:39`: `string_t(const char*, uint32_t len)` takes a `uint32_t`.
  - Callers build `std::vector<char>` buffers of arbitrary size and pass `result.size()` (an `idx_t`). Examples: `src/core_functions/scalar/string/repeat.cpp:22`, `pad.cpp:79/102`.
- **Defect:** the length is implicitly narrowed modulo 2^32, so the result is a short, wrong string with no error.
- **Repro:**
  ```sql
  SELECT length(repeat('abcdefghijklmnop', 268435457));   -- 16 (expected 4294967312 or an error)
  ```
- **Fix:** add a checked constructor or helper that throws `OutOfRangeException` when `len > NumericLimits<uint32_t>::Maximum()`. In `repeat`, check `size_str * cnt` up front; that also avoids allocating many GB first.

### Minor (Low)
- **JSON path parser:**
  - **File:** `extension/json/json_common.cpp:55-78` (`ReadInteger`).
  - **Defect:** after 19 digits the loop stops without having seen `]`, yet it reports success. The next character is then skipped as if it were the closing bracket. So the malformed path `'$[00000000000000000012'` is accepted as `$[1]`.
  - **Fix:** after the loop, require `ptr != end && *ptr == ']'`.
- **`CreateTypeInfo::ToString`:**
  - **File:** `src/parser/parsed_data/create_type_info.cpp:34`.
  - **Defect:** enum values are concatenated without escaping `'`. The function also asserts ENUM-only.
  - **Status:** latent; no caller is reachable from SQL today.

---

## 5. Catalog / transactions / relation API

### C1 — `CREATE … IF NOT EXISTS` that does nothing still registers dependencies → later DROP cascades to unrelated objects (High, CONFIRMED)
- **File:** `src/catalog/catalog_set.cpp:~202` (`CatalogSet::CreateEntry`)
- **Defect:**
  - `DependencyManager::AddObject` runs before the duplicate-name check and before the lock is taken.
  - When the entry already exists (IF NOT EXISTS, or an ignored duplicate error), the dependency edges are still committed.
- **Repro 1** (`/tmp/cbh-scratch-txn/idx.sql`):
  ```sql
  CREATE TABLE t1(i INTEGER); CREATE TABLE t2(i INTEGER);
  CREATE UNIQUE INDEX idx ON t1(i); INSERT INTO t1 VALUES (1);
  CREATE UNIQUE INDEX IF NOT EXISTS idx ON t2(i);   -- no-op
  DROP TABLE t2;                                    -- silently drops idx on t1
  INSERT INTO t1 VALUES (1);                        -- succeeds: t1 now has duplicate 1,1 despite the UNIQUE index
  ```
- **Repro 2** (`seq.sql`):
  ```sql
  CREATE SEQUENCE s; CREATE TABLE t(i INT); INSERT INTO t VALUES (42);
  CREATE TABLE IF NOT EXISTS t(i INTEGER DEFAULT nextval('s'));
  DROP SEQUENCE s CASCADE;   -- drops table t and its data
  ```
- **Fix:** do the existence and conflict check (under the catalog lock) before `AddObject`. Alternatively, add the dependencies only once the entry is actually created.

### C2 — Cascaded DROP of a table bypasses foreign-key bookkeeping (High, reported CONFIRMED by reviewer)
- **Files:**
  - `src/catalog/dependency_manager.cpp:394`: calls `CatalogSet::DropEntry` directly.
  - `src/catalog/catalog_entry/duck_schema_entry.cpp:290-302`: the FK cleanup that gets skipped.
- **Impact:** FK links are left inconsistent. Effects include an infinite loop in `ReorderTableEntries` at checkpoint, lost committed data on WAL replay, and tables that can't be dropped.
- **Repros:** `/tmp/cbh-scratch-txn/fk.sql`, `fk2.sql`.
- **Fix:** route cascaded table drops through `SchemaCatalogEntry::DropEntry`, or run the FK alter logic there too.

### C3 — `Relation::Insert(const vector<vector<Value>>&)` targets the wrong schema (Medium, reviewer CONFIRMED)
- **File:** `src/main/relation.cpp:259`
- **Defect:** it uses `GetAlias()` (the bare table name), which resolves against the default schema.
- **Fix:** pass the relation's schema and table name.

### C4 — Failed commit leaves state inconsistent (Low, reviewer CONFIRMED)
- **Defects:**
  - `UndoBuffer::IteratorState` is uninitialized (`src/include/duckdb/transaction/undo_buffer.hpp:24`) and is read on a failed commit (`duck_transaction.cpp:121`).
  - Row-count drift is permanent after a failed commit (`commit_state.cpp:350`, `data_table.cpp:838`).
- **Fix:** value-initialize the iterator state, and roll back cardinality changes on commit failure.

### C5 — `COMMENT ON TABLE` fails for any table that has dependents (Low, reviewer CONFIRMED)
- **File:** `src/catalog/catalog_set.cpp:358`
- **Defect:** `SET_COMMENT` goes through `AlterObject`'s dependents check.
- **Fix:** exempt comment-only alters from that check.

---

## 6. C API (`src/main/capi/`) — reviewer findings, CONFIRMED with small C programs (`/tmp/cbh-scratch-capi/`)

**Main pattern:** C++ exceptions escape `extern "C"` functions, so the process ends in `std::terminate` instead of getting an error code.

- **A1 (High):** the legacy materialized result is half-built when one column has an unsupported type (UUID/ENUM/LIST/STRUCT/MAP/UNION/BIT).
  - Later columns are left with `__deprecated_nullmask == NULL`, so `duckdb_value_is_null` and `duckdb_value_*` dereference NULL.
  - Locations: `result-c.cpp:261-263, 348-353`; `value-c.cpp:177`.
- **A2 (High):** on early errors, `duckdb_execute_prepared` and `duckdb_execute_prepared_streaming` leave `out_result` uninitialized. A later `duckdb_destroy_result` then touches garbage. `prepared-c.cpp:331-344`.
- **A3 (High):** `duckdb_prepared_statement_type` dereferences NULL for a failed prepare. `prepared-c.cpp:350-357`.
- **A4 (High):** `duckdb_enum_dictionary_value` has no bounds check on `index`, giving an OOB read. `logical_types-c.cpp:185-193`.
- **A5 (High):** if a streaming result errors mid-stream, the legacy API loops over the types of an empty error result and ends in terminate. `result-c.cpp:323-337`.
- **A6 (Medium):** `duckdb_value_*` return 0/NULL for TIMESTAMP_TZ, TIMESTAMP_S/MS/NS and TIME_TZ because those switch cases are missing. `capi/cast/generic.hpp:26-72`.
- **A7 (Medium):** legacy decimal data for negative INT16/32/64-backed decimals has the wrong sign (`upper = 0`). `result-c.cpp:106-115`.
- **A8 (Medium):** `duckdb_result_chunk_count` and `duckdb_result_get_chunk` abort on an error result. `result-c.cpp:501-529`.
- **A9 (Medium):** `duckdb_prepare_extracted_statement` aborts when an index is reused (the unique_ptr was already moved out) and dereferences NULL `extracted_statements`. `prepared-c.cpp:47-54`.
- **A10 (Medium):** out-of-range struct/union child indexes abort instead of returning NULL. `logical_types-c.cpp:439-485`.
- **A11 (Medium):** `duckdb_arrow_scan` checks `== DuckDBError` instead of `!= 0`. It also leaks producer schemas. `arrow-c.cpp:195-203, 284-292`.
- **A12 (Medium):** `duckdb_to_date` and `duckdb_to_timestamp` abort on invalid input. `datetime-c.cpp:25-29, 83-90`.
- **A13 (Low):** several smaller defects:
  - `duckdb_bind_*` loses the out-of-range error message.
  - `duckdb_get_int64` mutates the caller's value.
  - `duckdb_append_data_chunk` doesn't validate the column count.
  - `deprecated_materialize_result` returns `DuckDBError` from a `bool` function, so the error reads as success.
  - `duckdb_decimal_to_double` with `scale > 38` reads past `DOUBLE_POWERS_OF_TEN`.
  - `duckdb_register_table_function` lets catalog exceptions escape.
- **General fix:** wrap every C entry point in `try/catch(...)` and return `DuckDBError`; initialize out-parameters on entry; add bounds checks.

---

## 7. Execution / optimizer / planner

| # | File:line | Defect | Repro | Fix |
|---|-----------|--------|-------|-----|
| E1 (High) | `src/execution/window_segment_tree.cpp:356,363,368,967,1060-1062` | EXCLUDE sub-frames (left/right of the current row or peer group) are not clipped to `[begin,end)`; TIES always adds the current row | `SELECT x, sum(x) OVER (ORDER BY x ROWS BETWEEN 2 FOLLOWING AND 3 FOLLOWING EXCLUDE CURRENT ROW) FROM range(4) t(x)` → x=0 gives 6 (expected 5) | Clamp: `left_end = min(end, cur_row/peer_begin)`, `right_begin = max(begin, cur_row+1/peer_end)`; add the TIES row only if it is inside the frame |
| E2 (High) | `src/execution/window_executor.cpp:1460,1496,1533` | FIRST/LAST/NTH_VALUE: `continue` on an empty frame skips `ResetMask`, so excluded rows stay masked | `first_value(x) OVER (ORDER BY x ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING EXCLUDE CURRENT ROW)` → NULL at x=1 (expected 0) | Reset the mask before `continue` |
| E3 (High) | `src/execution/physical_plan/plan_window.cpp:25` | FIRST_VALUE with no PARTITION/ORDER is always streamed, ignoring the frame | `first_value(x) OVER (ROWS BETWEEN 1 FOLLOWING AND 2 FOLLOWING)` over range(4) → 0,0,0,0 (expected 1,2,3,NULL) | Stream only for UNBOUNDED PRECEDING … CURRENT ROW / UNBOUNDED FOLLOWING |
| E4 (High) | `src/execution/operator/join/physical_asof_join.cpp:36,44,50` | `null_sensitive` stores `lhs_orders.size()` instead of the condition index, so a NULL inequality key is not filtered when an equality condition comes first | l=(1,NULL),(1,5); r=(1,1,10),(1,3,30); `l ASOF JOIN r ON l.k=r.k AND l.t>=r.t` → `(1,NULL,30)` returned | Push `cond_idx` |
| E5 (High) | `src/optimizer/statistics/operator/propagate_join.cpp:119-122` | ANTI join whose condition is always true by stats is replaced by an empty result, but an ANTI join returns all left rows when the right side is empty | `SELECT count(*) FROM l ANTI JOIN (SELECT * FROM r WHERE y%2=0) r2 ON l.x>r2.y` → 0 (expected 2) | Don't fold; or keep the left side when the right side is empty |
| E6 (High) | `src/optimizer/rule/move_constants.cpp:145-148` | In the `*` branch, a failed constant cast folds any comparison to FALSE | `CREATE TABLE t AS SELECT x::TINYINT x FROM range(3) r(x); SELECT count(*) FROM t WHERE x * -1 > -128` → 0 (expected 3) | Only fold for `=` (and `<>`); otherwise return nullptr |
| E7 (Medium) | `src/optimizer/rule/comparison_simplification.cpp:41`, `in_clause_simplification_rule.cpp:27` | `try_cast` is ignored when unwrapping the cast, so NULL becomes FALSE | `TRY_CAST(1000::BIGINT AS TINYINT)=1` → false (expected NULL) | Bail out when `try_cast` is set |
| E8 (High) | `src/planner/expression/bound_cast_expression.cpp:151-176` | VARCHAR→TIMESTAMP is considered invertible, so the comparison is rewritten to a string compare | rows '2020-01-01' and '2020-01-01 00:00:00'; `WHERE CAST(s AS TIMESTAMP) = TIMESTAMP '2020-01-01'` → 1 row (expected 2) | Casts from VARCHAR are never invertible |
| E9 (High) | `src/function/table/range.cpp:116`; used by `sum.cpp:93-123` | Cardinality is `(end-start)/increment` (truncated), so SUM stats pick the no-overflow int64 path | `SELECT sum(c) FROM (SELECT 4611686018427387904::BIGINT c FROM range(0,3,2))` → -9223372036854775808 | Use ceiling division |
| E10 (Medium) | `src/optimizer/rule/regex_optimizations.cpp:94,135` | `.` becomes the byte-wise `_`; `^`/`$` in the middle of a pattern are dropped | `regexp_matches(s,'a$b')` with s='ab' → true (expected false) | Don't convert `.` for non-ASCII input; only allow anchors at the ends |
| E11 (Medium) | `src/execution/window_executor.cpp:1413, 439/446/486/492` | NULL LEAD/LAG offset and NULL ROWS frame offset are read without `CellIsNull` | `lag(x, o)` with `o` NULL → returns x | Return NULL / raise an error for NULL offsets |
| E12 (Low) | `src/planner/binder/query_node/bind_select_node.cpp:100-105`; `bind_window_expression.cpp` | Negative OFFSET is accepted with LIMIT %; negative RANGE offsets are accepted | `SELECT * FROM range(10) LIMIT 50% OFFSET -2` → 0 rows | Reject negative values |
| E13 (Medium, SUSPECTED) | `src/optimizer/statistics/expression/propagate_cast.cpp:6-21` | Stats are cast with the default cast set, not the session (ICU) casts; `TIMESTAMPTZ→DATE` stats can be wrong in non-UTC time zones and prune rows | n/a (no ICU in the build) | Skip stats propagation for casts that aren't the default |

---

## 8. Casts and types (`src/common`, `src/function/cast`, strftime)

| # | Sev | File:line | Defect | Repro → got (expected) | Fix |
|---|-----|-----------|--------|-----------------------|-----|
| T1 | Medium | `src/include/duckdb/common/operator/integer_cast_operator.hpp:105-114` | Negative exponent: the loop stops when result==0 and keeps a stale rounding digit | `'5e-5'::INTEGER` → 1 (0) | `if (e < 0) state.decimal = 0` after the loop |
| T2 | Medium | `src/common/operator/cast_operators.cpp` ~1836 `DecimalCastOperation::HandleExponent` | Same as T1 for decimals | `'5e-3'::DECIMAL(4,0)` → 1 (0) | Clear `round_up` when breaking early |
| T3 | Medium/High | `cast_operators.cpp` ~1885-1930 `Finalize`/`RoundUpResult` | Rounding can exceed the declared width | `'999.99'::DECIMAL(4,1)` → 1000.0 (error) | Check `abs(result) < 10^width` after rounding |
| T4 | Medium | `cast_operators.cpp` `TruncateExcessiveDecimals` | `state.result /= 10.0` uses double division | `'1.99999999999999999'::DECIMAL(10,0)` → 3 (2) | Integer division |
| T5 | Medium | `cast_operators.cpp:2393` | FLOAT→DECIMAL scales in double, then narrows back to float | `1.5::FLOAT::DECIMAL(18,10)` → 1.5000000512 | Cast from the double |
| T6 | Medium | `cast_operators.cpp:1540-1567` | `HugeIntCastData::digits` is `uint8_t` and wraps on trailing zeros | `('999999999999999999'||repeat('0',256))::HUGEINT` → 999999999999999999 (overflow error) | Make it `idx_t` |
| T7 | Low | `cast_operators.cpp` ~1569-1690 | HUGEINT parse fails on many decimal digits | `'1.111…(41 digits)'::HUGEINT` → error (1) | Cap the number of accumulated decimals |
| T8 | Medium | `src/common/types/interval.cpp:141-145` | A negative time part negates all fields accumulated so far | `'1 hour -00:30:00'::INTERVAL` → -01:30:00 (00:30:00) | Negate only the time part |
| T9 | Medium | `src/function/scalar/operators/multiply.cpp:29-34` | INTERVAL × BIGINT narrows the multiplier to int32 | `INTERVAL '1 day' * 4294967297` → 1 day (error) | Multiply in int64, then range-check |
| T10 | Medium | `src/include/duckdb/common/types/interval.hpp:164-177` | `Normalize` doesn't reconcile fields with mixed signs, so comparisons are wrong | `(INTERVAL '1 day' - INTERVAL '86399999999 us') > INTERVAL '2 us'` → true (false) | Compare total spans in 128-bit |
| T11 | Medium | `src/common/types/bit.cpp:182` | `if (size > 2)` should be `> 1`, so byte 1 is left uninitialized | `'0000000011111111'::BIT::BLOB` → `\x00\x00` (`\x00\xFF`) | `size > 1` |
| T12 | Medium | `bit.cpp:237-269` | `bit_position` doesn't backtrack on a partial match | `bit_position('01'::BIT,'001'::BIT)` → 0 (2) | Restart at start+1, or use KMP |
| T13 | Low | `src/function/scalar/strftime_format.cpp:38-39, 262` | `%G` is fixed-width 4 and unsigned | `strftime(DATE '12345-06-01','%G')` → 2345 | Format like `%Y` |
| T14 | Medium | `subtract.cpp:53-55`, `interval.cpp:231,278-280,458-460` | Signed overflow / negation of INT_MIN (UB) in interval arithmetic | `INTERVAL '2147483647 months' - INTERVAL '-1 month'` → UBSan | Use checked operators |
| T15 | Medium | `src/common/types/hugeint.cpp:67`; `abs.hpp:24-27`; `arithmetic.cpp:435-449` | abs/negate of HUGEINT min overflows; `CanNegate` uses an unspecialized `numeric_limits<hugeint_t>` | `abs(HUGEINT_MIN)` → UBSan | Specialize the checks and throw |
| T16 | Medium | `strftime_format.cpp:760-763, 805-817` | strptime skips whitespace without a size check, so it reads past the end of the input | `try_strptime(repeat(' ',4096+i),'%Y')` → out-of-bounds read (gdb) | `while (size > 0 && isspace(*data))`; check `pos < size` |
| T17 | Low, SUSPECTED | `hugeint.cpp:57` | `POWERS_OF_TEN[39]` overflows hugeint, so the table holds garbage (currently harmless) | – | Don't use the entry |

---

## 9. Scalar / list / aggregate functions

These come from my own edge-case battery, run after the functions reviewer was cut off by a rate limit. Inputs are in `/tmp/cbh-scratch-main/fn/q2.txt`.

### FN1 — `list_resize` / `array_resize` with a huge size → integer overflow in vector sizing → heap-buffer-overflow WRITE (High, CONFIRMED by ASan)
- **Files:**
  - `src/function/scalar/list/list_resize.cpp:36-53`
  - `src/common/types/vector_buffer.cpp:66-72` (`VectorListBuffer::Reserve`)
  - `src/common/types/vector.cpp:357-363` (`Vector::Resize`)
- **Defect:**
  - `list_resize` sums the user-supplied sizes into `new_child_size` without any limit or overflow check, then calls `ListVector::Reserve`.
  - `Reserve` computes `NextPowerOfTwo(2^63-1) = 2^63`.
  - `Vector::Resize` allocates `new_size * type_size` bytes, which wraps to a tiny value (2^63 × 4 → 0 mod 2^64). It then does a `memcpy` of `cur_size * type_size` bytes into that allocation.
- **Repro:**
  ```sql
  SELECT list_resize([1,2], 9223372036854775807);
  -- AddressSanitizer: heap-buffer-overflow WRITE of size 8192
  --   #2 Vector::Resize vector.cpp:363  #3 VectorListBuffer::Reserve vector_buffer.cpp:72  #4 ListResizeFunction list_resize.cpp:53
  SELECT array_resize([1], 18446744073709551615);  -- INTERNAL assertion new_capacity >= to_reserve
  ```
- **Fix:**
  - Validate sizes in `list_resize` (reject sizes above a sane maximum, and use checked addition when summing).
  - In `Vector::Resize` and `Reserve`, check `new_size * type_size * multiplier` for overflow and throw `OutOfRangeException`. `NextPowerOfTwo` must not be applied to values above 2^63.

### FN2 — SUM/AVG over HUGEINT and DECIMAL(38) overflow silently (Medium, CONFIRMED by UBSan)
- **Files:**
  - `src/common/types/hugeint.cpp:797` (unchecked `hugeint_t::operator+`)
  - Used by `src/include/duckdb/core_functions/aggregate/sum_helpers.hpp:59` (`RegularAdd::AddNumber`)
- **Defect:** the aggregation adds with the unchecked operator. A release build wraps to a large negative number with no error; BIGINT sums, by contrast, are widened.
- **Repro:**
  ```sql
  SELECT sum(x) FROM (VALUES (170141183460469231731687303715884105727::HUGEINT),(1::HUGEINT)) t(x);
  -- UBSan: hugeint.cpp:797:9 signed integer overflow
  SELECT sum(x) FROM (VALUES (99999999999999999999999999999999999999::DECIMAL(38,0)),
                             (99999999999999999999999999999999999999::DECIMAL(38,0))) t(x);   -- same
  ```
- **Fix:** use `Hugeint::TryAddInPlace` in the HUGEINT sum path and throw `OutOfRangeException("Overflow in HUGEINT addition")`.

### FN3 — `repeat()` table function with a negative count runs (almost) forever (Medium, CONFIRMED)
- **File:** `src/function/table/repeat.cpp:29`
- **Defect:** `inputs[1].GetValue<int64_t>()` is stored into an `idx_t target_count` without a sign check. -1 becomes 2^64-1 rows, and the cardinality estimate is broken as well.
- **Repro:** `SELECT count(*) FROM (SELECT * FROM repeat(1, -1) LIMIT 5000000);` → 5000000 (expected 0, or an error).
- **Fix:** throw a `BinderException` if the count is negative.

### FN4 — `bit_count(HUGEINT)` result overflows TINYINT (Medium, CONFIRMED)
- **File:** `src/core_functions/scalar/math/numeric.cpp:239-240`. The return type is `LogicalType::TINYINT` with `int8_t`.
- **Repro:** `SELECT bit_count(-1::HUGEINT);` → `-128` (expected 128).
- **Fix:** return SMALLINT (or BIGINT) for the HUGEINT/UHUGEINT overloads.

### FN5 — `list_cosine_similarity` returns -1.0 for zero vectors (Medium, CONFIRMED)
- **File:** `src/core_functions/scalar/list/list_cosine_similarity.cpp:58-61`
- **Defect:** for an all-zero vector, `0 / (0 * x)` is NaN. `std::max(-1, std::min(NaN, 1))` evaluates to -1, so the function reports "perfectly opposite", which is the worst possible similarity, instead of undefined.
- **Repro:** `SELECT list_cosine_similarity([0.0, 0.0], [1.0, 1.0]);` → `-1.0`.
- **Fix:** return NaN or NULL (or throw) when either norm is 0, and don't run NaN through the clamp.

### FN6 — Signed overflow (UB) with INT64_MIN arguments (Low, CONFIRMED by UBSan)
- **Locations:**
  - `src/function/scalar/list/list_select.cpp:14`: `GetValue<int64_t>() - 1`.
  - `src/core_functions/scalar/string/repeat.cpp:17`: `remaining--` on INT64_MIN.
- **Repro:**
  - `SELECT list_select([1,2,3], [-9223372036854775808]);`
  - `SELECT repeat('x', -9223372036854775808);`
- **Fix:** check `<= 0` before decrementing, or compute in unsigned arithmetic.

### FN7 — `list_inner_product` asserts the child vectors are FLAT (Low, CONFIRMED)
- **File:** `src/core_functions/scalar/list/list_inner_product.cpp:18-19`
- **Repro:** `SELECT list_inner_product([]::DOUBLE[], []::DOUBLE[]);` → `INTERNAL Error: Assertion … FLAT_VECTOR`. In builds with assertions this invalidates the database.
- **Fix:** call `Flatten` or `ToUnifiedFormat` on the child vectors instead of asserting.

### FN8 — `fsum`/`favg` (Kahan) return NaN where the plain sum overflows to inf (Low, CONFIRMED)
- **Repro:** `SELECT fsum(x) FROM (VALUES (1e308),(1e308),(-1e308)) t(x);` → `-nan`.
- **Defect:** the compensation term computes `inf - inf`.
- **Fix:** skip compensation once the running sum is non-finite.

### Checked and found no problem
- substring/left/right extremes and range/generate_series extremes.
- gcd/lcm/abs/shift overflow checks.
- base64/hex/bin decoding; chr/unicode; LIKE/GLOB/ILIKE edge patterns; regexp options.
- grapheme functions; translate/replace/trim with UTF-8.
- quantile/mode/arg_min/histogram/bitstring_agg parameter validation.
- time_bucket/make_date/to_years range checks.
- The CSV sniffer on short/ragged/quoted inputs (no sanitizer reports).

---

## Coverage notes
- **Reviewed in depth:** storage compression (differential fuzz harness by a reviewer), gzip/compressed FS, read_file, CSV writer, partitioned COPY, pragma queries, config parsing, EXPORT/IMPORT, CLI renderer, parquet decoders, C API, catalog/dependency manager, window/ASOF/optimizer rules, casts/intervals/bit/strftime, JSON path parsing, ART key encoding, Arrow appender.
- **Not reviewed (or only lightly):** ICU, httpfs, JSON reader internals, WAL replay internals, and the CSV state-machine scanner beyond black-box tests. Scalar, list and aggregate functions were covered only by the black-box battery in section 9; no line-by-line review.
- **Totals:** about 95 defects reported. Most are CONFIRMED by a runtime repro. Findings marked "by reviewer" were reproduced by a sub-agent; I re-ran a sample of them (RLE, parquet ×3, catalog ×2, window, ASOF, ANTI join, MoveConstants, range/SUM, six cast/type items), and all of those reproduced.
