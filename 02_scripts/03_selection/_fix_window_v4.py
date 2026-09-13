# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_fix_window_v4.py —— 严格时间窗处理：移除日期晚于 2026-06-30 的记录"""
import os
import re
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FP = os.path.join(ANA, '分析数据集_final_v4.csv')

d = pd.read_csv(FP, low_memory=False)
bad = d[d['Half2'] == '2026-H2']
print('2026-H2（窗口外）：%d 条' % len(bad))
for _, r in bad.iterrows():
    print('   - %-78s Date=%s Year=%s' % (str(r['Title'])[:76], r['Date'], r['Year']))

if len(bad):
    d = d[~d['Half2'].isin(['2026-H2', '2027-H1', '2027-H2'])].copy()
    d['序号'] = range(1, len(d) + 1)
    d.to_csv(FP, index=False, encoding='utf-8-sig')
    pd.DataFrame([{'Title': t, 'action': 'REMOVED',
                   'reason': 'Published outside the prespecified date window (after 2026-06-30)'}
                  for t in bad['Title']]).to_csv(
        os.path.join(ANA, '时间窗外补充剔除_v4.csv'), index=False, encoding='utf-8-sig')
print('\n最终 N =', len(d))
print('Half2 分布：')
print(d['Half2'].value_counts().to_string())
