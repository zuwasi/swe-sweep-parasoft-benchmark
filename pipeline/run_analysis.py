#!/usr/bin/env python3
"""Parallel Parasoft analysis orchestrator.

Splits each repo's pre.bdf into chunks (by unit count / total lines), copies
pre-images to a WSL-native scratch dir, and runs up to --workers concurrent
cpptestcli processes. Reports land in reports/<name>/chunk_<i>/report.xml.

Usage: run_analysis.py --workers 6 repo1 repo2 ...
"""
import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
SCRATCH = Path("/home/danie/.swesweep_run")
CP = "/mnt/c/Users/danie/parasoft-std/cpptest/cpptestcli"
LANG = {"c": "SWEEP_C", "cpp": "SWEEP_CPP"}
CPP_REPOS = {"duckdb", "gdal", "arrow", "opencv", "tarantool", "cvc5",
             "php-src", "micropython", "proj", "godot", "jerryscript",
             "hdf5", "z3", "libexpat"}
MAX_UNITS = 8
MAX_LINES = 60000


def count_lines(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def split_bdf(name):
    """Split pre.bdf into chunk files; returns list of chunk bdf paths."""
    bdf = ROOT / "analysis" / name / "pre.bdf"
    if not bdf.exists():
        return []
    import re as _re
    text0 = bdf.read_text()
    raw_blocks = _re.split(r'(?=------- cpptestscan )', text0)
    entries = []
    for b in raw_blocks:
        b = b.strip("\n")
        if not b.strip():
            continue
        src = ""
        for line in b.splitlines():
            if line.startswith("arg=") and line[4:].endswith(
                    (".c", ".cc", ".cpp", ".cxx", ".C", ".h", ".hpp")):
                src = line[4:]
        entries.append((b, src))
    sized = []
    for b, src in entries:
        p = Path(src)
        sized.append((b, p, count_lines(p) if p.exists() else 1000))
    # greedy chunks
    sized.sort(key=lambda t: -t[2])
    chunks = []
    for b, p, n in sized:
        placed = False
        for ch in chunks:
            if ch["n_units"] < MAX_UNITS and ch["n_lines"] + n <= MAX_LINES:
                ch["blocks"].append(b)
                ch["n_units"] += 1
                ch["n_lines"] += n
                placed = True
                break
        if not placed:
            chunks.append({"blocks": [b], "n_units": 1, "n_lines": n})
    outdir = ROOT / "analysis" / name
    paths = []
    for i, ch in enumerate(chunks):
        p = outdir / f"pre_chunk{i}.bdf"
        p.write_text("\n".join(ch["blocks"]) + "\n")
        paths.append(p)
    return paths


HDR_EXT = (".h", ".hpp", ".hh", ".hxx", ".inc")


def add_hosts(name, text, scratch_pre, rundir):
    """Header-only units produce an empty scope. For each unit whose source is
    a header, append a host TU (a file including that header) using the same
    flags, so the header is actually analyzed."""
    blocks = [b for b in re.split(r'(?=------- cpptestscan )', text) if b.strip()]
    extra = []
    for b in blocks:
        lines = b.splitlines()
        src = ""
        for line in lines:
            if line.startswith("arg=") and line[4:].endswith(
                    (".c", ".cc", ".cpp", ".cxx", ".C") + HDR_EXT):
                src = line[4:]
        if not src.endswith(HDR_EXT):
            continue
        base = os.path.basename(src)
        r = subprocess.run(["grep", "-rl", "--include=*.c", "--include=*.cc",
                            "--include=*.cpp", "--include=*.cxx", base,
                            str(scratch_pre)], capture_output=True, text=True)
        hosts = [h for h in r.stdout.splitlines() if h]
        if not hosts:
            r = subprocess.run(["grep", "-rl", base, str(scratch_pre)],
                               capture_output=True, text=True)
            hosts = [h for h in r.stdout.splitlines()
                     if h.endswith((".c", ".cc", ".cpp", ".cxx"))]
        if not hosts:
            continue
        host = hosts[0]
        newb = list(lines)
        for k, line in enumerate(newb):
            if line.startswith("arg=") and line[4:] == src:
                newb[k] = f"arg={host}"
                break
        extra.append("\n".join(newb))
        print(f"  host added for header {base}: {os.path.basename(host)}",
              flush=True)
    if extra:
        text = text.rstrip("\n") + "\n" + "\n".join(extra) + "\n"
    return text


def run_chunk(args):
    name, chunk_path, i = args
    scratch_pre = SCRATCH / name / "pre"
    run_dir = SCRATCH / name / f"run_{i}"
    run_dir.mkdir(parents=True, exist_ok=True)
    scratch_bdf = run_dir / "chunk.bdf"
    scratch_rep = run_dir / "rep"
    lang = "cpp" if name in CPP_REPOS else "c"
    if not scratch_pre.exists():
        # copy pre dir to WSL-native scratch (fast I/O)
        src_pre = ROOT / "analysis" / name / "pre"
        scratch_pre.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_pre, scratch_pre, symlinks=True, dirs_exist_ok=True)
    text = Path(chunk_path).read_text()
    old = str(ROOT / "analysis" / name / "pre")
    text = text.replace(old, str(scratch_pre))
    text = add_hosts(name, text, scratch_pre, scratch_bdf.parent)
    scratch_bdf.write_text(text)
    scratch_rep.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    env = dict(os.environ)
    home = SCRATCH / "_home" / f"{name}_{i}"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    r = subprocess.run(
        [CP, "-input", str(scratch_bdf), "-config", f"user://{LANG[lang]}",
         "-compiler", "gcc_13-64", f"-module", f"{name}={scratch_pre}",
         "-report", str(scratch_rep / "report")],
        capture_output=True, text=True, timeout=7200, env=env,
        cwd=str(scratch_bdf.parent))
    dt = time.time() - t0
    ok = (scratch_rep / "report" / "report.xml").exists()
    return (name, i, ok, round(dt), r.returncode,
            (r.stdout + r.stderr)[-400:] if not ok else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("repos", nargs="+")
    a = ap.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)

    jobs = []
    for name in a.repos:
        chunks = split_bdf(name)
        # skip chunks whose report already exists (resumable)
        for i, cpath in enumerate(chunks):
            if (SCRATCH / name / f"run_{i}" / "rep" / "report" / "report.xml").exists():
                continue
            jobs.append((name, cpath, i))
        print(f"{name}: {len(chunks)} chunks")
    print(f"total {len(jobs)} chunk runs, {a.workers} workers")
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for res in ex.map(run_chunk, jobs):
            done += 1
            name, i, ok, dt, rc, err = res
            print(f"[{done}/{len(jobs)}] {name} chunk{i}: "
                  f"{'OK' if ok else 'FAIL'} {dt}s {err[:200] if err else ''}",
                  flush=True)
    print(f"all done in {round(time.time()-t0)}s")


if __name__ == "__main__":
    main()
