# -*- coding: utf-8 -*-
"""Derive the figure/legend numbers that are not in the statistics core."""
import os
from collections import Counter
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
ANA = os.path.join('03_数据', '08_分析用')
OUT = os.path.join('04_代码', '07_文档', '_tmp_extra_numbers.txt')
L = []

d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v6.csv'), low_memory=False)
g = pd.read_csv(os.path.join('03_数据', '09_软件表', '软件类别与来源表.csv'), low_memory=False)
g.columns = ['original_name', 'canonical_name', 'category', 'development_domain',
             'developer', 'source_url', 'url_status', 'n_studies']
cat = dict(zip(g['canonical_name'], g['category']))


def parse(v):
    try:
        return list(eval(v)) if isinstance(v, str) else list(v or [])
    except Exception:
        return []


fam = Counter()
for v in d['_soft2']:
    s = set(parse(v))
    for f in set(cat.get(x, '???') for x in s):
        fam[f] += 1

L.append('=== software family : unique studies (n = %d) ===' % len(d))
tot = 0
for k, v in fam.most_common():
    L.append('   %-8s %d' % (k, v))
    tot += v
L.append('   (sum = %d, multiplicative because a study may use several families)' % tot)
L.append('')

# ---- full-text availability
cands = [c for c in d.columns if 'PDF' in c.upper() or 'fulltext' in c.lower()
         or 'Full' in c or '全文' in c]
L.append('=== candidate full-text columns: %s' % cands)
for c in cands:
    L.append('   %s : nulls=%d  uniques=%s' % (c, d[c].isna().sum(),
                                               d[c].dropna().unique()[:5]))

# try the audit table that records retrievable full texts
for rel in [os.path.join('03_数据', '05_审计与核验', 'PDF核验', 'PDF软件核验_逐篇.csv'),
            os.path.join('03_数据', '07_PDF与语料对照', 'PDF对照_逐篇.csv')]:
    if os.path.exists(rel):
        t = pd.read_csv(rel, low_memory=False)
        L.append('')
        L.append('=== %s : %d rows, cols=%s' % (rel, len(t), list(t.columns)))

# ---- gap / advantage denominators
rq = None
import json
rq = json.load(open(os.path.join(ANA, 'RQ3_频次汇总.json'), encoding='utf-8'))
L.append('')
L.append('=== RQ3 derived ===')
a_none = [x for x in rq['advantages'] if x['code'] == 'A9'][0]['n']
c_none = [x for x in rq['challenges'] if x['code'] == 'C9'][0]['n']
gp_none = [x for x in rq['gaps'] if x['code'] == 'G9'][0]['n']
N = rq['N_analysed']
L.append('   advantages with >=1 code : %d (%.1f%%)' % (N - a_none, (N - a_none) / N * 100))
L.append('   no advantage (A9)        : %d (%.1f%%)' % (a_none, a_none / N * 100))
L.append('   challenges with >=1 code : %d (%.1f%%)' % (N - c_none, (N - c_none) / N * 100))
L.append('   no challenge (C9)        : %d (%.1f%%)' % (c_none, c_none / N * 100))
L.append('   gaps with >=1 code       : %d (%.1f%%)' % (N - gp_none, (N - gp_none) / N * 100))
L.append('   no gap (G9)              : %d (%.1f%%)' % (gp_none, gp_none / N * 100))

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
