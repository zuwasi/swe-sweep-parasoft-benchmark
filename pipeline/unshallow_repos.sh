#!/usr/bin/env bash
# Bring each shallow clone to full history so all pre-fix blobs are available.
set -u
ROOT=/mnt/c/Users/danie/swesweep-parasoft-benchmark
cd "$ROOT/repos"
for name in "$@"; do
  if [ ! -d "$name/.git" ]; then echo "SKIP $name"; continue; fi
  echo "== unshallow $name"
  if [ -f "$name/.git/shallow" ]; then
    git -C "$name" fetch -q --unshallow origin 2>&1 | tail -1 || \
    git -C "$name" fetch -q origin '+refs/heads/*:refs/remotes/origin/*' 2>&1 | tail -1
  else
    git -C "$name" fetch -q origin '+refs/heads/*:refs/remotes/origin/*' 2>&1 | tail -1
  fi
  echo "  objects: $(git -C "$name" rev-list --objects --all 2>/dev/null | wc -l)"
done
