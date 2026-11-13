# Pass-3 Boundary Re-Adjudication (2026-11-13)

## Motivation
The pass-1/pass-2 merge left ~400 low-confidence labels. Only labels near the
SA/NONSA boundary can move the conditional detection rate. We re-adjudicated
exactly the boundary-relevant low-confidence subset:

- 111 caught, labeled non-SA, low confidence (if really SA: rate rises)
-  77 uncaught, labeled SA, low confidence (if really LOGIC: rate falls)
-  40 caught, labeled SA, low confidence (if really LOGIC: rate falls)

228 cases total. Non-boundary labels and high-confidence labels were not touched.

## Method
- Worklists in `worklists/` (14 repos, 228 cases) carry, per case: the snippet
  (r=1 defective lines, i=1 added lines, r=0 context), a +/-15-line pre-image
  context window around each defect region when a unique pre-image blob exists,
  and the exact Parasoft rule IDs that fired.
- Five independent reviewers issued forced SA/NONSA decisions with a sharpened
  mechanism rubric (overflow-into-index = SA, missing null/bounds check = SA,
  unchecked return = ERROR = SA, wrong branch/constant/plumbing = NONSA).
  Memory/UB-flavored catching rules (ARR39, INT31, EXP33, EXP39, ...) counted as
  objective SA evidence; style/convention catches alone never decided.
- Output: `labels_v3/<repo>.jsonl` (one decision per case, high/low confidence,
  <=12-word reason). Verified: 228 lines, bug_id order identical to worklists.

## Result
10 flips, 5 in each direction, so the SA-detectable denominator stayed 162:

| variant                      | SA set | caught in SA (region) | strict |
|------------------------------|--------|-----------------------|--------|
| original final labels        | 162    | 63/162 = 38.9%        | 23.5%  |
| pass-3 adjudicated           | 162    | 67/162 = 41.4%        | 24.7%  |
| only high-confidence v3      | 160    | 62/160 = 38.8%        | 23.8%  |

All-bugs rates unchanged: region 183/488 = 37.5%, strict 21.1%.

## Flips
SA -> NONSA (5): arrow-b4b15ce0d6ab (MEMORY, high; actually missing `ordered`
flag plumbing, verified against GH-49689), opencv-dcdb346f556f (ERROR, high;
degenerate-case rotation math, verified against PR #25050), cvc5-308a909279a9
and cvc5-726a3ded06b0 (ERROR, low; plumbing / assert-predicate logic),
z3-6aeffc53878d (MEMORY, low; unsigned wrap feeds solver threshold, not memory).

NONSA -> SA (5): opencv-5cb9cd581ef5, opencv-6c432b0cd808, opencv-9147e633a50f
(LOGIC, low; shadowed-index OOB write, missing guards that throw), 
cvc5-aa2797db1fd7 (LOGIC, low; missing null check), libexpat-f67d952cb3de
(LOGIC, low; pool-stored encoding name UAF).

## Conclusion
The tightened conditional rate is ~39-41% region, ~23.5-24.7% strict. The
re-adjudication moves the estimate up ~2.5 pp but does not change the structure
of the finding: about one third of the 488 bugs are SA-addressable by mechanism;
static analysis catches roughly 40% of those; the other two thirds are logic
defects for review, requirements-based testing and coverage; LLM agents catch
4.5% of everything.
