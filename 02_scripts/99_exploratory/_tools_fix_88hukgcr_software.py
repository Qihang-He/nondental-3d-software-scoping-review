# -*- coding: utf-8 -*-
"""
_tools_fix_88hukgcr_software.py —— 规范化 88HUKGCR 的软件名为软件表规范名称。

背景：88HUKGCR 扩展时写入了 "VRMesh Studio" 与 "Algor"，但软件表规范名称为
"VRMesh"（RE）与 "ALGOR"（SIM）。本脚本把它们改为规范名称，保证 112→110 个去重软件包，
并使这两个软件能被正确计入软件功能族。
"""
import os
import shutil
import pandas as pd

ROOT = os.environ.get('SCOPING_ROOT') or r'd:\Desktop\v8 for JD'
P = os.path.join(ROOT, '03_数据', '08_分析用', '分析数据集_final_v5.csv')
BAK = os.path.join(ROOT, '03_数据', '08_分析用', '分析数据集_final_v5_backup_pre_canon.csv')

d = pd.read_csv(P, low_memory=False)
r = d[d['Key'] == '88HUKGCR']
assert len(r) == 1, '应恰好一条 88HUKGCR'

shutil.copy2(P, BAK)
print('已备份：', os.path.basename(BAK))

REMAP = {'VRMesh Studio': 'VRMesh', 'Algor': 'ALGOR'}


def fix_list(v):
    lst = eval(v) if isinstance(v, str) else list(v)
    return [REMAP.get(s, s) for s in lst]


def fix_fixed(v):
    if not isinstance(v, str):
        return v
    return ';'.join(REMAP.get(s.strip(), s.strip()) for s in v.split(';'))


idx = d['Key'] == '88HUKGCR'
d.loc[idx, '_soft2'] = d.loc[idx, '_soft2'].map(fix_list)
d.loc[idx, 'Software Used (fixed)'] = d.loc[idx, 'Software Used (fixed)'].map(fix_fixed)

d.to_csv(P, index=False, encoding='utf-8-sig')
print('88HUKGCR _soft2 =', d.loc[idx, '_soft2'].iloc[0])
print('88HUKGCR Software Used (fixed) =', d.loc[idx, 'Software Used (fixed)'].iloc[0])

# 验证去重软件包数
softs = set()
for v in d['_soft2']:
    softs.update(eval(v) if isinstance(v, str) else v)
print('去重软件包数 =', len(softs))
print('未在软件表中的软件 =', [
    s for s in softs
    if s not in set(pd.read_csv(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'))['规范名称'])
])
