# -*- coding: utf-8 -*-
"""Inspect software-related column formats before revision."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OUT = os.path.join('04_代码', '07_文档', '_tmp_colfmt.txt')
d = pd.read_csv(os.path.join('03_数据', '08_分析用', '分析数据集_final_v5.csv'), low_memory=False)

L = []
for c in ['Software Used', '_soft', '_soft2', 'Software Used (fixed)']:
    L.append('=== %s  dtype=%s  nulls=%d' % (c, d[c].dtype, d[c].isna().sum()))
    L.append('    samples:')
    for v in d[c].dropna().head(3):
        L.append('      %r' % (v,))
    L.append('')

L.append('=== shared/unused software columns check ===')
for c in ['_soft', '_soft2']:
    n0 = sum(1 for v in d[c].dropna() if 'R2 Gate' in str(v))
    L.append('   %s contains "R2 Gate": %d' % (c, n0))

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
