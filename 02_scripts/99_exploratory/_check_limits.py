# -*- coding: utf-8 -*-
"""Search the guide for any length limits, and measure the manuscript's word counts."""
import os
import re
import zipfile
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

# ---- 1) every string in the guide docx, including headers/footers/textboxes
src = os.path.join('01_投稿文件', 'JD guide for authors.docx')
with zipfile.ZipFile(src) as z:
    xml_parts = [n for n in z.namelist() if n.endswith('.xml')]
    blob = '\n'.join(z.read(n).decode('utf-8', 'ignore') for n in xml_parts)

text = re.sub(r'<[^>]+>', ' ', blob)
text = re.sub(r'\s+', ' ', text)
hits = []
for m in re.finditer(r'[^.]{0,220}(word|words|limit|limits|exceed|page limit|maximum|max\.)'
                     r'[^.]{0,220}\.', text, re.I):
    s = m.group(0).strip()
    if re.search(r'word|limit|exceed|maximum|max\.', s, re.I):
        hits.append(s)

print('=== guide: length-related sentences ===')
seen = set()
for h in hits:
    k = h[:60]
    if k in seen:
        continue
    seen.add(k)
    print(' -', h[:400])
print()

# ---- 2) manuscript word counts
p = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
md = open(p, encoding='utf-8').read()
lines = md.splitlines()

def words(s):
    s = re.sub(r'\[[\d,\u2013\-]+\]', ' ', s)      # strip citation brackets
    s = re.sub(r'[*#_`>|]', ' ', s)
    return len([w for w in s.split() if re.search(r'\w', w)])

total = words(md)
sections = {}
cur = 'PREFACE'
buf = []
order = []
for ln in lines:
    m = re.match(r'^#{1,3}\s+(.*)$', ln)
    if m:
        sections[cur] = sections.get(cur, '') + '\n'.join(buf)
        buf = []
        cur = m.group(1).strip()
        order.append(cur)
        continue
    buf.append(ln)
sections[cur] = sections.get(cur, '') + '\n'.join(buf)

print('=== manuscript word counts by section ===')
tot = 0
for k in ['PREFACE'] + order:
    if k not in sections:
        continue
    n = words(sections[k])
    tot += n
    print('  %-58s %5d' % (k[:58], n))
print('  %-58s %5d' % ('TOTAL (whole file)', total))
