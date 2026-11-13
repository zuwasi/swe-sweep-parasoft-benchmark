#!/usr/bin/env python3
"""Recompute conditional detection rate with pass-3 boundary decisions applied.

Reads classification/final/all.jsonl (488 labels), overrides the SA/NONSA
boundary for cases present in classification/adjudication3/labels_v3/*.jsonl,
and joins with reports/*_result.json to compute:
  - SA-detectable count and share of 488
  - Parasoft catches inside and outside the SA set
  - conditional rate caught-SA / SA, all-bugs rate for reference
Also reports the same numbers restricted to high-confidence v3 decisions.
"""
import json, glob, re, sys
from collections import Counter

root = os_root = None
SA = {"MEMORY", "RESOURCE", "ERROR"}

final = {}
for l in open('classification/final/all.jsonl'):
    d = json.loads(l)
    final[d['bug_id']] = d

results = {}
for f in glob.glob('reports/*_result.json'):
    for b in json.load(open(f)).get('bugs', []):
        results[b['bug_id']] = b

v3 = {}
for f in glob.glob('classification/adjudication3/labels_v3/*.jsonl'):
    for l in open(f):
        d = json.loads(l)
        v3[d['bug_id']] = d

assert len(final) == 488, len(final)
assert len(v3) == int(sys.argv[1]) if len(sys.argv) > 1 else True, len(v3)

def effective(bid):
    d = dict(final[bid])
    if bid in v3:
        v = v3[bid]
        d['sa_class'] = 'MEMORY' if v['decision'] == 'SA' else 'LOGIC'
        d['confidence'] = v['confidence']
        d['reason'] = 'v3: ' + v['reason']
        d['v3'] = True
    return d

eff = {bid: effective(bid) for bid in final}
def stats(eff_map, only_ids=None):
    sa = caught_sa = caught_nonsa = 0
    for bid, d in eff_map.items():
        if only_ids is not None and bid not in only_ids:
            continue
        r = results.get(bid, {})
        caught = bool(r.get('found_region'))
        if d['sa_class'] in SA:
            sa += 1
            if caught: caught_sa += 1
        elif caught:
            caught_nonsa += 1
    return sa, caught_sa, caught_nonsa

flips = Counter()
for bid, v in v3.items():
    old = 'SA' if final[bid]['sa_class'] in SA else 'NONSA'
    if old != v['decision']:
        flips[(old, v['decision'])] += 1

sa, c_sa, c_non = stats(eff)
hids = {b for b, v in v3.items() if v['confidence'] == 'high'}
# For the high-confidence variant: only apply v3 where v3 is high-confidence,
# else keep the original final label.
eff_h = {bid: effective(bid) if (bid not in v3 or v3[bid]['confidence'] == 'high') else dict(final[bid]) for bid in final}
sa_h, c_sa_h, c_non_h = stats(eff_h)

total = len(final)
print(f"v3 decisions: {len(v3)}, flips: {dict(flips)} (total {sum(flips.values())})")
print(f"\nall-bugs rate: {sum(1 for b in results.values() if b.get('found_region'))}/{total}")
print(f"\nAdjudicated (all v3 applied):")
print(f"  SA-detectable: {sa}/{total} = {sa/total*100:.1f}%")
print(f"  caught in SA set: {c_sa}/{sa} = {c_sa/sa*100:.1f}%  (conditional rate)")
print(f"  caught outside SA set: {c_non}")
print(f"\nHigh-confidence v3 applied only:")
print(f"  SA-detectable: {sa_h}/{total} = {sa_h/total*100:.1f}%")
print(f"  caught in SA set: {c_sa_h}/{sa_h} = {c_sa_h/sa_h*100:.1f}%  (conditional rate)")
print(f"  caught outside SA set: {c_non_h}")
