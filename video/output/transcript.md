# Demo transcript

## Scene 1

Can a method from the nineteen nineties still beat an AI agent at finding real bugs? We measured it.

## Scene 2

At the MISRA Conference 2026 in Manchester this November, one debate kept returning. If AI writes the code, are static analysis and coding standards still relevant for safety critical industries?

## Scene 3

We took the fourteen C and C++ repositories of the SWE sweep benchmark. Four hundred and eighty eight accepted, real bugs. We pointed Parasoft C/C++test at the exact buggy code, byte for byte.

## Scene 4

This is not an animation. A real scan of bug era HDF5 code, with the compiler flags captured from the project's own build system. Flow Analysis Standard, MISRA C 2025, and SEI CERT C rules. It collects the translation units, builds the control flow graphs, and reports twenty three thousand violations. No hints. Just the analyzer and the code.

## Scene 5

Flow Analysis flagged integer conversion overflows, on lines the upstream fixes later changed. Same bugs, found without being told where to look.

## Scene 6

Here is the result across all fourteen repositories. Parasoft flagged a finding inside the changed code of thirty seven point five percent of the bugs. The best AI agent process in the SWE sweep paper found four point five percent.

## Scene 7

Be honest about the limits. We pointed the tool at the buggy files. The agents had to search whole repositories. Not every flagged rule is the real bug. But the gap is enormous.

## Scene 8

We also classified every bug by mechanism, with three independent passes. Only a third, one hundred and sixty two bugs, are the kind static analysis targets at all. On that third, Parasoft found forty one point four percent, clearing the forty percent mark and beating its overall rate. The other two thirds are logic bugs. Those belong to review, requirements based testing, and coverage, layers the agents never touch.

## Scene 9

For safety critical software, deterministic static analysis is not old fashioned. It is the bar. Engineering Software Lab. Thank you for watching.
