#!/usr/bin/env python3
"""Parse gcc/cc/clang compile lines from a make -n / scons -n log into
raw_flags.json: [{directory, command, file}, ...]."""
import json
import shlex
import sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")
SRC_EXT = (".c", ".cc", ".cpp", ".cxx", ".C")


def extract(log_path, out_path):
    text = Path(log_path).read_text(errors="replace")
    entries = []
    seen = set()
    for line in text.splitlines():
        # strip make echoes like "gcc ..." possibly prefixed by cd or env
        if not any(ext in line for ext in SRC_EXT):
            continue
        # libtool --mode=compile lines: cut everything before the compiler
        m = re_search_libtool(line)
        if m:
            line = line[m.end():].strip()
        if not re_search_compiler(line):
            continue
        try:
            toks = shlex.split(line)
        except ValueError:
            continue
        if not toks or not re_search_compiler(toks[0]):
            continue
        srcs = [t for t in toks[1:]
                if t.endswith(SRC_EXT) and not t.startswith("-")]
        if not srcs:
            continue
        out = find_out(toks)
        src = srcs[-1]
        key = (src, out)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"directory": ".", "command": " ".join(toks), "file": src})
    Path(out_path).write_text(json.dumps(entries, indent=1))
    print(f"{log_path}: {len(entries)} compile lines -> {out_path}")


def re_search_compiler(line):
    import re
    return re.search(r'\b(gcc|g\+\+|cc|c\+\+|clang|clang\+\+)(\s|$)', line)


def re_search_libtool(line):
    import re
    return re.search(r'--mode=compile\s+', line)


def find_out(toks):
    for i, t in enumerate(toks):
        if t == "-o" and i + 1 < len(toks):
            return toks[i + 1]
    return ""


if __name__ == "__main__":
    log, out = sys.argv[1], sys.argv[2]
    extract(log, out)
