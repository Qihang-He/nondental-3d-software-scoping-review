# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_tools_fill_doi.py — 用 Crossref 标题检索补齐缺失 DOI（相似度 >=0.92 才采纳）"""
import os
import re
import json
import time
import unicodedata
import difflib
import pandas as pd
import requests

ANA = _os.path.join(_ROOTP, '03_数据', '08_分析用')
FP = os.path.join(ANA, '分析数据集_final_v3.csv')


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


d = pd.read_csv(FP)
miss = d[d['DOI'].isna() | (d['DOI'].astype(str).str.strip().isin(['', 'nan']))]
print('缺 DOI:', len(miss))

headers = {'User-Agent': 'ScopingReview/1.0 (mailto:author@example.org)'}
ev = []
fix = {}
for _, r in miss.iterrows():
    t = str(r['Title'])
    try:
        j = requests.get('https://api.crossref.org/works', headers=headers,
                         timeout=30, params={'query.bibliographic': t[:200],
                                             'rows': 5}).json()
    except Exception as e:
        ev.append({'序号': r['序号'], 'Title': t, 'DOI': '', '相似度': '', '备注': str(e)})
        continue
    best, bs = None, 0.0
    for it in j.get('message', {}).get('items', []):
        c = (it.get('title') or [''])
        c = c[0] if c else ''
        s = difflib.SequenceMatcher(None, nt(t), nt(c)).ratio()
        if s > bs:
            bs, best = s, it
    if best is not None and bs >= 0.92:
        doi = best.get('DOI', '')
        fix[r['序号']] = doi
        ev.append({'序号': r['序号'], 'Title': t, 'DOI': doi,
                   '相似度': round(bs, 3), '备注': '采纳'})
    else:
        ev.append({'序号': r['序号'], 'Title': t, 'DOI': '',
                   '相似度': round(bs, 3), '备注': '无可靠证据，留空'})
    time.sleep(0.4)

e = pd.DataFrame(ev)
e.to_csv(os.path.join(ANA, 'DOI补全_证据表.csv'), index=False, encoding='utf-8-sig')
print(e[['序号', 'DOI', '相似度', '备注']].to_string())

d['DOI'] = [fix.get(i, v) for i, v in zip(d['序号'], d['DOI'])]
d.to_csv(FP, index=False, encoding='utf-8-sig')
print('补全', len(fix), '条；仍缺', d['DOI'].isna().sum())
