# cvc5 scored (Gemini 4 Neon bug hunt vs benchmark bugs)

- Repo: cvc5, base commit eb02f250787ab591e98d1bd1f48781346c63a655
- Neon report: 130 findings (BUG-001..BUG-130), 103 CONFIRMED / 27 SUSPECTED
- Benchmark bugs: 38 (2 with empty region sets: cvc5-39fc8377f26f theory_model.cpp, cvc5-ffc998069294 sat_proof_manager.cpp; not matchable)

## Matcher result (reports/cvc5_matches.json)
- Region hits on 3 bugs; strict hits on 2 bugs.

## Accepted

| bug_id | reason | Neon finding | verdict |
|---|---|---|---|
| cvc5-50f4bf9c8c66 | fold over union order wrong | BUG-019 postRewriteFold/bags postRewriteFold union expansion unsound | ACCEPT region+strict |

Fix 234f379ebb ("Fix soundness issue with set.fold rewriting for set.union case", #12526) rewrote exactly the union case of TheorySetsRewriter::postRewriteFold (base lines 1035-1045, strict 1035/1039): the old rule folded t over A then over all of B, double-folding elements in the intersection. Neon's BUG-019 flagged the same rewrite rule as unsound (its symptom description, expansion order/congruence, differs from the maintainer's double-counting description, but the finding targets the same rule and lines and the fix rewrote it). Bags twin (BagsRewriter::postRewriteFold) is outside benchmark regions.

## Rejected overlaps

| bug_id | reason | Neon finding | why rejected |
|---|---|---|---|
| cvc5-308a909279a9 | inferences sent with wrong arguments | BUG-016, BUG-045 | Fix 9030457eb2 (#9589) changed the fact policy (asLemma flag) for inferences in ArrayCoreSolver. Neon's findings claim ill-typed SEQ_NTH construction and a skipped isHandledUpdateOrSubstr guard: different mechanisms, line overlap only. |
| cvc5-a874c6f84e37 | inst constant condition wrong | BUG-039 | Fix e21d67250b (#10524) removed the `options().quantifiers.cegqi` gate so inst-constant terms are rejected regardless of options (model unsoundness with --sygus-inst --no-cegqi). Neon BUG-039 claims CEGQI-in-get-qe trips a DebugUnhandled with an internal constant: adjacent lines, different defect. |

## Clear misses (all other 35 bugs)
No Neon finding touches their files/regions. The Neon hunt concentrated on API/parser/options/sep/bags/ff/bv-rewrites crash hunting; the benchmark bugs concentrate in theory solver internals (strings base_solver/sequences_rewriter/term_registry, arith rewriter/addition/nl_model/transcendental/sine solver, quantifiers MBQI/model_engine/equality_query/ce_guided_single_inv, datatypes infer_proof_cons, sets solver_state, learned_rewrite, int_to_bv, prop engine, sat proof manager, theory model).

## Final score
- Region: 1/38 = 2.6%
- Strict: 1/38 = 2.6%
- Parasoft published (38 bugs): region 71.1%, strict 31.6%
- Novel findings: 129 (no benchmark overlap)
