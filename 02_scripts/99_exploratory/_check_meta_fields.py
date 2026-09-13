# -*- coding: utf-8 -*-
"""_check_meta_fields.py —— 检查新增记录可用的元数据来源"""
import os
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
c = pd.read_csv(os.path.join(ROOT, '03_数据', '02_清洗后', '筛选语料_唯一记录_2556.csv'),
                nrows=3, low_memory=False)
print('语料列（关键）:',
      [x for x in c.columns if x in ('Country', 'Date', 'Publication Year',
                                     'Publication Title', 'Item Type', 'DOI', 'Key',
                                     'Journal Abbreviation', 'Author', 'Language')])
d = pd.read_csv(os.path.join(ROOT, '03_数据', '08_分析用', '分析数据集_final_v3.csv'),
                low_memory=False)
print('\nv3 列:', list(d.columns))
cols = ['序号', 'Key', 'Region', 'Date', 'Year', 'Dental Specialty',
        'Application Scenario', 'Software Used (fixed)', 'study_type', 'Half2']
print(d[cols].head(3).T.to_string())
print('\nRegion 缺失:', int(d['Region'].isna().sum()))
print('Region 取值样例:', d['Region'].dropna().unique()[:10])
