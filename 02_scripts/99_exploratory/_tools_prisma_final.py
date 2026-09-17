# -*- coding: utf-8 -*-
"""
_tools_prisma_final.py —— 汇总 PRISMA 排除原因，重写 PRISMA_链路.json
"""
import os
import json
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')

LBL = {1: 'R3_不属于口腔医学范畴',
       2: 'R2_文献类型不符（综述/社论/会议摘要等）',
       3: 'R4_未使用非牙科专用3D软件',
       4: 'R1_不在预设时间窗内',
       5: 'R7_其他或不可归类'}
SHORT = {'R3_不属于口腔医学范畴': 'Outside the scope of dentistry',
         'R2_文献类型不符（综述/社论/会议摘要等）':
             'Not an original research report (review, editorial, conference abstract)',
         'R4_未使用非牙科专用3D软件': 'No non-dental 3D software identified',
         'R1_不在预设时间窗内': 'Outside the prespecified date window',
         'R7_其他或不可归类': 'Other / not classifiable'}

rz = pd.read_csv(os.path.join(ANA, 'prisma_pass', 'reason_parsed.csv'), low_memory=False)
rz = rz.drop_duplicates('_nt')
print('已归类记录数:', len(rz), '（应为 1,943）')
print('未解析原因代码:', int(rz['原因代码'].isna().sum()))
rz['原因'] = rz['原因代码'].map(LBL).fillna('R7_其他或不可归类')
dist = rz['原因'].value_counts()

chain = {
    'identified_databases': {'PubMed': 1727, 'Web of Science': 1605,
                             'IEEE Xplore': 299, 'total': 3631},
    'duplicates_removed': 1075,
    'screened_title_abstract': 2556,
    'excluded_at_screening': int(len(rz)),
    'excluded_at_screening_by_reason': {k: int(v) for k, v in dist.items()},
    'excluded_at_screening_by_reason_en': {SHORT[k]: int(v) for k, v in dist.items()},
    'assessed_for_eligibility': 613,
    'excluded_after_assessment': 47,
    'excluded_after_assessment_breakdown': {
        'Not an original research report or other eligibility criteria (audits 1-2)': 41,
        'Software not verifiable / dental-specific software only (PDF verification)': 3,
        'Outside the prespecified date window': 3},
    'included_in_review': 566,
}
json.dump(chain, open(os.path.join(ANA, 'PRISMA_链路.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)

rz[['_nt', 'Key', 'Title', '原因代码', '原因']].to_csv(
    os.path.join(ANA, 'PRISMA_排除原因分类.csv'), index=False, encoding='utf-8-sig')
print(json.dumps(chain, ensure_ascii=False, indent=2))
