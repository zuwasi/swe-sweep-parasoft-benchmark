#!/usr/bin/env python3
"""Extract per-bug locations from SWE-sweep oracle patches for the C/C++ repos.

For each repo task under /tmp/swe-sweep/tasks/swe-sweep__<name>, read task.toml
(clone_url, upstream_commit, base_ref) and parse each tests/oracle/*.patch.
Each patch is one bug. Record, for every hunk in the pre-state (a/ side):
  - file path
  - old_start/old_count (the hunk region)
  - removed line numbers (lines that existed before the fix and were changed)
Bug locations = union of hunk regions and removed-line numbers per file.
"""
import configparser
import json
import re
import sys
from pathlib import Path

TASKS = Path("/tmp/swe-sweep/tasks")
OUT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark/analysis")
CPP_REPOS = [
    "duckdb", "gdal", "arrow", "opencv", "tarantool", "cvc5", "php-src",
    "micropython", "proj", "godot", "jerryscript", "hdf5", "z3", "libexpat",
]

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
DIFF_GIT = re.compile(r'^diff --git a/(.*) b/(.*)$')
INDEX = re.compile(r"^index (\S+)\.\.(\S+)")


def parse_patch(path: Path):
    bugs = []
    cur_file = None
    cur_blob = None
    hunk = None  # dict(file, old_start, old_count, removed=[])
    for raw in path.read_text(errors="replace").splitlines():
        m = DIFF_GIT.match(raw)
        if m:
            if hunk:
                bugs.append(hunk)
                hunk = None
            cur_file = m.group(1)
            cur_blob = None
            continue
        m = INDEX.match(raw)
        if m and cur_file:
            cur_blob = m.group(1)
            continue
        m = HUNK.match(raw)
        if m and cur_file:
            if hunk:
                bugs.append(hunk)
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) is not None else 1
            hunk = {"file": cur_file, "blob": cur_blob, "old_start": old_start,
                    "old_count": old_count, "removed": []}
            old_line = old_start
            continue
        if hunk is None:
            continue
        if raw.startswith("-"):
            hunk["removed"].append(old_line)
            old_line += 1
        elif raw.startswith("+"):
            pass
        elif raw.startswith(" ") or raw == "":
            old_line += 1
        elif raw.startswith("\\"):
            pass
        else:
            # hunk ended (new diff --git, mode change, etc.)
            pass
    if hunk:
        bugs.append(hunk)
    return bugs


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name in CPP_REPOS:
        tdir = TASKS / f"swe-sweep__{name}"
        if not tdir.exists():
            print(f"MISSING {name}", file=sys.stderr)
            continue
        meta = configparser.ConfigParser(interpolation=None)
        meta.read_string("[top]\n" + tdir.joinpath("task.toml").read_text())
        m = meta["metadata"]
        patches = sorted((tdir / "tests" / "oracle").glob("*.patch"))
        repo = {
            "repo": name,
            "clone_url": m.get("clone_url").strip('"'),
            "upstream_commit": m.get("upstream_commit").strip('"'),
            "base_ref": m.get("base_ref", "").strip('"'),
            "n_subtasks": meta["metadata"].getint("n_subtasks", fallback=0),
            "bugs": [],
        }
        for p in patches:
            hunks = parse_patch(p)
            repo["bugs"].append({
                "bug_id": p.stem,
                "patch": str(p),
                "hunks": hunks,
                "files": sorted({h["file"] for h in hunks}),
            })
        repo["n_bugs"] = len(repo["bugs"])
        units = {}
        for b in repo["bugs"]:
            for h in b["hunks"]:
                if h.get("blob") and h["blob"] != "0000000" and set(h["blob"]) != {"0"}:
                    units[(h["file"], h["blob"])] = True
        repo["analysis_units"] = sorted(
            [{"file": f, "blob": blob} for f, blob in units],
            key=lambda u: (u["file"], u["blob"]))
        repo["n_units"] = len(repo["analysis_units"])
        repo["bug_files"] = sorted({f for f, _ in units})
        outp = OUT / f"{name}_bugs.json"
        outp.write_text(json.dumps(repo, indent=1))
        summary[name] = {
            "bugs": repo["n_bugs"],
            "bug_files": len(repo["bug_files"]),
            "commit": repo["upstream_commit"][:10],
        }
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
