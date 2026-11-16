# Parasoft C/C++test vs SWE-sweep: static analysis versus autonomous LLM agents on real-world C/C++ bugs

**ESL (Engineering Software Lab) | eswlab.com** — benchmark, reconstruction pipeline, and raw evidence.

We took the 14 C/C++ repositories from [SWE-sweep](https://swesweep.com) ("SWE-sweep: Can Agents Autonomously Find and Fix Bugs?", Lieret et al., 2026), materialized the exact pre-fix code of all **488 accepted bugs**, and ran **Parasoft C/C++test** (Flow Analysis Standard + MISRA C 2025 + SEI CERT C for C repos on C/C++test Standard 2026.1.3; Flow Analysis Standard + MISRA C++ 2023 + SEI CERT C++ + SEI CERT C for C++ repos on 2025.2.0) on each **complete buildable codebase**: every file each project's own build system compiles, with the compile flags captured from that build system. The tool was given no hints about where the bugs are; this is exactly how static analysis runs in normal development. We then measured how many bugs the tool flags on the lines the maintainers-confirmed fixes changed, and compared that with the best autonomous agent result SWE-sweep itself published.

## Results

| Repo | Lang | Bugs | Parasoft found (region) | % (region) | % (strict line) | SWE-sweep best agent |
|---|---|---|---|---|---|---|
| duckdb | C++ | 109 | 75 | 68.8% | 32.1% | 2.8% |
| gdal | C++ | 72 | 3 | 4.2% | 1.4% | 0.0% |
| arrow | C++ | 47 | 11 | 23.4% | 8.5% | 2.1% |
| opencv | C++ | 47 | 35 | 74.5% | 40.4% | 2.1% |
| tarantool | C | 40 | 23 | 57.5% | 45.0% | 7.5% |
| cvc5 | C++ | 38 | 27 | 71.1% | 31.6% | 2.6% |
| php-src | C | 26 | 13 | 50.0% | 26.9% | 0.0% |
| micropython | C | 22 | 15 | 68.2% | 31.8% | 0.0% |
| proj | C++ | 21 | 13 | 61.9% | 33.3% | 9.5% |
| godot | C++ | 17 | 13 | 76.5% | 41.2% | 0.0% |
| jerryscript | C | 15 | 13 | 86.7% | 80.0% | 20.0% |
| hdf5 | C | 14 | 7 | 50.0% | 42.9% | 28.6% |
| z3 | C++ | 11 | 4 | 36.4% | 27.3% | 0.0% |
| libexpat | C | 9 | 7 | 77.8% | 33.3% | 44.4% |
| **Total** | | **488** | **259** | **53.1%** | **28.9%** | **~4.5%** |
| **Of which: the 162 mechanism bugs** | | **162** | **90** | **55.6%** | **32.1%** | | |

- Flow Analysis (deep interprocedural defect checks, BD-*) alone caught **20/488 (4.1%)**: integer wraparound, use-before-initialization, index out of range, unreachable switch branches, unused values, errno misuse. See the per-repo rule breakdowns in `results/REPORT.md`.
- The rest of the matches come from MISRA/CERT coding-standard rules landing on the buggy lines.
- **Bug classification.** We classified all 488 bugs by defect mechanism with two independent blind passes plus adjudication, then a third boundary pass re-judged the 228 labels closest to the static-analysis boundary with full pre-image context (`classification/RUBRIC.md`, `classification/adjudication3/`). Only **162 (33.2%)** are the kind of defect a static analyzer targets (memory/UB 120, leaks/concurrency 16, error handling 26); the other two thirds are logic and requirements bugs. On those 162, Parasoft flagged **90 (55.6%)** at the changed region and **52 (32.1%)** strictly on the removed line, above its all-bugs rates (53.1% / 28.9%). The logic bugs are what review, requirements-based testing, and structural coverage exist for, and neither the static analyzer nor the LLM agents (4.5%) reliably find them.

## How to read this honestly

- **Flag vs fix.** A static analysis flag is a lead for a human, not a fix. SWE-sweep's number requires the agent to understand the bug and produce a passing fix; this benchmark measures detection of the defect the maintainers later fixed.
- **Deep checks vs the rule sweep.** Flow Analysis alone explains 4.1% of the detections; the large gap to the agents' 4.5% closes there, and the real separation comes from the MISRA/CERT rule sweep plus Flow Analysis over the whole build, which is how the tool is used in practice.
- **Coverage caveats.** Some builds require generated headers we emulated per `REPRODUCE.md`; one godot file (`core/variant/variant_call.cpp`) exceeds the memory any single analysis process can address on a 64 GB machine and is excluded (no benchmark bug lives in it); 13 of 679 pre-image blobs were unavailable. Every caveat is reproducible from the published scripts.

Full methodology, per-repo rule breakdowns, and per-bug details: [`results/REPORT.md`](results/REPORT.md), `results_full/<repo>_full_result.json`, and the deduplicated violation exports in `results_full/violations/`.

## Why this matters for safety-critical industries

For teams working under DO-178C, ISO 26262, IEC 62304, and similar frameworks, the target audience of this benchmark, the conclusion is about qualification as much as detection:

- Deterministic static analysis with MISRA/CERT rule sets, run the way it is run in real projects, flags more than half of the real historical bugs it can fairly be expected to see, and every finding is auditable.
- Autonomous LLM agents resolved 4.5% of the same bugs and cannot be qualified as development tools under today's frameworks (nondeterministic, unverifiable success claims).
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
