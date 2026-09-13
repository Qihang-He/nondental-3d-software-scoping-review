# -*- coding: utf-8 -*-
"""_check_sw_rule.py —— 检验纳入集软件口径的一致性（是否只含具名第三方软件包）"""
import os
import re
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
sw = pd.read_csv(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'))

print('纳入集 N =', len(d))
print('软件列为空的研究数:', int(d['Software Used (fixed)'].isna().sum()))
print('软件包总数:', sw['规范名称'].nunique())

FRAME = re.compile(r'nnU|PyTorch|TensorFlow|Keras|scikit|OpenCV|custom|self-|in-?house|'
                   r'proprietary|algorithm|MATLAB|Python|Unity|Unreal|COMSOL|HyperMesh|'
                   r'SpaceClaim|NX|CATIA|Inventor|FreeCAD', re.I)
hits = []
for _, r in sw.iterrows():
    for c in ('规范名称', '原始名称'):
        if FRAME.search(str(r[c])):
            hits.append((r['规范名称'], r['类别'], r['研究数']))
            break
print('\n软件表中带"框架/通用计算/自研"特征的条目：')
for h in sorted(set(hits)):
    print('   %-30s 类别=%-8s 研究数=%s' % h)

print('\n各类别分布（研究数合计）：')
print(sw.groupby('类别')['研究数'].agg(['count', 'sum']).sort_values('sum', ascending=False).to_string())

# 每篇研究的软件数分布
d['_n_sw'] = d['Software Used (fixed)'].astype(str).str.split(';').map(
    lambda l: len([x for x in l if x.strip() and x.strip().lower() != 'nan']))
print('\n每篇研究的软件数分布：')
print(d['_n_sw'].value_counts().sort_index().to_string())
print('软件数为 0 的研究：', int((d['_n_sw'] == 0).sum()))
