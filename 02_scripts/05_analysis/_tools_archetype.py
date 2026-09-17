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
_tools_archetype.py  (v2)
工作流原型的数据驱动推导（无人工编码本时的替代方案）

特征 = 6 个应用场景(多热) + 7 个软件功能族(多热)
       软件功能族：MIP 医学图像处理 / RE 逆向工程·三维重建 / SIM 工程仿真
                   GEN3D 通用三维建模 / CAD 计算机辅助设计 / AM 增材制造 / SCI 科学计算绘图
方法 = Jaccard 距离 -> 平均连接层次聚类；k 由轮廓系数择优；bootstrap 100 次报告 ARI 稳定性
输出 = 03_数据/08_分析用/工作流分型_*.{csv,json}
"""
import os
import json
import numpy as np
import pandas as pd
from collections import Counter
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import silhouette_score, adjusted_rand_score

ROOT = _os.path.join(_ROOTP, '03_数据', '08_分析用')
d = pd.read_csv(os.path.join(ROOT, '分析数据集_final_v4.csv'), low_memory=False)
sw = pd.read_csv(_os.path.join(_ROOTP, '03_数据', '09_软件表', '软件类别与来源表.csv'))
name2cat = dict(zip(sw['规范名称'], sw['类别']))

d['_scen_l'] = d['_scen'].fillna('[]').map(eval)
d['_soft_l'] = d['_soft2'].fillna('[]').map(eval)

SCEN = ['Image Segmentation and 3D Reconstruction',
        '3D Data Analysis and Accuracy Assessment',
        'Biomechanical Analysis and Simulation',
        'Digital Design and Manufacturing',
        'Surgical Planning and Precise Implementation',
        'Morphological and Phenotypic Analysis']
SHORT = {'Image Segmentation and 3D Reconstruction': 'Segmentation/Reconstruction',
         '3D Data Analysis and Accuracy Assessment': 'Analysis/Accuracy',
         'Biomechanical Analysis and Simulation': 'Biomechanics',
         'Digital Design and Manufacturing': 'Design/Manufacturing',
         'Surgical Planning and Precise Implementation': 'Surgical planning',
         'Morphological and Phenotypic Analysis': 'Morphology/Phenotype'}

FAM = [('MIP', 'Medical image processing'),
       ('RE', 'Reverse engineering / 3D reconstruction'),
       ('SIM', 'Engineering simulation'),
       ('GEN3D', 'General-purpose 3D modelling'),
       ('CAD', 'Computer-aided design'),
       ('AM', 'Additive manufacturing'),
       ('SCI', 'Scientific computing / visualisation')]
FAM_CODES = [f[0] for f in FAM]
FAM_DESC = dict(FAM)

feat_names = [SHORT[s] for s in SCEN] + [n for _, n in FAM]
X = np.zeros((len(d), len(feat_names)), dtype=int)
for i in range(len(d)):
    for s in d['_scen_l'].iloc[i]:
        if s in SCEN:
            X[i, SCEN.index(s)] = 1
    for s in d['_soft_l'].iloc[i]:
        c = name2cat.get(s)
        if c in FAM_CODES:
            X[i, len(SCEN) + FAM_CODES.index(c)] = 1

D = squareform(pdist(X, metric='jaccard'))
Z = linkage(squareform(D, checks=False), method='average')

scores = {}
for k in range(2, 9):
    lab = fcluster(Z, k, criterion='maxclust')
    if len(set(lab)) < 2:
        continue
    try:
        scores[k] = silhouette_score(D, lab, metric='precomputed')
    except Exception:
        continue
    print('k=%d  silhouette=%.4f  sizes=%s' %
          (k, scores[k], sorted(Counter(lab).values(), reverse=True)))

# 择优：轮廓系数最大，且最小簇 >= 5% N（保证可解释、可展示）
min_n = 0.05 * len(d)
best_k, best_s = None, -1
for k, s in scores.items():
    lab = fcluster(Z, k, criterion='maxclust')
    if min(Counter(lab).values()) < min_n:
        continue
    if s > best_s:
        best_s, best_k = s, k
print('-> 选定 k=%d (silhouette=%.4f, 最小簇>=5%%)' % (best_k, best_s))

lab = fcluster(Z, best_k, criterion='maxclust')
orig = lab.copy()
order = [c for c, _ in Counter(lab).most_common()]
remap = {c: i + 1 for i, c in enumerate(order)}
lab = np.array([remap[c] for c in lab])
d['Archetype'] = lab

rng = np.random.default_rng(20260912)
aris = []
for _ in range(100):
    idx = rng.integers(0, len(d), len(d))
    try:
        Zb = linkage(squareform(D[np.ix_(idx, idx)], checks=False), method='average')
        lb = fcluster(Zb, best_k, criterion='maxclust')
        aris.append(adjusted_rand_score(orig[idx], lb))
    except Exception:
        pass
print('bootstrap ARI 均值=%.3f (SD=%.3f, n=%d)' % (np.mean(aris), np.std(aris), len(aris)))

rows = []
for a in sorted(set(lab)):
    sub = d[d['Archetype'] == a]
    scen = Counter()
    for lst in sub['_scen_l']:
        for s in lst:
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
desc.to_csv(os.path.join(ROOT, '工作流分型_描述.csv'), index=False, encoding='utf-8-sig')
d[['序号', 'Key', 'Title', 'Archetype']].to_csv(
    os.path.join(ROOT, '工作流分型_逐篇标签.csv'), index=False, encoding='utf-8-sig')
d.drop(columns=['_scen_l', '_soft_l']).to_csv(
    os.path.join(ROOT, '分析数据集_final_v4.csv'), index=False, encoding='utf-8-sig')

pd.set_option('display.width', 300)
pd.set_option('display.max_colwidth', 42)
print()
print(desc.to_string())

json.dump({'k': int(best_k), 'silhouette': float(best_s),
           'bootstrap_ARI_mean': float(np.mean(aris)),
           'bootstrap_ARI_sd': float(np.std(aris)), 'n_bootstrap': len(aris),
           'features': feat_names,
           'method': 'multi-hot (6 scenarios + 7 software families) -> Jaccard distance -> average-linkage hierarchical clustering'},
          open(os.path.join(ROOT, '工作流分型_方法参数.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('\n[saved] 工作流分型_描述.csv / 工作流分型_逐篇标签.csv / 工作流分型_方法参数.json')
