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
_tools_build_v4_dataset.py —— 合并 v3（566）与新增纳入记录，生成分析数据集 v4
要点：
  · 新增记录的全部字段与 v3 同列同名，取值口径一致
  · 重新计算半年度区间 Half2
  · 输出 分析数据集_final_v4.csv 与 变更日志_v3_to_v4.csv
"""
import os
import re
import ast
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
v3 = pd.read_pickle(os.path.join(ANA, '_base_v4.pkl'))
add = pd.read_pickle(os.path.join(ANA, '_add_v4.pkl'))
print('v3: %d ；新增: %d' % (len(v3), len(add)))


def half_of(y, m):
    if pd.isna(y):
        return 'unknown'
    y = int(y)
    if y == 2020:
        return '2020-H2'
    if y == 2026 and (pd.isna(m) or int(m) <= 6):
        return '2026-H1'
    if pd.isna(m):
        return 'unknown'
    return '%d-H%d' % (y, 1 if int(m) <= 6 else 2)


def split_months(s):
    s = str(s)
    y = re.search(r'(19|20)\d{2}', s)
    m = re.search(r'[/\-. ](\d{1,2})(?=[/\-. ]|$)', s)
    yy = int(y.group(0)) if y else None
    mm = int(m.group(1)) if m and 1 <= int(m.group(1)) <= 12 else None
    return yy, mm


rows = []
for _, r in add.iterrows():
    y, m = split_months(r.get('Date'))
    if y is None and pd.notna(r.get('Year')):
        y = int(r['Year'])
    row = {c: None for c in v3.columns}
    row.update({
        'Key': r.get('Key'), 'Title': r['Title'], 'DOI': r.get('DOI'),
        'Journal': r.get('Journal'), 'Item Type': r.get('Item Type'),
        'Date': r.get('Date'), 'Year': y,
        'Dental Specialty': r['Dental Specialty'],
        'Software Used': r.get('Software Used (fixed)'),
        'Application Scenario': r['Application Scenario'],
        'Region': r.get('Region'),
        'Software Used (fixed)': r.get('Software Used (fixed)'),
        'study_type': r['study_type'],
        '_year': y, '_month': m,
        'Half2': half_of(y, m),
    })
    row['_spec'] = str([r['Dental Specialty']])
    row['_scen'] = str([r['Application Scenario']])
    row['_soft'] = str([x.strip() for x in str(r.get('Software Used (fixed)')).split(';')
                        if x.strip()])
    row['_soft2'] = row['_soft']
    row['_来源'] = '全文再筛查补入'
    rows.append(row)

newdf = pd.DataFrame(rows)
for c in v3.columns:
    if c not in newdf.columns:
        newdf[c] = None
newdf['_来源'] = '全文再筛查补入'
v3['_来源'] = '原始筛查'
cols = list(dict.fromkeys(v3.columns.tolist() + ['_来源']))
merged = pd.concat([v3[cols], newdf.reindex(columns=cols)], ignore_index=True)
merged['序号'] = range(1, len(merged) + 1)
merged['Archetype'] = None      # 随后重算

merged.to_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), index=False,
              encoding='utf-8-sig')
log = pd.DataFrame([{'新增项': '纳入研究数', 'v3': len(v3), 'v4': len(merged),
                     '差异': len(merged) - len(v3)},
                    {'新增项': '期刊数', 'v3': v3['Journal'].nunique(),
                     'v4': merged['Journal'].nunique(),
                     '差异': merged['Journal'].nunique() - v3['Journal'].nunique()},
                    {'新增项': '软件名', 'v3': len({x for l in v3['_soft2'].dropna()
                                                     for x in ast.literal_eval(l) if x}),
                     'v4': len({x for l in merged['_soft2'].dropna()
                                for x in ast.literal_eval(l) if x})}])
log.to_csv(os.path.join(ANA, '变更日志_v3_to_v4.csv'), index=False,
           encoding='utf-8-sig')
print('v4 =', len(merged))
print(log.to_string())
print('Region 缺失:', int(merged['Region'].isna().sum()))
