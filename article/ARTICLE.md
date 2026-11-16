# Static Analysis Just Beat the Best AI Agents on 488 Real Bugs, by a Factor of Ten. Safety-Critical Teams Should Pay Attention.

**By ESL (Engineering Software Lab), eswlab.com**

The debate at MISRA Conference 2026 (Manchester, UK, 10 November 2026) was the one every quality manager in avionics, automotive, and medical devices is having right now: with LLM coding agents resolving GitHub issues end to end, are the traditional methods, static analysis, coding standards like MISRA, structural coverage, human review, still relevant, or are we funding yesterday's safety net?

Instead of arguing, we measured. We took the hardest autonomous-bug benchmark we could find, SWE-sweep, built by researchers from Meta FAIR, Harvard, and Stanford, and ran a commercial static analysis tool against exactly the same bugs, on exactly the same code, the way the tool is used in real projects. What we found should reset the conversation about AI versus deterministic tooling in any industry where a bug can cost lives.

*Disclosure: ESL is a Parasoft reseller. We benchmarked Parasoft C/C++test because it is the tool we sell, support, and know best. We did not evaluate other static analysis vendors. Everything, methodology, scripts, per-bug results, and the deduplicated tool findings, is public so you can verify, criticize, or repeat the work on any tool.*

## The benchmark: agents with no hints

Most AI coding benchmarks hand the agent a codebase and a specific issue: "here is the bug, fix it." SWE-sweep ("SWE-sweep: Can Agents Autonomously Find and Fix Bugs?", Lieret et al., 2026) removes the hint. The agent gets a repository containing dozens of real, confirmed bugs and one instruction: find and fix as many bugs as possible. No locations, no descriptions, no failing tests. The bugs are real historical defects, each confirmed by the upstream maintainers' own fix commit, collected from 100 serious open-source repositories (a quarter million lines of code on average).

The results SWE-sweep published were sobering for the agents: the best model resolved **4.7%** of the 4,068 bugs in the dataset.

### Who built it, what it builds on, and what a look costs

SWE-sweep comes out of **Meta FAIR (Fundamental AI Research) with Harvard, Stanford, and the University of Washington**; the author team (Lieret, Ma, Kindi, Wei, Press, Yang and colleagues, paper dated October 1, 2026, an ICLR submission with an open-sourced harness) includes people behind SWE-bench itself. Methodologically it is SWE-bench's issue-PR mining turned inside out: real bug-fix pull requests with hidden fail-to-pass tests, the SZZ algorithm dating each bug's introduction, and a "buggiest commit" of each repository as the starting state, so the agent gets zero issue text and must discover what is broken before it can fix anything.

Its leaderboard is the public record of what autonomous discovery can do. At the time of writing, 18 models have been evaluated with the mini-SWE-agent harness: the current leader, OpenAI's Astra 6, resolves **9.5%** of all 4,068 bugs for **$3,255** of inference per full sweep; the paper's original best (Sol 5.6 xhigh) resolved **4.7%** for **$7,230**. On the C and C++ side of the leaderboard, our 14 repositories, the best published results across all 18 models add up to **25 of 488 bugs (5.1%)**, with the single best repository result at 44.4% (libexpat, 4 of 9 bugs) and three repositories at exactly zero. And every agent look is a fresh purchase: assembling the leaderboard's best result per repository over our 14 codebases consumed roughly **$500** of inference, and repeating the attempt tomorrow costs the same again. The Parasoft scan that flagged 259 bugs took one fixed setup, real compile flags and a rule configuration, and once it exists it re-runs every night in CI for the cost of machine time. A nightly agent sweep of the same repositories would burn on the order of $180,000 of inference per year to keep resolving the same 25 bugs; a static analysis license covers years of daily full scans.

We asked the complementary question: on these same repositories, what does mature, deterministic static analysis see when it runs the way it runs in industry, over the whole build?

## What we did

We took the 14 C/C++ repositories from SWE-sweep's 100-repo dataset, the languages where static analysis fully applies: **duckdb, OpenCV, GDAL, Apache Arrow, tarantool, cvc5, PHP (php-src), MicroPython, PROJ, Godot, JerryScript, HDF5, Z3, and libexpat**. Together they contain **488 accepted bugs**.

Then we ran the tool the way a serious engineering organization runs it:

1. We captured the real compile flags for every translation unit from each project's own build system (CMake `compile_commands.json` for most, `make` and `scons` databases for the rest), because static analysis without real flags produces garbage.
2. We scanned each **complete buildable codebase**, every file the build system compiles, with **Parasoft C/C++test Standard** and the rule sets a safety-critical team would actually deploy: **Flow Analysis Standard + MISRA C 2025 + SEI CERT C** for the C repositories (C/C++test 2026.1.3), **Flow Analysis Standard + MISRA C++ 2023 + SEI CERT C++ + SEI CERT C** for the C++ repositories (C/C++test 2025.2.0). The tool received no hints of any kind about where bugs are.
3. The scan produced **2,193,448 unique findings** across the 14 codebases.
4. For every bug, we reconstructed the exact moment the bug existed: each SWE-sweep oracle patch names the file, the exact git blob hash, and the lines the maintainer's fix changed. We materialized 679 bug-era file versions byte-identically from git and aligned every bug's defect region into the scanned codebase.
5. We counted a bug as **found** when any violation landed on any line of the bug's changed region, and as **strictly found** when it landed on the exact line the eventual fix removed or rewrote.

## The results

| Repo | Language | Bugs | Parasoft found | Parasoft % | SWE-sweep best agent % |
|---|---|---|---|---|---|
| jerryscript | C | 15 | 13 | **86.7%** | 20.0% |
| libexpat | C | 9 | 7 | **77.8%** | 44.4% |
| godot | C++ | 17 | 13 | **76.5%** | 0.0% |
| opencv | C++ | 47 | 35 | **74.5%** | 2.1% |
| cvc5 | C++ | 38 | 27 | **71.1%** | 2.6% |
| duckdb | C++ | 109 | 75 | **68.8%** | 2.8% |
| micropython | C | 22 | 15 | **68.2%** | 9.1% |
| proj | C++ | 21 | 13 | **61.9%** | 9.5% |
| tarantool | C | 40 | 23 | **57.5%** | 7.5% |
| php-src | C | 26 | 13 | **50.0%** | 3.8% |
| hdf5 | C | 14 | 7 | **50.0%** | 28.6% |
| z3 | C++ | 11 | 4 | 36.4% | 0.0% |
| arrow | C++ | 47 | 11 | 23.4% | 2.1% |
| gdal | C++ | 72 | 3 | 4.2% | 0.0% |
| **Total** | | **488** | **259** | **53.1%** | **~5.1%** |

Parasoft C/C++test put a finding on the changed code of **more than half of all 488 real bugs**, including the many that are pure logic defects no deterministic tool targets. Counting only findings on the exact line the maintainer's fix changed, it still found **28.9%** of all bugs, nearly six times the agents' end-to-end resolution rate. Nine of the fourteen repositories cleared 50%, and duckdb alone contributed 75 detections on one of the hardest C++ codebases in the set.

And the sharpest number comes after the classification below: on the 162 bugs whose mechanism is a static analyzer's business, Parasoft flagged **55.6%**.

### Where the deep engine shines

The most interesting slice is not the style rules, it is Flow Analysis, the interprocedural engine that reasons about data flow rather than code shape. It independently caught **20 real defects** the coding standards do not reach, including:

- **Integer wraparound** in DuckDB's cast helpers and optimizer,
- **Use-before-initialization** in JerryScript's ECMAScript array operations,
- **Container index out of range** and **unreachable switch branches** in DuckDB's catalog and window binding,
- Six bugs in HDF5 caught largely by a single unused-value check,
- **Errno misuse** in JerryScript's date arithmetic.

Those are exactly the defect classes that matter in DO-178C and ISO 26262 land: arithmetic overflow, uninitialized state, out-of-bounds access. A flag is not a diagnosis, but for a reviewer it is a pointer to the exact line where a real bug lives.

The bulk of the detections, 240 of the 259, came from MISRA and CERT rules landing on buggy lines: type-category mismatches, C-style casts, pointer arithmetic, unused values, unchecked returns. That is the quiet workhorse of the method, and at this scale it is devastatingly effective.

### What static analysis could even see

A fair question follows: of the 488 bugs, how many are even the kind of defect a static analyzer targets? The SWE-sweep authors themselves note that most of their bugs can only be recognized by inferring the intended behavior from the repository. So we classified every bug by the mechanism of its defect, judged from the code the maintainers' fix removed, using two independent blind classification passes, adjudication of every disagreement, and a third targeted pass that re-examined the 228 boundary cases with the full pre-image code around each defect; the rubric and all 488 per-bug labels are published in the repository.

The result: only **162 of the 488 bugs (33.2%)** are in a static analyzer's wheelhouse, memory safety and undefined behavior (120), leaks and concurrency (16), and error handling or API contract violations (26). The other two thirds are logic and requirements bugs: wrong operators, wrong constants, wrong branch, wrong protocol step, wrong interpretation of a specification. No deterministic tool flags those by design, and the SWE-sweep agents did not reliably find them either.

On those 162 mechanism bugs, Parasoft flagged **90 (55.6%)** at the changed region and **52 (32.1%)** on the exact removed line, above its all-bugs rates of 53.1% and 28.9%. On its home ground, the class of bug it was built to catch, the tool clears the 50% mark: more than five in ten mechanism bugs flagged with an auditable pointer to the defect, versus roughly one in twenty for the autonomous agents across all bugs. The classification does not inflate the headline; it clarifies the division of labor. A third of real-world bugs are mechanism defects a deterministic tool can flag with auditable findings, and the tool's hit rate there is its highest ground. The other two thirds, the logic bugs, are what design review, requirements traceability, requirements-based testing, and structural coverage exist for, in every regulated industry. An LLM agent contributes little on either layer today: 5.1% overall, and it has no qualification story on either layer either.

## Read this honestly, please

- **A flag is not a fix.** Our 53.1% overall, 55.6% on the mechanism bugs, means a human would get a pointer to the defect; someone still has to judge and fix it. The agents' number, in turn, requires a passing fix, so the two measure different points of the same pipeline, and the gap between them is nonetheless ten to one.
- **On pure deep-defect detection the two approaches are close**: Flow Analysis alone caught 4.1% versus the agents' 5.1%. The enormous gap comes from what happens when you add a comprehensive MISRA/CERT rule sweep and run it over the entire build, which is precisely how static analysis is deployed in industry.
- **Coverage is imperfect, and we document every gap.** One godot source file exceeds the addressable memory of a single analysis process on a 64 GB machine and was excluded (no benchmark bug lives in it); gdal's accepted bugs are overwhelmingly logic-class, which its 4.2% reflects. All 488 bugs were mapped into the scanned codebases.

## Why safety-critical teams should care

If you build software under DO-178C, ISO 26262, IEC 62304, or IEC 61504, two conclusions follow directly.

**First, the traditional stack is not obsolete; it is the load-bearing wall.** Deterministic static analysis with MISRA/CERT rule sets, run over the whole build, flagged more than half of all real historical bugs at the defective lines and 55.6% of the mechanism bugs it is designed for, in codebases where the best autonomous agents closed at about five percent. And the traditional stack does not stop at static analysis: the two thirds of bugs that are logic and requirements defects are exactly what requirements-based testing, structural coverage up to MC/DC, and human review each add layers for, layers the agent result never touches.

**Second, and more decisive than any percentage: qualification.** Every tool in the traditional stack is deterministic and auditable, so it can be qualified under DO-330 or ISO 26262's tool confidence levels with documented criteria. An LLM agent is nondeterministic: the same repository can yield different results on consecutive runs, and its failures are silent, it reports success on code that does not work. In a safety argument, actively misleading evidence is worse than missing evidence. Until there is an accepted qualification scheme for nondeterministic learned tools, they cannot enter the certification evidence, regardless of how good their scores get.

The right posture is therefore not "AI versus tools" but division of labor: deterministic tools and qualified processes for anything that enters the safety case, humans to judge findings, and LLM assistants, if at all, on activities whose outputs pass through verifying gates. Our data suggests one concrete hybrid: agents are weak bug *finders*, so do not send them hunting raw repositories; point them at static analysis findings and let them propose candidate fixes for human judgment.

## Reproduce it or challenge it

Everything is public at **https://github.com/zuwasi/swe-sweep-parasoft-benchmark**: the complete pipeline (from patch parsing through whole-build scan orchestration to bug mapping), per-bug manifests with the exact file blob hashes and changed-line ranges, the Parasoft test configurations (685 C rules, 660 C++ rules), all 14 per-bug result files, and the deduplicated findings from our execution (2,193,448 file/line/rule triples), so you can recompute every number without rerunning the tool, or rerun it yourself on any static analysis tool and compare.

We thank the SWE-sweep team for building and open-sourcing the benchmark; if you are the authors reading this, we would be glad to discuss the static-analysis control condition and share anything useful for the paper.

## References

1. Lieret, K., Ma, J. J., Kindi, R., et al. "SWE-sweep: Can Agents Autonomously Find and Fix Bugs?" Meta FAIR et al., October 2026. https://swesweep.com/paper
2. Parasoft C/C++test documentation: Flow Analysis, MISRA C 2025, MISRA C++ 2023, SEI CERT. https://www.parasoft.com
3. Benchmark repository and raw evidence: https://github.com/zuwasi/swe-sweep-parasoft-benchmark

*ESL (Engineering Software Lab, eswlab.com) provides safety-critical software verification tooling, training, and services, and is a Parasoft reseller. Contact: daniel.l@eswlab.com*
