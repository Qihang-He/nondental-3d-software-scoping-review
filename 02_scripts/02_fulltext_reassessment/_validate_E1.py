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
_validate_E1.py —— 对 E1 判定做人工可读的抽样验证：打印真实上下文供逐条判读
"""
import os
import re
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
fr = pd.read_csv(os.path.join(ANA, 'triage_pass', 'candidates.pkl')
                 if False else os.path.join(ANA, 'triage_pass', 'triage_parsed.csv'),
                 low_memory=False)
cand = pd.read_pickle(os.path.join(ANA, 'triage_pass', 'candidates.pkl'))
m = cand.set_index('_nt')[['摘要', '上下文']].to_dict('index')

E1 = fr[fr['判定'] == 'E1'].copy()
E1['_nt'] = E1['_nt'].astype(str)
cand['_nt'] = cand['_nt'].astype(str)
E1 = E1.merge(cand[['_nt', '摘要', '上下文']], on='_nt', how='left')

rng = __import__('numpy').random.default_rng(7)
idx = rng.choice(len(E1), size=14, replace=False)
for i in idx:
    r = E1.iloc[i]
    print('=' * 104)
    print('题名:', r['Title'])
    print('期刊:', r['期刊'], '| 类型:', r['Item Type'], '| 流程原因:', r['流程原因'])
    print('AI理由:', str(r['理由'])[:160])
    print('摘要(前420):', str(r['摘要'])[:420].replace('\n', ' '))
    print('--- 全文软件上下文 ---')
    for seg in str(r['上下文']).split(' ||| ')[:3]:
        print('   *', seg[:420])
    print()
