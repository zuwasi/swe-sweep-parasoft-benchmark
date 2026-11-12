#!/usr/bin/env python3
"""Generate a Parasoft .bdf for one repo's bug pre-image analysis units.

Units are (file, blob) pairs, pre-images at analysis/<name>/pre/<blob>/<file>.
Flag source, in order:
  1. compile_commands.json anywhere under repos/<name>/: exact entry for the
     file, else same basename, else nearest directory.
  2. raw_flags.json (list of {directory, command, file}) captured from
     make -n / scons -n dumps.
  3. Fallback: gcc/g++ with harvested -I dirs and a language std flag.
Writes analysis/<name>/pre.bdf.
"""
import json
import os
import shlex
import sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
SRC_EXT = (".c", ".cc", ".cpp", ".cxx", ".C", ".h", ".hpp", ".inc", ".c++", ".cp")
FALLBACK_STD = {"c": ["-std=gnu99"], "cpp": ["-std=gnu++17"]}
# Per-repo extra defines added to every unit (compile_commands.json sometimes
# misses target_compile_definitions; pre-image blobs may need newer defines).
EXTRA_DEFS = {
    "libexpat": ["-DXML_GE=1"],
}
IGNORE_DIRS = {"build", "builddir", "pre"}


def find_compile_commands(name):
    repo = ROOT / "repos" / name
    cands = []
    for p in repo.rglob("compile_commands.json"):
        if not any(part in IGNORE_DIRS and "build" != part for part in ()):
            cands.append(p)
    cands.sort(key=lambda p: len(p.parts))
    return cands[0] if cands else None


def load_cc(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def is_src(t):
    return t.endswith(SRC_EXT) and not t.startswith("-")


def split_cmd(cmd):
    toks = shlex.split(cmd)
    if not toks:
        return None, [], []
    compiler = toks[0]
    flags, srcs = [], []
    skip = False
    for i, t in enumerate(toks[1:], start=1):
        if skip:
            skip = False
            continue
        if t == "-o":
            skip = True
            continue
        if t in ("-MF", "-MT", "-MQ", "-MJ"):
            skip = True
            continue
        if t == "-c":
            continue
        if is_src(t):
            srcs.append(t)
            continue
        if t.startswith("-j") or t.startswith("--output"):
            continue
        flags.append(t)
    return compiler, flags, srcs


def cc_for_file(entries, rel):
    for e in entries:
        if e.get("file", "").endswith(rel):
            return e
    base = os.path.basename(rel)
    d = os.path.dirname(rel)
    same_base = [e for e in entries if os.path.basename(e.get("file", "")) == base]
    if same_base:
        same_dir = [e for e in same_base if d and d in e.get("file", "")]
        return (same_dir or same_base)[0]
    if d:
        same_tree = [e for e in entries if d in e.get("directory", "") or d in e.get("file", "")]
        if same_tree:
            return same_tree[0]
    return entries[0] if entries else None


def build_bdf(name, lang, mode):
    data = json.loads((ROOT / "analysis" / f"{name}_bugs.json").read_text())
    pre = ROOT / "analysis" / name / "pre"
    units = data["analysis_units"]
    repo = ROOT / "repos" / name
    lines = []

    def add_entry(cwd, compiler, flags, src):
        lines.append("------- cpptestscan v.10.7.3 (generated) -------")
        lines.append(f"working_dir={cwd}")
        lines.append(f"project_name={name}")
        lines.append(f"arg={compiler}")
        for fl in EXTRA_DEFS.get(name, []) + flags:
            lines.append(f"arg={fl}")
        lines.append("arg=-c")
        lines.append(f"arg={src}")

    cc_path = find_compile_commands(name)
    raw_path = ROOT / "analysis" / name / "raw_flags.json"
    entries = load_cc(cc_path) if cc_path else []
    raw = json.loads(raw_path.read_text()) if raw_path.exists() else []
    n_cc = n_raw = n_fb = 0

    for unit in units:
        rel, blob = unit["file"], unit["blob"]
        src = str(pre / blob / rel)
        # Sibling headers resolved relative to the original source directory
        # (quote-include fallback), needed when the file is not in the repo tree.
        orig_dir_flag = "-I" + str((repo / rel).parent)
        used = False
        if entries and mode in ("cc", "auto"):
            e = cc_for_file(entries, rel)
            if e and e.get("command"):
                compiler, flags, _ = split_cmd(e["command"])
                add_entry(e.get("directory", str(repo)), compiler, flags + [orig_dir_flag], src)
                n_cc += 1
                used = True
        if not used and raw and mode in ("raw", "auto"):
            cands = [r for r in raw if r["file"].endswith(rel)]
            if not cands:
                cands = [r for r in raw
                         if os.path.basename(r["file"]) == os.path.basename(rel)]
            if cands:
                r = cands[0]
                compiler, flags, _ = split_cmd(r["command"])
                add_entry(r["directory"], compiler, flags + [orig_dir_flag], src)
                n_raw += 1
                used = True
        if not used:
            compiler = "g++" if lang == "cpp" else "gcc"
            std = FALLBACK_STD[lang]
            sdir = pre / blob / rel
            incs = ["-I" + str(sdir.parent), f"-I{repo}"]
            for sub in ("include", "src", "lib"):
                p = repo / sub
                if p.is_dir():
                    incs.append("-I" + str(p))
            add_entry(str(repo), compiler, std + incs + [orig_dir_flag], src)
            n_fb += 1

    out = ROOT / "analysis" / name / "pre.bdf"
    out.write_text("\n".join(lines) + "\n")
    print(f"{name}: units={len(units)} cc_flags={n_cc} raw_flags={n_raw} fallback={n_fb} -> {out}")


if __name__ == "__main__":
    name, lang = sys.argv[1], sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "auto"
    build_bdf(name, lang, mode)
