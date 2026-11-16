#!/usr/bin/env python3
"""Build a whole-project Parasoft .bdf per repo from the project's own build
system capture (compile_commands.json or raw_flags.json), exactly as
gen_bdf.py resolves flags, but covering EVERY translation unit the build
system sees, not only the bug files. Writes analysis_full/<name>/full.bdf.
"""
import json, os, sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
sys.path.insert(0, str(Path("/mnt/c/Projects/swe-sweep-parasoft-benchmark/pipeline")))
import gen_bdf  # reuse find_compile_commands, split_cmd, load_cc, EXTRA_DEFS

LANG = {"duckdb":"cpp","gdal":"cpp","arrow":"cpp","opencv":"cpp","tarantool":"cpp",
        "cvc5":"cpp","php-src":"c","micropython":"c","proj":"cpp","godot":"cpp",
        "jerryscript":"c","hdf5":"c","z3":"cpp","libexpat":"c"}
CFG  = {"c":"SWEEP_C","cpp":"SWEEP_CPP"}
# keep the config each repo actually ran with in the published benchmark
OVERRIDE_CFG = {"libexpat": "SWEEP_CPP"}  # run_analysis.py put libexpat in CPP_REPOS
# raw_flags captured against a since-deleted scratch root: rewrite onto the repo
ROOT_REWRITE = {"php-src": "/tmp/buildroot/php-8.2.12",
                "hdf5": "/tmp/buildroot/hdf5"}
REWRITE_SUFFIX = {"hdf5": "/build"}

def norm(e):
    f = e["file"]
    if not os.path.isabs(f):
        f = os.path.normpath(os.path.join(e.get("directory", "."), f))
    return f

def build(name):
    repo = ROOT / "repos" / name
    cc_path = gen_bdf.find_compile_commands(name)
    raw_path = ROOT / "analysis" / name / "raw_flags.json"
    entries = gen_bdf.load_cc(cc_path) if cc_path else []
    if not entries and raw_path.exists():
        entries = json.loads(raw_path.read_text())
    assert entries, f"{name}: no build capture"
    seen, blocks, missing = set(), [], 0
    for e in entries:
        rw = ROOT_REWRITE.get(name)
        if rw:
            src = norm(e).replace(rw, str(repo) + REWRITE_SUFFIX.get(name, ""))
            suf = REWRITE_SUFFIX.get(name, "")
            e = dict(e, file=e["file"].replace(rw, str(repo) + suf),
                     directory=e.get("directory", "").replace(rw, str(repo) + suf),
                     command=e.get("command", "").replace(rw, str(repo) + suf))
        src = norm(e)
        rel = os.path.relpath(src, repo)
        if rel.startswith(".."):
            continue  # outside the repo tree
        key = rel.replace("\\", "/").lower()
        if key in seen:
            continue
        seen.add(key)
        p = Path(src)
        if not p.exists():
            missing += 1
            continue
        compiler, flags, _ = gen_bdf.split_cmd(e.get("command", ""))
        if not compiler:
            continue
        flags = gen_bdf.EXTRA_DEFS.get(name, []) + flags
        lines = ["------- cpptestscan v.10.7.3 (generated) -------",
                 f"working_dir={e.get('directory', str(repo))}",
                 f"project_name={name}",
                 f"arg={compiler}"]
        lines += [f"arg={f}" for f in flags]
        lines += ["arg=-c", f"arg={src}"]
        blocks.append("\n".join(lines))
    outdir = ROOT / "analysis_full" / name
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "full.bdf").write_text("\n".join(blocks) + "\n")
    cfg = OVERRIDE_CFG.get(name, CFG[LANG[name]])
    json.dump({"units": len(blocks), "missing": missing, "config": cfg},
              open(outdir / "full_info.json", "w"))
    print(f"{name}: {len(blocks)} units ({missing} missing files) config={cfg}")

if __name__ == "__main__":
    for name in (sys.argv[1:] or list(LANG)):
        build(name)
