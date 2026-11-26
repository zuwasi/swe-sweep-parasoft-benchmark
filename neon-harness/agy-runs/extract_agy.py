#!/usr/bin/env python3
"""Extract Antigravity BUG-HUNT-REPORT.md findings into the Amp-arm findings schema."""
import json, re, sys, io

def parse_location(loc, files):
    # normalize dashes
    loc = loc.replace('\u2013','-').replace('\u2014','-').replace('`',' ')
    # split on separators that start new items
    parts = re.split(r'\band\b|;|\n', loc)
    cur = None
    for chunk in parts:
        chunk = chunk.strip()
        if not chunk: continue
        # find path:range patterns
        for m in re.finditer(r'([\w][\w./+\-]*?\.(?:c|h|cc|cpp|hpp|py|S))\s*:\s*(\d+)\s*(?:-\s*(\d+))?', chunk):
            path, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
            files.append([path, min(a,b), max(a,b)]); cur = path
        # bare ranges following a known path:  5383-5386  or  638-669
        if not re.search(r'\.(?:c|h|cc|cpp|hpp|py|S)\s*:', chunk) and cur:
            for m in re.finditer(r'(?<![\w:])(\d{1,5})\s*-\s*(\d{1,5})(?![\w-])', chunk):
                a, b = int(m.group(1)), int(m.group(2))
                files.append([cur, min(a,b), max(a,b)])
        elif cur and not re.finditer(r'([\w][\w./+\-]*?\.(?:c|h|cc|cpp|hpp|py|S))\s*:', chunk):
            for m in re.finditer(r'(?<![\w:])(\d{1,5})\s*-\s*(\d{1,5})(?![\w-])', chunk):
                a, b = int(m.group(1)), int(m.group(2))
                files.append([cur, min(a,b), max(a,b)])

def extract(report_path):
    text = io.open(report_path, encoding='utf-8').read()
    sections = re.split(r'\n(?=### )', text)
    out = []
    for sec in sections[1:]:
        head = sec.split('\n',1)[0]
        m = re.match(r'###\s+((?:BUG|MP)-\d+)\s*[:.]\s*(.*)', head)
        if not m: continue
        fid, title = m.group(1), m.group(2).strip()
        # trim title at trailing colon-dash artifacts
        sev, status = 'Medium', 'SUSPECTED'
        ms = re.search(r'\*\*Severity:?\*\*[:\s]*([A-Za-z]+)', sec)
        if ms: sev = ms.group(1).capitalize()
        ms = re.search(r'\*\*Status:?\*\*[:\s]*([A-Z]+)', sec)
        if ms: status = ms.group(1)
        files = []
        for lm in re.finditer(r'\*\*Location\*\*[:\s]*(.*)|\*\*Location\*\* :(.*)', sec):
            line = lm.group(1) or lm.group(2)
            parse_location(line, files)
        if not files:
            # fallback: any path:line patterns in the whole section
            parse_location(sec[:2000], files)
        # dedupe
        seen, ded = set(), []
        for f in files:
            k = tuple(f)
            if k not in seen: seen.add(k); ded.append(f)
        out.append({'id': fid, 'sev': sev, 'title': re.sub(r'\s+', ' ', title)[:180],
                    'status': status, 'files': ded})
    return out

if __name__ == '__main__':
    repo, report = sys.argv[1], sys.argv[2]
    fs = extract(report)
    json.dump(fs, io.open(f'/mnt/c/Projects/swe-sweep-parasoft-benchmark/neon-harness/agy-runs/{repo}/findings.json','w',encoding='utf-8'), indent=1)
    nof = [f['id'] for f in fs if not f['files']]
    print(repo, len(fs), 'findings;', 'no-location:', nof if nof else 'none')
