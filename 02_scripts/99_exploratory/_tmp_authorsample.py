# -*- coding: utf-8 -*-
"""Check whether the removed records overlap the author-verification samples."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
ANA = os.path.join('03_数据', '08_分析用')
OUT = os.path.join('04_代码', '07_文档', '_tmp_authorsample.txt')

log = pd.read_csv(os.path.join(ANA, '软件口径复核_修订记录.csv'), low_memory=False)
removed = set(log.loc[log['action'] == 'RECORD REMOVED', 'record_key'].astype(str))
L = ['removed records: %d' % len(removed), '']

for rel in [os.path.join('02_图表附件', 'R2_补充材料', 'Supplementary_File_4_Author_verification.xlsx'),
            os.path.join('03_数据', '08_分析用', '作者核验_纳入抽样100_已完成.csv'),
            os.path.join('03_数据', '08_分析用', '作者核验_排除抽样50_已完成.csv')]:
    if not os.path.exists(rel):
        L.append('MISSING %s' % rel)
        continue
    d = pd.read_excel(rel) if rel.endswith('.xlsx') else pd.read_csv(rel, low_memory=False)
    L.append('=== %s  shape=%s' % (rel, d.shape))
    keyc = None
    for c in d.columns:
        if str(c).strip().lower() in ('key', 'id', 'record_id'):
            keyc = c
            break
    if keyc is None:
        L.append('   no key column; cols=%s' % list(d.columns))
        continue
    keys = set(d[keyc].astype(str))
    L.append('   key column=%r  n=%d' % (keyc, len(keys)))
    hit = keys & removed
    L.append('   overlap with removed records: %d  %s' % (len(hit), sorted(hit)))
    L.append('')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
