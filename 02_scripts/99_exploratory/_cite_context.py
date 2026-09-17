# -*- coding: utf-8 -*-
"""Print every in-text citation with its surrounding sentence so the fit can be reviewed."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
P = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
md = open(P, encoding='utf-8').read()
body = md[md.index('## Introduction'):md.index('## References')]
flat = re.sub(r'\s+', ' ', body)

refs = {}
for line in md[md.index('## References'):].splitlines():
    m = re.match(r'^\[(\d+)\]\s*(.*)$', line)
    if m:
        refs[int(m.group(1))] = m.group(2).strip()


def shorten(r):
    r = re.sub(r'https?://\S+', '', r)
    parts = r.split('. ')
    return ' | '.join(p for p in parts[:3])[:150]


# split into sentences, keep the citation with the sentence that carries it
sents = re.split(r'(?<=[.;])\s+', flat)
print('in-text citations with context')
print('=' * 100)
for s in sents:
    for m in re.finditer(r'\[(\d+(?:\s*,\s*\d+)*|\d+\s*[–-]\s*\d+)\]', s):
        nums = []
        for part in re.split(r'\s*,\s*', m.group(1)):
            part = part.strip()
            if re.fullmatch(r'\d+', part):
                nums.append(int(part))
            elif re.fullmatch(r'\d+\s*[–-]\s*\d+', part):
                a, b = re.split(r'\s*[–-]\s*', part)
                nums.extend(range(int(a), int(b) + 1))
        print()
        print('CITED %s' % m.group(0))
        for n in nums:
            print('    [%d] %s' % (n, shorten(refs.get(n, 'MISSING'))))
        ctx = s.replace(m.group(0), m.group(0))
        print('    CONTEXT: %s' % ctx[:300])
