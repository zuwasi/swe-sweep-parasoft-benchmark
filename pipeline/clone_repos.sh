#!/usr/bin/env bash
# Clone every C/C++ SWE-sweep repo at its pinned base commit.
set -u
ROOT=/mnt/c/Users/danie/swesweep-parasoft-benchmark
cd "$ROOT/repos"

for name in "$@"; do
  json="$ROOT/analysis/${name}_bugs.json"
  url=$(python3 -c "import json;print(json.load(open('$json'))['clone_url'])")
  ref=$(python3 -c "import json;print(json.load(open('$json'))['base_ref'])")
  if [ -d "$name/.git" ]; then
    echo "SKIP $name (exists)"
    continue
  fi
  echo "== $name $ref"
  git init -q "$name" 2>/dev/null
  git -C "$name" remote add origin "$url" 2>/dev/null
  # Shallow fetch of the pinned base ref (tag or branch).
  if ! git -C "$name" fetch -q --depth 1 origin "$ref" 2>/dev/null; then
    echo "  shallow fetch failed, falling back to full clone"
    rm -rf "$name"
    git clone -q "$url" "$name" || { echo "  CLONE FAILED $name"; continue; }
    git -C "$name" checkout -q "$ref"
  fi
  git -C "$name" checkout -q FETCH_HEAD
  echo "  done: $(git -C "$name" rev-parse HEAD)"
done
