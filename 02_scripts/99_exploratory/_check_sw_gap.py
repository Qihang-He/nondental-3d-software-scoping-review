# -*- coding: utf-8 -*-
"""_check_sw_gap.py —— 核对"85 种软件"与软件表 81 条的差异来源"""
import os
import ast
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
sw = pd.read_csv(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'))

used = set()
for v in d['_soft2'].fillna('[]'):
    try:
        for x in ast.literal_eval(v):
            used.add(str(x).strip())
    except Exception:
        pass
gl = set(sw['规范名称'].astype(str).str.strip())
print('纳入集使用的软件名: %d' % len(used))
print('软件表规范名: %d' % len(gl))
print('\n在纳入集中使用但软件表未收录（%d 个）：' % len(used - gl))
for x in sorted(used - gl):
    n = sum(1 for v in d['_soft2'] if x in str(v))
    print('   %-34s %d 篇' % (x, n))
print('\n软件表收录但纳入集未用（%d 个）：' % len(gl - used))
for x in sorted(gl - used):
    print('   ', x)
