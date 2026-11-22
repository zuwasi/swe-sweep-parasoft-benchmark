import json, sys
B='/mnt/c/Users/danie/swesweep-parasoft-benchmark/analysis/tarantool_bugs.json'
PRE='/mnt/c/Users/danie/swesweep-parasoft-benchmark/analysis/tarantool/pre'
d=json.load(open(B))
bids=sys.argv[1:]
for b in d['bugs']:
    bid=b['bug_id']
    if bids and not any(x in bid for x in bids): continue
    print('=====', bid)
    for h in b['hunks']:
        # find pre-image dir with prefix match
        import os
        path=None
        for dd in os.listdir(PRE):
            if h['blob'] and h['blob'].startswith(dd[:2]) and dd[:4]==h['blob'][:4]:
                pass
        # simpler: exact dir matching prefix
        for dd in os.listdir(PRE):
            if h['blob'].startswith(dd) or dd.startswith(h['blob']):
                p=os.path.join(PRE,dd,h['file'])
                if os.path.exists(p): path=p; break
        if not path:
            print('  ',h['file'],'PRE MISSING',h['blob']); continue
        lines=open(path,encoding='utf-8',errors='replace').read().splitlines()
        st=h['old_start']-1
        print('  ---',h['file'],'@',h['old_start'],'cnt',h['old_count'],'removed idx',[i for i in h['removed']] if h['removed'] else '[]')
        for i in range(st, st+h['old_count']):
            mark='-' if (i-st+1) in (h['removed'] or []) else ' '
            print('   ',mark, i+1, lines[i] if i<len(lines) else '<<EOF>>')
