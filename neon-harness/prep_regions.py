#!/usr/bin/env python3
"""Precompute each bug's defect region/strict lines in base-tree coordinates.

Region = base lines mapped from the hunk's full pre-image range; strict = base
lines mapped from removed lines. Same alignment as pipeline_full/map_full.py.
Output: neon-harness/regions/<repo>.json
"""
import json
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
MAN = Path("/mnt/c/Projects/swe-sweep-parasoft-benchmark/manifests")
OUT = Path("/mnt/c/Projects/swe-sweep-parasoft-benchmark/neon-harness/regions")

def align_file(rel, blob, pre_root, base_root, cache):
    key = (rel, blob)
    if key in cache:
        return cache[key]
    pre_f = pre_root / blob / rel
    base_f = base_root / rel
    mapping = None
    if pre_f.exists() and base_f.exists():
        try:
            pre_lines = [l.rstrip() for l in pre_f.read_text(errors="replace").splitlines()]
            base_lines = [l.rstrip() for l in base_f.read_text(errors="replace").splitlines()]
            mapping = {}
            sm = SequenceMatcher(None, pre_lines, base_lines, autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    for k in range(i2 - i1):
                        mapping[i1 + k + 1] = j1 + k + 1
                elif tag in ("replace", "delete"):
                    anchor = min(max(j1, 1), max(len(base_lines), 1))
                    for k in range(i2 - i1):
                        mapping[i1 + k + 1] = anchor
        except OSError:
            pass
    cache[key] = mapping
    return mapping

def analyze(name):
    man = json.loads((MAN / f"{name}_manifest.json").read_text())
    cache = {}
    bugs = []
    n_un = 0
    for bug in man["bugs"]:
        regions, stricts = set(), set()
        for h in bug["hunks"]:
            rel = h["file"].replace("\\", "/")
            blob = h["blob"]
            if blob is None or rel is None:
                n_un += 1; continue
            mapping = align_file(rel, blob, ROOT / "analysis" / name / "pre",
                                 ROOT / "repos" / name, cache)
            if mapping is None:
                n_un += 1; continue
            s, c = h["old_start"], h["old_count"]
            if c == 0 or s - 1 + c > (max(mapping) if mapping else 0):
                n_un += 1; continue
            regions.update(mapping[n] for n in range(s, s + c) if n in mapping)
            stricts.update(mapping[n] for n in h.get("removed", []) if n in mapping)
        bugs.append({"bug_id": bug["bug_id"],
                     "files": sorted({h["file"].replace("\\", "/") for h in bug["hunks"]}),
                     "region": sorted(regions), "strict": sorted(stricts)})
    json.dump({"repo": name, "n_bugs": len(man["bugs"]), "bugs": bugs},
              open(OUT / f"{name}.json", "w"))
    print(f"{name}: {len(man['bugs'])} bugs, unaligned_hunks={n_un}")

if __name__ == "__main__":
    import sys
    for n in (sys.argv[1:] or []):
        analyze(n)
