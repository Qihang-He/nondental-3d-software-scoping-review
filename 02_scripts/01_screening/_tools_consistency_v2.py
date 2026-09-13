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
_tools_consistency_v2.py —— 在规范语料（2,556 条）上重算三轮复筛一致性
输入：07_AI重跑原始记录/run1-3/classification_parsed.csv + 03_数据/08_分析用/prisma_pass/run_extra_parsed.csv
输出：07_AI重跑原始记录/一致性分析/consistency_report_v2.json
      07_AI重跑原始记录/一致性分析/三轮逐条结果与多数标签_v2.csv
"""
import os
import json
import re
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.metrics import cohen_kappa_score

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')


def nt(s):
    s = re.sub(r'<[^>]+>', ' ', str(s))
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


def fleiss_kappa(M):
    """M: n_items x n_categories 计数矩阵"""
    n_items, n_cat = M.shape
    n_rat = M.sum(1)
    assert len(set(n_rat)) == 1, '每位评定者的评定数必须相同'
    n = n_rat[0]
    p_j = M.sum(0) / (n_items * n)
    P_i = (np.sum(M ** 2, 1) - n) / (n * (n - 1))
    P_bar = P_i.mean()
    P_e = np.sum(p_j ** 2)
    return (P_bar - P_e) / (1 - P_e)


corpus = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                  '筛选语料_唯一记录_2556.csv'), low_memory=False)
corpus['_nt'] = corpus['Title'].map(nt)

frames = {}
for i in (1, 2, 3):
    t = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'run%d' % i,
                                 'classification_parsed.csv'), low_memory=False)
    t['_nt'] = t['文献标题'].map(nt)
    t = t.drop_duplicates('_nt')
    frames['run%d' % i] = dict(zip(t['_nt'], t['分类结果']))

extra_fp = os.path.join(ANA, 'prisma_pass', 'run_extra_parsed.csv')
if os.path.exists(extra_fp):
    ex = pd.read_csv(extra_fp, low_memory=False)
    ex = ex[ex['分类结果'].notna()]
    for run in (1, 2, 3):
        sub = ex[ex['run'] == run]
        for _, r in sub.iterrows():
            frames['run%d' % run][r['_nt']] = r['分类结果']

rows = []
for _, r in corpus.iterrows():
    k = r['_nt']
    labs = [frames['run%d' % i].get(k) for i in (1, 2, 3)]
    if any(v is None for v in labs):
        continue
    cnt = Counter(labs)
    rows.append({'序号': r.get('序号'), 'Key': r.get('Key'), 'Title': r.get('Title'),
                 'run1': labs[0], 'run2': labs[1], 'run3': labs[2],
                 '一致': len(cnt) == 1, '一致度': cnt.most_common(1)[0][1] / 3,
                 '多数标签': cnt.most_common(1)[0][0]})
D = pd.DataFrame(rows)
cats = ['include', 'exclude', 'unsure']
M = np.zeros((len(D), 3))
for i, lab in enumerate(['run1', 'run2', 'run3']):
    for j, c in enumerate(cats):
        M[:, j] += (D[lab] == c).astype(int).values

rep = {
    '三轮总记录数': int(len(D)),
    '一致率(三轮完全相同)': round(float(D['一致'].mean()), 4),
    '两两一致率': {'run1_vs_run2': round(float((D.run1 == D.run2).mean()), 4),
                   'run1_vs_run3': round(float((D.run1 == D.run3).mean()), 4),
                   'run2_vs_run3': round(float((D.run2 == D.run3).mean()), 4)},
    'Fleiss_kappa': round(float(fleiss_kappa(M)), 4),
    '平均成对Cohen_kappa': round(float(np.mean([
        cohen_kappa_score(D.run1, D.run2), cohen_kappa_score(D.run1, D.run3),
        cohen_kappa_score(D.run2, D.run3)])), 4),
    '三轮分布': {c: {k: int((D[k] == c).sum()) for k in ['run1', 'run2', 'run3']}
                 for c in cats},
    '多数投票分布': {k: int(v) for k, v in D['多数标签'].value_counts().items()},
}
json.dump(rep, open(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), '一致性分析',
                                 'consistency_report_v2.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
D.to_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), '一致性分析', '三轮逐条结果与多数标签_v2.csv'),
         index=False, encoding='utf-8-sig')
print(json.dumps(rep, ensure_ascii=False, indent=2))
