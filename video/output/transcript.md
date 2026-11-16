# Demo transcript

## Scene 01

Can a method from the nineteen nineties still beat an AI agent at finding real bugs? We measured it.

## Scene 02

At the MISRA Conference 2026 in Manchester this November, one debate kept returning. If AI writes the code, are static analysis and coding standards still relevant for safety critical industries?

## Scene 03

We took the fourteen C and C++ repositories of the SWE sweep benchmark. Four hundred eighty eight accepted, real bugs. We ran Parasoft C/C++test on each complete buildable codebase, every file the project's own build system compiles. No hints. No shortcuts.

## Scene 04

This is not an animation. A real scan of bug era HDF5 code, with the compiler flags captured from the project's own build system. Flow Analysis Standard, MISRA C 2025, and SEI CERT C rules. It collects the translation units, builds the control flow graphs, and reports one hundred fifty thousand findings. No hints. Just the analyzer and the code.

## Scene 05

Flow Analysis flagged integer conversion overflows, on lines the upstream fixes later changed. Same bugs, found without being told where to look.

## Scene 06

Here is the result across all fourteen repositories. Parasoft flagged a finding inside the changed code of fifty three point one percent of all bugs. And on the one hundred sixty two bugs that are static analysis's kind of bug, it found fifty five point six percent, well past the fifty percent mark. The best AI agent process in the SWE sweep paper found four point five percent.

## Scene 07

Be honest about the limits. A flag is a lead for an engineer, not a fix. The agents in SWE sweep had to make hidden tests pass. We measure detection. Not every flagged rule is the real bug. But the gap is enormous.

## Scene 08

We also classified every bug by mechanism, with three independent passes. Only a third, one hundred sixty two bugs, are the kind static analysis targets at all. On that third, Parasoft found fifty five point six percent, clearing the fifty percent mark. The other two thirds are logic bugs. Those belong to review, requirements based testing, and structural coverage, layers the agents never touch.

## Scene 09

For safety critical software, deterministic static analysis is not old fashioned. It is the bar. Engineering Software Lab. Thank you for watching.
