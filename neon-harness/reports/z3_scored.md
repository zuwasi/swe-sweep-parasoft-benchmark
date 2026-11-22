# z3 · Neon bug-hunt vs SWE-Sweep oracle (scored)

- Neon findings: total entries in reports/z3_matches.json; 3 findings matched at least one oracle bug; 3 distinct bugs matched.
- Denominator: all 11 SWE-Sweep z3 bugs.
- Parasoft published: 36.4% region (4/11), 27.3% strict (3/11).

## Accepted (2 bugs, 2 findings)

Region+strict (1 bug):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| Z3-021 | f3cd4349f4cb | 479ff3476e6 | "Fix polymorphic application arity validation (#10179)": rewrites exactly the oracle's removed lines (api_ast.cpp 193-202, the polymorphism::util domain-match block) adding an arity guard and domain-index remapping for associative/chainable declarations; prevents the OOB m_domain reads the finding claims for polymorphic Z3_mk_app. The finding's Z3_mk_transitive_closure / Z3_add_rec_def claims are not part of this fix |

Region-only (1 bug):

| Finding | Bug | Fix commit | Evidence |
|---|---|---|---|
| Z3-102 | e0dd0ca5d4f1 | 922f49e1870 | "Fix MBP QEL soundness bug in datatype accessor elimination (#9571/#9692)": inserts exactly at the oracle's insertion-only hunk (mbp_dt_tg.cpp 163) a model check that skips rm_accessor when m_mdl does not confirm the accessor's constructor; the finding's claim verbatim. Oracle hunk is insertion-only, so no strict set |

## Rejected — line overlap, different mechanism

- Z3-051 / 6aeffc53878d: fix 2c48f2e6a9a "Fix unsigned underflow of cardinality bounds in pb internalization (#10515)" truncates k in lia2card to avoid unsigned underflow (bug reason: "unsigned k2 computation can wrap"); the finding claimed a missing num_user_scopes()==0 guard in pb::solver::convert_eq_k leaking constraints across pop. Different defect in the same solver.

## Final score

- Neon region: 2/11 = 18.2% (Parasoft published: 36.4%)
- Neon strict: 1/11 = 9.1% (Parasoft published: 27.3%)
- Novel findings: all findings except the 2 accepted ones
- Unresolved: none; all 3 matched pairs have verified fix commits.
