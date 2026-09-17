# -*- coding: utf-8 -*-
"""_sw_fix_check.py —— 对比 Software Used（原始）与 Software Used (fixed)（重编码后）"""
import os
import ast
from collections import Counter
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
sw = pd.read_csv(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'))
GL = set(sw['规范名称'].astype(str).str.strip())


def parse(v):
    return [x.strip() for x in str(v).split(';') if x.strip() and x.strip().lower() != 'nan']


print('Software Used (fixed) 缺失:', int(d['Software Used (fixed)'].isna().sum()))

raw = Counter()
for v in d['Software Used']:
    for x in parse(v):
        raw[x] += 1
fix = Counter()
for v in d['Software Used (fixed)']:
    for x in parse(v):
        fix[x] += 1

print('\n原始字段不同取值: %d ；重编码后: %d' % (len(raw), len(fix)))
print('重编码后不在软件表中的名字:', sorted(set(fix) - GL))
print('软件表有但重编码后未使用:', sorted(GL - set(fix)))

print('\n重编码后 Top 20：')
for k, n in fix.most_common(20):
    print('   %-30s %d' % (k, n))

print('\n原始字段中已被重编码消除的变体：')
for k, n in raw.most_common(200):
    if k not in fix and k not in GL:
        print('   %-30s %d' % (k, n))

print('\n软件赋值总数（原始）=%d ；重编码后=%d' % (sum(raw.values()), sum(fix.values())))
print('使用 >1 软件的研究（原始）=%d ；重编码后=%d'
      % (sum(1 for v in d['Software Used'] if len(parse(v)) > 1),
         sum(1 for v in d['Software Used (fixed)'] if len(parse(v)) > 1)))
