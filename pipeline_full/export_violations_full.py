#!/usr/bin/env python3
"""Export the deduped whole-project violations per repo as gzipped TSV.

One line per unique (relative path, line, rule) finding, so the bug mapping in
map_full.py can be recomputed without rerunning C/C++test or shipping the full
raw XML reports.
"""
import gzip, sys
from pathlib import Path
from map_full import parse_violations

OUT = Path("/mnt/c/Projects/swe-sweep-parasoft-benchmark/results_full/violations")

def main(names):
    OUT.mkdir(parents=True, exist_ok=True)
    for name in names:
        vios = parse_violations(name)
        path = OUT / f"{name}_violations.tsv.gz"
        with gzip.open(path, "wt") as fh:
            for rel, ln, rule in sorted(vios):
                fh.write(f"{rel}\t{ln}\t{rule}\n")
        print(f"{name}: {len(vios)} violations -> {path}", flush=True)

if __name__ == "__main__":
    main(sys.argv[1:])
