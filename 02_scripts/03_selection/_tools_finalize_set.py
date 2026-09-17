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
_tools_finalize_set.py —— 生成最终纳入集修订记录
  · v3 的 566 篇中，有 4 篇经归一化全文核查确认：存档全文中不含任何具名第三方非牙科3D软件，
    软件无法核实 → 剔除
  · 另有 3 篇原标注软件名与全文写作不一致（Rapidform/AVIEW Modeler/Fusion 360），核实后保留，
    并修正软件标注
  · 再补入全文再筛查确认合格的 304 篇
输出：03_数据/08_分析用/最终纳入集修订记录.csv
      03_数据/08_分析用/软件标注修正_3条.csv
"""
import os
import re
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')

v7 = pd.read_csv(os.path.join(ANA, '7篇归一化核查.csv'), low_memory=False)
drop = v7[v7['归一化核查结论'].str.startswith('不合格')].copy()
keep = v7[v7['归一化核查结论'].str.startswith('合格')].copy()

rows = []
for _, r in drop.iterrows():
    rows.append({'Title': r['Title'],
                 'action': 'REMOVED',
                 'reason': ('软件无法核实：存档全文（含图表文字）中不含任何具名第三方非牙科3D软件；'
                            '原注释标注为 %s，未能在全文中得到证实' % r['原标注软件']),
                 'software_found_in_fulltext': r['全文出现的软件名']})
for _, r in keep.iterrows():
    rows.append({'Title': r['Title'],
                 'action': 'RETAINED',
                 'reason': ('软件核实成立；全文中出现的实际产品名与注释不同：%s'
                            % r['全文出现的软件名']),
                 'software_found_in_fulltext': r['全文出现的软件名']})
rev = pd.DataFrame(rows)
rev.to_csv(os.path.join(ANA, '最终纳入集修订记录.csv'), index=False, encoding='utf-8-sig')

fix = keep[['Title', '原标注软件', '全文出现的软件名']].rename(
    columns={'全文出现的软件名': '应修正为'})
fix.to_csv(os.path.join(ANA, '软件标注修正_3条.csv'), index=False, encoding='utf-8-sig')

print('剔除 %d 篇：' % len(drop))
for t in drop['Title']:
    print('   -', str(t)[:88])
print('\n保留并修正软件标注 %d 篇：' % len(keep))
for _, r in fix.iterrows():
    print('   %-70s %s -> %s' % (str(r['Title'])[:68], r['原标注软件'], r['应修正为']))
print('\n预计最终 N = %d - %d + 304 = %d' % (566, len(drop), 566 - len(drop) + 304))
