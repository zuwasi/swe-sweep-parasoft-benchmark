#!/usr/bin/env python3
"""Materialize exact pre-fix bug file versions from git blob hashes.

One analysis unit = (file, blob). Writes analysis/<repo>/pre/<blob>/<file>.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/danie/swesweep-parasoft-benchmark")


def materialize(name):
    data = json.loads((ROOT / "analysis" / f"{name}_bugs.json").read_text())
    repo = ROOT / "repos" / name
    pre = ROOT / "analysis" / name / "pre"
    manifest, failed = [], []
    for unit in data["analysis_units"]:
        f, blob = unit["file"], unit["blob"]
        dest = pre / blob / f
        if dest.exists() and dest.stat().st_size > 0:
            manifest.append(unit)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", blob],
                           capture_output=True)
        if r.returncode != 0:
            failed.append((f, blob, r.stderr.decode()[:100]))
            continue
        dest.write_bytes(r.stdout)
        manifest.append(unit)
    (ROOT / "analysis" / name / "pre_manifest.json").write_text(
        json.dumps(manifest, indent=1))
    print(f"{name}: units={len(data['analysis_units'])} materialized={len(manifest)} "
          f"failed={len(failed)}")
    for f, blob, err in failed[:5]:
        print(f"  FAIL {f} {blob[:12]} {err}")


if __name__ == "__main__":
    for name in sys.argv[1:]:
        materialize(name)
