# -*- coding: utf-8 -*-
"""_sw_inspect.py —— 直接查看 _soft / _soft2 / Software Used / Software Used (fixed) 的实际取值"""
import os
import ast
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)

print('列:', [c for c in d.columns if 'oft' in c])
print()
for i in range(0, 8):
    r = d.iloc[i]
    print('--- 行 %d' % i)
    print('  Software Used          :', r['Software Used'])
    print('  Software Used (fixed)  :', r['Software Used (fixed)'])
    print('  _soft                  :', r['_soft'])
    print('  _soft2                 :', r['_soft2'])

# _soft2 是否为列表字符串
print()
print('_soft2 样例类型:', type(d['_soft2'].iloc[0]))
bad = 0
for v in d['_soft2'].head(50):
    try:
        ast.literal_eval(v)
    except Exception:
        bad += 1
print('前50条中无法解析的:', bad)
