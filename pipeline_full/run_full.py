#!/usr/bin/env python3
"""Whole-project Parasoft scan for all repos.

For each repo: copy the bug-era working tree (minus .git) to WSL-native
scratch, split analysis_full/<name>/full.bdf into chunks (same limits as the
published scan: <=8 units, <=60000 lines), run cpptestcli per chunk with the
repo's own config, 6 parallel workers across one global queue ordered small
repo first. Reports: reports_full/<name>/chunk_<i>/report.xml. Resumable.
"""
import json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
SCRATCH = Path("/home/danie/.swesweep_run/full")
CP = "/mnt/c/Users/danie/parasoft-std/cpptest/cpptestcli"
MAX_UNITS, MAX_LINES, TIMEOUT = 8, 60000, 7200
HDR_EXT = (".h", ".hpp", ".hh", ".hxx", ".inc")
ORDER = ["micropython", "arrow", "jerryscript", "proj", "php-src", "hdf5",
         "duckdb", "tarantool", "opencv", "cvc5", "z3", "gdal", "godot",
         "libexpat"]

def count_lines(path):
    try:
        with open(path, "rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0

def split_bdf(name):
    bdf = ROOT / "analysis_full" / name / "full.bdf"
    entries = []
    for b in re.split(r"(?=------- cpptestscan )", bdf.read_text()):
        b = b.strip("\n")
        if not b.strip():
            continue
        src = ""
        for line in b.splitlines():
            if line.startswith("arg=") and line[4:].endswith(
                    (".c", ".cc", ".cpp", ".cxx", ".C", ".h", ".hpp")):
                src = line[4:]
        p = Path(src)
        entries.append((b, p, count_lines(p) if p.exists() else 1000))
    entries.sort(key=lambda t: -t[2])
    chunks = []
    for b, p, n in entries:
        placed = False
        for ch in chunks:
            if ch["n_units"] < MAX_UNITS and ch["n_lines"] + n <= MAX_LINES:
                ch["blocks"].append(b); ch["n_units"] += 1; ch["n_lines"] += n
                placed = True; break
        if not placed:
            chunks.append({"blocks": [b], "n_units": 1, "n_lines": n})
    outdir = ROOT / "analysis_full" / name
    paths = []
    for i, ch in enumerate(chunks):
        q = outdir / f"full_chunk{i}.bdf"
        q.write_text("\n".join(ch["blocks"]) + "\n")
        paths.append(q)
    return paths

def copy_repo(name):
    src = ROOT / "repos" / name
    dst = SCRATCH / name / "repo"
    if dst.exists():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsync", "-a", "--exclude", ".git", f"{src}/", f"{dst}/"],
                   check=True)
    # Build-generated unity files may include sources by their absolute path
    # in the original checkout; re-anchor them onto the scratch module so
    # Parasoft attributes violations inside them to module-relative files.
    subprocess.run(
        ["bash", "-c",
         f"grep -rl '{ROOT}/repos/{name}' {dst} 2>/dev/null | "
         f"xargs -r sed -i 's|{ROOT}/repos/{name}|{dst}|g'"],
        check=False)
    return dst

def run_chunk(job):
    name, i, chunk_path, cfg = job
    scratch_repo = SCRATCH / name / "repo"
    run_dir = SCRATCH / name / f"run_{i}"
    run_dir.mkdir(parents=True, exist_ok=True)
    scratch_bdf = run_dir / "chunk.bdf"
    text = Path(chunk_path).read_text()
    scratch_bdf.write_text(text.replace(
        str(ROOT / "repos" / name), str(scratch_repo)))
    scratch_rep = run_dir / "rep"
    scratch_rep.mkdir(exist_ok=True)
    env = dict(os.environ)
    home = SCRATCH / "_home" / f"{name}_{i}"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    t0 = time.time()
    try:
        r = subprocess.run(
            [CP, "-input", str(scratch_bdf), "-config", f"user://{cfg}",
             "-compiler", "gcc_13-64", "-module", f"{name}={scratch_repo}",
             "-report", str(scratch_rep / "report")],
            capture_output=True, text=True, timeout=TIMEOUT, env=env,
            cwd=str(scratch_bdf.parent))
        rc, err = r.returncode, (r.stdout + r.stderr)[-400:]
    except subprocess.TimeoutExpired:
        rc, err = -9, "TIMEOUT"
    ok = (scratch_rep / "report" / "report.xml").exists()
    return (name, i, ok, round(time.time() - t0), rc,
            err if not ok else "")

def main():
    repos = sys.argv[1:] or ORDER
    jobs = []
    for name in ORDER:
        if name not in repos:
            continue
        info = json.loads((ROOT / "analysis_full" / name / "full_info.json").read_text())
        chunks = split_bdf(name)
        copy_repo(name)
        n_todo = 0
        for i, cp_ in enumerate(chunks):
            if (SCRATCH / name / f"run_{i}" / "rep" / "report" / "report.xml").exists():
                continue
            jobs.append((name, i, cp_, info["config"]))
            n_todo += 1
        print(f"{name}: {len(chunks)} chunks, {n_todo} to run", flush=True)
    print(f"total {len(jobs)} chunk runs", flush=True)
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        for res in ex.map(run_chunk, jobs):
            done += 1
            name, i, ok, dt, rc, err = res
            print(f"[{done}/{len(jobs)}] {name} chunk{i}: "
                  f"{'OK' if ok else 'FAIL'} {dt}s rc={rc} {err[:150] if err else ''}",
                  flush=True)
    print(f"all done in {round(time.time()-t0)}s", flush=True)

if __name__ == "__main__":
    main()
