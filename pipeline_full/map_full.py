#!/usr/bin/env python3
"""Map whole-project scan findings to SWE-sweep bugs.

SWE-sweep chains its tasks, so each bug's defect lines live in the base_ref
tree, possibly at shifted line numbers. For every bug hunk we locate the
hunk's pre-image lines in the base_ref file by exact content match, then map
the whole-project violations (resolved by relative path, deduped across
chunks) onto the aligned regions. found_region/found_strict use the same
definitions as the published bug-file scan.

Writes analysis_full/<name>_full_result.json and prints a comparison.
"""
import json, re, sys
from difflib import SequenceMatcher
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
MAN = Path("/mnt/c/Projects/swe-sweep-parasoft-benchmark/manifests")
VIOL = re.compile(r"<(FlowViol|StdViol|ClViol|CpViol)\b(.*?)/?>", re.S)

def parse_violations(name):
    out = set()
    repos_prefix = str(ROOT / "repos") + "/"
    reports = Path("/home/danie/.swesweep_run/full") / name
    for f in sorted(reports.glob("run_*/rep/report/report.xml")):
        text = f.read_text(errors="replace")
        for m in VIOL.finditer(text):
            a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(2)))
            rule, ln, loc = a.get("rule", ""), a.get("ln", ""), a.get("locFile", "")
            if not rule or not loc:
                continue
            rel = loc.lstrip("/")
            prefix = name + "/"
            if rel.startswith(prefix):
                rel = rel[len(prefix):]
            elif rel.startswith(repos_prefix):
                # Unity-build units include sources by absolute path into the
                # original checkout; re-anchor them onto the scanned module.
                tail = rel[len(repos_prefix):]
                if tail.startswith(name + "/"):
                    rel = tail[len(name) + 1:]
                else:
                    continue
            else:
                continue
            if ln.isdigit():
                out.add((rel, int(ln), rule))
    return out

def align_file(rel, blob, pre_root, base_root, cache):
    """Map pre-image line numbers onto base_ref line numbers via full-file diff."""
    key = (rel, blob)
    if key in cache:
        return cache[key]
    pre_f = pre_root / blob / rel
    base_f = base_root / rel
    mapping = None
    if pre_f.exists() and base_f.exists():
        try:
            pre_lines = [l.rstrip() for l in
                         pre_f.read_text(errors="replace").splitlines()]
            base_lines = [l.rstrip() for l in
                          base_f.read_text(errors="replace").splitlines()]
            mapping = {}
            sm = SequenceMatcher(None, pre_lines, base_lines, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    for k in range(i2 - i1):
                        mapping[i1 + k + 1] = j1 + k + 1
                elif tag in ("replace", "delete"):
                    # Nearest-surviving base line for pre lines that were
                    # rewritten or removed relative to base_ref.
                    anchor = min(max(j1, 1), max(len(base_lines), 1))
                    for k in range(i2 - i1):
                        mapping[i1 + k + 1] = anchor
        except OSError:
            pass
    cache[key] = mapping
    return mapping

def align(bug, pre_root, base_root, cache):
    regions, stricts, unaligned = set(), set(), 0
    for h in bug["hunks"]:
        rel, blob = h["file"].replace("\\", "/"), h["blob"]
        if blob is None or rel is None:
            unaligned += 1; continue
        mapping = align_file(rel, blob, pre_root, base_root, cache)
        if mapping is None:
            unaligned += 1; continue
        s, c = h["old_start"], h["old_count"]
        if c == 0 or s - 1 + c > (max(mapping) if mapping else 0):
            unaligned += 1; continue
        regions.update(mapping[n] for n in range(s, s + c) if n in mapping)
        stricts.update(mapping[n] for n in h.get("removed", []) if n in mapping)
    return regions, stricts, unaligned

def analyze(name):
    man = json.loads((MAN / f"{name}_manifest.json").read_text())
    vios = parse_violations(name)
    by_file = {}
    for rel, ln, rule in vios:
        by_file.setdefault(rel, []).append((ln, rule))
    res = {"repo": name, "bugs": [], "total_violations": len(vios)}
    n_reg = n_strict = n_unalign = 0
    cache = {}
    for bug in man["bugs"]:
        files = {h["file"].replace("\\", "/") for h in bug["hunks"]}
        regions, stricts, unaligned = align(bug, ROOT / "analysis" / name / "pre",
                                            ROOT / "repos" / name, cache)
        hits_r, hits_s = [], []
        for f in files:
            for ln, rule in by_file.get(f, []):
                if ln in regions:
                    hits_r.append(rule)
                if ln in stricts:
                    hits_s.append(rule)
        found_r = sorted(set(hits_r))
        found_s = sorted(set(hits_s))
        n_reg += bool(found_r); n_strict += bool(found_s)
        n_unalign += unaligned
        res["bugs"].append({"bug_id": bug["bug_id"],
                            "found_region": found_r, "found_strict": found_s,
                            "aligned_hunks": len(bug["hunks"]) - unaligned,
                            "unaligned_hunks": unaligned})
    res["n_bugs"] = len(man["bugs"])
    res["found_region_count"] = n_reg
    res["found_strict_count"] = n_strict
    res["unaligned_hunks_total"] = n_unalign
    out = ROOT / "analysis_full" / f"{name}_full_result.json"
    json.dump(res, open(out, "w"), indent=1)
    orig = json.loads((Path("/mnt/c/Projects/swe-sweep-parasoft-benchmark")
                       / "results" / f"{name}_result.json").read_text())
    o = {b["bug_id"]: b for b in orig["bugs"]}
    o_r = sum(1 for b in o.values() if b["found_region"])
    o_s = sum(1 for b in o.values() if b["found_strict"])
    print(f"{name}: FULL region {n_reg}/{res['n_bugs']} strict {n_strict}/{res['n_bugs']} "
          f"unaligned_hunks={n_unalign} viol={len(vios)} || "
          f"bug-file region {o_r} strict {o_s}", flush=True)
    return res

if __name__ == "__main__":
    for name in (sys.argv[1:] or []):
        analyze(name)
