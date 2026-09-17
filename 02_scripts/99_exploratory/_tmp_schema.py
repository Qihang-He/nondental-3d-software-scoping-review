# -*- coding: utf-8 -*-
"""Inspect the pre-revision glossary and the v5 canonical-name list schemas."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
SWD = os.path.join('03_数据', '09_软件表')
ANA = os.path.join('03_数据', '08_分析用')
OUT = os.path.join('04_代码', '07_文档', '_tmp_schema.txt')
L = []
for p in [os.path.join(SWD, '软件类别与来源表_backup_pre_scope.csv'),
          os.path.join(SWD, '软件类别与来源表.csv'),
          os.path.join(ANA, '软件规范名清单_v5.csv'),
          os.path.join(ANA, '软件规范名清单_v6.csv')]:
    if not os.path.exists(p):
        L.append('MISSING %s' % p)
        continue
    d = pd.read_csv(p, low_memory=False)
    L.append('=== %s' % p)
    L.append('   shape=%s' % (d.shape,))
    L.append('   cols=%s' % list(d.columns))
    L.append(d.head(4).to_string())
    L.append('')
open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
