# -*- coding: utf-8 -*-
"""Check remaining residual items: TRI/3D-BON, PreForm, and any package without a verified source."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OUT = os.path.join('04_代码', '07_文档', '_tmp_residual.txt')
L = []

g = pd.read_csv(os.path.join('03_数据', '09_软件表', '软件类别与来源表.csv'), low_memory=False)
g.columns = ['original_name', 'canonical_name', 'category', 'development_domain',
             'developer', 'source_url', 'url_status', 'n_studies']

d = pd.read_csv(os.path.join('03_数据', '08_分析用', '分析数据集_final_v5.csv'), low_memory=False)

L.append('=== ENTRIES WITH n_studies == 0 (listed but unused) ===')
for _, r in g[g['n_studies'] == 0].iterrows():
    L.append('   %-24s cat=%-5s n=0  %s' % (r['canonical_name'], r['category'], r['development_domain']))

L.append('')
L.append('=== ENTRIES WITHOUT A VERIFIED SOURCE URL ===')
bad = g[g['source_url'].isna() | (g['source_url'].astype(str).str.startswith('ERR'))]
for _, r in bad.iterrows():
    L.append('   %-24s cat=%-5s n=%-4s dom=%-46s dev=%s url=%s' % (
        r['canonical_name'], r['category'], r['n_studies'],
        str(r['development_domain'])[:46], str(r['developer'])[:18], str(r['source_url'])[:50]))
L.append('   --> %d of %d entries lack a verified source URL' % (len(bad), len(g)))

L.append('')
L.append('=== STUDIES USING SELECTED PACKAGES ===')
for pkg in ['TRI/3D-BON', 'PreForm', 'Geomagic (suite)', 'Simpleware', 'Simpleware ScanIP',
            'Cliniface', 'Artisynth', 'Brainlab CMF', 'Midas', 'CreatWare', 'Scalismo Lab',
            'Viewbox', 'R2 Gate']:
    rows = []
    for _, r in d.iterrows():
        v = r['_soft2']
        try:
            s = set(eval(v)) if isinstance(v, str) else set(v or [])
        except Exception:
            s = set()
        if pkg in s:
            rows.append('      %-10s | %-34s | %s' % (r['Key'], str(r['Software Used (fixed)'])[:34],
                                                      str(r['Title'])[:80]))
    L.append('   [%s] %d study(ies)' % (pkg, len(rows)))
    L.extend(rows)

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
