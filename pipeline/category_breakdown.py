#!/usr/bin/env python3
"""Category breakdown + aggregate table for the final report."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from map_findings import analyze, ROOT  # reuse

REPOS = ["duckdb", "gdal", "arrow", "opencv", "tarantool", "cvc5", "php-src",
         "micropython", "proj", "godot", "jerryscript", "hdf5", "z3", "libexpat"]


def cat(rule):
    if rule.startswith("BD-"):
        return "FA"
    if rule.startswith("CERT"):
        return "CERT"
    if rule.startswith("MISRA"):
        return "MISRA"
    return "OTHER"


def breakdown(name):
    data = json.loads((ROOT / "analysis" / f"{name}_bugs.json").read_text())
    # re-run the mapping logic but keep rule categories
    import re
    rep_files = [ROOT / "reports" / name / "report.xml"]
    scratch = Path("/home/danie/.swesweep_run") / name
    if scratch.exists():
        rep_files += sorted(scratch.glob("run_*/rep/report/report.xml"))
    finds = []
    for rf in rep_files:
        try:
            text = rf.read_text(errors="replace")
        except FileNotFoundError:
            continue
        for m in re.finditer(r'<(FlowViol|StdViol)\b(.*?)/?>', text, re.S):
            a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(2)))
            if a.get("rule") and a.get("locFile") and a.get("ln", "").isdigit():
                finds.append((a["locFile"], int(a["ln"]), a["rule"]))
    per_cat = {}
    detail = []
    for bug in data["bugs"]:
        hit = {"FA": set(), "CERT": set(), "MISRA": set(), "OTHER": set()}
        strict_hits = set()
        for h in bug["hunks"]:
            if not h.get("blob") or h["blob"] == "0000000" or set(h["blob"]) == {"0"}:
                continue
            loc = f"/{name}/{h['blob']}/{h['file']}"
            s, e = h["old_start"], h["old_start"] + h["old_count"] - 1
            for locfile, ln, rule in finds:
                if locfile == loc and s <= ln <= e:
                    hit[cat(rule)].add(rule)
                    if ln in h["removed"]:
                        strict_hits.add(cat(rule))
        for k, v in hit.items():
            if v:
                per_cat[k] = per_cat.get(k, 0) + 1
        detail.append({"bug": bug["bug_id"], "FA": sorted(hit["FA"]),
                       "CERT": sorted(hit["CERT"]), "MISRA": sorted(hit["MISRA"]),
                       "strict_cats": sorted(strict_hits)})
    return per_cat, detail


if __name__ == "__main__":
    out = {}
    for name in REPOS:
        pc, det = breakdown(name)
        out[name] = pc
        print(name, pc)
    (ROOT / "reports" / "category_breakdown.json").write_text(json.dumps(out, indent=1))
