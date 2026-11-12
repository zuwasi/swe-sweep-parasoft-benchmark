#!/usr/bin/env python3
"""Build the final comparison report (Markdown) from result JSONs."""
import json
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
ORDER = ["duckdb", "gdal", "arrow", "opencv", "tarantool", "cvc5", "php-src",
         "micropython", "proj", "godot", "jerryscript", "hdf5", "z3", "libexpat"]
NOTES = {
    "cvc5": "Analysis environment partially built: only 2 of 54 C++ units preprocessed cleanly (API drift between the bug-era dev code and generated headers from master); result is a lower bound.",
    "php-src": "3 of 31 pre-image blobs absent from fetched branch history (PR-only commits); those 3 bugs could not be analyzed.",
    "duckdb": "2 of 196 pre-image blobs absent from branch history; analyzed 194.",
    "gdal": "1 pre-image blob absent. Build environment needed a from-source PROJ build.",
    "micropython": "Flags captured from `make -n` of mpy-cross; 7 units without make entries used fallback flags.",
    "php-src2": "",
}


def main():
    rows = []
    tot_bugs = tot_region = tot_strict = 0
    swe_bugs = 0.0
    for name in ORDER:
        r = json.loads((ROOT / "reports" / f"{name}_result.json").read_text())
        cb = json.loads((ROOT / "reports" / "category_breakdown.json").read_text())[name]
        fa, cert, misra = cb.get("FA", 0), cb.get("CERT", 0), cb.get("MISRA", 0)
        n = r["n_bugs"]
        swe = r["swe_pct"]
        rows.append({
            "repo": name, "n": n, "fa": fa, "cert": cert, "misra": misra,
            "region": r["found_region"], "pct_region": r["pct_region"],
            "strict": r["found_strict"], "pct_strict": r["pct_strict"],
            "swe": swe, "swe_bugs": n * swe / 100.0,
        })
        tot_bugs += n
        tot_region += r["found_region"]
        tot_strict += r["found_strict"]
        swe_bugs += n * swe / 100.0

    lines = []
    lines.append("# Parasoft C/C++test vs SWE-sweep: bug detection on the 14 C/C++ SWESweep repositories")
    lines.append("")
    lines.append(f"Date: 2026-11-12. Tool: Parasoft C/C++test Standard 2025.2.0, Flow Analysis Standard "
                 f"+ MISRA C 2025 (C repos) / MISRA C++ 2023 + SEI CERT C++ (C++ repos), SEI CERT C for C repos. "
                 f"Benchmark: SWE-sweep (swesweep.com), 488 accepted bugs across the 14 C/C++ repositories.")
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append(f"- Parasoft flags at least one finding directly on the changed lines of "
                 f"**{tot_region}/{tot_bugs} bugs ({100*tot_region/tot_bugs:.1f}%)** (any rule; line in the bug's changed region).")
    lines.append(f"- Strictly on a line the fix removed or changed: **{tot_strict}/{tot_bugs} ({100*tot_strict/tot_bugs:.1f}%)**.")
    lines.append(f"- Flow Analysis (deep interprocedural checks, BD-*) alone: **16/488 (3.3%)**.")
    lines.append(f"- SWE-sweep's own best process (LLM agents searching the whole repo) resolved "
                 f"**{swe_bugs:.1f}/{tot_bugs} bugs ({100*swe_bugs/tot_bugs:.1f}%)** across these same repositories.")
    lines.append("")
    lines.append("## Per-repository results")
    lines.append("")
    lines.append("| Repo | Lang | Bugs | Found: FA | CERT | MISRA | Found (region) | % (region) | % (strict) | SWE-sweep best resolved |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lang = "C" if r["repo"] in ("php-src", "micropython", "jerryscript", "hdf5", "libexpat", "tarantool") else "C++"
        lines.append(f"| {r['repo']} | {lang} | {r['n']} | {r['fa']} | {r['cert']} | {r['misra']} "
                     f"| {r['region']} | {r['pct_region']}% | {r['pct_strict']}% | {r['swe']}% |")
    lines.append("")
    lines.append("| Aggregate | Bugs | Found (region) | % (region) | % (strict) | SWE-sweep |")
    lines.append("|---|---|---|---|---|---|")
    lines.append(f"| 14 C/C++ repos | {tot_bugs} | {tot_region} | {100*tot_region/tot_bugs:.1f}% "
                 f"| {100*tot_strict/tot_bugs:.1f}% | {100*swe_bugs/tot_bugs:.1f}% |")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("1. For every C/C++ repo in SWE-sweep's publication split, the oracle patches (one per accepted bug) "
                 "were parsed: each patch names the pre-fix file blob hash and the exact changed lines in the pre-fix file.")
    lines.append("2. Each pre-fix file version (679 file versions total) was materialized from git at the exact blob hash, "
                 "so analysis targets byte-identical bug-era code.")
    lines.append("3. Compile flags came from each project's own build system (CMake configure with CMAKE_EXPORT_COMPILE_COMMANDS=ON "
                 "for 11 repos, `make -n` for micropython/php-src, scons compiledb for godot). gdal required building PROJ from source; "
                 "cvc5 required building GMP 6.3 from source.")
    lines.append("4. Parasoft C/C++test (cpptestcli) ran Flow Analysis Standard + MISRA C 2025 + CERT C (C repos) or "
                 "MISRA C++ 2023 + CERT C++ (C++ repos) on those files in WSL, 6 parallel runs.")
    lines.append("5. A bug counts as *found (region)* when any violation lands on any line of the bug's changed region "
                 "in the pre-fix file; *strict* when it lands on a line the fix removed/rewrote.")
    lines.append("")
    lines.append("## Reading the numbers honestly")
    lines.append("")
    lines.append("- Scope: analysis ran on the bug files only (not whole-repo search), so this measures detection on the buggy code, "
                 "not autonomous discovery in a 1M-line repo. SWE-sweep's agents had to search the whole repo without hints; Parasoft here was pointed at the files.")
    lines.append("- Rule mix: most hits are coding-standard rules (CERT/MISRA) firing on the buggy lines, e.g. CERT INT31 (unsafe integer conversion) "
                 "and ARR39 (pointer arithmetic), MISRA 0.1.2 (unused value), 8.0.1. Deep Flow Analysis findings (null deref, overflow, OOB) "
                 "account for 16 of the 183 found bugs.")
    lines.append("- Coverage gaps: a handful of pre-image blobs (13 of 679) were absent from fetched git history; cvc5's generated headers "
                 "mostly mismatch the bug-era code, so its 44.7% is a lower bound; gdal's large generated/external surface made many files fail to preprocess (4.2%).")
    lines.append("- SWE-sweep percentages are each repo's best published agent result (micro-averaged per repo on their leaderboard).")
    lines.append("")
    lines.append("## Top rules hitting bug lines (all repos)")
    lines.append("")
    lines.append("| Rule | Found-bug hits | Meaning |")
    lines.append("|---|---|---|")
    for rule, n, meaning in [
        ("MISRACPP2023-8_0_1-b", 53, "side effects in assertions / admissibility"),
        ("CERT_C-MSC41-a", 46, "unused return value"),
        ("MISRACPP2023-6_9_2-a", 35, "unused value"),
        ("MISRACPP2023-9_5_1-a", 33, "cast to void of a value with side effects"),
        ("MISRACPP2023-9_3_1-b", 25, "dead code / unreachable"),
        ("MISRACPP2023-7_0_5-a", 24, "expression result unused"),
        ("MISRACPP2023-11_6_1-a", 22, "void* to data pointer cast"),
        ("MISRACPP2023-0_1_2-a", 20, "value never read"),
        ("CERT_C-INT31-j", 19, "integer conversion overflow"),
        ("CERT_C-ARR39-b", 17, "invalid pointer arithmetic"),
        ("MISRACPP2023-7_0_6-a", 19, "unused static function"),
    ]:
        lines.append(f"| {rule} | {n} | {meaning} |")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    lines.append("- Per-bug detail: `C:\\Users\\danie\\swesweep-parasoft-benchmark\\reports\\<repo>_result.json`")
    lines.append("- Category breakdown: `C:\\Users\\danie\\swesweep-parasoft-benchmark\\reports\\category_breakdown.json`")
    lines.append("- Raw Parasoft XML reports: `C:\\Users\\danie\\swesweep-parasoft-benchmark\\reports\\<repo>\\` and scratch `~\\.swesweep_run\\<repo>\\run_*\\rep\\`")
    lines.append("- Scripts: `C:\\Users\\danie\\swesweep-parasoft-benchmark\\scripts\\`")

    out = "\n".join(lines)
    (ROOT / "reports" / "REPORT.md").write_text(out)
    print(out)


if __name__ == "__main__":
    main()
