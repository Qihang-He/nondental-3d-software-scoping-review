# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_tools_cutlist47.py — 将 3 条时间窗剔除记录追加进剔除清单（41 -> 44 条）"""
import os
import pandas as pd

ROOT = _os.path.join(_ROOTP, '03_数据')
cut = pd.read_csv(os.path.join(ROOT, r'06_锁定数据集\剔除清单_共41条.csv'))
out = pd.read_csv(os.path.join(ROOT, r'08_分析用\窗口外剔除_3条.csv'))
v22 = pd.read_csv(os.path.join(ROOT, r'06_锁定数据集\最终数据集_v2.2.csv'),
                  low_memory=False)
m = v22[['序号', 'Title', 'Item Type', 'Date']].set_index('序号')

add = []
for _, r in out.iterrows():
    i = r['序号']
    reason = ('检索时间窗之外（%s；预设纳入窗为 2020-07-01 至 2026-06-30），'
              '严格按预设时间窗剔除' % r['_窗判定'])
    add.append({
        '序号': i,
        'Title': m.loc[i, 'Title'] if i in m.index else r['Title'],
        'Item Type': m.loc[i, 'Item Type'] if i in m.index else '',
        'Date': r['Date'],
        '裁定理由': reason,
        '审核轮次': '时间窗核验',
    })

cut2 = pd.concat([cut, pd.DataFrame(add)], ignore_index=True)
fp = os.path.join(ROOT, r'06_锁定数据集\剔除清单_共44条.csv')
cut2.to_csv(fp, index=False, encoding='utf-8-sig')
print('新剔除清单:', cut2.shape, '->', fp)
print(cut2['审核轮次'].value_counts().to_string())
print('613 -', len(cut2), '=', 613 - len(cut2))
