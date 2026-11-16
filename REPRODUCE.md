# Reproducing the benchmark

This document describes how to reconstruct and rerun the full benchmark:
Parasoft C/C++test static analysis (Flow Analysis Standard + MISRA C 2025 +
CERT C for C repos, Flow Analysis Standard + MISRA C++ 2023 + CERT C++ for
C++ repos) on the **complete buildable codebase** of each of the 14 C/C++
repositories (every file the project's own build system compiles), and the
mapping of findings back to individual SWE-sweep bugs.

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

5. **Run Parasoft over the whole buildable codebase (published configuration).**

   ```bash
   python3 pipeline_full/build_full_bdf.py <repo>...
   python3 pipeline_full/run_full.py
   python3 pipeline_full/map_full.py <repo>...
   python3 pipeline_full/export_violations_full.py <repo>...
   ```

   `build_full_bdf.py` converts each repo's compile database into Parasoft
   build data files and splits it into chunks sized for one cpptestcli run
   (794 chunks across the 14 repos). Builds whose headers are generated were
   provisioned first: micropython's `mpy-cross` and php-src were built from
   the pinned sources; hdf5's build directory was supplied from a matching
   build; cvc5 received GMP 6.3 headers and gdal received PROJ 9.8.1 headers
   from matching conda packages. `run_full.py` runs
   `cpptestcli -config "user://SWEEP_C"` (C repos) or `"user://SWEEP_CPP"`
   (C++ repos) with compiler id `gcc_13-64`, several parallel runs, each in
   its own working directory and HOME to avoid `.cpptest` lock collisions;
   it is fully resumable (chunks with an existing `report.xml` are skipped).
   One godot file, `core/variant/variant_call.cpp`, exceeds the memory a
   single analysis process can address on a 64 GB machine and is excluded;
   no benchmark bug lives in it. `map_full.py` deduplicates violations across
   chunks by (file, line, rule) — 2,193,448 unique findings for our execution —
   aligns every bug's changed region from the pre-fix file into the base_ref
   tree by full-file diff, and reports per-bug matches. A bug counts as
   **found (region)** when any violation lands on any line of the bug's
   changed region; **strict** when it lands on a line the fix removed or
   rewrote. `export_violations_full.py` writes the deduplicated findings to
   `results_full/violations/<repo>_violations.tsv.gz` so the mapping can be
   recomputed without rerunning the tool.

6. **Aggregate.**

   ```bash
   python3 pipeline/category_breakdown.py
   python3 pipeline/build_report.py
   ```

   Produces `results_full/<repo>_full_result.json` (per-bug matched rule IDs)
   and the aggregate tables in `results/REPORT.md`.

   `pipeline/` also retains the single-file execution mode used for spot
   checks (`pipeline/run_analysis.py`, `pipeline/map_findings.py`); the
   published numbers come from the whole-project scan above.

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

`results_full/violations/<repo>_violations.tsv.gz` contains the deduplicated
findings (file, line, rule) from the published whole-project execution
(2,193,448 triples across the 14 repositories). Every number in
`results/REPORT.md` can be recomputed from these files plus `manifests/`,
without rerunning C/C++test. The full raw XML reports of that execution are
hundreds of gigabytes and are not shipped; they can be regenerated with
`pipeline_full/`. `raw-reports/<repo>/` keeps gzipped XML reports from
single-file spot-check runs.

## Known limitations (inherited by any reproduction)

- One godot file, `core/variant/variant_call.cpp`, exceeds the memory a
  single analysis process can address on a 64 GB machine and is excluded;
  no benchmark bug lives in it.
- gdal's accepted bugs are heavily logic-class even within the mechanism
  bucket, which its 4.2% detection rate reflects.
- 13 of 679 pre-image blobs were absent from fetched git history
  (PR-only commits): duckdb 2, php-src 3, cvc5 1, gdal 1.
