#!/usr/bin/env python3
"""v2: richer per-bug diff snippets. Per hunk: 5 lines context on each side;
lines in `removed` marked r=1; when a hunk has no removed lines the whole hunk
span is marked i=1 (insertion point: the defect is code that is missing here)."""
import json, sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
MANIFESTS = Path("/mnt/c/Projects/swe-sweep-parasoft-benchmark/manifests")
OUT = ROOT / "classification" / "snippets_v2"
CTX = 5
MAX_LINES = 90

def pre_file(repo, blob, rel):
    if not blob:
        return None
    base = ROOT / "analysis" / repo / "pre"
    for pre in (blob[:8], blob[:7]):
        p = base / pre / rel
        if p.exists():
            return p
    pref = blob[:6]
    if base.exists():
        for d in base.iterdir():
            if d.name.startswith(pref):
                p = d / rel
                if p.exists():
                    return p
    return None

def main(repos):
    OUT.mkdir(parents=True, exist_ok=True)
    for repo in repos:
        man = json.load(open(MANIFESTS / f"{repo}_manifest.json"))
        rows = []
        for b in man["bugs"]:
            pieces = []
            seen = set()
            for h in b["hunks"]:
                pf = pre_file(repo, h.get("blob"), h["file"])
                if pf is None:
                    continue
                try:
                    src = pf.read_text(errors="replace").splitlines()
                except OSError:
                    continue
                removed = set(h.get("removed", []))
                span = set(range(h["old_start"], h["old_start"] + h["old_count"]))
                s = max(1, h["old_start"] - CTX)
                e = min(len(src), h["old_start"] + h["old_count"] + CTX)
                for n in range(s, e + 1):
                    key = (h["file"], n)
                    if key in seen:
                        continue
                    seen.add(key)
                    pieces.append({"f": h["file"].split("/")[-1], "n": n,
                                   "t": src[n-1][:110],
                                   "r": 1 if n in removed else 0,
                                   "i": 1 if (not removed and n in span) else 0})
            pieces = pieces[:MAX_LINES]
            rows.append({"bug_id": b["bug_id"], "files": b.get("files", []),
                         "n_removed": sum(p["r"] for p in pieces),
                         "lines": pieces})
        with open(OUT / f"{repo}.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        empty = sum(1 for r in rows if not r["lines"])
        print(repo, len(rows), "empty:", empty)

if __name__ == "__main__":
    main(sys.argv[1:])
