#!/usr/bin/env python3
"""Map Parasoft findings to SWE-sweep bug locations and build the comparison.

Reads reports/<name>/report.xml (Parasoft HTML report's XML), extracts
violations (FlowViol / StdViol), resolves each to (blob, file, line), and
checks against each bug's hunk regions.

A bug counts as found (region) if any finding lands on any line of any of the
bug's hunks (the changed region in the pre-fix file); strict means the line is
one of the removed/replaced lines.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")

# SWE-sweep published "Best resolved" percentages (swesweep.com/repositories)
SWE_PCT = {
    "duckdb": 2.8, "gdal": 0.0, "arrow": 2.1, "opencv": 2.1, "tarantool": 7.5,
    "cvc5": 2.6, "php-src": 0.0, "micropython": 0.0, "proj": 9.5,
    "godot": 0.0, "jerryscript": 20.0, "hdf5": 28.6, "z3": 0.0,
    "libexpat": 44.4,
}


def parse_report(path):
    findings = []
    try:
        text = path.read_text(errors="replace")
    except FileNotFoundError:
        return findings
    for m in re.finditer(
            r'<(FlowViol|StdViol|ClViol|CpViol)\b(.*?)/?>', text, re.S):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(2)))
        rule = attrs.get("rule", "")
        ln = attrs.get("ln", "")
        loc = attrs.get("locFile", "")
        if rule and loc:
            findings.append({"locFile": loc, "ln": int(ln) if ln.isdigit() else None,
                             "rule": rule})
    return findings


def resolve(locfile, name):
    # locFile like "/<module name>/<blob>/<orig path>"
    parts = locfile.lstrip("/").split("/", 2)
    if len(parts) != 3 or parts[0] != name:
        return None
    blob, rest = parts[1], parts[2]
    if not re.fullmatch(r"[0-9a-f]{6,40}", blob):
        return None
    return blob, rest


def analyze(name):
    data = json.loads((ROOT / "analysis" / f"{name}_bugs.json").read_text())
    rep_files = [ROOT / "reports" / name / "report.xml"]
    scratch = Path("/home/danie/.swesweep_run") / name
    if scratch.exists():
        rep_files += sorted(scratch.glob("run_*/rep/report/report.xml"))
    findings = []
    for rf in rep_files:
        findings += parse_report(rf)
    res = []
    for f in findings:
        r = resolve(f["locFile"], name)
        if r:
            f["blob"], f["file"] = r
            res.append(f)
    by_unit = {}
    for f in res:
        by_unit.setdefault((f["blob"], f["file"]), []).append(f)

    bugs_found_region = 0
    bugs_found_strict = 0
    detail = []
    for bug in data["bugs"]:
        found_region = []
        found_strict = []
        for h in bug["hunks"]:
            if not h.get("blob") or h["blob"] == "0000000":
                continue
            key = (h["blob"], h["file"])
            for f in by_unit.get(key, []):
                ln = f["ln"]
                start = h["old_start"]
                end = h["old_start"] + h["old_count"] - 1
                if ln is not None and start <= ln <= end:
                    found_region.append((f["rule"], ln, h["file"], h["blob"][:8]))
                    if ln in h["removed"]:
                        found_strict.append((f["rule"], ln, h["file"], h["blob"][:8]))
        if found_region:
            bugs_found_region += 1
        if found_strict:
            bugs_found_strict += 1
        detail.append({
            "bug_id": bug["bug_id"],
            "files": bug["files"],
            "found_region": sorted(set(x[0] for x in found_region)),
            "found_strict": sorted(set(x[0] for x in found_strict)),
        })
    n = data["n_bugs"]
    out = {
        "repo": name,
        "n_bugs": n,
        "n_findings_total": len(findings),
        "found_region": bugs_found_region,
        "found_strict": bugs_found_strict,
        "pct_region": round(100.0 * bugs_found_region / n, 1) if n else 0.0,
        "pct_strict": round(100.0 * bugs_found_strict / n, 1) if n else 0.0,
        "swe_pct": SWE_PCT.get(name),
        "bugs": detail,
    }
    (ROOT / "reports" / f"{name}_result.json").write_text(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    results = []
    for name in (sys.argv[1:] or ["libexpat"]):
        r = analyze(name)
        results.append(r)
        print(f"{r['repo']}: bugs={r['n_bugs']} found(region)={r['found_region']} "
              f"({r['pct_region']}%) strict={r['found_strict']} ({r['pct_strict']}%) "
              f"SWE-sweep={r['swe_pct']}% findings={r['n_findings_total']}")
