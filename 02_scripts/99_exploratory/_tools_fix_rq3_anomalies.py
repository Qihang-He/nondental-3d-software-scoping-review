# -*- coding: utf-8 -*-
"""
_tools_fix_rq3_anomalies.py —— 修正 RQ3 编码中“空码+实码”的异常混合。

规则：A9/C9/G9 是“未报告”占位码，不应与其他实码（A1-A8 / C1-C8 / G1-G8）并存。
发现 3 条优势异常 + 1 条挑战异常，移除冗余的空码后重算汇总。
"""
import os
import shutil
import pandas as pd

ROOT = os.environ.get('SCOPING_ROOT') or r'd:\Desktop\v8 for JD'
P = os.path.join(ROOT, '03_数据', '08_分析用', 'rq3_pass', 'rq3_parsed.csv')
BAK = os.path.join(ROOT, '03_数据', '08_分析用', 'rq3_pass', 'rq3_parsed_backup_pre_fix.csv')

shutil.copy2(P, BAK)
rq = pd.read_csv(P, low_memory=False)
rq['Key'] = rq['Key'].astype(str)

FIX = {
    '8FWPXUE2': {'优势': 'A5', '挑战': 'C4', '缺口': 'G1,G2'},
    'ZAXSXJM9': {'优势': 'A1', '挑战': 'C4', '缺口': 'G1,G4'},
    '8HPQKBVZ': {'优势': 'A5', '挑战': 'C4', '缺口': 'G1,G4'},
}
for k, vals in FIX.items():
    m = rq['Key'] == k
    assert m.sum() == 1, 'Key %s 应唯一' % k
    for col, v in vals.items():
        rq.loc[m, col] = v
    print('fixed', k, vals)

rq.to_csv(P, index=False, encoding='utf-8-sig')
print('saved', os.path.basename(P))
