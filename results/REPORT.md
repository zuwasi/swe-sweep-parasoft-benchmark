# Parasoft C/C++test vs SWE-sweep: bug detection on the 14 C/C++ SWESweep repositories

Date: 2026-11-12. Tool: Parasoft C/C++test Standard: 2026.1.3 for the six C repos (Flow Analysis Standard + MISRA C 2025 + SEI CERT C) and 2025.2.0 for the eight C++ repos (Flow Analysis Standard + MISRA C++ 2023 + SEI CERT C++ + SEI CERT C). Benchmark: SWE-sweep (swesweep.com), 488 accepted bugs across the 14 C/C++ repositories.

## Headline

- Parasoft flags at least one finding directly on the changed lines of **183/488 bugs (37.5%)** (any rule; line in the bug's changed region).
- On the **162** bugs whose defect mechanism is one a static analyzer targets (classification below), it flags **67 (41.4%)** at the changed region and **40 (24.7%)** on the exact removed line.
- Strictly on a line the fix removed or changed: **103/488 (21.1%)**.
- Flow Analysis (deep interprocedural checks, BD-*) alone: **16/488 (3.3%)**.
- SWE-sweep's own best process (LLM agents searching the whole repo) resolved **22.0/488 bugs (4.5%)** across these same repositories.

## Per-repository results

| Repo | Lang | Bugs | Found: FA | CERT | MISRA | Found (region) | % (region) | % (strict) | SWE-sweep best resolved |
|---|---|---|---|---|---|---|---|---|---|
| duckdb | C++ | 109 | 4 | 32 | 46 | 56 | 51.4% | 25.7% | 2.8% |
| gdal | C++ | 72 | 0 | 2 | 3 | 3 | 4.2% | 1.4% | 0.0% |
| arrow | C++ | 47 | 0 | 6 | 9 | 10 | 21.3% | 8.5% | 2.1% |
| opencv | C++ | 47 | 2 | 12 | 31 | 32 | 68.1% | 29.8% | 2.1% |
| tarantool | C | 40 | 0 | 4 | 5 | 5 | 12.5% | 7.5% | 7.5% |
| cvc5 | C++ | 38 | 0 | 7 | 15 | 17 | 44.7% | 26.3% | 2.6% |
| php-src | C | 26 | 1 | 6 | 11 | 11 | 42.3% | 26.9% | 0.0% |
| micropython | C | 22 | 0 | 4 | 4 | 4 | 18.2% | 13.6% | 0.0% |
| proj | C++ | 21 | 0 | 9 | 7 | 10 | 47.6% | 28.6% | 9.5% |
| godot | C++ | 17 | 0 | 6 | 6 | 7 | 41.2% | 35.3% | 0.0% |
| jerryscript | C | 15 | 4 | 12 | 13 | 13 | 86.7% | 80.0% | 20.0% |
| hdf5 | C | 14 | 5 | 5 | 6 | 6 | 42.9% | 28.6% | 28.6% |
| z3 | C++ | 11 | 0 | 0 | 3 | 3 | 27.3% | 9.1% | 0.0% |
| libexpat | C | 9 | 0 | 2 | 5 | 6 | 66.7% | 44.4% | 44.4% |

| Aggregate | Bugs | Found (region) | % (region) | % (strict) | SWE-sweep |
|---|---|---|---|---|---|
| 14 C/C++ repos | 488 | 183 | 37.5% | 21.1% | 4.5% |

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
disagreements by reading the snippets, with the 16 bugs caught by Parasoft Flow
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
analyzer's wheelhouse, Parasoft flagged **67 (41.4%)** at the changed region and
**40 (24.7%)** strictly on a removed line, above the all-bugs rates (37.5% /
21.1%). On its home ground, the class of bug it was built to catch, the tool
clears the 40% mark: roughly four in ten mechanism bugs flagged with an
auditable pointer to the defect. The classification does not change the
headline; it changes the division of labor:

- About one third of real-world bugs are mechanism defects a deterministic tool
  can flag, and Parasoft flags a meaningful share of them with auditable
  findings on the defective lines.
- The remaining two thirds are logic and requirements defects. Neither static
  analysis (by design) nor the SWE-sweep agents (4.5% overall) reliably finds
  those. They are exactly what design review, requirements traceability,
  requirements-based testing, and structural coverage are for in regulated
  development.
- Caveats: labels are per-bug single-mechanism judgments from fix snippets;
  19 bugs could not be classified. After the third pass, every remaining
  low-confidence label that could move the conditional rate has been re-judged
  with pre-image context; the rate is bracketed at 38.8% to 41.4% across
  independent passes and does not hinge on any single judgment.

## Methodology

1. For every C/C++ repo in SWE-sweep's publication split, the oracle patches (one per accepted bug) were parsed: each patch names the pre-fix file blob hash and the exact changed lines in the pre-fix file.
2. Each pre-fix file version (679 file versions total) was materialized from git at the exact blob hash, so analysis targets byte-identical bug-era code.
3. Compile flags came from each project's own build system (CMake configure with CMAKE_EXPORT_COMPILE_COMMANDS=ON for 11 repos, `make -n` for micropython/php-src, scons compiledb for godot). gdal required building PROJ from source; cvc5 required building GMP 6.3 from source.
4. Parasoft C/C++test (cpptestcli) ran Flow Analysis Standard + MISRA C 2025 + CERT C (C repos) or MISRA C++ 2023 + CERT C++ (C++ repos) on those files in WSL, 6 parallel runs.
5. A bug counts as *found (region)* when any violation lands on any line of the bug's changed region in the pre-fix file; *strict* when it lands on a line the fix removed/rewrote.

## Reading the numbers honestly

- Scope: analysis ran on the bug files only (not whole-repo search), so this measures detection on the buggy code, not autonomous discovery in a 1M-line repo. SWE-sweep's agents had to search the whole repo without hints; we pointed Parasoft at the bug files.
- Rule mix: most hits are coding-standard rules (CERT/MISRA) firing on the buggy lines, e.g. CERT INT31 (unsafe integer conversion) and ARR39 (pointer arithmetic), MISRA 0.1.2 (unused value), 8.0.1. Deep Flow Analysis findings (null deref, overflow, OOB) account for 16 of the 183 found bugs.
- Coverage gaps: a handful of pre-image blobs (13 of 679) were absent from fetched git history; cvc5's generated headers mostly mismatch the bug-era code, so its 44.7% is a lower bound; gdal's large generated/external surface made many files fail to preprocess (4.2%).
- SWE-sweep percentages are each repo's best published agent result (micro-averaged per repo on their leaderboard).

## Top rules hitting bug lines (all repos)

| Rule | Found-bug hits | Meaning |
|---|---|---|
| MISRACPP2023-8_0_1-b | 53 | side effects in assertions / admissibility |
| CERT_C-MSC41-a | 46 | unused return value |
| MISRACPP2023-6_9_2-a | 35 | unused value |
| MISRACPP2023-9_5_1-a | 33 | cast to void of a value with side effects |
| MISRACPP2023-9_3_1-b | 25 | dead code / unreachable |
| MISRACPP2023-7_0_5-a | 24 | expression result unused |
| MISRACPP2023-11_6_1-a | 22 | void* to data pointer cast |
| MISRACPP2023-0_1_2-a | 20 | value never read |
| CERT_C-INT31-j | 19 | integer conversion overflow |
| CERT_C-ARR39-b | 17 | invalid pointer arithmetic |
| MISRACPP2023-7_0_6-a | 19 | unused static function |

## Artifacts

- Per-bug detail: `C:\Users\danie\swesweep-parasoft-benchmark\reports\<repo>_result.json`
- Category breakdown: `C:\Users\danie\swesweep-parasoft-benchmark\reports\category_breakdown.json`
- Raw Parasoft XML reports: `C:\Users\danie\swesweep-parasoft-benchmark\reports\<repo>\` and scratch `~\.swesweep_run\<repo>\run_*\rep\`
- Scripts: `C:\Users\danie\swesweep-parasoft-benchmark\scripts\`
