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
_tools_final_audit.py —— 终检：正文/回复信数字与统计核心、PRISMA 链路、补充材料是否一致
"""
import os
import re
import json

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
S = json.load(open(os.path.join(ANA, '统计核心.json'), encoding='utf-8'))
CH = json.load(open(os.path.join(ANA, 'PRISMA_链路.json'), encoding='utf-8'))
E = json.load(open(os.path.join(ANA, '补充统计_v3.json'), encoding='utf-8'))
A = json.load(open(os.path.join(ANA, '工作流分型_方法参数.json'), encoding='utf-8'))
RQ = json.load(open(os.path.join(ANA, 'RQ3_频次汇总.json'), encoding='utf-8'))
L = json.load(open(os.path.join(ROOT, _os.path.join(_ROOTP, '05_图表'), 'fig5_stats.json'), encoding='utf-8'))

ms = open(os.path.join(ROOT, '01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md'),
          encoding='utf-8').read()
rp = open(os.path.join(ROOT, '01_投稿文件', 'R2_草稿', 'Response_to_reviewers_R2.md'),
          encoding='utf-8').read()

CHECK = [
    ('纳入研究数', str(S['N']), '566'),
    ('期刊数', str(S['n_journals']), '188'),
    ('会议论文集', str(S['n_conference_proceedings']), '4'),
    ('国家数', str(S['n_countries']), '51'),
    ('软件包数', str(S['n_software_packages']), '85'),
    ('软件赋值', str(S['software_assignments']), '917'),
    ('多软件研究', str(S['n_studies_multi_software']), '224'),
    ('多软件占比', str(S['pct_multi_software']), '39.6'),
    ('专科赋值', str(S['speciality_assignments']), '783'),
    ('场景赋值', str(S['scenario_assignments']), '755'),
    ('趋势基数', str(S['trend_denominator']), '559'),
    ('识别总数', str(CH['identified_databases']['total']), '3,631'),
    ('去重', str(CH['duplicates_removed']), '1,075'),
    ('筛查语料', str(CH['screened_title_abstract']), '2,556'),
    ('筛查排除', str(CH['excluded_at_screening']), '1,943'),
    ('资格评估', str(CH['assessed_for_eligibility']), '613'),
    ('资格排除', str(CH['excluded_after_assessment']), '47'),
    ('无软件原因', str(CH['excluded_at_screening_by_reason_en']
                    ['No non-dental 3D software identified']), '1,127'),
    ('chi2', '%.1f' % L['chi2'], '216.2'),
    ('cramers_v', '%.3f' % L['cramers_v'], '0.229'),
    ('趋势斜率(全部)', '%.2f' % E['trend_all']['slope'], '2.17'),
    ('趋势斜率(排除26H1)', '%.2f' % E['trend_excl_2026H1']['slope'], '2.96'),
    ('原型k', str(A['k']), '5'),
    ('原型ARI', '%.2f' % A['bootstrap_ARI_mean'], '0.64'),
    ('κ', str(S['ai_consistency']['Fleiss_kappa']), '0.936'),
    ('A6优势', str(next(x['n'] for x in RQ['advantages'] if x['code'] == 'A6')), '250'),
    ('A6占比', str(next(x['pct'] for x in RQ['advantages'] if x['code'] == 'A6')), '44.2'),
    ('C4挑战', str(next(x['n'] for x in RQ['challenges'] if x['code'] == 'C4')), '167'),
    ('G1缺口', str(next(x['n'] for x in RQ['gaps'] if x['code'] == 'G1')), '353'),
]

print('%-22s %-14s %-14s %s' % ('项目', '计算值', '正文/回复信', '结果'))
bad = 0
for name, val, expect in CHECK:
    in_ms = val in ms or val in rp or val.replace(',', '') in ms
    ok = (val == expect) and in_ms
    if not ok:
        bad += 1
    print('%-22s %-14s %-14s %s' % (name, val, expect,
                                    'OK' if ok else '!! 需核对'))

print('\n不一致项:', bad)

# 图与补充材料存在性
need = ['Figure1_PRISMA', 'Figure2_landscape', 'Figure3_software', 'Figure4_workflows',
        'Figure5_contingency', 'Figure6_rq3', 'Supplementary_Figure_S1_journals']
for n in need:
    for ext in ('.png', '.pdf'):
        p = os.path.join(ROOT, _os.path.join(_ROOTP, '05_图表'), n + ext)
        if not os.path.exists(p):
            print('!! 缺少图件', n + ext)
print('图件检查完成')

for p in ['02_图表附件/R2_补充材料/Supplementary_File_2_R2.xlsx',
          '02_图表附件/R2_补充材料/Supplementary_File_3.xlsx',
          '02_图表附件/R2_补充材料/Dataset_provenance_table.csv',
          '02_图表附件/R2_补充材料/作者核验工作簿.xlsx',
          '01_投稿文件/R2_草稿/Revised_manuscript_R2.docx',
          '01_投稿文件/R2_草稿/Response_to_reviewers_R2.docx',
          '06_公共仓库/README.md']:
    print(('OK  ' if os.path.exists(os.path.join(ROOT, p)) else '!! 缺 '), p)
