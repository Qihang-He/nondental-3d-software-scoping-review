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
_tools_supp3_v2.py —— 重建 Supplementary File 3（N = 863）与版本溯源表
工作表：
  1_Included studies      逐篇纳入研究（含工作流原型、研究设计、软件与类别）
  2_Software glossary     软件包词典（类别 + 原始开发领域 + 官方来源）
  3_Eligibility audit     全部 47 条资格阶段剔除及其理由
  4_Definitions and notes 编码与流程定义、AI 使用声明、证据边界说明
输出：02_图表附件/R2_补充材料/Supplementary_File_3.xlsx + Dataset_provenance_table.csv
"""
import os
import ast
import json
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
LOCK = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '06_锁定数据集')
FINAL = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '04_最终表', '最终表.xlsx')
SWT = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv')
OUTD = os.path.join(ROOT, _os.path.join(_ROOTP, '02_图表附件'), 'R2_补充材料')
os.makedirs(OUTD, exist_ok=True)

S = json.load(open(os.path.join(ANA, '统计核心.json'), encoding='utf-8'))
N = S['N']


def nrm(s):
    import re
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())


def pl(x):
    if isinstance(x, list):
        return x
    try:
        return ast.literal_eval(x) if isinstance(x, str) else []
    except Exception:
        return []


d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)
old = pd.read_excel(FINAL)
old['_n'] = old['Title'].map(nrm)
ref = dict(zip(old['_n'], old['Refrence']))
pur = dict(zip(old['_n'], old['Main Purposes']))
aut = dict(zip(old['_n'], old['Author']))
d['_n'] = d['Title'].map(nrm)
d['Reference'] = d['_n'].map(ref)
d['Main purposes'] = d['_n'].map(pur)
d['First author'] = d['_n'].map(aut)

sw = pd.read_csv(SWT, encoding='utf-8-sig')
cat = dict(zip(sw['规范名称'], sw['类别']))
d['_soft_l'] = d['_soft2'].map(pl)

STUDY_LABEL = {'computational': 'Computational/simulation', 'in_vitro': 'In vitro/laboratory',
               'clinical': 'Clinical study', 'case_report': 'Case report',
               'technical_note': 'Technical note', 'educational': 'Educational'}
ARCH_LABEL = {1: 'Image-guided planning and procedure execution',
              2: 'Quantitative measurement and accuracy assessment of 3D data',
              3: 'Computational biomechanical simulation',
              4: 'Digital design and manufacturing',
              5: 'Morphometric and phenotypic analysis'}
CATNAME = {'MIP': 'Medical image processing',
           'GEN3D': 'General-purpose 3D modelling/rendering',
           'CAD': 'Engineering computer-aided design',
           'SIM': 'Engineering simulation (FEA/CFD)',
           'RE': 'Reverse engineering and metrology',
           'AM': 'Additive manufacturing / slicing',
           'PHOTO': 'Photogrammetry / 3D scanning',
           'RT': 'Real-time / XR engine',
           'SCI': 'Scientific imaging and analysis',
           'DICOM': 'DICOM viewer',
           '???': 'To verify',
           '?': 'To verify'}

studies = pd.DataFrame({
    'Reference': d['Reference'],
    'First author': d['First author'],
    'Title': d['Title'],
    'DOI': d['DOI'],
    'Journal': d['Journal'],
    'Year': d['Year'],
    'Country/region (ISO-3)': d['Region'],
    'Study design': d['study_type'].map(STUDY_LABEL),
    'Workflow archetype': d['Archetype'].map(ARCH_LABEL),
    'Dental speciality(ies)': d['Dental Specialty'],
    'Application scenario(s)': d['Application Scenario'],
    'Main purposes': d['Main purposes'],
    'Non-dental 3D software used': d['Software Used (fixed)'],
    'Software category(ies)': d['_soft_l'].map(
        lambda l: ';'.join(sorted({CATNAME.get(cat.get(s), str(cat.get(s))) for s in l}))),
})

glossary = sw[['规范名称', '类别', '原始开发领域', '开发商', '来源URL', 'URL状态', '研究数']].rename(
    columns={'规范名称': 'Software', '类别': 'Category',
             '原始开发领域': 'Original development domain', '开发商': 'Developer',
             '来源URL': 'Source (official product page)', 'URL状态': 'URL status',
             '研究数': 'Studies (n)'})
glossary['Category'] = glossary['Category'].map(lambda c: CATNAME.get(c, c))

# ---- 资格阶段剔除（47 条）----
audit = pd.read_csv(os.path.join(LOCK, '剔除清单_共44条.csv'), encoding='utf-8-sig')
extra = pd.DataFrame([
    {'序号': 947,
     'Title': 'Accuracy of dynamic computer-assisted implant surgery in fully edentulous patients',
     'Item Type': 'journalArticle', 'Date': '',
     '裁定理由': 'PDF verified: only dental-specific software (Navident / EvaluNav)',
     '审核轮次': 'PDF 核验'},
    {'序号': 1104,
     'Title': 'A Novel Virtual Planned-Orthodontic-Surgical Approach for Proportional Condylectomy',
     'Item Type': 'journalArticle', 'Date': '',
     '裁定理由': 'PDF verified: only dental-specific software (NEMOfab / Nemotec)',
     '审核轮次': 'PDF 核验'},
    {'序号': 318,
     'Title': "Modelling growth curves of the normal infant's mandible: 3D measurements",
     'Item Type': 'journalArticle', 'Date': '',
     '裁定理由': 'No full text available; software (Robins 3D) could not be verified',
     '审核轮次': 'PDF 核验'},
])
audit_all = pd.concat([audit[['序号', 'Title', 'Item Type', 'Date', '裁定理由', '审核轮次']],
                       extra], ignore_index=True)
audit_all = audit_all.sort_values('审核轮次', kind='stable')

notes = pd.DataFrame({'Item': [
    'Review question (PCC)',
    'Inclusion criteria',
    'Exclusion criteria',
    'Multi-label coding rule',
    'Screening corpus',
    'Screening procedure',
    'Language and date limits',
    'Full-text verification of software names',
    'Workflow archetypes',
    'Study-design classification',
    'Dataset version',
    'Search date',
], 'Definition / value': [
    'Population/Context: any discipline of dentistry. Concept: explicit use of non-dental 3D software. '
    'Context: peer-reviewed original research, technical notes and case reports.',
    'Peer-reviewed original research, technical notes or case reports; any dental discipline; explicit use of '
    'at least one non-dental 3D software package; English language; published between 2020-07-01 and 2026-06-30.',
    'Reviews (narrative, systematic, scoping, meta-analysis), editorials, commentaries, conference abstracts, '
    'preprints and video articles; topics outside dentistry; studies using only dental-specific software; '
    'studies without 3D data processing or modelling; records outside the prespecified date window.',
    'A study could be assigned to more than one dental speciality and to more than one application scenario. '
    'All speciality and scenario counts are therefore reported as study–speciality assignments alongside unique '
    'study counts; the denominator for percentages is the number of included studies (n = %d).' % N,
    '%d unique records after de-duplication of the %d records exported from Zotero (PubMed 1,727, '
    'Web of Science 1,605, IEEE Xplore 299).' % (S['N'] if False else 2556, 2572),
    'Title and abstract screening was performed with large-language-model assistance (three independent runs '
    'with identical prompts and decoding parameters). Exclusion reasons were assigned by a documented '
    'single-choice pass and are reported in the PRISMA diagram. Prompts, raw API responses, model metadata and '
    'decoding parameters are deposited in the public repository.',
    'The English-language restriction and the date window were applied at the database-search level and were '
    'not delegated to the language model.',
    'Software names were checked against full texts by reproducible text matching. Of the 516 included studies '
    'for which a full text was available, 455 (88.2%%) had every annotated software name found in the extracted '
    'text. This verifies the presence of the names only and does not verify the role or purpose of each package. '
    'Geomagic product names were re-coded from full texts (128 corrections).',
    'Workflow archetypes were derived by unsupervised clustering of structured metadata (six application '
    'scenarios and seven software families; Jaccard distance; average-linkage hierarchical clustering; '
    'k selected by silhouette). They are data-driven groupings and were neither predefined nor manually coded.',
    'Each included study was classified into one of six study designs by two independent model-assisted coding '
    'passes with 97.6%% raw agreement (kappa = 0.966). This figure describes coding stability rather than '
    'agreement between two human raters.',
    'Dataset v4 (locked); N = %d. Traceability of every dataset revision is provided in the provenance table.' % N,
    '2026-06-30 (databases); revision searches completed by 2026-07-31.',
]})

xlsx = os.path.join(OUTD, 'Supplementary_File_3.xlsx')
with pd.ExcelWriter(xlsx, engine='openpyxl') as w:
    studies.to_excel(w, sheet_name='1_Included studies', index=False)
    glossary.to_excel(w, sheet_name='2_Software glossary', index=False)
    audit_all.to_excel(w, sheet_name='3_Eligibility audit', index=False)
    notes.to_excel(w, sheet_name='4_Definitions and notes', index=False)
    wb = w.book
    WIDTH = {'Title': 58, 'DOI': 30, 'Journal': 26, 'Dental speciality(ies)': 30,
             'Application scenario(s)': 34, 'Main purposes': 40,
             'Non-dental 3D software used': 28, 'Software category(ies)': 32,
             'Workflow archetype': 34, 'Item': 34, 'Definition / value': 96,
             'Source (official product page)': 46, 'Original development domain': 34,
             '裁定理由': 60, 'Title': 58}
    for sname in wb.sheetnames:
        ws = wb[sname]
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(row=1, column=c)
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='1F4E78')
            cell.alignment = Alignment(vertical='center', wrap_text=True)
        ws.freeze_panes = 'A2'
        ws.row_dimensions[1].height = 30
        headers = [ws.cell(row=1, column=c).value for c in range(1, ws.max_column + 1)]
        for i, h in enumerate(headers, 1):
            ws.column_dimensions[get_column_letter(i)].width = WIDTH.get(h, 18)
print('已生成:', xlsx)
print('studies:', studies.shape, '| glossary:', glossary.shape, '| audit:', audit_all.shape)

# ---------------- 版本溯源表（交给专用脚本生成，保证与 v4 一致）----------------
import sys
import subprocess
_HERE = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, os.path.join(_HERE, '_tools_provenance_v4.py')], check=True)
print('版本溯源表: 由 _tools_provenance_v4.py 生成')
