# Reproducing the benchmark

This document describes how to reconstruct and rerun the full benchmark:
Parasoft C/C++test static analysis (Flow Analysis Standard + MISRA C 2025 +
CERT C for C repos, Flow Analysis Standard + MISRA C++ 2023 + CERT C++ for
C++ repos) on the exact pre-fix code of every accepted SWE-sweep bug in the
14 C/C++ repositories, and the mapping of findings back to individual bugs.

## What you need

1. **The SWE-sweep dataset.** This benchmark consumes SWE-sweep's oracle
   patches (one per bug). The dataset is described at https://swesweep.com
   and in "SWE-sweep: Can Agents Autonomously Find and Fix Bugs?"
   (Lieret et al., 2026). Download the dataset from the official SWE-sweep
   release and note the path; below it is assumed to be `/tmp/swe-sweep`.
   We do not redistribute the dataset here because its license terms are
   defined by its authors. All *derived* metadata needed for reconstruction
   (per-bug file paths, pre-fix git blob hashes, and changed-line ranges) is
   included in `manifests/`, so the upstream repositories alone plus this
   repo are sufficient to re-materialize the analyzed code.
2. **Parasoft C/C++test.** The benchmark used C/C++test Standard 2026.1.3
   (`cpptestcli`) for the six C repositories and C/C++test Standard 2025.2.0
   for the eight C++ repositories, on Linux x64 with a working license
   (DTP or standalone).
   Static analysis rules are the merged test configurations in
   `parasoft-configs/`:
   - `SWEEP_C.properties`: Flow Analysis Standard + MISRA C 2025 + CERT C
     (685 rules) for C repositories.
   - `SWEEP_CPP.properties`: Flow Analysis Standard + MISRA C++ 2023 +
     CERT C++ + CERT C (660 rules) for C++ repositories.
   Copy them into `<cpptest-install>/configs/user/` or reference them with
   `-config "user://SWEEP_C"`.
3. **Python 3, git, and the build prerequisites of each project**
   (CMake, a system compiler toolchain; see per-repo notes below).

## Pipeline

The pipeline scripts live in `pipeline/`. Run them from the repository root
(or a work directory of your choice). Adjust the `ROOT` path in
`build_report.py` if you relocate the tree.

1. **Fetch the 14 repositories at the pinned base refs.**

   ```bash
   pipeline/fetch_repos.sh repos/
   ```

   `manifests/*_manifest.json` record each repo's upstream clone URL and the
   `base_ref` (release tag) SWE-sweep built its tasks from. Full clones are
   required (not shallow) because per-bug pre-images are materialized from
   git blob hashes.

2. **Extract per-bug metadata.**

   ```bash
   python3 pipeline/extract_bugs.py
   ```

   Parses each oracle patch (`/tmp/swe-sweep/tasks/swe-sweep__<repo>/tests/oracle/*.patch`)
   and writes `analysis/<repo>_bugs.json`: per bug, the pre-fix file blob
   hash and the exact changed-line ranges. `manifests/` already contains the
   same data with dataset paths stripped.

3. **Materialize pre-images.**

   ```bash
   python3 pipeline/materialize_preimages.py
   ```

   Writes each analyzed file version to `analysis/<repo>/pre/<blob>/<path>`,
   byte-identical to the bug-era code (blob hashes come from the patch
   `index <old>..<new>` lines; 13 of 679 blobs were absent from fetched
   history and are skipped and reported).

4. **Capture real compile flags.**

   ```bash
   pipeline/capture_flags.sh      # CMake repos: cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
   pipeline/capture_make_flags.py # micropython, php-src: make -n parsing
   ```
   - 11 repos use `compile_commands.json` from their own CMake configure.
   - `godot` uses `scons compiledb=yes compiledb`.
   - `gdal` requires PROJ built from source; `cvc5` requires GMP 6.3 from
     source (see `capture_flags*.sh` for the exact buildroot paths).
   - `libexpat` needs `-DXML_GE=1` (see `gen_bdf.py`).

5. **Run Parasoft.**

   ```bash
   python3 pipeline/run_analysis.py
   ```

   Generates a build data file per repo (`gen_bdf.py`), chunks it, and runs
   `cpptestcli -config "user://SWEEP_C"` (C repos) or `"user://SWEEP_CPP"`
   (C++ repos) with compiler id `gcc_13-64`, 6 parallel runs, each in its
   own working directory and HOME to avoid `.cpptest` lock collisions.

6. **Map findings back to bugs.**

   ```bash
   python3 pipeline/map_findings.py
   ```

   A bug counts as **found (region)** when any violation lands on any line
   of the bug's changed region in the pre-fix file; **strict** when it lands
   on a line the fix removed or rewrote. `verify_alignment.py` sanity-checks
   the blob/line alignment.

7. **Aggregate.**

   ```bash
   python3 pipeline/category_breakdown.py
   python3 pipeline/build_report.py
   ```

   Produces `results/<repo>_result.json`, `results/category_breakdown.json`,
   and `results/REPORT.md`.

## Reproducing the bug classification

The classification of all 488 bugs into defect mechanisms (MEMORY / RESOURCE /
ERROR / LOGIC / OTHER / UNKNOWN) is published in `classification/` so it can be
audited or re-derived:

1. `classification/snippets_v2/<repo>.jsonl` holds, for every bug, the exact
   lines the maintainers' fix removed or rewrote (`"r": 1`) and the insertion
   points for fixes that only add code (`"i": 1`), extracted from the
   materialized pre-fix files. `pipeline/extract_class_snippets_v2.py`
   regenerates them from `manifests/` and the pre-images.
2. `classification/labels_pass1/` and `classification/labels_v2/` are two
   independent blind classification passes over those snippets, using the rubric
   in `classification/RUBRIC.md`. `classification/labels_final_overrides.jsonl`
   records every adjudicated disagreement and the 16 Flow Analysis ground-truth
   forcings.
3. `pipeline/merge_classification.py` merges the two passes and the overrides
   into `classification/final/` and writes `classification/adjudication.csv`
   with all disagreements. Aggregate statistics land in
   `results/bug_classification.json`.

## Raw evidence

`raw-reports/<repo>/` contains the gzipped Parasoft XML reports (both
`FlowViol` and `StdViol` entries) from every run chunk of the original
benchmark execution. Every number in `results/` can be recomputed from
these files plus `manifests/`. The six C repositories ship one gzipped
report per run chunk (`run<i>.xml.gz`) from the MISRA C 2025 execution
(C/C++test Standard 2026.1.3); C++ repositories keep the merged reports
from the 2025.2.0 execution.

## Known limitations (inherited by any reproduction)

- Analysis scope is the bug files only, with real per-file compile flags;
  this measures detection on buggy code, not whole-repo discovery.
- cvc5: pre-images come from master commits newer than the 1.0.5 tag; only
  2 of 54 C++ units preprocessed cleanly; its result is a lower bound.
- gdal: large generated/external surface caused many preprocessing
  failures (4.2% detection).
- 13 of 679 pre-image blobs were absent from fetched git history
  (PR-only commits): duckdb 2, php-src 3, cvc5 1, gdal 1.
