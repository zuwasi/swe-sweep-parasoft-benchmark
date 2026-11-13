# Demo storyboard: Parasoft C/C++test vs SWE-sweep - static analysis vs AI agents on 488 real bugs

Scene 01 is the ESL title card; the last scene is the ESL end card.
Scenes 04 and 05 are one real, unscripted terminal recording of a Parasoft C/C++test
Standard scan of bug-era HDF5 code (recorded with asciinema, idle time compressed).
Nothing in the recording is mocked. Numbers come from the published benchmark:
Parasoft 183/488 (37.5%) region detection on all bugs, 67/162 (41.4%) on the mechanism bugs, vs SWE-sweep best agent 4.5%.

| # | Headline (what you'll see) | Action recorded on screen | What it achieves | Narration (read by the voice) | Target sec |
|---|----------------------------|---------------------------|------------------|-------------------------------|------------|
| 01 | Title | Title card | Sets the goal | Can a method from the nineteen nineties still beat an AI agent at finding real bugs? We measured it. | 8 |
| 02 | The debate | ESL slide + MISRA Conference 2026 flash | Frame the question from the MISRA conference | At the MISRA Conference 2026 in Manchester this November, one debate kept returning. If AI writes the code, are static analysis and coding standards still relevant for safety critical industries? | 13 |
| 03 | The benchmark | ESL slide | Explain the experiment | We took the fourteen C and C++ repositories of the SWE sweep benchmark. Four hundred and eighty eight accepted, real bugs. We pointed Parasoft C/C++test at the exact buggy code, byte for byte. | 15 |
| 04 | The real scan | Terminal recording: cpptestcli runs on bug-era HDF5 code, Flow Analysis Standard, MISRA C 2025, SEI CERT C | Prove the tool really runs, show scale | This is not an animation. A real scan of bug era HDF5 code, with the compiler flags captured from the project's own build system. Flow Analysis Standard, MISRA C 2025, and SEI CERT C rules. It collects the translation units, builds the control flow graphs, and reports twenty three thousand violations. No hints. Just the analyzer and the code. | 25 |
| 05 | What it found | Terminal recording: violation summary and the Flow Analysis findings | Show real findings on screen | Flow Analysis flagged integer conversion overflows, on lines the upstream fixes later changed. Same bugs, found without being told where to look. | 9 |
| 06 | The result | ESL slide | Deliver the headline number | Here is the result across all fourteen repositories. Parasoft flagged a finding inside the changed code of thirty seven point five percent of all bugs. And on the one hundred sixty two bugs that are static analysis's kind of bug, it found forty one point four percent, clearing the forty percent mark. The best AI agent process in the SWE sweep paper found four point five percent. | 16 |
| 07 | Honest limits | ESL slide | Keep credibility with a technical audience | Be honest about the limits. We pointed the tool at the buggy files. The agents had to search whole repositories. Not every flagged rule is the real bug. But the gap is enormous. | 13 |
| 08 | Classification | ESL slide | Show the fair-to-static-analysis conditional rate and the division of labor | We also classified every bug by mechanism, with three independent passes. Only a third, one hundred and sixty two bugs, are the kind static analysis targets at all. On that third, Parasoft found forty one point four percent, clearing the forty percent mark and beating its overall rate. The other two thirds are logic bugs. Those belong to review, requirements based testing, and coverage, layers the agents never touch. | 22 |
| 09 | End | End card | Close and credit | For safety critical software, deterministic static analysis is not old fashioned. It is the bar. Engineering Software Lab. Thank you for watching. | 9 |
