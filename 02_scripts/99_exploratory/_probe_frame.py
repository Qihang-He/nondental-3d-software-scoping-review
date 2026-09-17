# -*- coding: utf-8 -*-
"""Why is the sampling frame 1,939 when 1,943 records were excluded at title/abstract?"""
import csv, io, os, sys, collections

sys.stdout.reconfigure(encoding='utf-8')
B = r'd:\Desktop\v8 for JD\03_数据\08_分析用'
with io.open(os.path.join(B, 'PRISMA_排除原因分类.csv'), encoding='utf-8-sig', newline='') as fh:
    rows = list(csv.DictReader(fh))
print('rows:', len(rows))
keys = [ (r.get('Key') or '').strip() for r in rows ]
empty = sum(1 for k in keys if not k)
c = collections.Counter(keys)
dupes = [k for k, v in c.items() if v > 1]
print('empty keys:', empty, '| duplicate keys:', len(dupes), dupes[:8])
print('reason distribution:')
for k, v in collections.Counter((r.get('原因') or '').strip() for r in rows).most_common(10):
    print(f'   {v:5d}  {k[:70]}')
print('unique keys:', len([k for k in keys if k]) - 0, '| distinct:', len(set(k for k in keys if k)))
