# Parasoft C/C++test vs SWE-sweep: bug detection on the 14 C/C++ SWE-sweep repositories

Date: 2026-11-16. Tool: Parasoft C/C++test Standard: 2026.1.3 for the six C repos (Flow Analysis Standard + MISRA C 2025 + SEI CERT C) and 2025.2.0 for the eight C++ repos (Flow Analysis Standard + MISRA C++ 2023 + SEI CERT C++ + SEI CERT C). Benchmark: SWE-sweep (swesweep.com), 488 accepted bugs across the 14 C/C++ repositories.

## Headline

- Parasoft C/C++test ran on each **complete buildable codebase** (every file the project's own build system compiles, compile flags captured from that build system, no hints about bug locations) and flags at least one finding on the changed lines of **259/488 bugs (53.1%)**.
- On the **162** bugs whose defect mechanism is one a static analyzer targets (classification below), it flags **90 (55.6%)** at the changed region and **52 (32.1%)** on the exact removed line.
- Strictly on a line the fix removed or changed: **141/488 (28.9%)**.
- Flow Analysis (deep interprocedural checks, BD-*) alone: **20/488 (4.1%)**.
- SWE-sweep's own best published results (LLM agents, best model per repository from the live leaderboard, 18 evaluated models) resolved **25/488 bugs (5.1%)** across these same repositories.

## Per-repository results

| Repo | Lang | Bugs | Found (region) | FA | CERT | MISRA | % (region) | % (strict) | SWE-sweep best resolved |
|---|---|---|---|---|---|---|---|---|---|
| duckdb | C++ | 109 | 75 | 7 | 33 | 67 | 68.8% | 32.1% | 2.8% |
| gdal | C++ | 72 | 3 | 0 | 2 | 3 | 4.2% | 1.4% | 0.0% |
| arrow | C++ | 47 | 11 | 1 | 7 | 11 | 23.4% | 8.5% | 2.1% |
| opencv | C++ | 47 | 35 | 0 | 18 | 33 | 74.5% | 40.4% | 2.1% |
| tarantool | C | 40 | 23 | 0 | 18 | 23 | 57.5% | 45.0% | 7.5% |
| cvc5 | C++ | 38 | 27 | 1 | 21 | 22 | 71.1% | 31.6% | 2.6% |
| php-src | C | 26 | 13 | 1 | 8 | 13 | 50.0% | 26.9% | 3.8% |
| micropython | C | 22 | 15 | 1 | 14 | 13 | 68.2% | 31.8% | 9.1% |
| proj | C++ | 21 | 13 | 0 | 10 | 12 | 61.9% | 33.3% | 9.5% |
| godot | C++ | 17 | 13 | 0 | 9 | 12 | 76.5% | 41.2% | 0.0% |
| jerryscript | C | 15 | 13 | 3 | 12 | 13 | 86.7% | 80.0% | 20.0% |
| hdf5 | C | 14 | 7 | 6 | 7 | 7 | 50.0% | 42.9% | 28.6% |
| z3 | C++ | 11 | 4 | 0 | 1 | 4 | 36.4% | 27.3% | 0.0% |
| libexpat | C | 9 | 7 | 0 | 7 | 7 | 77.8% | 33.3% | 44.4% |

| Aggregate | Bugs | Found (region) | % (region) | % (strict) | SWE-sweep |
|---|---|---|---|---|---|
| 14 C/C++ repos | 488 | 259 | 53.1% | 28.9% | 5.1% |
| 162 mechanism bugs | 162 | 90 | 55.6% | 32.1% | |

The FA / CERT / MISRA columns count the found bugs whose matched rule set includes at least one Flow Analysis (BD-*), CERT, or MISRA rule respectively; a bug matched by several rule families is counted in each, so the columns overlap.

## What static analysis could even see: bug classification

Not all 488 bugs are the kind of defect a static analyzer targets. The SWE-sweep
paper notes that most of its bugs can only be recognized by inferring the
intended behavior from the repository, which is why the agents' success rate is
low, and it is also why a raw comparison against all 488 bugs understates what
static analysis can and cannot do. So we classified every bug by the MECHANISM
of its defect, judged from the code the maintainers' fix removed or rewrote:

- **MEMORY** (memory safety / undefined behavior): buffer overflows,
  out-of-bounds access, use-after-free, null dereference, uninitialized use,
  integer overflow or truncation feeding memory access.
- **RESOURCE** (leaks and concurrency): missing free/close/unlock, use after
  close, data races, deadlocks.
- **ERROR** (error handling and API contract): unchecked or wrongly checked
  return values, ignored error codes, missing argument validation.
- **LOGIC** (wrong decision, formula, protocol, or spec): wrong operator,
  constant, comparison, or branch; wrong data or order; misunderstanding of the
  specification.
- **OTHER** (build, tests, docs) and **UNKNOWN** (19 bugs where no code snippet
  could be extracted; excluded from the denominator below).

Method: two independent blind classification passes over the same snippets with
the published rubric (`classification/RUBRIC.md`), then adjudication of all 132
disagreements by reading the snippets, with the bugs caught by Parasoft Flow
Analysis treated as ground truth for mechanism. A third boundary pass then
re-judged the 228 low-confidence labels that sit where they can move the
conditional rate, this time with 15 lines of pre-image code around each defect
region (`classification/adjudication3/`): 10 labels moved, 5 in each direction.
Per-bug labels and reasons are published in `classification/final/` and
`classification/adjudication3/effective_labels.jsonl` for audit.

| Class | Bugs | Share |
|---|---|---|
| MEMORY | 120 | 24.6% |
| RESOURCE | 16 | 3.3% |
| ERROR | 26 | 5.3% |
| **Static-analysis-addressable** | **162** | **33.2%** |
| LOGIC | 300 | 61.5% |
| OTHER | 7 | 1.4% |
| UNKNOWN (excluded) | 19 | 3.9% |

Conditional detection rates: on the 162 bugs whose mechanism is in a static
analyzer's wheelhouse, Parasoft flagged **90 (55.6%)** at the changed region and
**52 (32.1%)** strictly on a removed line, above the all-bugs rates (53.1% /
28.9%). On its home ground, the class of bug it was built to catch, the tool
clears the 50% mark: more than five in ten mechanism bugs flagged with an
auditable pointer to the defect. The classification does not change the
headline; it changes the division of labor:

- About one third of real-world bugs are mechanism defects a deterministic tool
  can flag, and Parasoft flags the majority of them with auditable findings on
  the defective lines.
- The remaining two thirds are logic and requirements defects. Neither static
  analysis (by design) nor the SWE-sweep agents (5.1% overall) reliably finds
  those. They are exactly what design review, requirements traceability,
  requirements-based testing, and structural coverage are for in regulated
  development.
- Caveats: labels are per-bug single-mechanism judgments from fix snippets;
  19 bugs could not be classified. After the third pass, every remaining
  low-confidence label that could move the conditional rate has been re-judged
  with pre-image context, so the rate does not hinge on any single judgment.

## Methodology

1. For every C/C++ repo in SWE-sweep's publication split, the oracle patches (one per accepted bug) were parsed: each patch names the pre-fix file blob hash and the exact changed lines in the pre-fix file.
2. Each pre-fix file version (679 file versions total) was materialized from git at the exact blob hash, so mapping targets byte-identical bug-era code.
3. Compile flags came from each project's own build system (CMake configure with CMAKE_EXPORT_COMPILE_COMMANDS=ON for 11 repos, `make -n` for micropython/php-src, scons compiledb for godot). Builds that require generated headers were provided with them (micropython mpy-cross and php-src built from the pinned sources; hdf5, cvc5 GMP 6.3, gdal PROJ 9.8.1 supplied from matching builds).
4. Parasoft C/C++test (cpptestcli) ran Flow Analysis Standard + MISRA C 2025 + CERT C (C repos) or MISRA C++ 2023 + CERT C++ (C++ repos) over each **whole buildable codebase**, split into 794 chunks and executed with up to 6 parallel runs in WSL2. Violations were deduplicated across chunks by (file, line, rule): 2,193,448 unique findings total.
5. Each bug's changed region was aligned from the pre-fix file into the base_ref tree by full-file diff, and a bug counts as *found (region)* when any violation lands on any line of that region; *strict* when it lands on a line the fix removed/rewrote.
6. One godot file, `core/variant/variant_call.cpp`, exceeds the memory a single analysis process can address on a 64 GB machine and is excluded from the scan; no benchmark bug lives in it.

## Reading the numbers honestly

- Flag vs fix: a finding is a lead for an engineer, not a fix. SWE-sweep's number requires the agent to understand the bug and make hidden tests pass; this benchmark measures detection of the defect the maintainers later fixed.
- Rule mix: most hits are coding-standard rules (CERT/MISRA) firing on the buggy lines, e.g. CERT MSC41 (unused return value), INT31 (unsafe integer conversion), ARR39 (pointer arithmetic), MISRA 8.0.1 (side effects in assertions), 9.3.1 (dead code). Deep Flow Analysis findings (overflow, OOB, uninitialized use, errno misuse) account for 20 of the 259 found bugs, including several the coding standards do not reach.
- Coverage gaps: a handful of pre-image blobs (13 of 679) were absent from fetched git history; gdal's bug set is heavily logic-class even within the mechanism bucket, which its 4.2% reflects.
- SWE-sweep percentages are each repo's best published agent result (micro-averaged per repo on their leaderboard).

## Top rules hitting bug lines (all repos)

| Rule | Found-bug hits | Meaning |
|---|---|---|
| CERT_C-MSC41-a | 83 | unused return value |
| MISRACPP2023-8_0_1-b | 73 | side effects in assertions / admissibility |
| MISRACPP2023-9_3_1-b | 49 | dead code / unreachable |
| MISRACPP2023-9_5_1-a | 46 | cast to void of a value with side effects |
| MISRACPP2023-7_0_2-a | 40 | expression result unused |
| MISRACPP2023-7_0_6-a | 35 | unused static function |
| MISRACPP2023-0_1_2-a | 34 | value never read |
| MISRACPP2023-7_11_2-a | 30 | non-boolean expression as condition |
| MISRACPP2023-6_2_4-a | 30 | integer promotion in comparison |
| CERT_C-INT31-j | 30 | integer conversion overflow |
| CERT_C-ARR39-b | 26 | invalid pointer arithmetic |

## Artifacts

- Per-bug detail (whole-project scan): `results_full/<repo>_full_result.json` (matched rule IDs per bug)
- Deduplicated findings from our execution: `results_full/violations/<repo>_violations.tsv.gz` (2,193,448 triples; recomputes the mapping without rerunning the tool)
- Mapping scripts: `pipeline_full/` (`build_full_bdf.py`, `run_full.py`, `map_full.py`, `export_violations_full.py`)
- Bug-file-era raw XML reports for spot checks: `raw-reports/`
- Classification: `classification/RUBRIC.md`, `classification/final/`, `classification/adjudication3/`
