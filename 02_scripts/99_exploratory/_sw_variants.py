# -*- coding: utf-8 -*-
"""_sw_variants.py —— 查看软件字段的原始取值与变体分布"""
import os
import ast
from collections import Counter
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
sw = pd.read_csv(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'))

print('=== Software Used (fixed) 原始串（前 20 个不同取值）===')
for v, n in Counter(d['Software Used (fixed)'].astype(str)).most_common(20):
    print('  %-70s %d' % (v[:68], n))

c = Counter()
for v in d['_soft2'].fillna('[]'):
    try:
        for x in ast.literal_eval(v):
            c[str(x).strip()] += 1
    except Exception:
        pass
print('\n=== _soft2 逐名计数（Top 30）===')
for k, n in c.most_common(30):
    ing = '✓' if k in set(sw['规范名称'].astype(str)) else '×'
    print('  %s %-34s %d' % (ing, k, n))

print('\n=== 软件表全部 81 条 ===')
print(sw[['规范名称', '类别', '研究数']].to_string())
