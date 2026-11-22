import json, subprocess, sys, os
repo = sys.argv[1]
only = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
os.chdir(f'/mnt/c/Users/danie/swesweep-parasoft-benchmark/repos/{repo}')
bugs = json.load(open(f'/mnt/c/Users/danie/swesweep-parasoft-benchmark/analysis/{repo}_bugs.json'))
needmap = {}
for b in bugs['bugs']:
    if only and b['bug_id'] not in only: continue
    need = {}
    for h in b['hunks']:
        if h['blob'] and set(h['blob']) != {'0'}:
            need.setdefault(h['file'], h['blob'])
    needmap[b['bug_id']] = need
allfiles = sorted({f for need in needmap.values() for f in need})
filelog = {}
for f in allfiles:
    log = subprocess.check_output(['git','log','--all','--format=%H %P','--', f], text=True)
    cl = []
    for l in log.splitlines():
        if not l.strip(): continue
        parts = l.split()
        cl.append((parts[0], parts[1] if len(parts) > 1 else None))
    filelog[f] = cl
# resolve parent blobs per (parent, file) that matter, positionally
specs = []; metas = []
for bid, need in needmap.items():
    if not need: continue
    common = None
    for f in need:
        s = {p for _, p in filelog.get(f, []) if p}
        common = s if common is None else (common & s)
    for p in sorted(common or set()):
        for f in need:
            specs.append(f'{p}:{f}'); metas.append((p, f))
out = subprocess.run(['git','cat-file','--batch-check'], input='\n'.join(specs) + '\n', capture_output=True, text=True)
lines = out.stdout.splitlines()
blob = {}
for (p, f), line in zip(metas, lines):
    t = line.split()
    if len(t) >= 2 and t[1] == 'blob':
        blob[(p, f)] = t[0]
for bid, need in needmap.items():
    if not need:
        print(bid, 'NO-BLOBS'); continue
    common = None
    for f in need:
        s = {p for _, p in filelog.get(f, []) if p}
        common = s if common is None else (common & s)
    hits = []
    for p in sorted(common or set()):
        if all(blob.get((p, f), '').startswith(bl) for f, bl in need.items()):
            for sha, par in filelog[sorted(need)[0]]:
                if par == p: hits.append(sha)
    desc = []
    for h in sorted(set(hits))[:6]:
        msg = subprocess.check_output(['git','log','-1','--format=%ad %s','--date=short',h], text=True).strip()
        desc.append(f'{h[:11]} {msg}')
    print(bid, '|', ' ; '.join(desc) if desc else 'NO-HIT')
