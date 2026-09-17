# -*- coding: utf-8 -*-
"""Probe evidence for borderline software (R2 Gate / CreatWare / Midas / Viewbox)."""
import os
import pandas as pd

pd.set_option('display.max_colwidth', 600)
pd.set_option('display.width', 260)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

TARGETS = ['CreatWare', 'Midas', 'R2 Gate', 'R2Gate', 'Viewbox']

CANDIDATES = [
    os.path.join('03_数据', '05_审计与核验', 'PDF软件核验_逐篇.csv'),
    os.path.join('03_数据', '08_分析用', '纳入集复核_确定性核查.csv'),
    os.path.join('03_数据', '08_分析用', 'final_pass', 'final_parsed.csv'),
    os.path.join('03_数据', '08_分析用', 'fulltext_pass', 'fulltext_parsed.csv'),
]

for rel in CANDIDATES:
    if not os.path.exists(rel):
        print('MISSING:', rel)
        continue
    try:
        d = pd.read_csv(rel, low_memory=False)
    except Exception as e:
        print('ERR', rel, e)
        continue
    cols = [c for c in d.columns if d[c].dtype == object]
    if not cols:
        continue
    mask = pd.Series(False, index=d.index)
    for c in cols:
        mask |= d[c].astype(str).str.contains('|'.join(TARGETS), na=False, regex=True)
    sub = d[mask]
    print('==== %s  (%d rows matched)' % (rel, len(sub)))
    if len(sub) == 0:
        continue
    for _, r in sub.iterrows():
        print('----')
        for c in d.columns:
            v = str(r[c])
            if v in ('', 'nan'):
                continue
            if len(v) > 600:
                v = v[:600] + ' ...[trunc]'
            print('   %s: %s' % (c, v))
    print()
