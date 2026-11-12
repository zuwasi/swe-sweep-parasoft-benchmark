# Parasoft C/C++test vs SWE-sweep: static analysis versus autonomous LLM agents on real-world C/C++ bugs

**ESL (Engineering Software Lab) | eswlab.com** — benchmark, reconstruction pipeline, and raw evidence.

We took the 14 C/C++ repositories from [SWE-sweep](https://swesweep.com) ("SWE-sweep: Can Agents Autonomously Find and Fix Bugs?", Lieret et al., 2026), materialized the exact pre-fix code of all **488 accepted bugs**, and ran **Parasoft C/C++test** (Flow Analysis Standard + MISRA C 2025 + SEI CERT C for C repos on C/C++test Standard 2026.1.3; Flow Analysis Standard + MISRA C++ 2023 + SEI CERT C++ + SEI CERT C for C++ repos on 2025.2.0) on that code. We then measured how many bugs the tool flags on the exact lines SWE-sweep's maintainers-confirmed fixes changed, and compared that with the best autonomous agent result SWE-sweep itself published.

## Results

| Repo | Lang | Bugs | Parasoft found (region) | % (region) | % (strict line) | SWE-sweep best agent |
|---|---|---|---|---|---|---|
| duckdb | C++ | 109 | 56 | 51.4% | 25.7% | 2.8% |
| gdal | C++ | 72 | 3 | 4.2% | 1.4% | 0.0% |
| arrow | C++ | 47 | 10 | 21.3% | 8.5% | 2.1% |
| opencv | C++ | 47 | 32 | 68.1% | 29.8% | 2.1% |
| tarantool | C | 40 | 5 | 12.5% | 7.5% | 7.5% |
| cvc5 | C++ | 38 | 17 | 44.7% (lower bound) | 26.3% | 2.6% |
| php-src | C | 26 | 11 | 42.3% | 26.9% | 0.0% |
| micropython | C | 22 | 4 | 18.2% | 13.6% | 0.0% |
| proj | C++ | 21 | 10 | 47.6% | 28.6% | 9.5% |
| godot | C++ | 17 | 7 | 41.2% | 35.3% | 0.0% |
| jerryscript | C | 15 | 13 | 86.7% | 80.0% | 20.0% |
| hdf5 | C | 14 | 6 | 42.9% | 28.6% | 28.6% |
| z3 | C++ | 11 | 3 | 27.3% | 9.1% | 0.0% |
| libexpat | C | 9 | 6 | 66.7% | 44.4% | 44.4% |
| **Total** | | **488** | **183** | **37.5%** | **21.1%** | **~4.5%** |

- Flow Analysis (deep interprocedural defect checks, BD-*) alone caught **16/488 (3.3%)**: integer wraparound, use-before-initialization, index out of range, unreachable switch branches, unused values, errno misuse. See the per-repo rule breakdowns in `results/REPORT.md`.
- The rest of the matches come from MISRA/CERT coding-standard rules landing on the buggy lines.

## How to read this honestly

- **Different tasks.** Parasoft was pointed at the known buggy files; SWE-sweep agents had to search whole repositories (up to 1.9M lines) with no hints, understand each bug, and produce a passing fix. This benchmark measures detection on buggy code, not autonomous discovery.
- **Flag vs fix.** A static analysis flag is a lead for a human, not a fix. SWE-sweep's number requires the agent to make hidden tests pass.
- **Deep checks vs style.** On true-defect detection (Flow Analysis alone), the tool's 3.3% and the agents' 4.5% are comparable. The large gap is in the rule-based sweep of the buggy lines.
- **Coverage caveats.** cvc5's result is a lower bound (generated-header drift); gdal's rate reflects preprocessing failures; 13 of 679 pre-image blobs were unavailable (see `REPRODUCE.md`).

Full methodology, per-repo rule breakdowns, and per-bug details: [`results/REPORT.md`](results/REPORT.md) and `results/<repo>_result.json`.

## Why this matters for safety-critical industries

For teams working under DO-178C, ISO 26262, IEC 62304, and similar frameworks, the target audience of this benchmark, the conclusion is about qualification as much as detection:

- Deterministic static analysis with MISRA/CERT rule sets flags a large fraction of real historical bugs at the defective lines, and every finding is auditable.
- Autonomous LLM agents resolved 4.5% of the same bugs and cannot be qualified as development tools under today's frameworks (nondeterministic, unverifiable success claims).
- The practical model for regulated environments: deterministic tools in the loop, humans judging findings, and LLM assistants confined to activities whose outputs pass through verifying gates.

## Reproducing

See [`REPRODUCE.md`](REPRODUCE.md). In short: `pipeline/fetch_repos.sh` clones the 14 upstream repositories at the pinned base refs recorded in `manifests/`; the pipeline re-materializes every per-bug pre-image from git blob hashes, captures real compile flags from each project's own build system, runs `cpptestcli` with the exact test configurations in `parasoft-configs/`, and maps every violation back to individual bugs. Raw Parasoft XML reports from our execution are in `raw-reports/`, so every number can be recomputed without rerunning the tool.

We do not redistribute the SWE-sweep dataset itself; obtain it from the [SWE-sweep authors](https://swesweep.com) under their license terms. All derived metadata needed for reconstruction is included here.

## Citation

If you use this benchmark, please cite both works:

- Lieret, K., et al. "SWE-sweep: Can Agents Autonomously Find and Fix Bugs?" Meta FAIR, 2026. https://swesweep.com/paper
- Liezrowice, D. "Parasoft C/C++test vs SWE-sweep: static analysis versus autonomous LLM agents on real-world C/C++ bugs." Engineering Software Lab (ESL), 2026. https://github.com/zuwasi/swe-sweep-parasoft-benchmark

## Disclosure

ESL (eswlab.com) is a Parasoft reseller and Parasoft partner. This benchmark was executed with Parasoft C/C++test because it is the tool we sell, support, and know best. We did not evaluate other static analysis tools; other tools may perform better or worse. Nothing here should be read as a comparison between Parasoft and other vendors. The benchmark methodology, all raw evidence, and all reconstruction scripts are published so anyone can verify, criticize, or extend the work, including on other tools.

## License

Benchmark code, manifests, and results: MIT (see `LICENSE`). The analyzed repositories and their fix patches remain under their respective upstream licenses. The SWE-sweep dataset is governed by its authors' license.
