# Bug Classification Rubric

Each of the 488 SWE-sweep bugs is assigned exactly one `sa_class` describing the
MECHANISM of the defect, judged from the code the maintainers' fix removed or
rewrote (the defective lines), or from the insertion point when the fix only
adds code. The mechanism, not the feature area, decides the class.

## Classes

- `MEMORY`: memory safety or undefined behavior. Buffer or array overflow,
  out-of-bounds read or write, use-after-free, double free, dangling pointer,
  null pointer dereference, use of uninitialized memory, arithmetic that can
  overflow or wrap and then corrupts memory or indexes it, wrong signedness or
  width conversion feeding a memory access, format string flaw, type confusion,
  missing null or bounds check (even though the fix is an added `if`).
- `RESOURCE`: leak of memory, descriptor, or handle; missing cleanup, free, or
  close; use after close; missing release on an error path; concurrency defects
  (data race, deadlock, missing unlock).
- `ERROR`: error handling and API contract. Unchecked or wrongly checked return
  value, ignored error code, wrong errno handling, mechanically checkable wrong
  API use, missing argument validation where the contract requires the caller
  to validate.
- `LOGIC`: wrong decision, formula, protocol, state machine, or requirement.
  Wrong operator, constant, comparison, or branch; wrong data or order;
  misunderstanding of the specification; wrong output for valid input with no
  memory or contract angle.
- `OTHER`: test-only, build system, documentation, portability, pure refactor.
- `UNKNOWN`: no code snippet could be extracted for the bug (19 bugs; excluded
  from the static-analysis-detectable denominator).

## Method

Two independent blind passes over the same snippets with this rubric:

1. `labels_pass1/` (13 repos by parallel reviewers, godot by the analyst).
2. `labels_v2/` (five parallel reviewers, blind to pass 1, sharpened anchors).

Disagreements were adjudicated by reading the snippets, with priority to the
bugs Parasoft C/C++test actually caught (16 bugs; those ground truths are
mechanically static-analysis defects, so their class is forced to the matching
SA class). Per-bug labels and reasons are published for audit.

Low-confidence judgments are flagged and reported separately; they are kept in
the totals because excluding only low-confidence cases would bias the estimate
in our favor in the same way as any post-hoc filter.
