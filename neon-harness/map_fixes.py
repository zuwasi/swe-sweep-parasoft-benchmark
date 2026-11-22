import os, subprocess, sys
from collections import defaultdict
base='/mnt/c/Users/danie/swesweep-parasoft-benchmark'
repo=sys.argv[1]
pre=os.path.join(base,'analysis',repo,'pre')
rd=os.path.join(base,'repos',repo)
blobs={}
for d in sorted(os.listdir(pre)):
    p=os.path.join(pre,d)
    if not os.path.isdir(p): continue
    files=[]
    for root,_,fs in os.walk(p):
        for f in fs:
            files.append(os.path.relpath(os.path.join(root,f),p).replace('\\','/'))
    blobs[d]=files
fb=defaultdict(set)
for b,fs in blobs.items():
    for f in fs: fb[f].add(b)
# collect candidate commits per file with their first parent, in one rev-list per file
cand=defaultdict(set)   # file -> set(commit)
for f in fb:
    r=subprocess.run(['git','-C',rd,'rev-list','--all','--parents','--',f],capture_output=True,text=True)
    for line in r.stdout.splitlines():
        parts=line.split()
        if len(parts)>=2: cand[f].add(parts[0])
# batch-resolve parent blobs
pairs=[]
for f,cs in cand.items():
    for c in cs: pairs.append((f,c))
# query in chunks via cat-file --batch-check
out=defaultdict(set)
proc=subprocess.Popen(['git','-C',rd,'cat-file','--batch-check=%(objectname)'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
inputs=[]; meta=[]
for f,c in pairs: inputs.append(f'{c}:{f}')
allin='\n'.join(inputs)+'\n'
res=proc.communicate(allin)[0].splitlines()
for (f,c),line in zip(pairs,res):
    b=line.strip()[:10]
    if not b or b=='<none>' or len(b)<9: continue
    for blob in fb[f]:
        if b.startswith(blob) or blob.startswith(b):
            out[blob].add(c)
# fetch subjects in one batch
def subjects(cs):
    if not cs: return []
    r=subprocess.run(['git','-C',rd,'log','--no-walk=unsorted','--format=%h %s']+list(cs),capture_output=True,text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]
for b in sorted(blobs):
    print(b, '->', subjects(out.get(b,[])) or 'NO-MATCH', '|', blobs[b])
