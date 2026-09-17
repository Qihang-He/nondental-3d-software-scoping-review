# -*- coding: utf-8 -*-
"""_check_country.py —— 检查语料 Country 字段能否映射为 ISO3"""
import os
from collections import Counter
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
u = pd.read_csv(os.path.join(ROOT, '03_数据', '02_清洗后', '筛选语料_唯一记录_2556.csv'),
                low_memory=False)
print('Country 非空:', int(u['Country'].notna().sum()), '/', len(u))
print('Country 取值（Top 25）:')
for k, v in Counter(u['Country'].dropna().astype(str)).most_common(25):
    print('   %-40s %d' % (k[:38], v))

# 已有 566 的 Region 是否可由 Country 推出
d = pd.read_csv(os.path.join(ROOT, '03_数据', '08_分析用', '分析数据集_final_v3.csv'),
                low_memory=False)
m = dict(zip(u['Key'].astype(str), u['Country']))
d['_country'] = d['Key'].astype(str).map(m)
print('\n已有 566 中有 Country 的:', int(d['_country'].notna().sum()))
tab = d.groupby(['_country', 'Region']).size().sort_values(ascending=False)
print(tab.head(25).to_string())
