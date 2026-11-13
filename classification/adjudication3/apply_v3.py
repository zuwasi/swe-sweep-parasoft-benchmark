#!/usr/bin/env python3
"""Apply pass-3 boundary decisions (labels_v3) to the 488 final labels.

Writes classification/adjudication3/effective_labels.jsonl (all 488 bugs, the
labels the published numbers use) and prints the recomputed totals. For the
five NONSA -> SA flips, the SA class follows the mechanism recorded in the
pass-3 reason (map below). Everything else keeps its final class.
"""
import json, glob, re, sys
from collections import Counter

SA = {"MEMORY", "RESOURCE", "ERROR"}

NEW_SA_CLASS = {
    'cvc5-aa2797db1fd7': 'MEMORY',   # missing null check
    'opencv-5cb9cd581ef5': 'MEMORY', # shadowed-index OOB write
    'opencv-6c432b0cd808': 'ERROR',  # missing guard the API contract requires
    'opencv-9147e633a50f': 'ERROR',  # missing empty-ROI guard
    'libexpat-f67d952cb3de': 'MEMORY', # pool-stored name UAF
}

final = {}
for line in open('classification/final/all.jsonl'):
    d = json.loads(line)
    final[d['bug_id']] = d

v3 = {}
for f in glob.glob('classification/adjudication3/labels_v3/*.jsonl'):
    for line in open(f):
        d = json.loads(line)
        v3[d['bug_id']] = d

results = {}
for f in glob.glob('reports/*_result.json'):
    for b in json.load(open(f)).get('bugs', []):
        results[b['bug_id']] = b

eff = {}
for bid, d in final.items():
    e = dict(d)
    if bid in v3:
        v = v3[bid]
        e['pass3'] = v['decision']
        e['pass3_confidence'] = v['confidence']
        e['pass3_reason'] = v['reason']
        if v['decision'] == 'SA':
            e['sa_class'] = d['sa_class'] if d['sa_class'] in SA else NEW_SA_CLASS[bid]
        else:
            e['sa_class'] = d['sa_class'] if d['sa_class'] not in SA else 'LOGIC'
        e['confidence'] = v['confidence']
        e['reason'] = 'pass3: ' + v['reason']
    eff[bid] = e

out = 'classification/adjudication3/effective_labels.jsonl'
with open(out, 'w') as fh:
    for bid in final:
        fh.write(json.dumps(eff[bid]) + '\n')

assert len(eff) == 488
class_counts = Counter(e['sa_class'] for e in eff.values())
sa = sum(1 for e in eff.values() if e['sa_class'] in SA)
reg = sum(1 for e in eff.values() if e['sa_class'] in SA and results[e['bug_id']].get('found_region'))
stri = sum(1 for e in eff.values() if e['sa_class'] in SA and results[e['bug_id']].get('found_strict'))
print(json.dumps(class_counts, indent=1))
print(f"SA={sa} region={reg} ({reg/sa*100:.1f}%) strict={stri} ({stri/sa*100:.1f}%)")

# per-repo for the JSON updates
per_repo = {}
repo_of = {}
for f in glob.glob('reports/*_result.json'):
    repo = re.match(r'reports/(.+)_result.json', f).group(1)
    for b in json.load(open(f)).get('bugs', []):
        repo_of[b['bug_id']] = repo
for bid, e in eff.items():
    r = repo_of[bid]
    p = per_repo.setdefault(r, {'class_counts': Counter(), 'sa': 0, 'reg': 0, 'stri': 0, 'all': 0})
    p['class_counts'][e['sa_class']] += 1
    res = results[bid]
    if e['sa_class'] in SA:
        p['sa'] += 1
        if res.get('found_region'): p['reg'] += 1
        if res.get('found_strict'): p['stri'] += 1
    if res.get('found_region'): p['all'] += 1
json.dump({r: {'class_counts': dict(p['class_counts']), 'sa': p['sa'], 'reg': p['reg'], 'stri': p['stri'], 'all': p['all'], 'bugs': sum(p['class_counts'].values())} for r, p in sorted(per_repo.items())}, open('/tmp/per_repo_eff.json', 'w'), indent=1)
print(open('/tmp/per_repo_eff.json').read())
