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
_tools_stats_core.py  —— 全项目唯一数字来源（single source of truth）
输入：03_数据/08_分析用/分析数据集_final_v4.csv （N=863，含 Archetype）
输出：03_数据/08_分析用/统计核心.json
     08_留痕文档/12_最终统计汇总_863.md
所有图表、正文、回复信、补充材料均只引用此文件的数字。
"""
import os
import re
import json
from collections import Counter
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)

HALF_ORDER = ['2020-H2', '2021-H1', '2021-H2', '2022-H1', '2022-H2', '2023-H1',
              '2023-H2', '2024-H1', '2024-H2', '2025-H1', '2025-H2', '2026-H1']


def parse_list(v):
    if isinstance(v, list):
        return v
    try:
        return eval(v) if isinstance(v, str) and v.strip().startswith('[') else []
    except Exception:
        return []


d['_spec_l'] = d['_spec'].map(parse_list)
d['_scen_l'] = d['_scen'].map(parse_list)
d['_soft_l'] = d['_soft2'].map(parse_list)

S = {}
S['N'] = int(len(d))

# ---------- 文献类型与来源 ----------
items = d['Item Type'].value_counts().to_dict()
S['item_types'] = {k: int(v) for k, v in items.items()}
CONF_PAT = re.compile(r'\bConference\b|Annual International Conference|Symposium|'
                      r'International Conference|Proceedings', re.I)
conf_mask = d['Journal'].astype(str).str.contains(CONF_PAT)
S['n_conference_proceedings'] = int(conf_mask.sum())
S['n_journals'] = int(d.loc[~conf_mask, 'Journal'].nunique())
S['n_sources_total'] = int(d['Journal'].nunique())
S['n_missing_journal'] = int(d['Journal'].isna().sum())
S['n_missing_doi'] = int(d['DOI'].isna().sum())
S['n_missing_country'] = int(d['Region'].isna().sum())
S['n_countries'] = int(d['Region'].nunique())

# ---------- 期刊 / 国家 Top ----------
S['journal_top'] = {str(k): int(v) for k, v in
                    d.loc[~conf_mask, 'Journal'].value_counts().head(10).items()}
S['journal_top10_share'] = round(float(
    d.loc[~conf_mask, 'Journal'].value_counts().head(10).sum() / S['N'] * 100), 1)
S['region_top'] = {str(k): int(v) for k, v in d['Region'].value_counts().head(12).items()}

# ---------- 半年度趋势 ----------
tr = d['Half2'].value_counts()
S['trend'] = {h: int(tr.get(h, 0)) for h in HALF_ORDER}
S['trend_denominator'] = int(sum(S['trend'].values()))
S['n_year_only'] = int(S['N'] - S['trend_denominator'])
S['trend_excl_2026H1'] = {h: v for h, v in S['trend'].items() if h != '2026-H1'}

# ---------- 多标签统计（同时报告 唯一研究数 与 赋次数）----------
def multistat(col):
    uniq, assigns = Counter(), 0
    for lst in d[col]:
        for x in set(lst):
            uniq[x] += 1
        assigns += len(lst)
    return uniq, assigns


spec_u, spec_a = multistat('_spec_l')
scen_u, scen_a = multistat('_scen_l')
soft_u, soft_a = multistat('_soft_l')
S['speciality'] = {k: int(v) for k, v in sorted(spec_u.items(), key=lambda x: -x[1])}
S['speciality_assignments'] = int(spec_a)
S['n_studies_multispeciality'] = int(sum(1 for l in d['_spec_l'] if len(set(l)) > 1))
S['scenario'] = {k: int(v) for k, v in sorted(scen_u.items(), key=lambda x: -x[1])}
S['scenario_assignments'] = int(scen_a)
S['n_studies_multiscenario'] = int(sum(1 for l in d['_scen_l'] if len(set(l)) > 1))
S['n_software_packages'] = int(len(soft_u))
S['software_assignments'] = int(soft_a)
S['software_top'] = {k: int(v) for k, v in sorted(soft_u.items(), key=lambda x: -x[1])[:15]}
S['n_studies_multi_software'] = int(sum(1 for l in d['_soft_l'] if len(set(l)) > 1))
S['pct_multi_software'] = round(S['n_studies_multi_software'] / S['N'] * 100, 1)
S['n_studies_single_software'] = int(S['N'] - S['n_studies_multi_software'])

# ---------- 研究设计 ----------
S['study_type'] = {k: int(v) for k, v in d['study_type'].value_counts().items()}
S['study_type_pct'] = {k: round(v / S['N'] * 100, 1) for k, v in S['study_type'].items()}

# ---------- 工作流原型 ----------
if 'Archetype' in d.columns:
    arch = d['Archetype'].value_counts().sort_index()
    S['archetype_n'] = {int(k): int(v) for k, v in arch.items()}
    ap = os.path.join(ANA, '工作流分型_方法参数.json')
    if os.path.exists(ap):
        S['archetype_method'] = json.load(open(ap, encoding='utf-8'))

# ---------- AI 复筛一致性（将随后用 2,556 版重算，此处先留位）----------
cp = os.path.join(ROOT, '05_AI重跑', '一致性分析', 'consistency_report.json')
if os.path.exists(cp):
    S['ai_consistency_v1'] = json.load(open(cp, encoding='utf-8'))

# ---------- 时间窗 ----------
S['window'] = {'start': '2020-07-01', 'end': '2026-06-30'}

with open(os.path.join(ANA, '统计核心.json'), 'w', encoding='utf-8') as f:
    json.dump(S, f, ensure_ascii=False, indent=2)

# ---------- Markdown 汇总 ----------
L = ['# 最终统计汇总（N = %d）' % S['N'], '',
     '> 唯一数据源：`03_数据/08_分析用/分析数据集_final_v4.csv`；本文件由 `_tools_stats_core.py` 自动生成。', '',
     '## 一、总体', '',
     '- 纳入研究：**%d**（期刊论文 %d，会议论文 %d）' % (
         S['N'], S['item_types'].get('journalArticle', 0),
         S['item_types'].get('conferencePaper', 0)),
     '- 来源期刊：**%d** 种；会议论文集 **%d** 种；缺刊名 **%d** 条' % (
         S['n_journals'], S['n_conference_proceedings'], S['n_missing_journal']),
     '- 国家/地区：**%d** 个；缺国家 **%d** 条' % (S['n_countries'], S['n_missing_country']),
     '- 缺 DOI：**%d** 条' % S['n_missing_doi'], '',
     '## 二、半年度发文趋势', '', '| 期间 | 篇数 |', '|---|---|']
for k, v in S['trend'].items():
    L.append('| %s | %d |' % (k, v))
L += ['', '> 有月份信息 **%d** 篇；仅有年份 **%d** 篇（未纳入趋势）。' % (
    S['trend_denominator'], S['n_year_only']),
    '> 2026-H1 为检索截止（2026-06-30）前的**不完整期**，存在索引滞后。', '',
    '## 三、研究设计分层', '', '| 研究设计 | 篇数 | 占比 |', '|---|---|---|']
for k, v in S['study_type'].items():
    L.append('| %s | %d | %.1f%% |' % (k, v, S['study_type_pct'][k]))
L += ['', '## 四、专科分布（多标签）', '',
      '> 唯一研究数 %d 次赋值；%d 篇涉及多个专科。轴标签应标为 "study–speciality assignments"。'
      % (S['speciality_assignments'], S['n_studies_multispeciality']), '',
      '| 专科 | 唯一研究数 |', '|---|---|']
for k, v in S['speciality'].items():
    L.append('| %s | %d |' % (k, v))
L += ['', '## 五、应用场景（多标签）', '',
      '> %d 次赋值；%d 篇涉及多个场景。' % (S['scenario_assignments'], S['n_studies_multiscenario']),
      '', '| 应用场景 | 唯一研究数 |', '|---|---|']
for k, v in S['scenario'].items():
    L.append('| %s | %d |' % (k, v))
L += ['', '## 六、软件', '',
      '- 软件包总数：**%d** 种；赋值 **%d** 次' % (S['n_software_packages'], S['software_assignments']),
      '- 使用 >1 个软件包的研究：**%d** 篇（%.1f%%）' % (S['n_studies_multi_software'], S['pct_multi_software']),
      '', '| 软件（Top 15） | 唯一研究数 |', '|---|---|']
for k, v in S['software_top'].items():
    L.append('| %s | %d |' % (k, v))
L += ['', '## 七、期刊 Top 10', '',
      '> Top 10 合计占 N 的 %.1f%%' % S['journal_top10_share'], '',
      '| 期刊 | 篇数 |', '|---|---|']
for k, v in S['journal_top'].items():
    L.append('| %s | %d |' % (k, v))
L += ['', '## 八、国家/地区 Top 12', '', '| 国家/地区 | 篇数 |', '|---|---|']
for k, v in S['region_top'].items():
    L.append('| %s | %d |' % (k, v))
if 'archetype_n' in S:
    L += ['', '## 九、工作流原型（数据驱动聚类）', '',
          '- 方法：%s' % S.get('archetype_method', {}).get('method', ''),
          '- k = %s；轮廓系数 = %s；bootstrap ARI = %s' % (
              S['archetype_method'].get('k'), round(S['archetype_method'].get('silhouette', 0), 3),
              round(S['archetype_method'].get('bootstrap_ARI_mean', 0), 3)),
          '', '| 原型 | 篇数 | 占比 |', '|---|---|---|']
    for k, v in S['archetype_n'].items():
        L.append('| %d | %d | %.1f%% |' % (k, v, v / S['N'] * 100))

open(os.path.join(ROOT, '08_留痕文档', '12_最终统计汇总_863.md'), 'w',
     encoding='utf-8').write('\n'.join(L))

print('N =', S['N'])
print('期刊 %d 种（会议论文集 %d）' % (S['n_journals'], S['n_conference_proceedings']))
print('国家 %d 个' % S['n_countries'])
print('软件 %d 种 / %d 次赋值' % (S['n_software_packages'], S['software_assignments']))
print('多软件研究 %d (%.1f%%)' % (S['n_studies_multi_software'], S['pct_multi_software']))
print('专科赋值 %d；场景赋值 %d' % (S['speciality_assignments'], S['scenario_assignments']))
print('趋势基数 %d；仅年份 %d' % (S['trend_denominator'], S['n_year_only']))
print('研究设计:', S['study_type'])
print('原型:', S.get('archetype_n'))
print('[saved] 统计核心.json / 12_最终统计汇总_863.md')
