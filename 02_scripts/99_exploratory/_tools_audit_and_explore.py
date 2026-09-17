# -*- coding: utf-8 -*-
"""
_tools_audit_and_explore.py —— 投稿前数据终检 + 候选新分析

A. 终检：锁定数据集内部一致性、与统计核心/PRISMA/补充材料的一致性
B. 探索：3 组可能产生有价值结论的分析
   B1 时间趋势 × 软件功能族（开源/通用工具是否在上升）
   B2 软件功能族共现结构（工作流"架构"）
   B3 研究设计 / 专科 × 所报缺口（差距是否集中在临床转化）
"""
import os
import ast
import json
import itertools
from collections import Counter

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
SW = pd.read_csv(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'), low_memory=False)
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)
S = json.load(open(os.path.join(ANA, '统计核心.json'), encoding='utf-8'))
P = json.load(open(os.path.join(ANA, 'PRISMA_链路_v2.json'), encoding='utf-8'))
N = len(d)


def pl(x):
    if isinstance(x, list):
        return x
    try:
        return ast.literal_eval(x) if isinstance(x, str) and x.strip().startswith('[') else []
    except Exception:
        return []


d['_spec_l'] = d['_spec'].map(pl)
d['_scen_l'] = d['_scen'].map(pl)
d['_soft_l'] = d['_soft2'].map(pl)

print('=' * 78)
print('A. 数据终检')
print('=' * 78)
rows = []


def chk(name, ok, detail=''):
    rows.append((name, 'OK' if ok else '!! 不一致', detail))
    print('  %-46s %s %s' % (name, 'OK' if ok else '!!', detail))


chk('数据集行数 = 统计核心 N', len(d) == S['N'] == P['included'], '%d / %d / %d'
    % (len(d), S['N'], P['included']))
chk('序号唯一且连续', d['序号'].is_unique and d['序号'].min() == 1
    and d['序号'].max() == N)
chk('Key 唯一', d['Key'].is_unique)
chk('无缺刊名', int(d['Journal'].isna().sum()) == 0)
chk('无缺国家', int(d['Region'].isna().sum()) == 0)
chk('专科赋值数一致', int(d['_spec_l'].map(len).sum()) == S['speciality_assignments'],
    '%d vs %d' % (int(d['_spec_l'].map(len).sum()), S['speciality_assignments']))
chk('场景赋值数一致', int(d['_scen_l'].map(len).sum()) == S['scenario_assignments'])
chk('软件赋值数一致', int(d['_soft_l'].map(len).sum()) == S['software_assignments'])
chk('多软件研究数一致', int(d['_soft_l'].map(lambda x: len(set(x)) > 1).sum())
    == S['n_studies_multi_software'])
chk('单软件研究数一致', int(d['_soft_l'].map(lambda x: len(set(x)) == 1).sum())
    == S['n_studies_single_software'],
    '%d vs %d' % (int(d['_soft_l'].map(lambda x: len(set(x)) == 1).sum()),
                   S['n_studies_single_software']))
chk('无零软件研究', int(d['_soft_l'].map(lambda x: len(set(x)) == 0).sum()) == 0)
chk('研究设计覆盖全部', int(d['study_type'].isna().sum()) == 0)
chk('原型覆盖全部', int(d['Archetype'].isna().sum()) == 0)
chk('趋势半年度合计 = 有月份记录数',
    sum(S['trend'].values()) == S['trend_denominator'],
    '%d vs %d' % (sum(S['trend'].values()), S['trend_denominator']))
chk('PRISMA 排除合计自洽',
    P['excluded_after_fulltext_assessment'] == sum(P['exclusion_breakdown'].values()),
    str(P['exclusion_breakdown']))
chk('PRISMA 评估数 - 排除数 = 纳入',
    P['assessed_for_eligibility_full_text'] - P['excluded_after_fulltext_assessment']
    == P['included'])
chk('PRISMA 全文重评 304 条', P['fulltext_recheck']['records_reclassified_as_eligible'] == 304)
chk('PRISMA 标题摘要排除 = 1943 - 304',
    P['excluded_at_title_abstract'] == 1943 - 304,
    str(P['excluded_at_title_abstract']))
chk('分类变量无缺失',
    all(int(d[c].isna().sum()) == 0 for c in ['Half2', 'study_type', 'Archetype', '_来源']))

bad = [r for r in rows if r[1] != 'OK']
print('\n  终检结论：%d 项通过，%d 项不一致' % (len(rows) - len(bad), len(bad)))

# ---------------------------------------------------------------- B
print('\n' + '=' * 78)
print('B. 候选新分析')
print('=' * 78)

name2cat = dict(zip(SW['规范名称'].astype(str), SW['类别'].astype(str)))
FAM = {'MIP': 'Medical image processing', 'RE': 'Reverse engineering',
       'GEN3D': 'General-purpose 3D modelling', 'SIM': 'Engineering simulation',
       'CAD': 'Computer-aided design', 'AM': 'Additive manufacturing',
       'SCI': 'Scientific computing', 'DICOM': 'DICOM viewers',
       'PHOTO': 'Photogrammetry', 'RT': 'Radiotherapy planning'}
d['_fam'] = d['_soft_l'].map(lambda L: {name2cat.get(s) for s in L} & set(FAM))

# ---- B1 时间趋势 × 软件功能族 ----
print('\nB1. 半年度 × 软件功能族（每百篇研究的赋值占比）')
HALF = [h for h in ['2020-H2', '2021-H1', '2021-H2', '2022-H1', '2022-H2', '2023-H1',
                    '2023-H2', '2024-H1', '2024-H2', '2025-H1', '2025-H2', '2026-H1']]
years = d['_year'].astype('Int64')
d['_y'] = d['Year'].astype('Int64')
b1 = {}
for f in ['MIP', 'RE', 'GEN3D', 'SIM', 'CAD']:
    ser = d['_fam'].map(lambda s, f=f: f in s)
    b1[f] = {}
    for y in [2020, 2021, 2022, 2023, 2024, 2025, 2026]:
        sub = d[d['_y'] == y]
        b1[f][y] = round(ser[sub.index].mean() * 100, 1) if len(sub) else np.nan
    print('  %-32s %s' % (FAM[f], ' '.join('%5.1f' % b1[f][y] for y in
                                           [2020, 2021, 2022, 2023, 2024, 2025, 2026])))

print('\n  开源/免费工具占比（按软件名人工标记的开源集）')
OPEN = {'3D Slicer', 'Blender', 'ITK-SNAP', 'MeshLab', 'FreeCAD', 'Python', 'GNU Octave',
        'InVesalius', 'Open3D', 'Trimesh', 'Iso2mesh', 'ImageJ', 'Z88', 'Onshape',
        'TensorFlow', 'Keras', 'CloudCompare', 'ParaView', 'Slicer'}
d['_open'] = d['_soft_l'].map(lambda L: bool({s for s in L if s in OPEN}))
for y in [2020, 2021, 2022, 2023, 2024, 2025, 2026]:
    sub = d[d['_y'] == y]
    if len(sub):
        print('   %d: %2d 篇中 %2d 篇用了开源工具（%.0f%%）'
              % (y, len(sub), int(d.loc[sub.index, '_open'].sum()),
                 d.loc[sub.index, '_open'].mean() * 100))

# ---- B2 软件功能族共现 ----
print('\nB2. 软件功能族共现（同时出现在同一研究中的篇数）')
fams = ['MIP', 'RE', 'GEN3D', 'SIM', 'CAD']
M = pd.DataFrame(0, index=fams, columns=fams)
for s in d['_fam']:
    for a, b in itertools.combinations_with_replacement(sorted(s), 2):
        if a in fams and b in fams:
            M.loc[a, b] += 1
            if a != b:
                M.loc[b, a] += 1
print(M.to_string())
print('\n  各族的"伴随族"（条件概率 P(伴随|主族)）')
for a in fams:
    tot = M.loc[a, a]
    others = [(b, M.loc[a, b] / tot * 100) for b in fams if b != a and M.loc[a, b]]
    others.sort(key=lambda x: -x[1])
    print('   %-30s n=%3d -> %s' % (FAM[a], tot,
                                    ', '.join('%s %.0f%%' % (b, v) for b, v in others)))

# ---- B3 研究设计 × 所报缺口 ----
print('\nB3. 研究设计 × 是否报告"需临床验证"缺口')
rq = pd.read_csv(os.path.join(ANA, 'rq3_pass', 'rq3_parsed.csv'), low_memory=False)
rq['Key'] = rq['Key'].astype(str)
dd = d.copy()
dd['Key'] = dd['Key'].astype(str)
dd = dd.merge(rq[['Key', '缺口', '挑战']], on='Key', how='left')
dd['gap_G1'] = dd['缺口'].fillna('').astype(str).str.contains('G1')
tab = pd.crosstab(dd['study_type'], dd['gap_G1'])
print(tab.to_string())
if tab.shape[0] > 1 and tab.shape[1] > 1 and tab.values.sum() > 0:
    chi2, p, dof, exp = chi2_contingency(tab)
    v = np.sqrt(chi2 / (tab.values.sum() * (min(tab.shape) - 1)))
    print('   chi2=%.1f df=%d p=%.2e CramersV=%.3f' % (chi2, dof, p, v))
    print('   各设计报告 G1 的比例：')
    for k in tab.index:
        r = tab.loc[k]
        print('     %-16s %3d/%3d = %.0f%%' % (k, r.get(True, 0), r.sum(),
                                                r.get(True, 0) / r.sum() * 100))
