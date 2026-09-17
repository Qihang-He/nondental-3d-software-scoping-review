# -*- coding: utf-8 -*-
"""Look for the provenance of the 12 / 42 / 54 / 613 numbers and the T/A-excluded count."""
import csv, io, os, sys, glob, collections

sys.stdout.reconfigure(encoding='utf-8')
B = r'd:\Desktop\v8 for JD\03_数据'

targets = {12, 42, 54, 613, 566, 866, 870, 1939, 1943, 931, 775, 1168}
hits = collections.defaultdict(list)
for f in glob.glob(os.path.join(B, '**', '*.csv'), recursive=True):
    try:
        with io.open(f, encoding='utf-8-sig', newline='') as fh:
            n = sum(1 for _ in csv.reader(fh)) - 1
    except Exception:
        continue
    if n in targets:
        hits[n].append(os.path.relpath(f, B))
for k in sorted(hits):
    print(f'{k:6d} rows ->')
    for p in hits[k][:6]:
        print('        ', p)

print('\n--- distribution of 原AI理由 in PRISMA_未进入全文评估_1927.csv ---')
f = os.path.join(B, '08_分析用', 'PRISMA_未进入全文评估_1927.csv')
with io.open(f, encoding='utf-8-sig', newline='') as fh:
    rows = list(csv.DictReader(fh))
c = collections.Counter((r.get('原AI理由') or '').strip()[:60] for r in rows)
for k, v in c.most_common(15):
    print(f'   {v:5d}  {k}')
