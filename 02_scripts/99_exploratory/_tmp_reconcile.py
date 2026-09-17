# -*- coding: utf-8 -*-
"""Reconcile the software-family counts and the full-text availability counts."""
import os
from collections import Counter
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
ANA = os.path.join('03_数据', '08_分析用')
OUT = os.path.join('04_代码', '07_文档', '_tmp_reconcile.txt')
L = []

g = pd.read_csv(os.path.join('03_数据', '09_软件表', '软件类别与来源表_backup_pre_scope.csv'),
                low_memory=False)
g.columns = ['original_name', 'canonical_name', 'category', 'development_domain',
             'developer', 'source_url', 'url_status', 'n_studies']
cat = dict(zip(g['canonical_name'], g['category']))
FAMILY = ['MIP', 'RE', 'SIM', 'GEN3D', 'CAD', 'AM', 'SCI', 'DICOM', 'PHOTO', 'RT']


def parse(v):
    try:
        return list(eval(v)) if isinstance(v, str) else list(v or [])
    except Exception:
        return []


def famcounts(path, label):
    d = pd.read_csv(path, low_memory=False)
    uniq, assign = Counter(), Counter()
    for v in d['_soft2']:
        s = set(parse(v))
        fs = set()
        for x in s:
            c = cat.get(x)
            if c in FAMILY:
                fs.add(c)
                assign[c] += 1
        for f in fs:
            uniq[f] += 1
    L.append('=== %s   N=%d' % (label, len(d)))
    for f in FAMILY:
        if uniq[f] or assign[f]:
            L.append('   %-7s unique-studies=%-5d assignments=%d' % (f, uniq[f], assign[f]))
    L.append('')


famcounts(os.path.join(ANA, '分析数据集_final_v5_backup_pre_scope.csv'), 'v5 (pre-scope, 861)')
famcounts(os.path.join(ANA, '分析数据集_final_v6.csv'), 'v6 (853)')

# ---- full-text availability audit
ap = os.path.join('人工核验包', '无全文记录_摘要证据审计.csv')
L.append('=== %s' % ap)
if os.path.exists(ap):
    a = pd.read_csv(ap, low_memory=False)
    L.append('   rows=%d cols=%s' % (len(a), list(a.columns)))
    for c in a.columns:
        if a[c].dtype == object and a[c].nunique() < 8:
            L.append('   %s : %s' % (c, a[c].value_counts().to_dict()))
    keycol = None
    for c in a.columns:
        if c.lower() in ('key', 'id', '序号'):
            keycol = c
    if keycol:
        d6 = pd.read_csv(os.path.join(ANA, '分析数据集_final_v6.csv'), low_memory=False)
        d5 = pd.read_csv(os.path.join(ANA, '分析数据集_final_v5_backup_pre_scope.csv'),
                         low_memory=False)
        s6 = set(d6[keycol].astype(str))
        s5 = set(d5[keycol].astype(str))
        aud = set(a[keycol].astype(str))
        L.append('   audited keys=%d ; still present in v6=%d ; removed by scope=%d'
                 % (len(aud), len(aud & s6), len(aud - s6)))
        L.append('   keys in audit but not in v5=%d' % len(aud - s5))
else:
    L.append('   NOT FOUND')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
