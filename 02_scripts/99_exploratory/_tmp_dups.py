# -*- coding: utf-8 -*-
"""Diagnose duplicate rows in the software glossary backup."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OUT = os.path.join('04_代码', '07_文档', '_tmp_dups.txt')

g = pd.read_csv(os.path.join('03_数据', '09_软件表',
                             '软件类别与来源表_backup_pre_scope.csv'), low_memory=False)
L = ['columns: %s' % list(g.columns), '']
dup = g[g.duplicated('规范名称', keep=False)].sort_values('规范名称')
L.append('duplicated canonical names: %d rows' % len(dup))
for name, sub in dup.groupby('规范名称'):
    L.append('=== %s' % name)
    for i, (_, r) in enumerate(sub.iterrows()):
        L.append('   [%d] 原始名称=%r' % (i, r['原始名称']))
        L.append('        类别=%r 领域=%r' % (r['类别'], r['原始开发领域']))
        L.append('        开发商=%r URL=%r 状态=%r n=%r' % (
            r['开发商'], r['来源URL'], r['URL状态'], r['研究数']))
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
