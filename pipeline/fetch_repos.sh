#!/usr/bin/env bash
# Clone the 14 C/C++ SWE-sweep repositories at the exact pinned base refs used
# in the benchmark. Manifests in manifests/ carry the clone URL and base_ref.
#
# Usage: ./fetch_repos.sh [target-dir]
# Each repo is cloned full (not shallow) because per-bug pre-images are
# materialized from git blob hashes recorded in the manifests.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-$HERE/../repos}"
mkdir -p "$TARGET"
for mf in "$HERE"/../manifests/*_manifest.json; do
  repo=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['repo'])" "$mf")
  url=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['clone_url'])" "$mf")
  ref=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['base_ref'])" "$mf")
  dest="$TARGET/$repo"
  if [ ! -d "$dest/.git" ]; then
    echo "== cloning $repo from $url"
    git clone "$url" "$dest"
  fi
  echo "== checking out $repo at $ref"
  git -C "$dest" fetch origin --tags --force
  git -C "$dest" checkout "$ref" || git -C "$dest" checkout "tags/$ref"
done
echo "All repositories fetched at pinned refs."
