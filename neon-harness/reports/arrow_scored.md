# arrow scoring (Gemini 4 Neon in Amp, base per regions/arrow.json, 47 bugs)

Agent report: 269 findings (62 Critical / 134 High / 67 Medium / 6 Low).
Parasoft published: region 23.4%, strict 8.5%.
Regions file verified: n_bugs = 47 (one bug, arrow-4c84f1faa214, has an empty region: not matchable).

All maintainer fixes below were verified by parent-blob prefix match against the oracle blob AND by
checking that the commit's diff removes/changes exactly the oracle's removed lines at the oracle's
old_start locations.

## Accepted matches (11 region, 10 strict of 47 benchmark bugs; 10 distinct findings)

| bug_id | defect (maintainer fix) | Neon finding | verdict | region | strict |
|---|---|---|---|---|---|
| arrow-1a3fe19e8bf0 | e9ec38396e GH-45266: Abort ignores ALL_TASKS_STARTED; aborted_ made atomic; ExecuteMore marks current task finished (oracle path compute/exec/task_util.cc, fix path acero/task_util.cc after file rename; all 10 oracle hunk old_starts match the diff hunks exactly) | ARROW-032 TaskSchedulerImpl::Abort ignores TaskGroupState::ALL_TASKS_STARTED, causing UAF and double callback; related races in StartTaskGroup and ExecuteMore | exact same defect, all three claims fixed in one commit | yes | yes |
| arrow-2fd06f68a200 | ca8a194bd1 GH-50063: inserts `RETURN_NOT_OK(CheckTensorStridesValidity(data, shape, tmp_strides, type));` inside the strides-empty branch of ValidateTensorParameters (oracle hunk is insertion-only at 216/6) | ARROW-018 Tensor::Make / ValidateTensorParameters skips buffer-size validation whenever strides is empty (default row-major) | exact same defect (pure insertion, so the bug's strict set is empty: strict not countable) | yes | no (strict set empty) |
| arrow-9f952a8a44b5 | 0f747311a4 GH-36311: `max_slice_codepoints = (opt.stop - opt.start + opt.step - 1) / opt.step` replaced by clamped `stop` plus `Negate()` helper for `-opt.stop` overflows | ARROW-026 Signed int64_t overflow in utf8_slice_codeunits and binary_slice (MaxCodeunits) causes 0-byte / undersized allocation and buffer overflow | exact same defect; ascii (binary_slice) span not touched by this commit but the utf8 claim at the matched lines is the fixed defect | yes | yes |
| arrow-369f913202de | 9cb051b723 GH-39784: removes `llvm::Constant* ptr_int_cast = types->i64_constant((int64_t)(dex_instance.in_holder().get()));` in VisitInExpression<DecimalScalar128>, replaces with `LoadVectorAtIndex(arg_holder_ptrs_, ...)` loaded in entry block (cached-object-code UAF) | ARROW-046 Use-after-free of InHolder<DecimalScalar128> baked as raw pointer constant into cached LLVM object code | exact same defect | yes | yes |
| arrow-f5b99cc3814b | 39125bac39 GH-50355: `char_len += 1;` in utf8_length_ignore_invalid replaced by `char_len = j; break;` (invalid glyph no longer swallows following bytes) | ARROW-054 Heap buffer overflow, unbounded OOB read, and negative *out_len in lpad/rpad and utf8_length_ignore_invalid | bundled finding; the utf8_length_ignore_invalid OOB-read claim at the matched lines (span 199-216) is the fixed defect; the lpad/rpad and *out_len claims were not part of this fix | yes | yes |
| arrow-98c930cfb2f6 | e2e3a9df28 GH-35423: `-  if (uncompressed_len > static_cast<int>(decompression_buffer_->size())) { ... Resize(uncompressed_len, /*shrink_to_fit=*/false)); }` replaced by unconditional `PARQUET_THROW_NOT_OK(decompression_buffer_->Resize(uncompressed_len, ...))` so the buffer is forced smaller | ARROW-071 SerializedPageReader::DecompressIfNeeded never shrinks/slices decompression_buffer_ and discards Decompress() actual byte count | same defect at the matched lines ("never shrinks decompression_buffer_" is exactly the guard the maintainer removed); borderline: the "discards Decompress() actual byte count" half of the claim is broader than the one-line fix | yes | yes (borderline) |
| arrow-c1cc8abccb1b | 281122c018 GH-41306: CopyBitmap of the null bitmap in BinaryToBinaryCastExec wrapped in `if (input.buffers[0].data != NULLPTR)` | ARROW-113 Null pointer dereference and signed int32_t offset overflow when casting sliced FixedSizeBinary to Binary/String | null-deref half of the claim is exactly the fixed defect (offset-overflow half not part of the fix) | yes | yes |
| arrow-67205dcd9782 | d66780d90c GH-38879: `- if (literal_pattern == nullptr) {` to `+ if (literal_suppress_errors == nullptr) {` in ToDateHolder::Make | ARROW-177 Guaranteed null-pointer dereference in ToDateHolder::Make checking literal_pattern instead of literal_suppress_errors | exact same defect (1-line fix, 1-line claim) | yes | yes |
| arrow-eb9c7276cf24 | 05c8b222c4 GH-34086: DataPageV2 constructed with new `num_rows = static_cast<int32_t>(num_buffered_rows_)` instead of `num_values`; num_buffered_rows_ tracked alongside rows_written_ | ARROW-200 ColumnWriterImpl::BuildDataPageV2 writes num_values as num_rows, writes null_count=0 when stats disabled, and leaks a wasted CopySlice | bundled finding; the "writes num_values as num_rows" claim is exactly the fixed defect; null_count-when-stats-disabled and wasted-CopySlice claims were not part of this fix | yes | yes |
| arrow-479fccb220cc | 3dd8b66f0c GH-46841: DATE_TRUNC_FIXED_UNIT gains `millis >= 0 ? (millis / N) * N : ((millis - N + 1) / N) * N` | ARROW-254 Corrupted millisecond formatting (castVARCHAR_timestamp_int64) and forward truncation (date_trunc_*) on pre-1970 timestamps | bundled finding; the date_trunc_* claim is exactly the fixed defect | yes | yes |
| arrow-be576c6bbb37 | d436b238a9 GH-49454: castVARCHAR_timestamp_int64 rewritten with `EpochTimePoint tp(in); ... millis = tp.TimeOfDay().subseconds().count();` replacing `extract*` calls and `millis = in % MILLIS_IN_SEC` | ARROW-254 (same finding, second bug) | bundled finding; the castVARCHAR_timestamp corrupted-millisecond claim is exactly the fixed defect | yes | yes |

## Rejected line-overlaps (7 pair verdicts on 6 bugs)

- arrow-264e1ebbe40c / ARROW-007: fix e837f73b47 (GH-14923, "Fix DELTA_BINARY_PACKED problem on reading the last block with malford bit-width") moves bit-width validation from InitBlock into InitMiniBlock ("non-conformant bitwidth entries are allowed by the Parquet spec for extraneous miniblocks in the last block"). Neon claims signed int32 truncation / overflow on total_value_count_ and padding_bits in DeltaBitPack/DeltaLengthByteArray/DeltaByteArray decoders: a different defect in the same class. Line overlap only.
- arrow-48d0b45c48f0 / ARROW-112: fix 0980dbe330 (GH-35448, "Fix detection of %z in strptime format") removes the spurious `cur++;` inside the '%' branch of GetZone (double increment broke %%-escaped %z detection). Neon claims a size_t underflow in `cur < format.size() - 1` on an empty format string; that condition is untouched by the fix (the latent OOB read remains after it). Same function, real but different defect.
- arrow-5abdc0d1a217 / ARROW-097: fix 450b79379a (GH-37004, "Fix dropped child data when viewing/casting extension-typed fields") makes AccumulateLayouts and ViewDataImpl traverse the extension storage type's children. Neon claims ViewDataImpl OOB vector read in GetDictionaryView and undersized/misaligned null bitmap on sliced Struct views: different mechanism, overlap only because both hit data.cc lines 747/920.
- arrow-9a0cb740d8ac / ARROW-107: fix 3e0ca5b7fd (GH-37969) adds closed-file checks (`RETURN_NOT_OK(CheckClosed());` in parquet/arrow/writer.cc, `if (contents_) ... else throw ParquetException("Cannot get properties from closed file")` in file_writer.cc). Neon's finding is about the CSV writer (cpp/src/arrow/csv/writer.cc) on 0-length chunks; it matched only because the matcher compares file basenames and csv/writer.cc collides with parquet/arrow/writer.cc. Different subsystem entirely.
- arrow-9a0cb740d8ac / ARROW-108: same collision (csv/writer.cc 0-column schema claims vs parquet closed-file checks). Rejected.
- arrow-b831ede509b4 / ARROW-139: fix b868201da5 (GH-46420, "Fix DatasetWriter deadlock on writting batch greater than max_rows_queued") corrects the Throttle conditions: `values + current_value_ > max_value_` becomes `current_value_ >= max_value_` and `in_waiting_ + current_value_ <= max_value_` becomes `current_value_ < max_value_`. Neon claims DoWriteRecordBatch leaks rows_in_flight_throttle permits on open_files_throttle stall (that mechanism corresponds to a different upstream fix, f7286a9530 GH-38884, at dataset_writer.cc ~621-640, not to this bug's Throttle lines 61/78). Same deadlock theme, different root cause.

## Clear misses (36 bugs, incl. 1 not matchable)

arrow-0cc9fb2dd29f (file_parquet.cc), arrow-121fb8b54251 (scalar.cc), arrow-19465d9c4aac
(expression.cc), arrow-264e1ebbe40c (DeltaBitPack bit-width, rejected overlap above),
arrow-26f5542e1be5 (parquet metadata/statistics), arrow-2cdadc752c2e (expression_internal/registry),
arrow-3d2dc9c86ad0 (result.h), arrow-3e14973c5f12 (chunked_array.cc), arrow-40583d085a58
(ipc/writer.cc), arrow-48d0b45c48f0 (strptime GetZone, rejected overlap above),
arrow-4bbc9f6cd795 (scalar.cc), arrow-4c84f1faa214 (array_nested.cc; empty region, not matchable),
arrow-4e8d0cead54f (decimal_wrapper.cc), arrow-5a279df3fd5a (type.cc/range.h),
arrow-5abdc0d1a217 (ViewDataImpl, rejected overlap above), arrow-60dfbaf3519c (column_reader.cc),
arrow-624e0738ed5f (expression.cc), arrow-6cc9de91ea5e (reader_internal/schema.cc),
arrow-836fa5c90cf9 (gdv_string_function_stubs.cc), arrow-8a41d3fa0ac8 (vector_replace.cc),
arrow-8a6d1850de5a (ipc/metadata_internal.cc), arrow-8c472a2596ce (parquet schema.cc),
arrow-97c0b6198f30 (hash_aggregate.cc), arrow-97ed55fe5885 (value_parsing.h),
arrow-9a0cb740d8ac (parquet closed-file checks, rejected overlaps above),
arrow-a642ccf7200e (array/data.cc), arrow-a7cd3ba57ac2 (scalar_if_else.cc),
arrow-b4b15ce0d6ab (builder_dict.h/builder.cc), arrow-b831ede509b4 (DatasetWriter Throttle,
rejected overlap above), arrow-c844b43f97c5 (array/data.cc),
arrow-d0cd5512a992 (function_registry_string/string_ops.cc), arrow-d4e732abe1d1 (light_array),
arrow-d7a1dcf3bafd (expression.cc), arrow-db58ca99eaa0 (array_primitive.cc),
arrow-e4fc3a8e2c13 (parquet stream_reader.cc), arrow-eef26b83f5e8 (column_writer.cc).

## Score

- Neon: region 11/47 (23.4%), strict 10/47 (21.3%; one accepted finding counts region-only because
  its bug's oracle is insertion-only with an empty strict set; one accept tagged borderline)
- Parasoft: region 23.4%, strict 8.5%
- Novel findings: 259 of 269 findings did not accept any benchmark bug
  (10 findings accepted at least one bug: ARROW-018, ARROW-026, ARROW-032, ARROW-046, ARROW-054,
  ARROW-071, ARROW-113, ARROW-177, ARROW-200, ARROW-254)
