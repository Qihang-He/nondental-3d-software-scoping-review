# -*- coding: utf-8 -*-
"""Audit ALL software packages against the review's nondental-3D-software definition.

Definition (manuscript, Introduction / 2.4):
  (1) ORIGIN  : primary development purpose outside dental applications
  (2) NATURE  : a 3D software package (general-purpose 3D modelling, engineering
                simulation, medical image processing, reverse engineering / metrology,
                real-time 3D engine, scientific 3D visualisation)
  (3) NAMED   : a specific third-party named package performing a stated role;
                general references to "software" or to self-developed algorithms
                without a named package are NOT sufficient.

Output: an audit table written to UTF-8 text (console mojibake-safe).
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

GLOSS = os.path.join('03_数据', '09_软件表', '软件类别与来源表.csv')
DATA = os.path.join('03_数据', '08_分析用', '分析数据集_final_v5.csv')
OUT = os.path.join('04_代码', '07_文档', '_tmp_software_audit.txt')

g = pd.read_csv(GLOSS, low_memory=False)
g.columns = ['original_name', 'canonical_name', 'category', 'development_domain',
             'developer', 'source_url', 'url_status', 'n_studies']

d = pd.read_csv(DATA, low_memory=False)

# per-study assignment counts straight from the locked dataset (authoritative)
from collections import Counter
cnt = Counter()
for v in d['_soft2'].dropna():
    try:
        s = eval(v) if isinstance(v, str) else v
    except Exception:
        continue
    for x in set(s):
        cnt[x] += 1

g['n_from_dataset'] = g['canonical_name'].map(lambda x: cnt.get(x, 0))

# duplicates by canonical name
dup = g[g.duplicated('canonical_name', keep=False)].sort_values('canonical_name')

lines = []
lines.append('TOTAL ROWS: %d   UNIQUE CANONICAL NAMES: %d' % (len(g), g['canonical_name'].nunique()))
lines.append('TOTAL ASSIGNMENTS (dataset): %d' % sum(cnt.values()))
lines.append('')
lines.append('=== DUPLICATED CANONICAL NAMES ===')
for _, r in dup.iterrows():
    lines.append('  %-28s cat=%-4s domain=%s' % (r['canonical_name'], r['category'],
                                                 r['development_domain']))
lines.append('')
lines.append('=== ALL PACKAGES (sorted by n_studies desc) ===')
lines.append('%-30s %-5s %-6s %-6s %s' % ('CANONICAL', 'CAT', 'N_TAB', 'N_DATA', 'DEVELOPMENT DOMAIN'))
for _, r in g.sort_values(['category', 'n_studies'], ascending=[True, False]).iterrows():
    flag = '' if r['n_studies'] == r['n_from_dataset'] else '   <-- MISMATCH'
    lines.append('%-30s %-5s %-6s %-6s %s%s' % (
        str(r['canonical_name'])[:30], str(r['category']), r['n_studies'],
        r['n_from_dataset'], str(r['development_domain'])[:70], flag))

lines.append('')
lines.append('=== BY CATEGORY ===')
for cat, sub in g.groupby('category'):
    names = sorted(set(sub['canonical_name']))
    lines.append('')
    lines.append('[%s]  %d packages, %d assignments' % (cat, len(names), sub['n_studies'].sum()))
    for _, r in sub.sort_values('n_studies', ascending=False).iterrows():
        lines.append('   %-30s n=%-4s %s' % (str(r['canonical_name'])[:30], r['n_studies'],
                                             str(r['development_domain'])[:70]))

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('written:', OUT)
print('rows=%d unique=%d assignments=%d' % (len(g), g['canonical_name'].nunique(), sum(cnt.values())))
