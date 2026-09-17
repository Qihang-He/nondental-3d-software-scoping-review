# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""
_tools_extra_stats_v3.py —— N=566 的补充统计
  · 半年度趋势的线性回归（全部期 / 排除 2026-H1 / 仅完整期）
  · 软件共现对（Top 30）
  · 专科 × 软件族 列联分析（精确 χ²、Cramér's V、标准化残差、期望频数<5 比例）
  · 专科规模归一后的软件族占比（回应"未按专科规模归一"的质疑）
输出：03_数据/08_分析用/补充统计_v3.json
"""
import os
import ast
import json
from itertools import combinations
from collections import Counter
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, linregress, chi2 as chi2dist

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
S = json.load(open(os.path.join(ANA, '统计核心_v5.json'), encoding='utf-8'))
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v5.csv'), low_memory=False)
SW = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
name2cat = dict(zip(SW['规范名称'], SW['类别']))
N = len(d)
HALF = ['2020-H2', '2021-H1', '2021-H2', '2022-H1', '2022-H2', '2023-H1', '2023-H2',
        '2024-H1', '2024-H2', '2025-H1', '2025-H2', '2026-H1']


def pl(x):
    if isinstance(x, list):
        return x
    try:
        return ast.literal_eval(x) if isinstance(x, str) else []
    except Exception:
        return []


d['_soft_l'] = d['_soft2'].map(pl)
d['_spec_l'] = d['_spec'].map(pl)
R = {}

# ---------- 趋势回归 ----------
y = np.array([S['trend'][h] for h in HALF], dtype=float)
x = np.arange(len(HALF), dtype=float)
R['trend_all'] = dict(zip(['slope', 'intercept', 'r', 'p', 'stderr'],
                          [float(v) for v in linregress(x, y)]))
y2 = y[:-1]
x2 = x[:-1]
R['trend_excl_2026H1'] = dict(zip(['slope', 'intercept', 'r', 'p', 'stderr'],
                                  [float(v) for v in linregress(x2, y2)]))
m = np.array([v > 0 for v in y])
R['trend_complete_periods_only'] = dict(zip(['slope', 'intercept', 'r', 'p', 'stderr'],
                                            [float(v) for v in linregress(x[:11], y[:11])]))
R['trend_counts'] = {h: int(v) for h, v in zip(HALF, y)}

# ---------- 软件共现 ----------
pair = Counter()
for lst in d['_soft_l']:
    s = sorted(set(lst))
    for a, b in combinations(s, 2):
        pair[(a, b)] += 1
R['software_pairs_top'] = [{'a': a, 'b': b, 'n': int(c)}
                           for (a, b), c in pair.most_common(30)]

# ---------- 专科 × 软件族 列联 ----------
FAMS = ['MIP', 'RE', 'SIM', 'GEN3D', 'CAD']

FULL = {'Image Segmentation and 3D Reconstruction':
            'Image segmentation and 3D reconstruction',
        '3D Data Analysis and Accuracy Assessment':
            '3D data analysis and accuracy assessment',
        'Biomechanical Analysis and Simulation': 'Biomechanical analysis and simulation',
        'Digital Design and Manufacturing': 'Digital design and manufacturing',
        'Surgical Planning and Precise Implementation':
            'Surgical planning and precise implementation',
        'Morphological and Phenotypic Analysis':
            'Morphological and phenotypic analysis'}

spec_list = list(S['speciality'].keys())
M_all = np.zeros((len(spec_list), len(FAMS)), dtype=int)
for _, r in d.iterrows():
    sps = set(r['_spec_l'])
    fams = {name2cat.get(s) for s in r['_soft_l']}
    for i, sp in enumerate(spec_list):
        if sp in sps:
            for j, f in enumerate(FAMS):
                if f in fams:
                    M_all[i, j] += 1

# 主分析：与图 5 完全一致（前 8 个专科 × 5 个软件族）
spec_main = spec_list[:8]
M = M_all[:8]
chi2, p, dof, exp = chi2_contingency(M)
V = float(np.sqrt(chi2 / (M.sum() * (min(M.shape) - 1))))
resid = (M - exp) / np.sqrt(exp * (1 - M.sum(1, keepdims=True) / M.sum())
                           * (1 - M.sum(0, keepdims=True) / M.sum()))
R['contingency_full'] = {
    'config': 'top 8 specialities x 5 software families (same as Figure 5)',
    'chi2': float(chi2), 'dof': int(dof), 'p': float(p), 'cramers_v': V,
    'n_specialities': len(spec_main), 'n_families': len(FAMS),
    'pct_expected_below_5': round(float((exp < 5).mean() * 100), 1),
    'min_expected': float(exp.min()),
    'spec': spec_main, 'families': FAMS,
    'counts': M.tolist(), 'residuals': np.round(resid, 2).tolist()}

# 敏感性分析：其余专科合并为 "Other"
rest = M_all[8:].sum(0).reshape(1, -1)
M2b = np.vstack([M, rest])
chi2b, pb, dofb, expb = chi2_contingency(M2b)
Vb = float(np.sqrt(chi2b / (M2b.sum() * (min(M2b.shape) - 1))))
R['contingency_merged_small_specialities'] = {
    'config': 'top 8 specialities + Other (remaining 4) x 5 software families',
    'chi2': float(chi2b), 'dof': int(dofb), 'p': float(pb), 'cramers_v': Vb,
    'pct_expected_below_5': round(float((expb < 5).mean() * 100), 1),
    'merged_specialities': spec_list[8:]}

# 全 12 专科（仅作参考）
chi2c, pc, dofc, expc = chi2_contingency(M_all)
R['contingency_all12'] = {
    'config': 'all 12 specialities x 5 software families',
    'chi2': float(chi2c), 'dof': int(dofc), 'p': float(pc),
    'cramers_v': float(np.sqrt(chi2c / (M_all.sum() * (min(M_all.shape) - 1)))),
    'pct_expected_below_5': round(float((expc < 5).mean() * 100), 1)}

# ---------- 专科规模归一后的软件族占比 ----------
norm = []
for i, sp in enumerate(spec_main):
    row = M[i]
    tot = int(row.sum())
    if tot == 0:
        continue
    norm.append({'speciality': sp, 'studies': int(S['speciality'][sp]),
                 'assignments': tot,
                 **{FAMS[j]: round(float(row[j] / tot * 100), 1) for j in range(len(FAMS))}})
R['software_family_share_by_speciality'] = norm

json.dump(R, open(os.path.join(ANA, '补充统计_v3.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)

print('趋势斜率（全部期）= %.2f / 半年' % R['trend_all']['slope'])
print('趋势斜率（排除2026-H1）= %.2f' % R['trend_excl_2026H1']['slope'])
print('列联：chi2=%.1f df=%d p=%.3g V=%.3f；期望<5 占 %.1f%%'
      % (chi2, dof, p, V, R['contingency_full']['pct_expected_below_5']))
print('合并小专科后：chi2=%.1f df=%d V=%.3f' % (chi2b, dofb, Vb))
print('\nTop 共现对：')
for it in R['software_pairs_top'][:12]:
    print('   %-24s + %-24s %d' % (it['a'], it['b'], it['n']))
print('\n[saved] 补充统计_v3.json')
