# Transcript: Static Analysis vs the AI Agents (Parasoft C/C++test vs SWE-sweep)

Total length: 1:53. Voice: en-GB-RyanNeural. Subtitles are burned into the video.

| Scene | Time | Narration |
|---|---|---|
| 01 | 00:00 | Can a method from the nineteen nineties still beat an AI agent at finding real bugs? We measured it. |
| 02 | 00:07 | At the MISRA conference, one debate kept returning. If large language models write the code, are static analysis and coding standards still relevant for safety critical industries? |
| 03 | 00:18 | We took the fourteen C and C++ repositories of the SWE sweep benchmark. Four hundred and eighty eight accepted, real bugs. We pointed Parasoft C/C++test at the exact buggy code, byte for byte. |
| 04 | 00:34 | This is not an animation. A real scan of bug era HDF5 code, with the compiler flags captured from the project's own build system. Flow Analysis Standard, MISRA C 2025, and SEI CERT C rules. It collects the translation units, builds the control flow graphs, and reports twenty three thousand violations. No hints. Just the analyzer and the code. |
| 05 | 01:01 | Flow Analysis flagged integer conversion overflows, on lines the upstream fixes later changed. Same bugs, found without being told where to look. |
| 06 | 01:12 | Here is the result across all fourteen repositories. Parasoft flagged a finding inside the changed code of thirty seven point five percent of the bugs. The best AI agent process in the SWE sweep paper found four point five percent. |
| 07 | 01:27 | Be honest about the limits. We pointed the tool at the buggy files. The agents had to search whole repositories. Not every flagged rule is the real bug. But the gap is enormous. |
| 08 | 01:41 | For safety critical software, deterministic static analysis is not old fashioned. It is the bar. Engineering Software Lab. Thank you for watching. |

Notes:
- Scene 04 and 05 are a genuine, unscripted recording of Parasoft C/C++test Standard 2026.1.3
  scanning bug-era HDF5 code (SWE-sweep bug blobs) with the C configuration
  (Flow Analysis Standard + MISRA C 2025 + SEI CERT C), rendered from an asciinema capture.
- Rule findings are capped at 1,000 per rule by the tool; that is the "Limit reached"
  lines visible in the recording.
- Full data and reproduction steps: https://github.com/zuwasi/swe-sweep-parasoft-benchmark
