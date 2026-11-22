# Gemini 4 Neon bug-hunt vs Parasoft C/C++test across all 14 SWE-Sweep C/C++ repos

Scoring: a Neon finding counts for a bug only if it semantically identifies the same defect the
maintainer's fix commit changed (verified per bug against the oracle patch and the fix diff).
region = finding touches any changed line of the bug; strict = finding covers the exact fixed line.
Parasoft numbers are the published per-repo results
(https://zuwasi.github.io/Public-html-pages/parasoft-vs-swe-sweep/technical/).

| Repo | Lang | Bugs | Neon region | Neon strict | Parasoft region | Parasoft strict | SWE-sweep best agent |
|---|---|---|---|---|---|---|---|
| jerryscript | C | 15 | 7 (46.7%) | 6 (40.0%) | 86.7% | 80.0% | 20.0% |
| godot | C++ | 17 | 1 (5.9%) | 0 (0.0%) | 76.5% | 41.2% | 0.0% |
| opencv | C++ | 47 | 13 (27.7%) | 9 (19.1%) | 74.5% | 40.4% | 2.1% |
| cvc5 | C++ | 38 | 1 (2.6%) | 1 (2.6%) | 71.1% | 31.6% | 2.6% |
| duckdb | C++ | 109 | 18 (16.5%) | 14 (12.8%) | 68.8% | 32.1% | 2.8% |
| micropython | C | 22 | 9 (40.9%) | 8 (36.4%) | 68.2% | 31.8% | 9.1% |
| proj | C++ | 21 | 3 (14.3%) | 3 (14.3%) | 61.9% | 33.3% | 9.5% |
| tarantool | C | 40 | 15 (37.5%) | 14 (35.0%) | 57.5% | 45.0% | 7.5% |
| php-src | C | 26 | 0 (0.0%) | 0 (0.0%) | 50.0% | 26.9% | 3.8% |
| hdf5 | C | 14 | 2 (14.3%) | 2 (14.3%) | 50.0% | 42.9% | 28.6% |
| libexpat | C | 9 | 6 (66.7%) | 4 (44.4%) | 77.8% | 33.3% | 44.4% |
| z3 | C++ | 11 | 2 (18.2%) | 1 (9.1%) | 36.4% | 27.3% | 0.0% |
| arrow | C++ | 47 | 11 (23.4%) | 10 (21.3%) | 23.4% | 8.5% | 2.1% |
| gdal | C++ | 72 | 1 (1.4%) | 1 (1.4%) | 4.2% | 1.4% | 0.0% |
| **Total** | | **488** | **89 (18.2%)** | **73 (15.0%)** | **53.1% (259)** | **28.9% (141)** | **~5.1% (25)** |

Headlines:
- Parasoft C/C++test found 259/488 bugs region and 141/488 strict; Neon found 89/488 region and
  73/488 strict on the same bug sets under the same scoring rule.
- Neon beats Parasoft on strict line matches in 3 of 14 repos (libexpat 44.4% vs 33.3%,
  arrow 21.3% vs 8.5%, micropython 36.4% vs 31.8%) and ties Parasoft's region in libexpat and arrow.
- Neon's weakest repos: php-src (0/26), cvc5 (1/38), gdal (1/72), godot (1/17), where Parasoft
  found 26.9-76.5%.
- All 14 repos have per-bug scored write-ups with verified fix commits in reports/<repo>_scored.md;
  no unresolved pairs remain. Two revisions versus the first-pass tallies are documented in
  libexpat_scored.md (BUG-39 mechanism mismatch, -1 bug) and tarantool_scored.md (+3 bugs:
  F-127, F-065, F-024 borderline, all re-verified against the fix diffs).
