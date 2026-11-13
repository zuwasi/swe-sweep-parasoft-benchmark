# We Ran a Commercial Static Analysis Tool Against the Hardest LLM Bug Benchmark Available. Safety-Critical Teams Should Pay Attention.

**By ESL (Engineering Software Lab), eswlab.com**

The debate at MISRA Conference 2026 (Manchester, UK, 10 November 2026) was the one every quality manager in avionics, automotive, and medical devices is having right now: with LLM coding agents resolving GitHub issues end to end, are the traditional methods, static analysis, coding standards like MISRA, structural coverage, human review, still relevant, or are we funding yesterday's safety net?

Instead of arguing, we measured. We took the hardest autonomous-bug benchmark we could find, SWE-sweep, built by researchers from Meta FAIR, Harvard, and Stanford, and pointed a commercial static analysis tool at exactly the same bugs. This article reports what happened, how we made the comparison fair, and why we believe the results matter for anyone shipping software where a bug can cost lives.

*Disclosure: ESL is a Parasoft reseller. We benchmarked Parasoft C/C++test because it is the tool we sell, support, and know best. We did not evaluate other static analysis vendors. Everything, methodology, scripts, per-bug results, and raw tool output, is public so you can verify, criticize, or repeat the work on any tool.*

## The benchmark: agents with no hints

Most AI coding benchmarks hand the agent a codebase and a specific issue: "here is the bug, fix it." SWE-sweep ("SWE-sweep: Can Agents Autonomously Find and Fix Bugs?", Lieret et al., 2026) removes the hint. The agent gets a repository containing dozens of real, confirmed bugs and one instruction: find and fix as many bugs as possible. No locations, no descriptions, no failing tests. The bugs are real historical defects, each confirmed by the upstream maintainers' own fix commit, collected from 100 serious open-source repositories (a quarter million lines of code on average).

The results SWE-sweep published were sobering for the agents: the best model resolved **4.7%** of the 4,068 bugs in the dataset.

We asked the complementary question. If we know where every bug is, what does mature static analysis see?

## What we did

We took the 14 C/C++ repositories from SWE-sweep's 100-repo dataset, the languages where static analysis fully applies: **duckdb, OpenCV, GDAL, Apache Arrow, tarantool, cvc5, PHP (php-src), MicroPython, PROJ, Godot, JerryScript, HDF5, Z3, and libexpat**. Together they contain **488 accepted bugs**.

For every bug, we reconstructed the exact moment the bug existed:

1. Each SWE-sweep oracle patch tells us which file, at which exact git blob hash, the fix changed, and which lines.
2. We materialized 679 bug-era file versions byte-identically from git.
3. We captured the real compiler flags for each file from each project's own build system (CMake `compile_commands.json` for most, `make` and `scons` databases for the rest), because static analysis without real flags produces garbage.
4. We ran **Parasoft C/C++test Standard** with the rule sets a safety-critical team would actually deploy: **Flow Analysis Standard + MISRA C 2025 + SEI CERT C** for the C repositories (C/C++test 2026.1.3), **Flow Analysis Standard + MISRA C++ 2023 + SEI CERT C++** for the C++ repositories (C/C++test 2025.2.0).
5. We counted a bug as **found** when any violation landed on any line of the bug's changed region, and as **strictly found** when it landed on the exact line the eventual fix removed or rewrote.

## The results

| Repo | Language | Bugs | Parasoft found | Parasoft % | SWE-sweep best agent % |
|---|---|---|---|---|---|
| jerryscript | C | 15 | 13 | **86.7%** | 20.0% |
| opencv | C++ | 47 | 32 | **68.1%** | 2.1% |
| duckdb | C++ | 109 | 56 | **51.4%** | 2.8% |
| libexpat | C | 9 | 6 | **66.7%** | 44.4% |
| proj | C++ | 21 | 10 | 47.6% | 9.5% |
| php-src | C | 26 | 11 | 42.3% | 0.0% |
| cvc5 | C++ | 38 | 17 | 44.7%* | 2.6% |
| hdf5 | C | 14 | 6 | 42.9% | 28.6% |
| godot | C++ | 17 | 7 | 41.2% | 0.0% |
| z3 | C++ | 11 | 3 | 27.3% | 0.0% |
| micropython | C | 22 | 4 | 18.2% | 0.0% |
| arrow | C++ | 47 | 10 | 21.3% | 2.1% |
| tarantool | C | 40 | 5 | 12.5% | 7.5% |
| gdal | C++ | 72 | 3 | 4.2% | 0.0% |
| **Total** | | **488** | **183** | **37.5%** | **~4.5%** |

\* cvc5's figure is a lower bound: only 2 of 54 files preprocessed cleanly against its bug-era headers.

Counting only findings on the exact line the maintainer's fix changed, Parasoft still found **21.1%** of all bugs, roughly five times the agents' end-to-end resolution rate.

And 37.5% is the tool working across *all* bugs, the majority of which are logic defects no deterministic tool targets. After the classification below, the sharper number appears: on the 162 bugs whose mechanism is a static analyzer's business, Parasoft flagged **41.4%**.

### Where the deep engine shines

The most interesting slice is not the style rules, it is Flow Analysis, the interprocedural engine that reasons about data flow rather than code shape. It independently caught **16 real defects**, including:

- **Integer wraparound** in DuckDB's cast helpers and optimizer,
- **Use-before-initialization** in JerryScript's ECMAScript array operations,
- A **container index out of range** in DuckDB's catalog search path,
- **Unreachable switch branches** in DuckDB's window binding,
- Five bugs in HDF5 caught by a single unused-value check.

Those are exactly the defect classes that matter in DO-178C and ISO 26262 land: arithmetic overflow, uninitialized state, out-of-bounds access. One verified example: JerryScript's date-`fmod` bug was flagged by Flow Analysis rule BD-PB-ERRNO on the precise line the maintainers later rewrote.

The other 167 matches came from MISRA and CERT rules landing on buggy lines: type-category mismatches, C-style casts, pointer arithmetic, unused values. A flag is not a diagnosis, but for a reviewer it is a pointer to the exact line where a real bug lives.

### What static analysis could even see

A fair question follows: of the 488 bugs, how many are even the kind of defect a static analyzer targets? The SWE-sweep authors themselves note that most of their bugs can only be recognized by inferring the intended behavior from the repository. So we classified every bug by the mechanism of its defect, judged from the code the maintainers' fix removed, using two independent blind classification passes, adjudication of every disagreement, and a third targeted pass that re-examined the 228 boundary cases with the full pre-image code around each defect; the rubric and all 488 per-bug labels are published in the repository.

The result: only **162 of the 488 bugs (33.2%)** are in a static analyzer's wheelhouse, memory safety and undefined behavior (119), leaks and concurrency (16), and error handling or API contract violations (27). The other two thirds are logic and requirements bugs: wrong operators, wrong constants, wrong branch, wrong protocol step, wrong interpretation of a specification. No deterministic tool flags those by design, and the SWE-sweep agents did not reliably find them either.

On those 162 mechanism bugs, Parasoft flagged **67 (41.4%)** at the changed region and **40 (24.7%)** on the exact removed line, above its all-bugs rates of 37.5% and 21.1%. On its home ground, the class of bug it was built to catch, the tool clears the 40% mark: roughly four in ten mechanism bugs flagged with an auditable pointer to the defect, versus one in twenty-two for the autonomous agents across all bugs. Independent classification passes bracket the number between 38.8% and 41.4%, so the conclusion does not hinge on any single judgment call. The classification does not inflate the headline; it clarifies the division of labor. A third of real-world bugs are mechanism defects a deterministic tool can flag with auditable findings, and the tool's hit rate there is its highest ground. The other two thirds, the logic bugs, are what design review, requirements traceability, requirements-based testing, and structural coverage exist for, in every regulated industry. An LLM agent contributes little on either layer today: 4.5% overall, and it has no qualification story on either layer either.

## Read this honestly, please

Two numbers this close in a table invite over-reading, so here is what the comparison does and does not say:

- **The tasks are different.** We pointed the tool at the known buggy files. SWE-sweep agents had to find the bugs inside repositories of up to 1.9 million lines, understand them, and produce fixes that pass hidden tests. Static analysis detection at a known location is an easier problem than autonomous discovery and repair. This is a comparison of *detection on buggy code* versus *autonomous end-to-end resolution*, and we say so everywhere it counts.
- **A flag is not a fix.** Our 37.5% overall, 41.4% on the mechanism bugs, means a human would get a pointer to the defect; someone still has to judge and fix it.
- **On pure deep-defect detection the two approaches are close**: Flow Analysis alone caught 3.3% versus the agents' 4.5%. The large gap comes from the rule-based sweep of the buggy lines.
- **Coverage is imperfect.** 13 of 679 bug-era files could not be recovered from git history; GDAL's generated-code surface defeated preprocessing for many files. The details and workarounds are documented in the repository.

## Why safety-critical teams should care

If you build software under DO-178C, ISO 26262, IEC 62304, or IEC 61504, two conclusions follow directly.

**First, the traditional stack is not obsolete; it is the load-bearing wall.** Deterministic static analysis with MISRA/CERT rule sets flagged a third of all real historical bugs at the defective lines, a fifth of them on the exact line, in codebases where the best autonomous agent closed under five percent. And the traditional stack does not stop at static analysis: the two thirds of bugs that are logic and requirements defects are exactly what requirements-based testing, structural coverage up to MC/DC, and human review each add layers for, layers the agent result never touches.

**Second, and more decisive than any percentage: qualification.** Every tool in the traditional stack is deterministic and auditable, so it can be qualified under DO-330 or ISO 26262's tool confidence levels with documented criteria. An LLM agent is nondeterministic: the same repository can yield different results on consecutive runs, and its failures are silent, it reports success on code that does not work. In a safety argument, actively misleading evidence is worse than missing evidence. Until there is an accepted qualification scheme for nondeterministic learned tools, they cannot enter the certification evidence, regardless of how good their scores get.

The right posture is therefore not "AI versus tools" but division of labor: deterministic tools and qualified processes for anything that enters the safety case, humans to judge findings, and LLM assistants, if at all, on activities whose outputs pass through verifying gates. Our data suggests one concrete hybrid: agents are weak bug *finders*, so do not send them hunting raw repositories; point them at static analysis findings and let them propose candidate fixes for human judgment.

## Reproduce it or challenge it

Everything is public at **https://github.com/zuwasi/swe-sweep-parasoft-benchmark**: the complete pipeline (14 scripts from patch parsing to report generation), per-bug manifests with the exact file blob hashes and changed-line ranges, the Parasoft test configurations (700 C rules, 676 C++ rules), all 14 result files, and the raw Parasoft XML reports from our runs, so you can recompute every number without rerunning the tool, or rerun it yourself on any static analysis tool and compare.

We thank the SWE-sweep team for building and open-sourcing the benchmark; if you are the authors reading this, we would be glad to discuss the static-analysis control condition and share anything useful for the paper.

## References

1. Lieret, K., Ma, J. J., Kindi, R., et al. "SWE-sweep: Can Agents Autonomously Find and Fix Bugs?" Meta FAIR et al., October 2026. https://swesweep.com/paper
2. Parasoft C/C++test documentation: Flow Analysis, MISRA C 2025, MISRA C++ 2023, SEI CERT. https://www.parasoft.com
3. Benchmark repository and raw evidence: https://github.com/zuwasi/swe-sweep-parasoft-benchmark

*ESL (Engineering Software Lab, eswlab.com) provides safety-critical software verification tooling, training, and services, and is a Parasoft reseller. Contact: daniel.l@eswlab.com*
