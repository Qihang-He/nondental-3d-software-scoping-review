# -*- coding: utf-8 -*-
"""
_tools_archetype_derive_v5.py —— 从锁定 v5 数据集现有 Archetype 列派生工作流分型文件。

不重跑聚类（重跑会改变标签）；Archetype 列以锁定数据集 分析数据集_final_v5.csv 为准。
输出：
  03_数据/08_分析用/工作流分型_描述.csv
  03_数据/08_分析用/工作流分型_逐篇标签.csv
"""
import os
import json
import numpy as np
import pandas as pd
from collections import Counter

ROOT = os.environ.get('SCOPING_ROOT') or r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')

SHORT = {'Image Segmentation and 3D Reconstruction': 'Segmentation/Reconstruction',
         '3D Data Analysis and Accuracy Assessment': 'Analysis/Accuracy',
         'Biomechanical Analysis and Simulation': 'Biomechanics',
         'Digital Design and Manufacturing': 'Design/Manufacturing',
         'Surgical Planning and Precise Implementation': 'Surgical planning',
         'Morphological and Phenotypic Analysis': 'Morphology/Phenotype'}
FAM_CODES = ['MIP', 'RE', 'SIM', 'GEN3D', 'CAD', 'AM', 'SCI']
FAM_DESC = {'MIP': 'Medical image processing', 'RE': 'Reverse engineering / 3D reconstruction',
            'SIM': 'Engineering simulation', 'GEN3D': 'General-purpose 3D modelling',
            'CAD': 'Computer-aided design', 'AM': 'Additive manufacturing',
            'SCI': 'Scientific computing / visualisation'}

d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v5.csv'), low_memory=False)
sw = pd.read_csv(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'))
name2cat = dict(zip(sw['规范名称'], sw['类别']))

d['_scen_l'] = d['_scen'].fillna('[]').map(eval)
d['_soft_l'] = d['_soft2'].fillna('[]').map(eval)

rows = []
for a in sorted(d['Archetype'].unique()):
    sub = d[d['Archetype'] == a]
    scen = Counter()
    for lst in sub['_scen_l']:
        for s in lst:
            if s in SHORT:
                scen[SHORT[s]] += 1
    fams = Counter()
    for lst in sub['_soft_l']:
        for s in lst:
            c = name2cat.get(s)
            if c in FAM_CODES:
                fams[FAM_DESC[c]] += 1
    s1 = scen.most_common(1)
    s2 = scen.most_common(2)
    f1 = fams.most_common(1)
    f2 = fams.most_common(2)
    rows.append({
        'Archetype': a, 'n': len(sub), '占比%': round(100 * len(sub) / len(d), 1),
        '场景1': s1[0][0] if s1 else '', '场景1%': round(100 * s1[0][1] / len(sub)) if s1 else 0,
        '场景2': s2[1][0] if len(s2) > 1 else '', '场景2%': round(100 * s2[1][1] / len(sub)) if len(s2) > 1 else 0,
        '软件族1': f1[0][0] if f1 else '', '软件族2': f2[1][0] if len(f2) > 1 else '',
        '研究类型': ', '.join('%s(%d)' % (k, v) for k, v in Counter(sub['study_type']).most_common(2)),
    })
desc = pd.DataFrame(rows)
desc.to_csv(os.path.join(ANA, '工作流分型_描述.csv'), index=False, encoding='utf-8-sig')
d[['序号', 'Key', 'Title', 'Archetype']].to_csv(
    os.path.join(ANA, '工作流分型_逐篇标签.csv'), index=False, encoding='utf-8-sig')

pd.set_option('display.width', 300)
pd.set_option('display.max_colwidth', 42)
print(desc.to_string())
print('\n[saved] 工作流分型_描述.csv / 工作流分型_逐篇标签.csv (N=%d)' % len(d))
