# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_check_included_review.py —— 汇总现有纳入集的同标准复核结果"""
import os
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
fp = os.path.join(ANA, 'fulltext_pass', 'fulltext_included_parsed.csv')
d = pd.read_csv(fp, low_memory=False)
print('复核记录数:', len(d))
print(d['判定'].value_counts(dropna=False).to_dict())
ex = d[d['判定'].astype(str).str.upper().str.startswith('EXCLUDE')]
print('\n判为 EXCLUDE（可能需剔除）:', len(ex))
for _, r in ex.iterrows():
    print('  -', str(r['Title'])[:88])
    print('     理由:', str(r['判定理由'])[:200])
d.to_csv(os.path.join(ANA, '全文再筛查_原纳入集复核_全量.csv'), index=False,
         encoding='utf-8-sig')
d[d['判定'].astype(str).str.upper().str.startswith('INCLUDE')].to_csv(
    os.path.join(ANA, '全文再筛查_原纳入集复核.csv'), index=False, encoding='utf-8-sig')
print('\n[v3 纳入集 566 中，可复核 %d 篇；其中未通过 %d 篇；无可获取全文 %d 篇]'
      % (len(d), len(ex), 566 - len(d)))
