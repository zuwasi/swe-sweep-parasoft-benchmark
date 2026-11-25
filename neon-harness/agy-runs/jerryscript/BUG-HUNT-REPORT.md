# JerryScript Quality Review — Bug Hunt Report

**Repository:** JerryScript (`jerry-core/` and `jerry-ext/`)  
**Commit:** `5fdeb7c1d68e8c5209e186e1760bc703a723d588` (v2.2.0, February 2020)  
**Build used for dynamic verification:** Debug + ASan/UBSan (`es2015-subset` profile, snapshot save/exec enabled, `jerry-ext` enabled)

## Summary Table

| ID | Severity | Subsystem | One-line Title | Status |
|---|---|---|---|---|
| BUG-001 | Critical | Parser / Lexer | Heap buffer overflow in raw template literal containing escaped U+2028/U+2029 | CONFIRMED |
| BUG-002 | Critical | TypedArray | Heap buffer overflow & type confusion via `ArrayBuffer` `Symbol.species` in TypedArray constructor | CONFIRMED |
| BUG-003 | Critical | TypedArray | Use-after-free of element/index `ecma_value_t` in `TypedArray.prototype.filter` | CONFIRMED |
| BUG-004 | Critical | Snapshot API | Heap/stack buffer overflow in `jerry_get_literals_from_snapshot` when `is_c_format` is true | CONFIRMED |
| BUG-005 | High | RegExp | `memset` uses capture count instead of byte size in `ecma_regexp_replace_helper_fast` and ES5.1 `split` | CONFIRMED |
| BUG-006 | High | RegExp | Non-ASCII `RegExp.prototype[@@replace]` advances UTF-8 pointer by match byte size instead of character count, causing OOB/corruption crash | CONFIRMED |
| BUG-007 | High | RegExp | Unchecked `ECMA_VALUE_ERROR` from `ecma_regexp_exec_helper` in `@@replace` slow path causes crash | CONFIRMED |
| BUG-008 | High | RegExp | Assertion crash / unhandled error in sticky `@@replace` when `lastIndex` is non-writable and out of bounds | CONFIRMED |
| BUG-009 | High | TypedArray | Memory leak of `source_obj` and `source_length` on `ToLength` error in `TypedArray.prototype.set` | CONFIRMED |
| BUG-010 | Critical | jerry-ext / handle-scope | `jerryx_close_handle_scope` frees parent before child, causing heap UAF (dynamic scopes), dangling `current`, and leaked child scopes | CONFIRMED |
| BUG-011 | High | jerry-ext / handle-scope | `jerryx_escape_handle` on prelist handle when overflow heap list is non-empty leaks all remaining heap handles and one prelist handle | CONFIRMED |
| BUG-012 | High | jerry-ext / handle-scope | `jerryx_remove_handle` on heap-allocated handle leaves `*result` uninitialized and leaks `jerryx_handle_t` | CONFIRMED |
| BUG-013 | High | Core API | `jerry_define_own_property` checks `is_enumerable` instead of `is_configurable` and returns raw `ECMA_VALUE_ERROR` | CONFIRMED |
| BUG-014 | High | Core API | `jerry_create_regexp_sz` returns raw `ECMA_VALUE_ERROR` on invalid pattern and passes UTF-8 to CESU-8 constructor | CONFIRMED |
| BUG-015 | High | Core API | `jerry_create_typedarray_for_arraybuffer` passes byte length as element count, failing for multi-byte TypedArrays | CONFIRMED |
| BUG-016 | High | Core API | `jerry_create_dataview` leaks heap-allocated `ecma_number_t` arguments for offsets/lengths > `ECMA_INTEGER_NUMBER_MAX` | CONFIRMED |
| BUG-017 | High | Core API | `jerry_json_stringify` dereferences/uses error argument before error-reference check and omits `jerry_return()` | SUSPECTED |
| BUG-018 | High | Debugger | `jerry_debugger_send_eval` and `jerry_debugger_send_scope_variables` crash on `Symbol` / throwing `toString` / accessor properties | SUSPECTED |
| BUG-019 | High | Snapshot API | `jerry_snapshot_result` lacks bounds checks on `func_offsets[func_index]` / `func_offset` and omits `ecma_create_error_reference_from_context()` | SUSPECTED |
| BUG-020 | Medium | RegExp | `re_parse_next_token` treats NUL (`\0`) as EOF, truncating patterns containing NUL bytes | CONFIRMED |
| BUG-021 | Medium | RegExp | 32-bit integer overflow in `{min,max}` quantifier parsing allows invalid/wrapped quantifiers | CONFIRMED |
| BUG-022 | Medium | RegExp | Character class range `[a-\d]` uses `LIT_CHAR_UNDEF` (`0xFFFF`) as range end, compiling as `[a-\uFFFF]` | CONFIRMED |
| BUG-023 | Medium | RegExp | Unicode greedy iterator backtracking steps back a single UTF-16 code unit, splitting surrogate pairs | CONFIRMED |
| BUG-024 | Medium | RegExp | `RE_OP_BACKREFERENCE` uses `memcmp` and ignores `/i` (`ignoreCase`) flag | CONFIRMED |
| BUG-025 | Medium | RegExp | `ecma_regexp_exec_helper` wraps `lastIndex` via `ToUint32`, matching at 0 when `lastIndex === 2**32` | CONFIRMED |
| BUG-026 | Medium | RegExp | Sticky non-global `RegExp.prototype[@@replace]` fast path ignores sticky flag and scans forward without updating `lastIndex` | CONFIRMED |
| BUG-027 | Medium | RegExp | Undefined behavior passing `NULL` to `memset` in `ecma_regexp_initialize_context` | CONFIRMED |
| BUG-028 | Medium | DataView | `ecma_op_dataview_create` truncates `byteOffset` >= `2**32` via `(uint32_t)` cast (UB + silent wraparound) and evaluates offset twice | CONFIRMED |
| BUG-029 | Medium | TypedArray | `TypedArray.prototype.set` with overlapping different-typed views over the same `ArrayBuffer` clobbers unread source bytes | CONFIRMED |
| BUG-030 | Medium | TypedArray | `ecma_typedarray_set_uint8_clamped_element` performs undefined `(uint8_t) NaN` cast | SUSPECTED |
| BUG-031 | Medium | jerry-ext / module | `jerryx_module_check_cache` uses `jerry_has_property` instead of `jerry_has_own_property`, allowing `Object.prototype` properties to resolve as modules | CONFIRMED |
| BUG-032 | Medium | jerry-ext / debugger | Multiple defects in `debugger-serial.c` (even parity sets `PARODD`, double `close(fd)`, leaked `fd`, unterminated `strncpy`, raw baud passed to `cfsetispeed`) | SUSPECTED |
| BUG-033 | Medium | jerry-ext / debugger | `jerryx_debugger_ws_create` registers transport and returns `true` when handshake fails after disconnect | SUSPECTED |
| BUG-034 | Medium | Core API | `jerry_set_prototype` does not check for prototype cycles, enabling infinite loops | SUSPECTED |
| BUG-035 | Critical | GC / Generator | GC fails to mark VM stack contexts in suspended generators, causing use-after-free and live object reuse | CONFIRMED |
| BUG-036 | Critical | TypedArray | Double-free, use-after-free, and memory leak in `TypedArray.prototype.toLocaleString` | CONFIRMED |
| BUG-037 | Critical | GC / WeakMap | `ecma_gc_free_object` ignores property hashmap on `WeakMap`/`WeakSet`, causing assertion crash / memory corruption | CONFIRMED |
| BUG-038 | Critical | Array | Fast-array TOCTOU heap out-of-bounds read / NULL dereference in `Array.prototype.indexOf`, `lastIndexOf`, and `slice` | CONFIRMED |
| BUG-039 | Critical | VM / Spread | Out-of-bounds stack read/free and argument leak on spread error in `opfunc_spread_arguments` | CONFIRMED |
| BUG-040 | Critical | RegExp | Use-after-free in `RegExp.prototype.compile` when compiling a RegExp from itself | CONFIRMED |
| BUG-041 | Critical | Objects / Enumeration | Stack buffer overflow and skipped prototype lazy properties in `ecma_op_object_get_property_names` | CONFIRMED |
| BUG-042 | Critical | String | Use-after-free of heap-allocated float value in `String.fromCodePoint` | SUSPECTED |
| BUG-043 | High | Generator / Function | Nested generator call in default parameter clears `current_function_obj_p`, causing NULL-dereference crash | CONFIRMED |
| BUG-044 | High | Promise / JobQueue | `ecma_free_all_enqueued_jobs` frees `PromiseResolveThenableJob` with wrong size and leaks `then` | CONFIRMED |
| BUG-045 | High | String | Infinite loop leading to OOM in `String.raw` when `next_index >= number_of_substitutions` | CONFIRMED |
| BUG-046 | High | Iterators / Generator | `ecma_op_iterator_return` passes C `true` (`1`) instead of `ECMA_VALUE_TRUE` to `ecma_create_iter_result_object` | CONFIRMED |
| BUG-047 | High | VM / Exceptions | `VM_OC_CONTEXT_END` ignores pending exception raised by `for-of` `iterator.return()` | CONFIRMED |
| BUG-048 | High | JSON | `JSON.stringify` crashes on `NULL` string when `new String().toString()` throws | CONFIRMED |
| BUG-049 | High | Promise | Memory leak of `capability` in `Promise.resolve` / `Promise.reject` when resolve/reject function throws | CONFIRMED |
| BUG-050 | High | String | Memory leak of `search_symbol` in `String.prototype.search` when `@@search` is non-callable | CONFIRMED |
| BUG-051 | High | Iterators | `ArrayIterator.prototype.next` crashes on frozen iterator at index 65535 and leaks large heap float indices | CONFIRMED |
| BUG-052 | High | Iterators | `StringIterator.prototype.next` `uint16_t` overflow wraps index `65534 + 2` to `0` on surrogate pair, causing infinite iteration | CONFIRMED |
| BUG-053 | High | Conversion / Object | `ecma_op_same_value` uses `==` instead of `&&` for NaN check, breaking `Object.is` and allowing mutation of frozen float properties | CONFIRMED |
| BUG-054 | High | Global | `parseFloat` compares only 1 byte of `"Infinity"` due to `sizeof(*infinity_str_p)` | CONFIRMED |
| BUG-055 | High | Object | `Object.freeze`, `Object.seal`, `Object.isFrozen`, and `Object.isSealed` ignore Symbol properties | CONFIRMED |
| BUG-056 | High | Date | `Date.prototype.get*` on Invalid Date (`NaN`) returns string `"NaN"` instead of number `NaN` | CONFIRMED |
| BUG-057 | High | String Helpers | Reversed subtraction `LIT_MAGIC_STRING__COUNT - magic_string_ex_id` causes `uint32_t` underflow and OOB read in `ecma_string_get_chars_fast` | SUSPECTED |
| BUG-058 | High | Snapshot / Literals | `ecma_save_literals_add_compiled_code` reads `literal_p[0..argument_end-1]` past literal pool into bytecode/OOB and truncates >64 KB strings | SUSPECTED |
| BUG-059 | Medium | String | Multiple logic bugs in `String.prototype.startsWith`, `endsWith`, `indexOf`, and `lastIndexOf` | CONFIRMED |
| BUG-060 | Medium | String | `String.prototype.repeat` and `String.prototype.substr` wrap 32-bit counts/indices via `ToUint32` | CONFIRMED |
| BUG-061 | Medium | Array / Objects | `Object.preventExtensions` on a fast array prevents modifying existing writable elements | CONFIRMED |
| BUG-062 | Medium | TypedArray | `TypedArray` indexed `[[Put]]` swallows `ToNumber` exceptions | CONFIRMED |
| BUG-063 | Medium | TypedArray | `TypedArray.prototype.indexOf` fails / invokes UB on negative `fromIndex < -length` | CONFIRMED |
| BUG-064 | Medium | Global | `unescape` fails to reset `hex_digits` on invalid sequences and mishandles `%%xx` | CONFIRMED |
| BUG-065 | Medium | JSON | `JSON.stringify` ignores empty replacer array `[]` | CONFIRMED |
| BUG-066 | Medium | Promise | `Promise.all` / `Promise.race` inverted `is_done` check skips iterator close and continues iterating rejected promise on non-iterable input | CONFIRMED |
| BUG-067 | Medium | Generator | `Generator.prototype.return` and `.throw` on completed generators ignore argument / fail to throw | CONFIRMED |
| BUG-068 | Medium | Number | `Number.prototype.toString` wraps radix via `ToUint32` and `Number.prototype.toFixed` drops minus sign for `abs(x) >= 1e21` | CONFIRMED |
| BUG-069 | Medium | Date | `Date.prototype[Symbol.toPrimitive]` accepts invalid hints, `setTime` returns unclipped value, and `new Date(obj)` calls `valueOf()` twice | CONFIRMED |
| BUG-070 | Medium | Reflect | Multiple `Reflect` API contract violations (`preventExtensions`, `setPrototypeOf`, `defineProperty`, `apply`) | CONFIRMED |
| BUG-071 | Medium | Map / Set | `Map`/`Set` `forEach` omits 3rd argument & visits cleared entries; re-insertion after `delete` preserves stale order | CONFIRMED |
| BUG-072 | Medium | Class / Parser / VM | `class C extends B` silently ignores primitive/null `B.prototype` and named class expressions omit inner binding | CONFIRMED |
| BUG-073 | Medium | Array | `Array[Symbol.species]` is ignored by `ecma_op_array_species_create` and `Array` `length` setter ignores first `ToNumber` value | CONFIRMED |
| BUG-074 | Medium | Parser | `for (var x = init in obj)` skips executing `init` (violating Annex B) | CONFIRMED |
| BUG-075 | Medium | Conversion / VM / Math | Undefined behavior: 64-bit shift overflow in `ecma_utf8_string_to_number`, negative/overflow left shifts in `vm_loop`/`opfunc_bitwise`/`ecma_integer_multiply`, and `INT32_MIN` negation in TypedArray | CONFIRMED |
| BUG-076 | Medium | Function / Prototype | `ecma_op_get_prototype_from_constructor` leaks non-object `prototype` values | SUSPECTED |
| BUG-077 | Medium | VM / Debugger | `vm_run_eval` debugger `chain_index` error leaks `this_binding` and `bytecode_data_p` | SUSPECTED |
| BUG-078 | Medium | Memory Allocator | `jmem_heap_alloc` fast path can set `jmem_heap_list_skip_p` to `area + 0xffffffff` when `next_offset == JMEM_HEAP_END_OF_LIST` | SUSPECTED |

---

## Detailed Findings

### BUG-001: Heap buffer overflow in raw template literal containing escaped U+2028/U+2029
- **Severity:** Critical
- **Subsystem:** Parser / Lexer
- **Location:** `jerry-core/parser/js/js-lexer.c:974-980`, `jerry-core/parser/js/js-lexer.c:1974-2150`, `jerry-core/parser/js/js-parser-tagged-template-literal.c:69-79`
- **Status:** CONFIRMED
- **Mechanism:** When `lexer_parse_string` scans a tagged template literal in raw mode (`LEXER_STRING_RAW`, where `raw_length_inc == 1`), line 942 adds `1` to `length` for the backslash, and lines 959 and 969 add `raw_length_inc` for `\r` and `\n`. However, the branch for `\<U+2028>` / `\<U+2029>` at lines 974-980 advances `source_p += 3` without adding `3 * raw_length_inc` to `length`. Subsequently, `lexer_convert_literal_to_chars` allocates a heap buffer of size `literal_p->length` (when `length > LEXER_MAX_LITERAL_LOCAL_BUFFER_SIZE`), and because `is_raw` is true, copies both the backslash and all 3 UTF-8 bytes of U+2028/U+2029 into `destination_p`, overflowing the heap buffer by 3 bytes per occurrence (and hitting `JERRY_ASSERT (destination_p == destination_start_p + literal_p->length)` at line 2150 in debug builds).
- **Repro:**
  ```sh
  python3 -c 'open("/tmp/test_tpl_ovf.js","wb").write(("String.raw`"+"A"*300+"\\\u2028"*20+"`").encode("utf-8"))'
  ./build/asan-debug/bin/jerry /tmp/test_tpl_ovf.js
  # Aborted (exit 134)
  ```

### BUG-002: Heap buffer overflow & type confusion via `ArrayBuffer` `Symbol.species` in TypedArray constructor
- **Severity:** Critical
- **Subsystem:** TypedArray
- **Location:** `jerry-core/ecma/operations/ecma-typedarray-object.c:528-558`, `jerry-core/ecma/operations/ecma-typedarray-object.c:645-672`
- **Status:** CONFIRMED
- **Mechanism:** In `ecma_typedarray_create_object_with_length`, when `src_buffer_p != NULL` (constructing a TypedArray from another TypedArray), it invokes the `ArrayBuffer` `Symbol.species` constructor via `ecma_op_function_construct` (lines 537-540). It fails to: (1) check `ECMA_IS_VALUE_ERROR(new_arraybuffer)`, (2) verify that the returned object is actually an `ArrayBuffer` (type confusion if `{}` is returned), and (3) verify that the returned `ArrayBuffer`'s `byteLength >= byte_length`. In `ecma_typedarray_create_object_with_typedarray` (line 654), `memcpy(dst_buf_p, src_buf_p, array_length << element_size_shift)` then writes past the end of the undersized/non-ArrayBuffer object on the heap.
- **Repro:**
  ```js
  var a = new Uint8Array(64);
  a.fill(0x41);
  a.buffer.constructor = {};
  a.buffer.constructor[Symbol.species] = function() { return new ArrayBuffer(0); };
  var b = new Uint8Array(a); // Heap buffer overflow -> Aborted (exit 134)
  ```
  And type confusion variant:
  ```js
  var a = new Uint8Array(8);
  a.buffer.constructor = {};
  a.buffer.constructor[Symbol.species] = function() { return {}; };
  new Uint8Array(a); // Aborted (exit 134)
  ```

### BUG-003: Use-after-free of element/index `ecma_value_t` in `TypedArray.prototype.filter`
- **Severity:** Critical
- **Subsystem:** TypedArray
- **Location:** `jerry-core/ecma/builtin-objects/typedarray/ecma-builtin-typedarray-prototype.c:731-742`
- **Status:** CONFIRMED
- **Mechanism:** Inside the loop in `ecma_builtin_typedarray_prototype_filter`, `current_index` and `get_value` are placed in `call_args[]`, and then **immediately freed** with `ecma_fast_free_value` on lines 739-740 *before* `ecma_op_function_call(func_object_p, cb_this_arg, call_args, 3)` is invoked on line 742. For any heap-allocated float value (e.g., `Float64Array`/`Float32Array` values or integers outside inline range), the callback receives a dangling `ecma_value_t` pointing to freed heap memory. Allocating inside the callback overwrites the float storage, corrupting `x` (and triggering UBSan in `ecma-helpers-conversion.c:671` when converting corrupted bits).
- **Repro:**
  ```js
  var a = new Float64Array([1.5, 2.5, 3.5]);
  var r = a.filter(function(x) {
    var t = [9.9, 8.8, 7.7, 6.6];
    return x === 1.5 || x === 2.5 || x === 3.5;
  });
  print(r.length); // prints 0 instead of 3; UBSan shift-exponent error on corrupted float
  ```

### BUG-004: Heap/stack buffer overflow in `jerry_get_literals_from_snapshot` when `is_c_format` is true
- **Severity:** Critical
- **Subsystem:** Snapshot API
- **Location:** `jerry-core/api/jerry-snapshot.c:1673-1686`
- **Status:** CONFIRMED
- **Mechanism:** `jerry_get_literals_from_snapshot` relies on `jerry_append_chars_to_buffer` returning `buffer_end_p + 1` to stop writing once `lit_buf_p` exceeds `buffer_end_p`. However, in the C-format escaping loop (lines 1673-1686), characters and hex digits are written directly via `*lit_buf_p++ = ...` (lines 1675, 1677, 1683, 1685) with no bounds check against `buffer_end_p`. When `lit_buf_size` is smaller than the formatted output, this causes an unbounded out-of-bounds write past `lit_buf_p`.
- **Repro:** Confirmed via C harness calling `jerry_get_literals_from_snapshot(snap, snap_size, malloc(70), 70, true)` on a snapshot generated from `"var very_long_identifier_name_1234567890 = 'hello\\\\\"world\\x01';"`: ASan reports `ERROR: AddressSanitizer: heap-buffer-overflow WRITE of size 1 at jerry-snapshot.c:1685`.

### BUG-005: `memset` uses capture count instead of byte size in `ecma_regexp_replace_helper_fast` and ES5.1 `split`
- **Severity:** High
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:2189` and `jerry-core/ecma/operations/ecma-regexp-object.c:2029`
- **Status:** CONFIRMED
- **Mechanism:** Both lines execute `memset (re_ctx.captures_p, 0, re_ctx.captures_count)` instead of `memset (re_ctx.captures_p, 0, re_ctx.captures_count * sizeof (ecma_regexp_capture_t))`. Since `sizeof (ecma_regexp_capture_t)` is `2 * sizeof(void*)` (16 bytes on 64-bit, 8 bytes on 32-bit), this only zeroes a fraction of the capture array: stale pointers from previous matches remain in `captures_p[1..]`, and when `captures_count > sizeof(ecma_regexp_capture_t)`, `memset` partially zeroes the low bytes of a capture pointer, corrupting it into a wild pointer.
- **Repro:** Code inspection + runtime observation in `ecma_regexp_replace_helper_fast` (line 2189). With 17+ capturing groups, bytes `16..17` of `captures_p` (low bytes of `captures_p[1].begin_p`) are overwritten with zeros while high bytes remain intact.

### BUG-006: Non-ASCII `RegExp.prototype[@@replace]` advances UTF-8 pointer by match byte size instead of character count
- **Severity:** High
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:2749-2750`
- **Status:** CONFIRMED
- **Mechanism:** In the slow path of `ecma_regexp_replace_helper`, `source_position_p` is updated to `JERRY_MIN (match_position_p + matched_str_size, string_end_p)` while `replace_ctx.index` is updated to `JERRY_MIN (position + matched_str_length, string_length)`. When a custom `exec` returns a match string whose CESU-8 byte size differs from the bytes at `match_position_p` in a non-ASCII input string (e.g. `"a"` = 1 byte vs `"\u20AC"` = 3 bytes), `source_position_p` is positioned in the middle of a multi-byte UTF-8 sequence. Subsequent `lit_utf8_incr` calls and `ecma_stringbuilder_append_raw` corrupt UTF-8 encoding and abort/over-read.
- **Repro:**
  ```js
  var i = 0;
  var r = {
    global: true,
    exec: function() {
      if (i === 0) { i++; var a = ["a"]; a.index = 0; return a; }
      if (i === 1) { i++; var a = ["a"]; a.index = 2; return a; }
      return null;
    }
  };
  RegExp.prototype[Symbol.replace].call(r, "\u20AC\u20AC\u20AC", "X"); // Aborted (exit 134)
  ```

### BUG-007: Unchecked `ECMA_VALUE_ERROR` from `ecma_regexp_exec_helper` in `@@replace` slow path
- **Severity:** High
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:2533-2543`
- **Status:** CONFIRMED
- **Mechanism:** When `this.exec` is non-callable on a RegExp object, `ecma_regexp_replace_helper` calls `ecma_regexp_exec_helper(this_obj_p, string_p)` at line 2533 without checking `if (ECMA_IS_VALUE_ERROR(result))`. If `ecma_regexp_exec_helper` throws (e.g., `lastIndex` `ToInteger` throws), `ECMA_VALUE_ERROR` is pushed into `results_p` and later dereferenced via `ecma_get_object_from_value(*current_p)` at line 2634, causing an assertion abort / crash.
- **Repro:**
  ```js
  var r = /a/y;
  r.exec = null;
  Object.defineProperty(r, "lastIndex", { value: { valueOf: function() { throw 1; } } });
  "a".replace(r, "b"); // Aborted (exit 134)
  ```

### BUG-008: Assertion crash / unhandled error in sticky `@@replace` when `lastIndex` is non-writable and out of bounds
- **Severity:** High
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:2471-2475`
- **Status:** CONFIRMED
- **Mechanism:** In `ecma_regexp_replace_helper`, when `sticky && !global` and `lastIndex > string_length`, line 2471 calls `ecma_op_object_put(this_obj_p, lastIndex, 0, true)` and line 2475 asserts `JERRY_ASSERT(ecma_is_value_true(result))`. If `lastIndex` is non-writable, `ecma_op_object_put` throws a `TypeError` (`ECMA_VALUE_ERROR`), aborting debug builds and leaving an uncleared pending exception in release builds. Additionally, lines 2448 and 2464 leak `function_p` on error paths.
- **Repro:**
  ```js
  var r = /a/y;
  Object.defineProperty(r, "lastIndex", { value: 99, writable: false });
  "a".replace(r, "b"); // Aborted (exit 134)
  ```

### BUG-009: Memory leak of `source_obj` and `source_length` on `ToLength` error in `TypedArray.prototype.set`
- **Severity:** High
- **Subsystem:** TypedArray
- **Location:** `jerry-core/ecma/builtin-objects/typedarray/ecma-builtin-typedarray-prototype.c:964-977`
- **Status:** CONFIRMED
- **Mechanism:** Inside two nested `ECMA_TRY_CATCH` scopes (`source_obj` and `source_length`), line 976 executes `return ECMA_VALUE_ERROR;` directly when `ecma_op_to_length` fails, bypassing `ECMA_FINALIZE(source_length)` and `ECMA_FINALIZE(source_obj)` and leaking both values.
- **Repro:**
  ```js
  try {
    new Uint8Array(1).set({ length: { valueOf: function() { throw 1; } } });
  } catch (e) {}
  // Aborted (exit 134) in jmem_finalize due to leaked heap blocks
  ```

### BUG-010: `jerryx_close_handle_scope` frees parent before child, causing heap UAF, dangling `current`, and leaked child scopes
- **Severity:** Critical
- **Subsystem:** jerry-ext / handle-scope
- **Location:** `jerry-ext/handle-scope/handle-scope.c:71-87`, `jerry-ext/handle-scope/handle-scope-allocator.c:109-138, 194-224`
- **Status:** CONFIRMED
- **Mechanism:** `jerryx_close_handle_scope` walks top-down from `scope` to its children, freeing each scope before advancing to its child. Because `jerryx_handle_scope_free` decrements `pool.count` immediately, `jerryx_handle_scope_get_child` (line 133: `idx >= pool.count - 1`) stops prematurely and skips remaining prelist child scopes. For dynamic heap scopes (beyond `JERRYX_SCOPE_PRELIST_SIZE == 20`), freeing a parent `dy_scope` before its child causes `jerryx_handle_scope_free` on the child to dereference freed `dy_scope->parent` (heap use-after-free at line 216 `dy_scope->parent->child = dy_scope->child` and line 204 setting `jerryx_handle_scope_current` to the freed parent!).
- **Repro:** Confirmed via C test opening 30 nested scopes (so scopes 20..29 are dynamically allocated) and calling `jerryx_close_handle_scope(scopes[22])`: ASan reports `ERROR: AddressSanitizer: heap-use-after-free WRITE of size 8 at handle-scope-allocator.c:216`.

### BUG-011: `jerryx_escape_handle` on prelist handle with non-empty overflow list leaks heap handles and one prelist handle
- **Severity:** High
- **Subsystem:** jerry-ext / handle-scope
- **Location:** `jerry-ext/handle-scope/handle-scope.c:126-143, 191-196, 41`
- **Status:** CONFIRMED
- **Mechanism:** When `scope->prelist_handle_count == JERRYX_HANDLE_PRELIST_SIZE && scope->handle_ptr != NULL`, `jerryx_hand_scope_escape_handle_from_prelist` moves one handle from the heap overflow list into the vacated prelist slot, leaving the prelist full (`JERRYX_HANDLE_PRELIST_SIZE` handles). However, `jerryx_escape_handle_internal` unconditionally decrements `--scope->prelist_handle_count` at line 195. As a result, `handle_prelist[JERRYX_HANDLE_PRELIST_SIZE - 1]` is leaked, and when `jerryx_handle_scope_release_handles` later checks `if (prelist_handle_count == JERRYX_HANDLE_PRELIST_SIZE && scope->handle_ptr != NULL)` (line 41), the condition is false and the entire remaining heap chain `scope->handle_ptr` (both `malloc`'d nodes and their `jerry_value_t` refs) is leaked.
- **Repro:** Confirmed via C test opening an escapable scope, adding 25 objects (> prelist size), escaping the 1st object, closing scopes, and calling `jerry_cleanup()` -> `Aborted (exit 134)` in `jmem_finalize` with leaked objects.

### BUG-012: `jerryx_remove_handle` on heap-allocated handle leaves `*result` uninitialized and leaks `jerryx_handle_t`
- **Severity:** High
- **Subsystem:** jerry-ext / handle-scope
- **Location:** `jerry-ext/handle-scope/handle-scope.c:248-260`
- **Status:** CONFIRMED
- **Mechanism:** In `jerryx_escape_handle_internal`, when the target handle is found in the heap chain (`scope->handle_ptr`) and `should_promote == false` (`jerryx_remove_handle`), the `if (should_promote)` block at line 248 is skipped, so `*result` is never assigned (uninitialized output) and `found_handle` (allocated with `malloc`) is never `free()`d.
- **Repro:** Confirmed via C test + ASan LeakSanitizer: `Direct leak of 16 byte(s) in 1 object(s) allocated from jerryx_create_handle_in_scope (handle-scope.c:341)` and `*result` remained untouched sentinel `0xDEADBEEF`.

### BUG-013: `jerry_define_own_property` checks `is_enumerable` instead of `is_configurable` and returns raw `ECMA_VALUE_ERROR`
- **Severity:** High
- **Subsystem:** Core API
- **Location:** `jerry-core/api/jerry.c:2469-2473`, `jerry-core/api/jerry.c:2537-2539`
- **Status:** CONFIRMED
- **Mechanism:** (1) Line 2471 tests `prop_desc_p->is_enumerable ? ECMA_PROP_IS_CONFIGURABLE : ECMA_PROP_NO_OPTS` instead of `prop_desc_p->is_configurable`, so defining a property with `enumerable=false, configurable=true` creates a non-configurable property. (2) Line 2537 returns `ecma_op_object_define_own_property(...)` directly without wrapping in `jerry_return(...)`. Because `ECMA_PROP_IS_THROW` is set, failure returns internal `ECMA_VALUE_ERROR` (`0x38`) instead of an API error reference (`jerry_value_is_error` returns `false`), leaving a dangling pending exception in `JERRY_CONTEXT(error_value)`.
- **Repro:** Confirmed via C test: defining `configurable=true, enumerable=false` produced `configurable=0`; subsequent redefinition returned `0x38` with `jerry_value_is_error() == 0`.

### BUG-014: `jerry_create_regexp_sz` returns raw `ECMA_VALUE_ERROR` on invalid pattern and passes UTF-8 to CESU-8 constructor
- **Severity:** High
- **Subsystem:** Core API
- **Location:** `jerry-core/api/jerry.c:1707-1717`
- **Status:** CONFIRMED
- **Mechanism:** (1) Line 1717 returns `ret_val` from `ecma_op_create_regexp_object` directly without `jerry_return(ret_val)`. When `pattern_p` is an invalid RegExp (e.g. `"["`), it returns raw `ECMA_VALUE_ERROR` (`jerry_value_is_error` is `false`) and leaves a pending exception uncleared, aborting `jerry_cleanup()`. (2) Line 1707 validates UTF-8 (`lit_is_valid_utf8_string`), then line 1712 passes it to `ecma_new_ecma_string_from_utf8` which expects CESU-8 (unlike `ecma_new_ecma_string_from_utf8_converted_to_cesu8`), breaking on valid 4-byte UTF-8 characters.
- **Repro:** Confirmed via C test: `jerry_create_regexp("[", 0)` returned raw `0x18`/`ECMA_VALUE_ERROR` (`jerry_value_is_error == 0`) and aborted on `jerry_cleanup()` (exit 134).

### BUG-015: `jerry_create_typedarray_for_arraybuffer` passes byte length as element count
- **Severity:** High
- **Subsystem:** Core API
- **Location:** `jerry-core/api/jerry.c:4095-4096`
- **Status:** CONFIRMED
- **Mechanism:** `jerry_create_typedarray_for_arraybuffer` obtains `byteLength = jerry_get_arraybuffer_byte_length(arraybuffer)` and passes it as the `length` (element count) parameter to `jerry_create_typedarray_for_arraybuffer_sz`. For any TypedArray whose element size is > 1 byte (`INT16`, `UINT16`, `INT32`, `UINT32`, `FLOAT32`, `FLOAT64`) with non-zero buffer length, the requested byte size exceeds the ArrayBuffer's length and always fails with `RangeError`.
- **Repro:** Confirmed via C test: `jerry_create_typedarray_for_arraybuffer(JERRY_TYPEDARRAY_INT32, jerry_create_arraybuffer(8))` returned an error (`is_error=1, is_typedarray=0`).

### BUG-016: `jerry_create_dataview` leaks heap-allocated `ecma_number_t` arguments
- **Severity:** High
- **Subsystem:** Core API
- **Location:** `jerry-core/api/jerry.c:3790-3797`
- **Status:** CONFIRMED
- **Mechanism:** `jerry_create_dataview` creates `ecma_make_uint32_value(byte_offset)` and `ecma_make_uint32_value(byte_length)` in `arguments_p[1..2]` and never calls `ecma_free_value` on them after `ecma_op_dataview_create` returns (unlike `jerry_create_typedarray_for_arraybuffer_sz` at lines 4061-4062). Whenever `byte_offset` or `byte_length` exceeds `ECMA_INTEGER_NUMBER_MAX` (`134217727`), heap-allocated float values are permanently leaked.
- **Repro:** Confirmed via C test: `jerry_create_dataview(ab, 200000000u, 1)` followed by releasing `dv`, `ab` and `jerry_cleanup()` -> `Aborted (exit 134)` in `jmem_finalize` due to leaked heap block.

### BUG-017: `jerry_json_stringify` uses error argument before error-reference check and omits `jerry_return()`
- **Severity:** High
- **Subsystem:** Core API
- **Location:** `jerry-core/api/jerry.c:4252-4264`
- **Status:** SUSPECTED
- **Mechanism:** Line 4252 calls `ecma_builtin_json_string_from_object(object_to_stringify)` *before* checking `if (ecma_is_value_error_reference(object_to_stringify))` on line 4254, passing an invalid error-reference value into internal ECMA code (crashing/asserting or leaking `ret_value`). Furthermore, line 4264 returns `ret_value` without `jerry_return(ret_value)`, so internal `ECMA_VALUE_ERROR` (e.g., from a circular object or throwing getter/`toJSON`) is returned raw instead of as an API error reference.

### BUG-018: Debugger crashes on `Symbol`, throwing `toString`, and accessor properties
- **Severity:** High
- **Subsystem:** Debugger
- **Location:** `jerry-core/debugger/debugger.c:505-510, 573-577, 1535-1538`
- **Status:** SUSPECTED
- **Mechanism:** (1) `jerry_debugger_send_eval` (lines 573-574) calls `ecma_op_to_string(result)` and passes `str_p` directly to `ecma_make_string_value(str_p)` without checking for `NULL` (returned on `Symbol`, `Object.create(null)`, or throwing `toString`). (2) `jerry_debugger_send_scope_variables` (lines 505-510) reads `prop_pair_p->values[i].value` without checking if the property is `ECMA_PROPERTY_TYPE_NAMEDACCESSOR` (type confusion: getter/setter cpointers treated as `ecma_value_t`), crashes `jerry_debugger_get_variable_type` on `Symbol` or uninitialized TDZ bindings, and asserts `str_p != NULL` after `ecma_op_to_string`. (3) `jerry_debugger_send_exception_string` (line 1535) crashes if a `Symbol` is thrown. (4) Multi-part `JERRY_DEBUGGER_EVAL` leaks previous `eval_uint8_data_p` if sent twice during one breakpoint pause (lines 969-979 vs 1190-1194).

### BUG-019: `jerry_snapshot_result` lacks bounds checks on `func_offsets` / `func_offset` and returns raw `ECMA_VALUE_ERROR`
- **Severity:** High
- **Subsystem:** Snapshot API
- **Location:** `jerry-core/api/jerry-snapshot.c:949-958, 982-985, 220-223`
- **Status:** SUSPECTED
- **Mechanism:** (1) `jerry_snapshot_result` checks `func_index >= header_p->number_of_funcs` without verifying that `header_p->func_offsets[func_index]` lies within `snapshot_size`, and never validates that `func_offset < snapshot_size` (or `< header_p->lit_table_offset`), allowing out-of-bounds reads on malformed snapshots. (2) Line 984 returns `ecma_raise_type_error(...)` directly instead of calling `ecma_create_error_reference_from_context()`. (3) `snapshot_add_compiled_code` (lines 220-223) truncates `pattern_size` to `uint16_t` in `copied_code_p->refs` for RegExp patterns >= 64 KB.

### BUG-020: `re_parse_next_token` treats NUL (`\0`) as EOF, truncating RegExp patterns
- **Severity:** Medium
- **Subsystem:** RegExp
- **Location:** `jerry-core/parser/regexp/re-parser.c:633-637`
- **Status:** CONFIRMED
- **Mechanism:** `case LIT_CHAR_NULL:` sets `out_token_p->type = RE_TOK_EOF`, terminating RegExp parsing at any embedded NUL character. Patterns such as `new RegExp("a\0b")` silently compile as `/a/`.
- **Repro:** `print(new RegExp("a\0b").test("a"));` outputs `true` (expected `false`).

### BUG-021: 32-bit integer overflow in `{min,max}` quantifier parsing
- **Severity:** Medium
- **Subsystem:** RegExp
- **Location:** `jerry-core/parser/regexp/re-parser.c:172-180`
- **Status:** CONFIRMED
- **Mechanism:** `re_parse_iterator` accumulates quantifier digits into a `uint32_t qmin` while allowing up to `ECMA_NUMBER_MAX_DIGITS` (19) digits without checking for `uint32_t` overflow. Values >= `2^32` wrap modulo `2^32`, turning `a{4294967296}` into `a{0}` and accepting invalid `a{4294967296,1}` as `a{0,1}` instead of throwing `SyntaxError`.
- **Repro:** `print(new RegExp("a{4294967296}").test(""), new RegExp("a{4294967296,1}").test("a"));` outputs `true true`.

### BUG-022: Character class range `[a-\d]` uses `LIT_CHAR_UNDEF` (`0xFFFF`) as range end
- **Severity:** Medium
- **Subsystem:** RegExp
- **Location:** `jerry-core/parser/regexp/re-compiler.c:407-471, 493-507`
- **Status:** CONFIRMED
- **Mechanism:** Inside `re_parse_char_class`, character class escapes (`\d`, `\D`, `\s`, `\S`, `\w`, `\W`) append their ranges and set `ch = LIT_CHAR_UNDEF` (`0xFFFF`). If preceded by `a-` (`is_range == true`), lines 497-503 compare `start > 0xFFFF` (false) and append the range `[start, 0xFFFF]`! Thus `/[a-\d]/` matches any character from `'a'` through `'\uFFFF'`.
- **Repro:** `print(/[a-\d]/.test("b"));` outputs `true` (expected `false` or `SyntaxError`).

### BUG-023: Unicode greedy iterator backtracking splits surrogate pairs
- **Severity:** Medium
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:1118`
- **Status:** CONFIRMED
- **Mechanism:** In `RE_OP_GREEDY_ITERATOR`, forward matching of `.` or a character class in `/u` (Unicode) mode consumes an entire surrogate pair (2 UTF-16 code units = 6 CESU-8 bytes) per iteration. When backtracking at line 1118, it calls `lit_cesu8_read_prev(&str_curr_p)` only once, stepping into the middle of a surrogate pair and failing valid matches.
- **Repro:** `print(/^.+\uD83D\uDE00$/u.exec("\uD83D\uDE00\uD83D\uDE00"));` outputs `null` (expected match).

### BUG-024: `RE_OP_BACKREFERENCE` ignores `/i` (`ignoreCase`) flag
- **Severity:** Medium
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:719`
- **Status:** CONFIRMED
- **Mechanism:** Backreference matching compares the input against the captured slice using raw `memcmp(str_curr_p, capture.begin_p, capture_size)`, ignoring `RE_FLAG_IGNORE_CASE`.
- **Repro:** `print(/(a)\1/i.test("aA"));` outputs `false` (expected `true`).

### BUG-025: `ecma_regexp_exec_helper` wraps `lastIndex` via `ToUint32`
- **Severity:** Medium
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:1316`
- **Status:** CONFIRMED
- **Mechanism:** `lastIndex` is converted using `ecma_number_to_uint32(lastindex_num)` instead of `ToLength`. Setting `lastIndex = 4294967296` (`2^32`) wraps to `0`, causing a match at index 0 instead of returning `null`.
- **Repro:** `var r = /a/g; r.lastIndex = 4294967296; print(r.exec("a"));` outputs `a` (expected `null`).

### BUG-026: Sticky non-global `RegExp.prototype[@@replace]` fast path ignores sticky flag
- **Severity:** Medium
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:2187-2293`
- **Status:** CONFIRMED
- **Mechanism:** In `ecma_regexp_replace_helper_fast`, when a RegExp has the `y` (sticky) flag without `g` (global), a mismatch at `lastIndex` does not abort the loop; instead it increments `current_p` and continues scanning forward through the string, and never updates `lastIndex`.
- **Repro:** `var r = /b/y; r.lastIndex = 0; print("ab".replace(r, "X"), r.lastIndex);` outputs `aX 0` (expected `ab 0`).

### BUG-027: Undefined behavior passing `NULL` to `memset` in `ecma_regexp_initialize_context`
- **Severity:** Medium
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/operations/ecma-regexp-object.c:1206-1211`
- **Status:** CONFIRMED
- **Mechanism:** When a RegExp has 0 non-capturing groups (or 0 total groups), `jmem_heap_alloc_block(0)` returns `NULL`, which is passed directly as argument 1 to `memset(NULL, 0, 0)` (undefined behavior in C99/C11).
- **Repro:** Any RegExp without groups under UBSan, e.g. `/a/.test("a")`: `runtime error: null pointer passed as argument 1, which is declared to never be null` at lines 1207 and 1211.

### BUG-028: `ecma_op_dataview_create` truncates `byteOffset` >= `2^32` and evaluates offset twice
- **Severity:** Medium
- **Subsystem:** DataView
- **Location:** `jerry-core/ecma/operations/ecma-dataview-object.c:70-87`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_op_dataview_create` calls both `ecma_get_number(arguments_list_p[1], ...)` and `ecma_op_to_integer(arguments_list_p[1], ...)` (invoking `valueOf()` twice), and then casts `offset = (uint32_t) offset_num` without checking `offset_num <= UINT32_MAX`. Passing `4294967296` (`2^32`) invokes float-to-uint32 UB and wraps to `offset = 0`, succeeding instead of throwing `RangeError`.
- **Repro:** `var dv = new DataView(new ArrayBuffer(8), 4294967296); print(dv.byteOffset, dv.byteLength);` outputs `0 8` (expected `RangeError`).

### BUG-029: `TypedArray.prototype.set` with overlapping different-typed views clobbers unread source bytes
- **Severity:** Medium
- **Subsystem:** TypedArray
- **Location:** `jerry-core/ecma/builtin-objects/typedarray/ecma-builtin-typedarray-prototype.c:893-906`
- **Status:** CONFIRMED
- **Mechanism:** When `target.set(src, offset)` is called with two TypedArrays of different element types sharing the same `ArrayBuffer`, the loop copies element-by-element in-place without cloning the source buffer (violating ES2015 22.2.3.22.2 step 23). Writing a wider target element overwrites unread source elements.
- **Repro:** `var ab = new ArrayBuffer(4); var u8 = new Uint8Array(ab); u8[0]=1; u8[1]=2; var u16 = new Uint16Array(ab); u16.set(u8.subarray(0, 2)); print(u16[0], u16[1]);` outputs `1 0` (expected `1 2`).

### BUG-030: `ecma_typedarray_set_uint8_clamped_element` performs undefined `(uint8_t) NaN` cast
- **Severity:** Medium
- **Subsystem:** TypedArray
- **Location:** `jerry-core/ecma/operations/ecma-typedarray-object.c:191-202`
- **Status:** SUSPECTED
- **Mechanism:** For `value = NaN`, both `value > 255` and `value <= 0` evaluate to `false`, falling through to `clamped = (uint8_t) value`, which is undefined behavior in C (and may produce non-zero values depending on architecture/compiler instead of `0` per ES2015 `ToUint8Clamp`).

### BUG-031: `jerryx_module_check_cache` uses `jerry_has_property` instead of `jerry_has_own_property`
- **Severity:** Medium
- **Subsystem:** jerry-ext / module
- **Location:** `jerry-ext/module/module.c:120`
- **Status:** CONFIRMED
- **Mechanism:** The module cache is an ordinary JS object inheriting from `Object.prototype`. `jerryx_module_check_cache` checks `jerry_has_property(cache, module_name)`, which traverses the prototype chain. Resolving any unregistered module whose name exists on `Object.prototype` (e.g., `"toString"`, `"constructor"`, `"valueOf"`) succeeds and returns the prototype property instead of failing with "Module not found".
- **Repro:** Confirmed via C test: `jerryx_module_resolve("toString", ...)` returned `Object.prototype.toString` (`is_error=0, is_function=1`).

### BUG-032: Multiple defects in `jerryx_debugger_serial_*` (`debugger-serial.c`)
- **Severity:** Medium
- **Subsystem:** jerry-ext / debugger
- **Location:** `jerry-ext/debugger/debugger-serial.c:119-120, 168-173, 225, 333-337, 354, 363-366`
- **Status:** SUSPECTED
- **Mechanism:** (1) Lines 168-173: `case 'E':` (even parity) sets `options.c_cflag |= PARODD` instead of clearing `PARODD`, configuring odd parity instead of even parity. (2) Lines 225 & 354: if `tcflush()` fails, `jerryx_debugger_serial_configure_attributes` closes `fd` and returns `false`, and the caller `jerryx_debugger_serial_create` closes `fd` a second time (double `close`). (3) Lines 363-366: if `read()` or `set_blocking()` fails, `jerryx_debugger_serial_create` returns `false` without closing `fd` (descriptor leak). (4) Lines 333-337: `strncpy(tmp_config, config, CONFIG_SIZE)` does not NUL-terminate `tmp_config` if `strlen(config) >= 255`, causing a stack buffer over-read in `strtok`. (5) Lines 119-120: raw integer `115200` is passed to `cfsetispeed`/`cfsetospeed` instead of POSIX `B115200` constant.

### BUG-033: `jerryx_debugger_ws_create` succeeds and registers transport after failed handshake on disconnect
- **Severity:** Medium
- **Subsystem:** jerry-ext / debugger
- **Location:** `jerry-ext/debugger/debugger-ws.c:426-429`
- **Status:** SUSPECTED
- **Mechanism:** Line 426 checks `if (!is_handshake_ok && jerry_debugger_transport_is_connected ()) return false;`. When `jerryx_process_handshake` fails because the transport disconnected (line 158 asserts `!jerry_debugger_transport_is_connected()`), the `&&` condition is false, so `jerryx_debugger_ws_create` proceeds to allocate `header_p`, add it to the closed transport stack, and return `true`.

### BUG-034: `jerry_set_prototype` does not check for prototype cycles
- **Severity:** Medium
- **Subsystem:** Core API
- **Location:** `jerry-core/api/jerry.c:2824-2847`
- **Status:** SUSPECTED
- **Mechanism:** `jerry_set_prototype` directly assigns `obj_p->u2.prototype_cp` without checking whether `obj_p` is already in `proto_obj_val`'s prototype chain (unlike `ecma_op_object_set_prototype_of`). Setting `jerry_set_prototype(a, a)` or a cycle `a -> b -> a` causes any subsequent property lookup or `instanceof` to hang in an infinite loop.


### BUG-035: GC fails to mark VM stack contexts in suspended generators, causing use-after-free and live object reuse
- **Severity:** Critical
- **Subsystem:** GC / Generator
- **Location:** `jerry-core/ecma/base/ecma-gc.c:437-448`, `jerry-core/vm/opcodes.c:700-708`
- **Status:** CONFIRMED
- **Mechanism:** When a generator suspends, `opfunc_resume_executable_object` (`opcodes.c:700-708`) decrements the refcount of all objects stored on the saved VM stack, including objects inside active VM stack contexts (`VM_CONTEXT_FOR_OF` iterator & result, `VM_CONTEXT_FOR_IN` target object, `VM_CONTEXT_FINALLY_RETURN` / `VM_CONTEXT_FINALLY_THROW` saved values), relying on GC marking to keep them alive. However, `ecma_gc_mark_executable_object` (`ecma-gc.c:437`) advances `register_p += executable_object_p->frame_ctx.context_depth` and **completely skips** all stack context slots. When GC runs while the generator is suspended, those objects are freed and can be reallocated to unrelated objects, causing crashes or live object confusion upon `.next()`.
- **Repro:**
  ```js
  // Crash variant (Aborted, exit 134):
  function* g() { for (var x of [1, 2, 3]) { yield x; } }
  var it = g();
  it.next();
  for (var i = 0; i < 10000; i++) { ({a: i, b: [i]}); }
  it.next();

  // Live object-reuse corruption variant (returns {"a":9998,"b":[9998]} instead of {"secret":12345}):
  function* g2() { try { return { secret: 12345 }; } finally { yield 1; } }
  var it2 = g2();
  it2.next();
  for (var i = 0; i < 10000; i++) { ({a: i, b: [i]}); }
  print(JSON.stringify(it2.next()));
  ```

### BUG-036: Double-free, use-after-free, and memory leak in `TypedArray.prototype.toLocaleString`
- **Severity:** Critical
- **Subsystem:** TypedArray
- **Location:** `jerry-core/ecma/builtin-objects/typedarray/ecma-builtin-typedarray-prototype.c:2017, 2048-2058`
- **Status:** CONFIRMED
- **Mechanism:** In `ecma_builtin_typedarray_prototype_to_locale_string`: (1) `element_value` is freed at line 2017, but if `ecma_op_to_string(call_value)` fails at line 2049, line 2052 calls `ecma_free_value(element_value)` a **second time** (double-free -> ASan SEGV in `jmem_pools_collect_empty`). (2) On success at line 2058, `ret_value = ecma_make_string_value(str_p); ecma_deref_ecma_string(str_p);` immediately frees `str_p` when its refcount is 1 (use-after-free), and `call_value` is never freed (memory leak).
- **Repro:**
  ```js
  // Double-free -> ASan SEGV:
  Number.prototype.toLocaleString = function() { return { toString: function() { throw 42; } }; };
  try { new Float64Array([1.5]).toLocaleString(); } catch (e) {}

  // UAF + leak -> Aborted (exit 134):
  Number.prototype.toLocaleString = function() { return { toString: function() { return "A".repeat(100) + this; } }; };
  new Uint8Array([1, 2]).toLocaleString();
  ```

### BUG-037: `ecma_gc_free_object` ignores property hashmap on `WeakMap`/`WeakSet`, causing assertion crash / memory corruption
- **Severity:** Critical
- **Subsystem:** GC / WeakMap
- **Location:** `jerry-core/ecma/base/ecma-gc.c:1087-1091`
- **Status:** CONFIRMED
- **Mechanism:** When `ecma_gc_free_object` sweeps a `WeakMap` or `WeakSet` (`LIT_INTERNAL_MAGIC_STRING_CONTAINER` with `ECMA_CONTAINER_FLAGS_WEAK`), it walks `container_p->object.u1.property_list_cp` asserting `ECMA_PROPERTY_IS_PROPERTY_PAIR(prop_iter_p)` without checking for and skipping a leading `ECMA_PROPERTY_TYPE_HASHMAP` header (unlike `ecma_gc_mark_container_object` at lines 313-323 and `ecma_gc_free_properties` at lines 851-862). Once a `WeakMap`/`WeakSet` grows large enough to allocate a property hashmap (> ~32 entries), collecting it aborts in debug builds and misinterprets hashmap bytes as property pairs in release builds.
- **Repro:**
  ```js
  var keys = [];
  (function() {
    var wm = new WeakMap();
    for (var i = 0; i < 100; i++) { var k = {}; keys.push(k); wm.set(k, i); }
  })();
  for (var i = 0; i < 5000; i++) ({}); // Aborted (exit 134)
  ```

### BUG-038: Fast-array TOCTOU heap out-of-bounds read / NULL dereference in `Array.prototype.indexOf`, `lastIndexOf`, and `slice`
- **Severity:** Critical
- **Subsystem:** Array
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-array-prototype.c:829-888, 1596-1641, 1695-1739`
- **Status:** CONFIRMED
- **Mechanism:** `indexOf`, `lastIndexOf`, and `slice` capture `len` (and in `slice`, `use_fast_path`) before invoking user-observable JavaScript callbacks (`fromIndex.valueOf()`, `end.valueOf()`, or `Array.prototype.constructor` getter during `ecma_op_array_species_create`). If the callback shrinks `a.length = 0` or converts the fast array to normal mode, the subsequent fast-array loop continues dereferencing `buffer_p` using the stale `len` or `JMEM_CP_NULL`, causing out-of-bounds heap reads or NULL dereference crashes.
- **Repro:**
  ```js
  // Each crashes with Aborted (exit 134):
  var a = [1,2,3,4,5,6,7,8];
  a.indexOf(99, { valueOf: function() { a.length = 0; return 0; } });

  var b = [1,2,3,4,5,6,7,8];
  b.lastIndexOf(99, { valueOf: function() { b.length = 0; return 7; } });

  var c = [1,2,3,4,5,6,7,8];
  c.slice(0, { valueOf: function() { c.length = 0; return 8; } });

  var d = [1,2,3,4,5,6,7,8];
  Object.defineProperty(Array.prototype, "constructor", { get: function() { d.length = 0; return Array; } });
  d.slice(0);
  ```

### BUG-039: Out-of-bounds stack read/free and argument leak on spread error in `opfunc_spread_arguments`
- **Severity:** Critical
- **Subsystem:** VM / Spread
- **Location:** `jerry-core/vm/opcodes.c:447-450`
- **Status:** CONFIRMED
- **Mechanism:** When `ecma_op_get_iterator` fails during argument spreading, the error cleanup loop iterates `for (uint32_t j = i + 1; j < argument_list_len; j++) { ecma_free_value (*(++stack_top_p)); }`. Because `stack_top_p` already points to argument `i + 1` (not `i`), the pre-increment `++stack_top_p` skips and leaks argument `i + 1`, and on the final iteration reads and calls `ecma_free_value` on an out-of-bounds stack slot past the argument list.
- **Repro:**
  ```js
  function f() {}
  try { f(...123, {}); } catch (e) {} // Aborted (exit 134)
  ```

### BUG-040: Use-after-free in `RegExp.prototype.compile` when compiling a RegExp from itself
- **Severity:** Critical
- **Subsystem:** RegExp
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-regexp-prototype.c:344-352`
- **Status:** CONFIRMED
- **Mechanism:** When `RegExp.prototype.compile` is called with an existing RegExp object (`pattern_arg`), lines 345-348 call `ecma_bytecode_deref((ecma_compiled_code_t *) current_bc_p)` *before* `ecma_bytecode_ref((ecma_compiled_code_t *) target_bc_p)`. When `this === pattern_arg` (`current_bc_p == target_bc_p`) and the compiled RegExp bytecode has refcount 1 (e.g., evicted from `re_cache`), `ecma_bytecode_deref` frees `target_bc_p`, and lines 348-352 immediately dereference the freed bytecode (`ecma_bytecode_ref`, `target_bc_p->source`, `target_bc_p->header.status_flags`).
- **Repro:**
  ```js
  var r = new RegExp("foo" + "bar");
  for (var i = 0; i < 32; i++) { new RegExp("evict_" + i); }
  r.compile(r); // Aborted (exit 134)
  ```

### BUG-041: Stack buffer overflow and skipped prototype lazy properties in `ecma_op_object_get_property_names`
- **Severity:** Critical
- **Subsystem:** Objects / Enumeration
- **Location:** `jerry-core/ecma/operations/ecma-objects.c:1858-1965, 2012-2058, 2194-2266`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_op_object_get_property_names` computes `type = ecma_get_object_type(obj_p)` and `obj_is_builtin = ecma_get_object_is_builtin(obj_p)` once *outside* the prototype-chain `while (true)` loop (lines 1858-1859), and then dispatches lazy property listing inside the loop on `obj_p` instead of `prototype_chain_iter_p` (lines 1890-1965). This causes two defects: (1) Lazy properties of prototype objects (e.g., `Object.create(new String("abc"))` or `Object.create(new Uint8Array([1,2,3]))`) are never enumerated by `for-in`. (2) If `obj_p` is a `String` or `TypedArray` with `N` lazy index properties and its prototype is a fast array of length `M < N`, on the prototype iteration lines 1906/1942 push `N` items into `prop_names_p`, line 2017 overwrites `array_index_named_properties_count = M`, line 2194 allocates local array `names_p` of size `M`, and lines 2209-2246 write `N` entries into `names_p` -> stack buffer overflow (and `JERRY_ASSERT(array_index_name_pos < array_index_named_properties_count)` abort in debug).
- **Repro:**
  ```js
  // Stack buffer overflow / assertion crash (Aborted, exit 134):
  var s = new String("abcde");
  Object.setPrototypeOf(s, [1]);
  for (var k in s) { print(k); }

  // Missing lazy prototype properties (prints []):
  var o = Object.create(new String("abc"));
  var keys = [];
  for (var k in o) keys.push(k);
  print(JSON.stringify(keys));
  ```

### BUG-042: Use-after-free of heap-allocated float value in `String.fromCodePoint`
- **Severity:** Critical
- **Subsystem:** String
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-string.c:301-305`
- **Status:** SUSPECTED
- **Mechanism:** `ecma_builtin_string_object_from_code_point` calls `ecma_free_value(to_number_value)` on line 302 and then passes the already-freed `to_number_value` to `ecma_op_to_integer(to_number_value, &to_int_num)` on line 305. Whenever `to_number_value` is a heap-allocated `ecma_number_t` (e.g., any non-integer float like `1.5`, `-0.0`, `NaN`, or integer > `ECMA_INTEGER_NUMBER_MAX`), `ecma_free_value` returns the block to `jmem_pools` and overwrites its first bytes with the pool free-list pointer, which `ecma_op_to_integer` then reads as a `double` (use-after-free).

### BUG-043: Nested generator call in default parameter clears `current_function_obj_p`, causing NULL-dereference crash
- **Severity:** High
- **Subsystem:** Generator / Function
- **Location:** `jerry-core/ecma/operations/ecma-function-object.c:998, 1058`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_op_function_call_simple` sets `JERRY_CONTEXT(current_function_obj_p) = func_obj_p` on entry to a generator function (line 998) and unconditionally clears `JERRY_CONTEXT(current_function_obj_p) = NULL` on exit (line 1058) without saving/restoring the previous value. If a generator's default parameter expression invokes another generator `g2()`, `g2()` returns and clears `current_function_obj_p` to `NULL` before the outer generator executes `CBC_EXT_CREATE_GENERATOR`, crashing when `opfunc_create_executable_object` dereferences `JERRY_CONTEXT(current_function_obj_p)`.
- **Repro:**
  ```js
  function* g2() {}
  function* g1(x = g2()) { yield x; }
  g1(); // Aborted (exit 134)
  ```

### BUG-044: `ecma_free_all_enqueued_jobs` frees `PromiseResolveThenableJob` with wrong size and leaks `then`
- **Severity:** High
- **Subsystem:** Promise / JobQueue
- **Location:** `jerry-core/ecma/operations/ecma-jobqueue.c:84-92, 122-132, 353-364`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_free_all_enqueued_jobs` unconditionally calls `ecma_free_promise_reaction_job(job_p)` (which frees 2 `ecma_value_t` fields and `sizeof(ecma_job_promise_reaction_t)` = 8 bytes) on every remaining queued job, even when the job is an `ecma_job_promise_resolve_thenable_t` (3 `ecma_value_t` fields, 12 bytes). This leaks the 3rd field (`job_p->then`) and frees the wrong block size into `jmem_heap`, corrupting heap accounting and aborting in `jmem_finalize`.
- **Repro:** Confirmed via C test running `jerry_eval("new Promise(function(r) { r({ then: function() {} }); });", ...)` followed by `jerry_cleanup()` without draining the job queue -> `Aborted (exit 134)`.

### BUG-045: Infinite loop leading to OOM in `String.raw` when `next_index >= number_of_substitutions`
- **Severity:** High
- **Subsystem:** String
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-string.c:236-255`
- **Status:** CONFIRMED
- **Mechanism:** Inside the `while (true)` loop of `ecma_builtin_string_object_raw`, when `next_index >= number_of_substitutions`, line 238 executes `continue;` *before* `next_index++` at line 255. Thus `next_index` never advances and the loop repeatedly appends `raw[next_index]` forever until memory is exhausted (`ERR_OUT_OF_MEMORY`, exit code 10).
- **Repro:**
  ```js
  String.raw({ raw: ["a", "b"] }); // Infinite loop -> OOM (exit 10)
  ```

### BUG-046: `ecma_op_iterator_return` passes C `true` (`1`) instead of `ECMA_VALUE_TRUE`
- **Severity:** High
- **Subsystem:** Iterators / Generator
- **Location:** `jerry-core/ecma/operations/ecma-iterator-object.c:311`
- **Status:** CONFIRMED
- **Mechanism:** When `yield*` delegates `.return(value)` to an inner iterator that has no `return` method, line 311 calls `ecma_create_iter_result_object(value, true)` passing C `bool` `true` (`1`) instead of `ECMA_VALUE_TRUE`. This fails `JERRY_ASSERT(ecma_is_value_boolean(done))` in debug builds and stores a malformed tagged `ecma_value_t` (`1`) as the `done` property in release builds.
- **Repro:**
  ```js
  var it = {};
  it[Symbol.iterator] = function() { return { next: function() { return { value: 1, done: false }; } }; };
  function* g() { yield* it; }
  var gen = g();
  gen.next();
  gen.return(42); // Aborted (exit 134)
  ```

### BUG-047: `VM_OC_CONTEXT_END` ignores pending exception raised by `for-of` `iterator.return()`
- **Severity:** High
- **Subsystem:** VM / Exceptions
- **Location:** `jerry-core/vm/vm.c:3662-3679`
- **Status:** CONFIRMED
- **Mechanism:** Unlike `VM_OC_JUMP_AND_EXIT_CONTEXT` (lines 3702-3708), `VM_OC_CONTEXT_END` does not check `jcontext_has_pending_exception()` after `vm_stack_find_finally` closes a `for-of` iterator. If `iterator.return()` throws while exiting a `try { break; } finally {}` inside `for-of`, execution continues normally with an uncleared pending exception and aborts on the next throw or cleanup.
- **Repro:**
  ```js
  var it = {};
  it[Symbol.iterator] = function() {
    return { next: function() { return { value: 1, done: false }; }, return: function() { throw 42; } };
  };
  for (var x of it) { try { break; } finally {} }
  throw 1; // Aborted (exit 134) due to dangling pending exception
  ```

### BUG-048: `JSON.stringify` crashes on `NULL` string when `new String().toString()` throws
- **Severity:** High
- **Subsystem:** JSON
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-json.c:1174-1178`
- **Status:** CONFIRMED
- **Mechanism:** When stringifying a boxed `String` object, `ecma_builtin_json_serialize_property` calls `str_p = ecma_op_to_string(value)` and passes `str_p` directly to `ecma_make_string_value(str_p)` without checking `if (str_p == NULL)`. If `toString` throws, `str_p` is `NULL`, triggering a crash/assertion abort.
- **Repro:**
  ```js
  var s = new String("a");
  s.toString = function() { throw 1; };
  try { JSON.stringify(s); } catch (e) {} // Aborted (exit 134)
  ```

### BUG-049: Memory leak of `capability` in `Promise.resolve` / `Promise.reject` when resolve/reject function throws
- **Severity:** High
- **Subsystem:** Promise
- **Location:** `jerry-core/ecma/operations/ecma-promise-object.c:795-798`
- **Status:** CONFIRMED
- **Mechanism:** In `ecma_promise_reject_or_resolve`, when calling the capability's `resolve` or `reject` function returns `ECMA_VALUE_ERROR`, line 797 returns `func_ret` directly without calling `ecma_free_value(capability)`, leaking the capability object and its references.
- **Repro:**
  ```js
  try {
    Promise.resolve.call(function(exec) { exec(function() { throw 1; }, function() {}); }, 42);
  } catch (e) {} // Aborted (exit 134) in jmem_finalize
  ```

### BUG-050: Memory leak of `search_symbol` in `String.prototype.search` when `@@search` is non-callable
- **Severity:** High
- **Subsystem:** String
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-string-prototype.c:647-651`
- **Status:** CONFIRMED
- **Mechanism:** When `search_symbol` (`regexp[Symbol.search]`) is neither `undefined` nor `null` and `!ecma_op_is_callable(search_symbol)`, line 650 returns `ecma_raise_type_error(...)` without freeing `search_symbol`.
- **Repro:**
  ```js
  RegExp.prototype[Symbol.search] = {};
  try { "a".search("a"); } catch (e) {} // Aborted (exit 134) in jmem_finalize
  ```

### BUG-051: `ArrayIterator.prototype.next` crashes on frozen iterator at index 65535 and leaks large heap float indices
- **Severity:** High
- **Subsystem:** Iterators
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-array-iterator-prototype.c:104-110, 131, 158`
- **Status:** CONFIRMED
- **Mechanism:** (1) When `index == ECMA_ITERATOR_INDEX_LIMIT` (`65535`), line 104 writes `LIT_INTERNAL_MAGIC_STRING_ITERATOR_NEXT_INDEX` via `ecma_op_object_put(obj_p, prop_name_p, ..., true)` and asserts `JERRY_ASSERT(ecma_is_value_true(put_result))`. If the iterator is non-extensible/frozen (`Object.freeze(it)`), `ecma_op_object_put` fails and returns `ECMA_VALUE_ERROR`, crashing debug builds and leaving an unhandled pending exception in release builds. (2) Lines 106, 131, and 158 pass `ecma_make_uint32_value(index)` directly without freeing it, leaking heap-allocated floats when `index > ECMA_INTEGER_NUMBER_MAX`.
- **Repro:**
  ```js
  var a = { length: 65540 };
  var it = Array.prototype.keys.call(a);
  Object.freeze(it);
  for (var i = 0; i < 65537; i++) { it.next(); } // Aborted (exit 134)
  ```

### BUG-052: `StringIterator.prototype.next` `uint16_t` overflow wraps index `65534 + 2` to `0` on surrogate pair
- **Severity:** High
- **Subsystem:** Iterators
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-string-iterator-prototype.c:85-88, 132`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_builtin_string_iterator_prototype_object_next` guards against `position == ECMA_ITERATOR_INDEX_LIMIT` (`0xFFFF`), but on line 132 computes `iterator_index = (uint16_t)(position + result_size)`. When `position == 65534` (`0xFFFE`) and the string has a surrogate pair at index 65534 (`result_size == 2`), `(uint16_t)(65534 + 2)` overflows to `0`, restarting iteration from index 0 in an infinite loop.
- **Repro:**
  ```js
  var s = "a".repeat(65534) + "\uD83D\uDE00";
  var it = s[Symbol.iterator]();
  for (var c = 0; c < 65540; c++) { if (it.next().done) break; }
  print(c, it.next().value); // prints "65540 a" instead of terminating at 65535
  ```

### BUG-053: `ecma_op_same_value` uses `==` instead of `&&` for NaN check, breaking `Object.is` and frozen float properties
- **Severity:** High
- **Subsystem:** Conversion / Object
- **Location:** `jerry-core/ecma/operations/ecma-conversion.c:101-104`
- **Status:** CONFIRMED
- **Mechanism:** When comparing two float `ecma_value_t` values, line 101 writes `if (ecma_number_is_nan(x_num) == ecma_number_is_nan(y_num)) return true;` instead of `&&`. Whenever *neither* float is `NaN` (`false == false`), `ecma_op_same_value` unconditionally returns `true`. This makes `Object.is` return `true` for any two distinct non-integer floats (e.g., `1.5` and `2.5`), and allows `Object.defineProperty` to mutate non-writable, non-configurable (frozen) float properties!
- **Repro:**
  ```js
  print(Object.is(1.5, 2.5)); // true (expected false)
  var o = {};
  Object.defineProperty(o, "x", { value: 1.5, writable: false, configurable: false });
  Object.defineProperty(o, "x", { value: 999.5 });
  print(o.x); // 999.5 (should throw TypeError and remain 1.5)
  ```

### BUG-054: `parseFloat` compares only 1 byte of `"Infinity"` due to `sizeof(*infinity_str_p)`
- **Severity:** High
- **Subsystem:** Global
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-global.c:343`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_builtin_global_object_parse_float` checks `memcmp(infinity_str_p, current_p, sizeof(*infinity_str_p))`. Because `infinity_str_p` is `const lit_utf8_byte_t *`, `sizeof(*infinity_str_p)` evaluates to `1` instead of `lit_get_magic_string_size(LIT_MAGIC_STRING_INFINITY_UL)` (`8`). Any input starting with `'I'`, `'+I'`, or `'-I'` (e.g., `"Invalid"`, `"-I"`) is parsed as `Infinity` / `-Infinity` instead of `NaN`.
- **Repro:** `print(parseFloat("I"), parseFloat("Invalid"), parseFloat("-I"));` outputs `Infinity Infinity -Infinity`.

### BUG-055: `Object.freeze`, `Object.seal`, `Object.isFrozen`, and `Object.isSealed` ignore Symbol properties
- **Severity:** High
- **Subsystem:** Object
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-object.c:309, 367, 464`
- **Status:** CONFIRMED
- **Mechanism:** `Object.freeze`, `Object.seal`, and `ecma_builtin_object_test_integrity_level` (`Object.isFrozen` / `Object.isSealed`) call `ecma_op_object_get_property_names` without `ECMA_LIST_SYMBOLS`. Own Symbol-keyed properties are never made non-configurable/non-writable by `freeze`/`seal` and are ignored by `isFrozen`/`isSealed`.
- **Repro:**
  ```js
  var s = Symbol("x");
  var o = {}; o[s] = 1;
  Object.freeze(o);
  o[s] = 2;
  print(o[s], Object.isFrozen(o)); // prints "2 true" (expected "1 true" with o[s] unchanged)
  ```

### BUG-056: `Date.prototype.get*` on Invalid Date (`NaN`) returns string `"NaN"` instead of number `NaN`
- **Severity:** High
- **Subsystem:** Date
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-date-prototype.c:238-241`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_builtin_date_prototype_dispatch_get` returns `ecma_make_magic_string_value(LIT_MAGIC_STRING_NAN)` instead of `ecma_make_nan_value()` when the date's time value is `NaN`. Every `get*` / `getUTC*` method (`getFullYear`, `getMonth`, `getTime`, etc.) on an Invalid Date returns the string `"NaN"` instead of numeric `NaN`.
- **Repro:** `print(typeof new Date(NaN).getFullYear(), new Date(NaN).getFullYear() === "NaN");` outputs `string true`.

### BUG-057: Reversed subtraction causes `uint32_t` underflow and OOB read in `ecma_string_get_chars_fast`
- **Severity:** High
- **Subsystem:** String Helpers
- **Location:** `jerry-core/ecma/base/ecma-helpers-string.c:175`
- **Status:** SUSPECTED
- **Mechanism:** When handling `ECMA_STRING_CONTAINER_MAGIC_STRING_EX` (external magic strings with ID > `ECMA_DIRECT_STRING_MAX_IMM`), line 175 computes `lit_magic_string_ex_id_t id = (lit_magic_string_ex_id_t)(LIT_MAGIC_STRING__COUNT - string_p->u.magic_string_ex_id);` instead of `string_p->u.magic_string_ex_id - LIT_MAGIC_STRING__COUNT` (compare with lines 1297, 1344, 1468). Because `magic_string_ex_id >= LIT_MAGIC_STRING__COUNT`, this underflows `uint32_t` to a huge index and reads far out of bounds of `JERRY_CONTEXT(lit_magic_string_ex_array)`.

### BUG-058: `ecma_save_literals_add_compiled_code` reads `literal_p[0..argument_end-1]` past literal pool and truncates >64 KB strings
- **Severity:** High
- **Subsystem:** Snapshot / Literals
- **Location:** `jerry-core/ecma/base/ecma-literal-storage.c:370-373, 502`
- **Status:** SUSPECTED
- **Mechanism:** (1) In `ecma_save_literals_add_compiled_code`, lines 370-373 iterate `for (uint32_t i = 0; i < argument_end; i++) ecma_save_literals_append_value(literal_p[i], lit_pool_p);` on `literal_p` (which points to the function's literal pool, not the mapped argument names at the end of the bytecode which are separately processed at lines 392-402). When `argument_end > const_literal_end`, this reads into child bytecode pointers and raw bytecode instructions (or past the allocation) and can dereference arbitrary byte patterns matching `ECMA_TYPE_STRING` or `ECMA_TYPE_FLOAT`. (2) Line 502 truncates `length` to `uint16_t` (`*(uint16_t *) destination_p = (uint16_t) length`) while copying `length` bytes, corrupting snapshots containing string literals >= 65536 bytes.

### BUG-059: Multiple logic bugs in `String.prototype.startsWith`, `endsWith`, `indexOf`, and `lastIndexOf`
- **Severity:** Medium
- **Subsystem:** String
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-helpers.c:483, 590, 612-615, 692`
- **Status:** CONFIRMED
- **Mechanism:** (1) Line 590 (`startsWith`): checks `if (pos_num + start > original_len) break;` instead of `start + search_str_len > original_len`, doubling `pos_num` and causing `startsWith` to return `false` whenever `pos > length / 2`. (2) Lines 612-615 (`endsWith`): resets `if (start == 0) start = original_len;`, making `endsWith(s, 0)` and `endsWith(s, -5)` ignore the explicit end position. (3) Line 692 (`ecma_builtin_helper_string_find_index`): for empty search string `""`, ignores `start_pos` and returns `0` or `original_len`. (4) Line 483 (`ecma_builtin_helper_string_index_normalize`): converts `index` with `ecma_number_to_uint32`, wrapping `2^32` to `0`.
- **Repro:**
  ```js
  print("abcd".startsWith("d", 3), "abcd".startsWith("", 2)); // false false (expected true true)
  print("abc".endsWith("c", 0), "abc".endsWith("c", -5));     // true true (expected false false)
  print("abc".indexOf("", 2), "abc".lastIndexOf("", 1));      // 0 3 (expected 2 1)
  print("abc".indexOf("a", 4294967296));                      // 0 (expected -1)
  ```

### BUG-060: `String.prototype.repeat` and `String.prototype.substr` wrap 32-bit counts/indices via `ToUint32`
- **Severity:** Medium
- **Subsystem:** String
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-string-prototype.c:1123-1143, 1257`
- **Status:** CONFIRMED
- **Mechanism:** `repeat` and `substr` narrow `ToInteger` results through `ecma_number_to_uint32` without checking against `UINT32_MAX`, causing counts/indices >= `2^32` to wrap modulo `2^32`.
- **Repro:** `print(JSON.stringify("a".repeat(4294967297)), JSON.stringify("abc".substr(4294967296)));` outputs `"a" "abc"` (expected `RangeError` and `""`).

### BUG-061: `Object.preventExtensions` on a fast array prevents modifying existing writable elements
- **Severity:** Medium
- **Subsystem:** Array / Objects
- **Location:** `jerry-core/ecma/operations/ecma-objects.c:1168-1173`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_op_object_put_with_receiver` checks `if (ecma_op_object_is_fast_array(object_p))` and rejects writes when `!ecma_get_object_extensible(object_p)`, even when updating an *already-existing* writable index `< length`.
- **Repro:** `var a = [1, 2, 3]; Object.preventExtensions(a); a[0] = 99; print(a[0]);` outputs `1` (expected `99`).

### BUG-062: `TypedArray` indexed `[[Put]]` swallows `ToNumber` exceptions
- **Severity:** Medium
- **Subsystem:** TypedArray
- **Location:** `jerry-core/ecma/operations/ecma-objects.c:1234-1241`
- **Status:** CONFIRMED
- **Mechanism:** When `ecma_op_typedarray_set_index_prop` returns `false` because `ecma_op_to_number` threw an exception, lines 1236-1241 call `jcontext_release_exception()` and `return ecma_reject(is_throw)`, discarding the thrown exception in non-strict mode and replacing it with a generic `TypeError` in strict mode.
- **Repro:** `var ta = new Uint8Array(2); ta[0] = { valueOf: function() { throw "BOOM"; } }; print("no throw");` prints `no throw`.

### BUG-063: `TypedArray.prototype.indexOf` fails / invokes UB on negative `fromIndex < -length`
- **Severity:** Medium
- **Subsystem:** TypedArray
- **Location:** `jerry-core/ecma/builtin-objects/typedarray/ecma-builtin-typedarray-prototype.c:1741-1742`
- **Status:** CONFIRMED
- **Mechanism:** When `fromIndex` is negative, line 1742 casts `info.length + num_var` directly to `uint32_t` without clamping negative values to `0`, invoking float-to-uint32 UB and skipping the entire array.
- **Repro:** `print(new Uint8Array([10, 20, 30]).indexOf(10, -10));` outputs `-1` (expected `0`).

### BUG-064: `unescape` fails to reset `hex_digits` on invalid sequences and mishandles `%%xx`
- **Severity:** Medium
- **Subsystem:** Global
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-global.c:1095-1117`
- **Status:** CONFIRMED
- **Mechanism:** When parsing a `%xx` escape encounters a non-hex digit, `hex_digits` is not reset to `0`, so its accumulated bits bleed into the next valid `%xx` escape. Additionally, a second `'%'` immediately after `'%'` is consumed as a failed hex digit rather than starting a new escape.
- **Repro:** `print(unescape("%1z%41").charCodeAt(3), JSON.stringify(unescape("%%41")));` outputs `321 "%%41"` (expected `65 "%A"`).

### BUG-065: `JSON.stringify` ignores empty replacer array `[]`
- **Severity:** Medium
- **Subsystem:** JSON
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-json.c:899`
- **Status:** CONFIRMED
- **Mechanism:** `ecma_builtin_json_serialize_object` checks `context_p->property_list_p->item_count > 0` to decide whether a replacer property list was provided. When `[]` is passed as replacer, `item_count == 0`, so it falls back to serializing all own enumerable properties instead of `{}`.
- **Repro:** `print(JSON.stringify({a: 1, b: 2}, []));` outputs `{"a":1,"b":2}` (expected `{}`).

### BUG-066: `Promise.all` / `Promise.race` inverted `is_done` check skips iterator close and iterates rejected promise
- **Severity:** Medium
- **Subsystem:** Promise
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-promise.c:503-504, 530-538, 556`
- **Status:** CONFIRMED
- **Mechanism:** (1) On error in the iteration loop, `if (is_done) ecma_op_iterator_close(...)` is inverted (`is_done` is `false` when the iterator is still open), so open iterators are never closed when `Promise.resolve` throws. (2) When the input is not iterable, `ecma_promise_all_or_race_get_iterator` rejects the capability and returns the rejected promise object; the caller checks only `ECMA_IS_VALUE_ERROR` and proceeds to call `ecma_op_iterator_step` on the rejected promise itself.
- **Repro:**
  ```js
  var closed = false;
  var it = {};
  it[Symbol.iterator] = function() {
    return { next: function() { return { value: 1, done: false }; }, return: function() { closed = true; return {}; } };
  };
  var P = function(e) { e(function(){}, function(){}); };
  P.resolve = function() { throw 1; };
  Promise.all.call(P, it);
  print("closed:", closed); // false (expected true)
  ```

### BUG-067: `Generator.prototype.return` and `.throw` on completed generators ignore argument / fail to throw
- **Severity:** Medium
- **Subsystem:** Generator
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-generator-prototype.c:99-102`
- **Status:** CONFIRMED
- **Mechanism:** For an already-completed generator, `ecma_builtin_generator_prototype_object_do` unconditionally returns `{ value: undefined, done: true }` regardless of whether the operation was `.next()`, `.return(arg)` (must return `{ value: arg, done: true }`), or `.throw(err)` (must throw `err`).
- **Repro:** `function* g() {} var it = g(); it.next(); print(JSON.stringify(it.return(42)), JSON.stringify(it.throw("BOOM")));` prints `{"done":true} {"done":true}` without throwing.

### BUG-068: `Number.prototype.toString` wraps radix via `ToUint32` and `toFixed` drops minus sign for `|x| >= 1e21`
- **Severity:** Medium
- **Subsystem:** Number
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-number-prototype.c:270, 688-691`
- **Status:** CONFIRMED
- **Mechanism:** (1) `toString` narrows radix with `ecma_number_to_uint32`, accepting `4294967298` (`2^32 + 2`) as radix `2` instead of throwing `RangeError`. (2) `toFixed` strips the sign via `num = fabs(num)` before checking `num >= 1e21` and delegating to `ecma_number_to_decimal`, dropping the leading `'-'` for negative numbers with `|x| >= 1e21`.
- **Repro:** `print((10).toString(4294967298), (-1e21).toFixed(0));` outputs `1010 1e+21`.

### BUG-069: `Date.prototype[Symbol.toPrimitive]` accepts invalid hints, `setTime` returns unclipped value, and `new Date(obj)` calls `valueOf()` twice
- **Severity:** Medium
- **Subsystem:** Date
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-date-prototype.c:205, 639-641`, `jerry-core/ecma/builtin-objects/ecma-builtin-date.c:756-778`
- **Status:** CONFIRMED
- **Mechanism:** (1) `Date.prototype[Symbol.toPrimitive]` only checks `hint === "string" || hint === "default"`, silently treating any other string (e.g. `"bogus"`) as `"number"` instead of throwing `TypeError`. (2) `setTime` assigns `ecma_date_time_clip(time)` to the internal slot but returns the unclipped `time`. (3) `new Date(obj)` invokes `ToPrimitive` / `valueOf` twice on object arguments.
- **Repro:** `print(new Date(0)[Symbol.toPrimitive]("bogus"), new Date(0).setTime(1e20));` outputs `0 1e+20`.

### BUG-070: Multiple `Reflect` API contract violations (`preventExtensions`, `setPrototypeOf`, `defineProperty`, `apply`)
- **Severity:** Medium
- **Subsystem:** Reflect
- **Location:** `jerry-core/ecma/builtin-objects/ecma-builtin-reflect.c:91-166`
- **Status:** CONFIRMED
- **Mechanism:** (1) `Reflect.preventExtensions(o)` returns `o` instead of boolean `true`. (2) `Reflect.setPrototypeOf({}, 123)` and `Reflect.defineProperty({}, "a", 123)` swallow the `TypeError` for non-object proto/descriptor and return `false`. (3) `Reflect.apply(fn, null, null)` calls `fn()` with 0 arguments instead of throwing `TypeError` for non-object `argumentsList`.
- **Repro:**
  ```js
  var o = {};
  print(Reflect.preventExtensions(o) === o, Reflect.setPrototypeOf({}, 123), Reflect.defineProperty({}, "a", 123));
  // prints "true false false"
  ```

### BUG-071: `Map`/`Set` `forEach` omits 3rd argument & visits cleared entries; re-insertion after `delete` preserves stale order
- **Severity:** Medium
- **Subsystem:** Map / Set
- **Location:** `jerry-core/ecma/operations/ecma-container-object.c:505-512, 551-596, 680-683`
- **Status:** CONFIRMED
- **Mechanism:** (1) `ecma_op_container_foreach` passes only 2 arguments `(value, key)` instead of 3 `(value, key, container)` to the callback, and snapshots entries up front so entries deleted/cleared during iteration are still visited. (2) `delete` marks slots deleted in place and subsequent `set`/`add` reuses the deleted slot rather than appending, violating insertion-order semantics.
- **Repro:**
  ```js
  var m = new Map([[1, "a"], [2, "b"]]);
  m.forEach(function(v, k, self) { print(k, self === m); m.clear(); });
  // prints "1 false" then "2 false"
  ```

### BUG-072: `class C extends B` silently ignores primitive/null `B.prototype` and named class expressions omit inner binding
- **Severity:** Medium
- **Subsystem:** Class / Parser / VM
- **Location:** `jerry-core/vm/vm.c:1673-1701`, `jerry-core/parser/js/js-parser-expr.c:699-703`
- **Status:** CONFIRMED
- **Mechanism:** (1) `VM_OC_SET_CLASS_INHERITANCE` does not throw `TypeError` when the superclass's `prototype` property is a non-null primitive (e.g., `42`). (2) Named class expressions (`var X = class Inner { static f() { return Inner; } }`) do not create an immutable inner binding for `Inner` inside the class body.
- **Repro:**
  ```js
  function B() {} B.prototype = 42;
  class C extends B {} // Does not throw TypeError
  var X = class Inner { static f() { return typeof Inner; } };
  print(X.f()); // "undefined" (expected "function")
  ```

### BUG-073: `Array[Symbol.species]` is ignored by `ecma_op_array_species_create` and `Array` `length` setter ignores first `ToNumber` value
- **Severity:** Medium
- **Subsystem:** Array
- **Location:** `jerry-core/ecma/operations/ecma-array-object.c:694-699, 947-979`
- **Status:** CONFIRMED
- **Mechanism:** (1) `ecma_op_array_species_create` never reads `constructor[Symbol.species]`, breaking ES2015 `Array` subclassing (`slice`, `map`, `filter`, `concat`, `splice`). (2) `ecma_op_array_object_set_length` evaluates `ToNumber(new_value)` twice for objects, overwrites `new_len_num` with the second result, and compares the second result against itself instead of comparing `ToUint32(first)` against `ToNumber(second)`.
- **Repro:**
  ```js
  var i = 0; var a = [];
  a.length = { valueOf: function() { return i++ === 0 ? NaN : 5; } };
  print(a.length); // 5 (expected RangeError)
  ```

### BUG-074: `for (var x = init in obj)` skips executing `init` (violating Annex B)
- **Severity:** Medium
- **Subsystem:** Parser
- **Location:** `jerry-core/parser/js/js-parser-statm.c:1307-1322`
- **Status:** CONFIRMED
- **Mechanism:** In non-strict mode, `parser_parse_for_statement_start` emits an unconditional `CBC_JUMP_FORWARD` over the `var` initializer expression in `for (var x = init in obj)` (comment: `/* Initialiser is never executed. */`), violating ES2015 Annex B.3.6 which requires evaluating `init` and assigning it to `x` even when `obj` has no properties.
- **Repro:** `var x = 0; for (var x = 42 in {}) {} print(x);` outputs `0` (expected `42`).

### BUG-075: Undefined behavior: 64-bit shift overflow, signed left-shift overflow / negative shift, and `INT32_MIN` negation
- **Severity:** Medium
- **Subsystem:** Conversion / VM / Math
- **Location:** `jerry-core/ecma/base/ecma-helpers-conversion.c:671`, `jerry-core/vm/vm.c:3058`, `jerry-core/vm/opcodes-ecma-bitwise.c:78`, `jerry-core/ecma/base/ecma-helpers-number.c:673, 678`, `jerry-core/ecma/operations/ecma-typedarray-object.c:153`
- **Status:** CONFIRMED
- **Mechanism:** Multiple C undefined behaviors verified under UBSan: (1) `ecma_utf8_string_to_number` shifts a `uint64_t` by 64 (`shift exponent 64 is too large for 64-bit type 'long unsigned int'`). (2) `vm_loop` and `opfunc_bitwise` left-shift signed `int32_t` values into the sign bit (`1 << 31`). (3) `ecma_integer_multiply` left-shifts negative signed `ecma_integer_value_t` values (`2 * -5`). (4) `ecma_typedarray_setter_number_to_uint32` negates `(int32_t) 0x80000000` (`-2147483648`).
- **Repro:** Run under UBSan: `0.1; 1 << 31; 2 * -5; new Uint32Array(1)[0] = -2147483648;` — triggers all 4 UBSan runtime errors.

### BUG-076: `ecma_op_get_prototype_from_constructor` leaks non-object `prototype` values
- **Severity:** Medium
- **Subsystem:** Function / Prototype
- **Location:** `jerry-core/ecma/operations/ecma-function-object.c:924-932`
- **Status:** SUSPECTED
- **Mechanism:** When `ecma_op_object_get_by_magic_id(ctor_obj_p, LIT_MAGIC_STRING_PROTOTYPE)` returns a non-object value `proto`, `ecma_op_get_prototype_from_constructor` falls back to `ecma_builtin_get(default_proto_id)` without calling `ecma_free_value(proto)`. Any heap-allocated primitive (dynamic string, float, symbol) returned by `ctor.prototype` is permanently leaked.

### BUG-077: `vm_run_eval` debugger `chain_index` error leaks `this_binding` and `bytecode_data_p`
- **Severity:** Medium
- **Subsystem:** VM / Debugger
- **Location:** `jerry-core/vm/vm.c:314-319`
- **Status:** SUSPECTED
- **Mechanism:** When `chain_index != 0` fails to locate the requested lexical environment in debugger eval mode, lines 317-318 return `ecma_raise_range_error(...)` directly without freeing `this_binding` (if copied) or dereferencing `bytecode_data_p` (`ecma_bytecode_deref`), leaking the compiled eval bytecode and `this_binding`.

### BUG-078: `jmem_heap_alloc` fast path can set `jmem_heap_list_skip_p` to `area + 0xffffffff`
- **Severity:** Medium
- **Subsystem:** Memory Allocator
- **Location:** `jerry-core/jmem/jmem-heap.c:167-172`
- **Status:** SUSPECTED
- **Mechanism:** When allocating from the first free block in the heap fast path (`free_block_p->size == size`), line 170 sets `JERRY_CONTEXT(jmem_heap_list_skip_p) = JMEM_HEAP_GET_ADDR_FROM_OFFSET(free_block_p->next_offset)` without checking `free_block_p->next_offset == JMEM_HEAP_END_OF_LIST` (`0xffffffff`). If the allocated block was the only free block, `jmem_heap_list_skip_p` becomes a wild pointer (`area + 0xffffffff`), causing out-of-bounds pointer arithmetic/dereferences on subsequent allocations.
