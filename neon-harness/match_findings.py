#!/usr/bin/env python3
"""Match agent findings (file, line ranges) to benchmark bugs via regions."""
import json, sys
from pathlib import Path

BASE = Path("/mnt/c/Projects/swe-sweep-parasoft-benchmark/neon-harness")

def main(repo, findings_file):
    regions = json.load(open(BASE / "regions" / f"{repo}.json"))
    finds = json.load(open(findings_file))
    # normalize agent file paths (strip leading dirs until they end with repo-known suffixes)
    bug_index = []  # (bug_id, file, region_set, strict_set)
    for b in regions["bugs"]:
        for f in b["files"]:
            bug_index.append((b["bug_id"], f, set(b["region"]), set(b["strict"])))
    res = []
    for f_ in finds:
        hits = {}
        for (file, lo, hi) in f_["files"]:
            lines = set(range(lo, hi + 1))
            for (bid, bf, reg, strict) in bug_index:
                # match file by basename suffix
                if not (file.endswith(bf) or bf.endswith(file) or file.split("/")[-1] == bf.split("/")[-1]):
                    continue
                r = lines & reg
                s = lines & strict
                if r or s:
                    e = hits.setdefault(bid, {"region": set(), "strict": set()})
                    e["region"] |= r
                    e["strict"] |= s
        if hits:
            res.append({"finding": f_["id"], "sev": f_["sev"], "title": f_["title"],
                        "bugs": {k: {"region": sorted(v["region"]), "strict": sorted(v["strict"])}
                                 for k, v in hits.items()}})
        else:
            res.append({"finding": f_["id"], "sev": f_["sev"], "title": f_["title"], "bugs": {}})
    json.dump(res, open(BASE / "reports" / f"{repo}_matches.json", "w"), indent=1)
    n_bug_region, n_bug_strict = {}, {}
    for r in res:
        for bid, v in r["bugs"].items():
            if v["region"]: n_bug_region.setdefault(bid, []).append(r["finding"])
            if v["strict"]: n_bug_strict.setdefault(bid, []).append(r["finding"])
    print(f"{repo}: {len(finds)} findings; region hits on {len(n_bug_region)} bugs; strict hits on {len(n_bug_strict)} bugs")
    for bid in sorted(n_bug_region):
        print(f"  {bid}: region via {n_bug_region[bid]}" + (f" STRICT via {n_bug_strict[bid]}" if bid in n_bug_strict else ""))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
