# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_rq3_summarize_v4.py —— 按最终纳入集（863）重算 RQ3 频次汇总"""
import os
import json
from collections import Counter
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')

d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)
keys = set(d['Key'].astype(str))
N = len(d)

rq = pd.read_csv(os.path.join(ANA, 'rq3_pass', 'rq3_parsed.csv'), low_memory=False)
rq['Key'] = rq['Key'].astype(str)
rq = rq[rq['Key'].isin(keys)].drop_duplicates('Key').copy()
print('RQ3 覆盖 %d / %d' % (len(rq), N))

old = json.load(open(os.path.join(ANA, 'RQ3_频次汇总.json'), encoding='utf-8'))
LAB = {}
for grp in old.values():
    if isinstance(grp, list):
        for e in grp:
            if isinstance(e, dict) and 'code' in e:
                LAB[e['code']] = e.get('label', '')
print('已载入标签 %d 个' % len(LAB))

miss = sorted(keys - set(rq['Key']))
if miss:
    print('未覆盖 %d 条：' % len(miss))
    for k in miss:
        t = d[d['Key'].astype(str) == k]['Title'].iloc[0]
        print('   %s  %s' % (k, str(t)[:70]))


def tally(col, denom):
    c = Counter()
    for v in rq[col].fillna(''):
        for x in str(v).replace('，', ',').split(','):
            x = x.strip()
            if x and x.lower() != 'nan':
                c[x] += 1
    out = [{'code': k, 'label': LAB.get(k, ''), 'n': n,
            'pct': round(n / denom * 100, 1)} for k, n in c.most_common()]
    return out


res = {
    'N_analysed': len(rq),
    'N_included': N,
    'n_studies': len(rq),
    'n_included_total': N,
    'advantages': tally('优势', len(rq)),
    'challenges': tally('挑战', len(rq)),
    'gaps': tally('缺口', len(rq)),
}
json.dump(res, open(os.path.join(ANA, 'RQ3_频次汇总.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
for k in ('advantages', 'challenges', 'gaps'):
    print('\n==', k)
    for e in res[k]:
        print('   %-4s %-52s %4d  %5.1f%%' % (e['code'], e['label'][:52], e['n'], e['pct']))
rq.to_csv(os.path.join(ANA, 'RQ3_编码明细_863.csv'), index=False, encoding='utf-8-sig')
