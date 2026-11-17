# Parasoft C/C++test vs SWE-sweep: static analysis versus autonomous LLM agents on real-world C/C++ bugs

**ESL (Engineering Software Lab) | eswlab.com** — benchmark, reconstruction pipeline, and raw evidence.

We took the 14 C/C++ repositories from [SWE-sweep](https://swesweep.com) ("SWE-sweep: Can Agents Autonomously Find and Fix Bugs?", Lieret et al., 2026), checked out each repository at its bug-era base ref, and ran **Parasoft C/C++test** (Flow Analysis Standard + MISRA C 2025 + SEI CERT C for C repos on C/C++test Standard 2026.1.3; Flow Analysis Standard + MISRA C++ 2023 + SEI CERT C++ + SEI CERT C for C++ repos on 2025.2.0) on each **complete buildable codebase**: every file each project's own build system compiles, with the compile flags captured from that build system. The tool was given no hints about where the bugs are; this is exactly how static analysis runs in normal development. We then measured how many bugs the tool flags on the lines the maintainers-confirmed fixes changed, and compared that with the best autonomous agent result SWE-sweep itself published.

## Results

| Repo | Lang | Bugs | Parasoft found (region) | % (region) | % (strict line) | SWE-sweep best agent |
|---|---|---|---|---|---|---|
| duckdb | C++ | 109 | 75 | 68.8% | 32.1% | 2.8% |
| gdal | C++ | 72 | 3 | 4.2% | 1.4% | 0.0% |
| arrow | C++ | 47 | 11 | 23.4% | 8.5% | 2.1% |
| opencv | C++ | 47 | 35 | 74.5% | 40.4% | 2.1% |
| tarantool | C | 40 | 23 | 57.5% | 45.0% | 7.5% |
| cvc5 | C++ | 38 | 27 | 71.1% | 31.6% | 2.6% |
| php-src | C | 26 | 13 | 50.0% | 26.9% | 3.8% |
| micropython | C | 22 | 15 | 68.2% | 31.8% | 9.1% |
| proj | C++ | 21 | 13 | 61.9% | 33.3% | 9.5% |
| godot | C++ | 17 | 13 | 76.5% | 41.2% | 0.0% |
| jerryscript | C | 15 | 13 | 86.7% | 80.0% | 20.0% |
| hdf5 | C | 14 | 7 | 50.0% | 42.9% | 28.6% |
| z3 | C++ | 11 | 4 | 36.4% | 27.3% | 0.0% |
| libexpat | C | 9 | 7 | 77.8% | 33.3% | 44.4% |
| **Total** | | **488** | **259** | **53.1%** | **28.9%** | **~5.1%** |
| **Of which: the 162 mechanism bugs** | | **162** | **90** | **55.6%** | **32.1%** | | |

- Flow Analysis (deep interprocedural defect checks, BD-*) alone caught **20/488 (4.1%)**: integer wraparound, use-before-initialization, index out of range, unreachable switch branches, unused values, errno misuse. See the per-repo rule breakdowns in `results/REPORT.md`.
- The rest of the matches come from MISRA/CERT coding-standard rules landing on the buggy lines.
- **Bug classification.** We classified all 488 bugs by defect mechanism with two independent blind passes plus adjudication, then a third boundary pass re-judged the 228 labels closest to the static-analysis boundary with full pre-image context (`classification/RUBRIC.md`, `classification/adjudication3/`). Only **162 (33.2%)** are the kind of defect a static analyzer targets (memory/UB 120, leaks/concurrency 16, error handling 26); the other two thirds are logic and requirements bugs. On those 162, Parasoft flagged **90 (55.6%)** at the changed region and **52 (32.1%)** strictly on the removed line, above its all-bugs rates (53.1% / 28.9%). The logic bugs are what review, requirements-based testing, and structural coverage exist for, and neither the static analyzer nor the LLM agents (5.1%) reliably find them.

## Follow-up experiment: Claude Code, cold start, on one repository

To probe the strongest agentic setup we could assemble against the same ground truth, we ran **Claude Code** (claude 2.1.303, subscription default model) equipped with the open-source **Claude-BugHunter** skill bundle (83 bug-hunting skills, MIT / CC-BY-4.0) on **duckdb** at exactly this benchmark's start state (v0.10.0, commit `20b1486d`). Cold start in the strict sense: a fresh session, no memory, no `CLAUDE.md` in the tree, skills installed project-locally only, filesystem deny rules blocking any access to this repository or any benchmark data, and a prompt containing no hints of any kind. In about 65 minutes of engagement (one interruption by the subscription rate limit), the agent built duckdb with AddressSanitizer and UBSan, ran parallel code reviews across storage, parquet, C API, window, optimizer, casts, and self-terminated with an explicit coverage statement. It reported **79 countable findings** (about 95 defects including minor items), most verified with SQL reproductions on its own sanitizer build.

Mapped against the same 109 accepted duckdb bugs with the same changed-line matching rule as the Parasoft evaluation:

| Method | Found (changed region) | Found (exact defect line) |
| --- | --- | --- |
| Parasoft C/C++test, whole-codebase scan (this benchmark) | **75 (68.8%)** | 60 (55.0%) |
| SWE-sweep leaderboard best on duckdb | 3 (2.8%) | n/a |
| Claude Code + Claude-BugHunter, one cold-start engagement | **7 (6.4%)** | 6 (5.5%) |

Reading: the strongest agentic setup we could assemble beats the published leaderboard best on duckdb, but only marginally, and it remains an order of magnitude below the deterministic tool. Caveats, stated plainly: the engagement ran about one hour rather than the 12-hour agent budget SWE-sweep gives, so this is a data point, not an equal-budget comparison; 5 of the 109 bugs are pure-addition fixes with no removed lines and are unmatchable by our rule for any detector; and 72 of the 79 findings are defects the benchmark never cataloged (parquet decoder corruption reachable from untrusted files, gzip header over-read, C API exceptions escaping `extern "C"`, window and optimizer wrong-result bugs), verified by the agent with SQL repros. That is the agentic mode's genuine strength, novel discovery at the cost of nondeterminism and, today, no qualification path into a safety case.

Evidence: `cbh-duckdb/` in this repository (the agent's full BUG-HUNT-REPORT.md, the bug-level mapping JSON, and both session logs).

## How to read this honestly

- **Flag vs fix.** A static analysis flag is a lead for a human, not a fix. SWE-sweep's number requires the agent to understand the bug and produce a passing fix; this benchmark measures detection of the defect the maintainers later fixed.
- **Deep checks vs the rule sweep.** Flow Analysis alone explains 4.1% of the detections; the large gap to the agents' 5.1% closes there, and the real separation comes from the MISRA/CERT rule sweep plus Flow Analysis over the whole build, which is how the tool is used in practice.
- **Coverage caveats.** Some builds require generated headers we emulated per `REPRODUCE.md`; one godot file (`core/variant/variant_call.cpp`) exceeds the memory any single analysis process can address on a 64 GB machine and is excluded (no benchmark bug lives in it). Every caveat is reproducible from the published scripts. Agent figures are each repository's best published leaderboard result (swesweep.com, 18 evaluated models, leaderboard state November 2026).

Full methodology, per-repo rule breakdowns, and per-bug details: [`results/REPORT.md`](results/REPORT.md), `results_full/<repo>_full_result.json`, and the deduplicated violation exports in `results_full/violations/`.

## Why this matters for safety-critical industries

For teams working under DO-178C, ISO 26262, IEC 62304, and similar frameworks, the target audience of this benchmark, the conclusion is about qualification as much as detection:

- Deterministic static analysis with MISRA/CERT rule sets, run the way it is run in real projects, flags more than half of the real historical bugs it can fairly be expected to see, and every finding is auditable.
- Autonomous LLM agents resolved 5.1% of the same bugs and cannot be qualified as development tools under today's frameworks (nondeterministic, unverifiable success claims).
- The practical model for regulated environments: deterministic tools in the loop, humans judging findings, and LLM assistants confined to activities whose outputs pass through verifying gates.

## Reproducing

See [`REPRODUCE.md`](REPRODUCE.md). In short: `pipeline/fetch_repos.sh` clones the 14 upstream repositories at the pinned base refs recorded in `manifests/`; `pipeline_full/build_full_bdf.py` captures each project's real compile database and splits it into chunks; `pipeline_full/run_full.py` runs `cpptestcli` over the whole codebase with the exact test configurations in `parasoft-configs/`; `pipeline_full/map_full.py` maps every violation back to individual bugs through the per-bug pre-images. The deduplicated findings from our execution (2.19M unique file/line/rule triples) are in `results_full/violations/`, so every number can be recomputed without rerunning the tool.

We do not redistribute the SWE-sweep dataset itself; obtain it from the [SWE-sweep authors](https://swesweep.com) under their license terms. All derived metadata needed for reconstruction is included here.

## Citation

If you use this benchmark, please cite both works:

- Lieret, K., et al. "SWE-sweep: Can Agents Autonomously Find and Fix Bugs?" Meta FAIR, 2026. https://swesweep.com/paper
- Liezrowice, D. "Parasoft C/C++test vs SWE-sweep: static analysis versus autonomous LLM agents on real-world C/C++ bugs." Engineering Software Lab (ESL), 2026. https://github.com/zuwasi/swe-sweep-parasoft-benchmark

## Disclosure

ESL (eswlab.com) is a Parasoft reseller and Parasoft partner. This benchmark was executed with Parasoft C/C++test because it is the tool we sell, support, and know best. We did not evaluate other static analysis tools; other tools may perform better or worse. Nothing here should be read as a comparison between Parasoft and other vendors. The benchmark methodology, all raw evidence, and all reconstruction scripts are published so anyone can verify, criticize, or extend the work, including on other tools.

## License

Benchmark code, manifests, and results: MIT (see `LICENSE`). The analyzed repositories and their fix patches remain under their respective upstream licenses. The SWE-sweep dataset is governed by its authors' license.
