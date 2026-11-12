#!/usr/bin/env python3
"""Verify bug hunk locations align with the checked-out base tag.

For each bug hunk, the checked-out file's lines in [old_start, old_start+old_count)
should contain the removed lines ('-' lines of the hunk) in order. Report drift.
"""
import json
import sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")


def hunk_matches(flines, hunk, removed):
    start = hunk["old_start"] - 1  # 0-based
    end = hunk["old_start"] + hunk["old_count"] - 1
    if start < 0 or end > len(flines):
        return False
    window = flines[start:end]
    it = iter(removed)
    cur = next(it, None)
    if cur is None:
        return True  # pure addition hunk, cannot verify; assume ok
    for w in window:
        if cur is not None and w == cur:
            cur = next(it, None)
    return cur is None


def main():
    repos = sys.argv[1:]
    for name in repos:
        data = json.loads((ROOT / "analysis" / f"{name}_bugs.json").read_text())
        ok = drift = missing = 0
        missing_files = set()
        for bug in data["bugs"]:
            for hunk in bug["hunks"]:
                f = ROOT / ROOT / "analysis" / name / "pre" / hunk["file"]
                if not f.exists():
                    missing += 1
                    missing_files.add(hunk["file"])
                    continue
                flines = f.read_text(errors="replace").splitlines()
                if hunk_matches(flines, hunk, hunk["removed"]):
                    ok += 1
                else:
                    drift += 1
        print(f"{name}: hunks ok={ok} drift={drift} missing_file={missing} "
              f"missing_files={sorted(missing_files)[:5]}")


if __name__ == "__main__":
    main()
