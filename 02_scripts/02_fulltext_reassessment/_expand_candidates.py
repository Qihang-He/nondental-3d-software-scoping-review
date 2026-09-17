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
_expand_candidates.py —— 用"软件名优先"的证据抽取，为**全部 1,180 篇**被排除记录构建候选
（此前 879 篇只经过"关键词窗口"版本，证据可能被引言中的 software 一词占满而漏取方法学软件名）
输出：03_数据/08_分析用/final_pass/candidates_all.pkl
"""
import os
import re
import pandas as pd
import pymupdf

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FTP = os.path.join(ANA, 'fulltext_pass')


def nt(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


B = pd.read_csv(os.path.join(FTP, 'fulltext_parsed.csv'), low_memory=False)
B['_nt'] = B['_nt'].astype(str)
uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                               '筛选语料_唯一记录_2556.csv'), low_memory=False)
uni['_nt'] = uni['Title'].map(nt)
meta = uni.set_index('_nt')[['Item Type', 'Publication Title', 'Key',
                             'Abstract']].to_dict('index')
pm = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '07_PDF与语料对照', 'pdf_match.csv'),
                 low_memory=False)
k2f = {}
for _, r in pm.iterrows():
    k = str(r.get('Key', '')).strip()
    if k and k != 'nan' and k not in k2f:
        k2f[k] = str(r['file'])

sw = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
NAMES = sorted({str(v).strip() for c in ('规范名称', '原始名称')
                for v in sw[c].dropna() if len(str(v).strip()) >= 5},
               key=len, reverse=True)
NAME_RX = re.compile(r'(?<![A-Za-z])(?:' + '|'.join(re.escape(n) for n in NAMES) +
                     r')(?![A-Za-z])', re.I)
GEN_RX = re.compile(r'(software|program(?:me)?\b|version\s*[\d.]|reverse[- ]engineer|'
                    r'finite[- ]element|FEA\b|CAD\b|computer-aided|segmentation|'
                    r'registration|superimpos|STL\b|DICOM|point cloud|mesh\b)', re.I)

rows = []
for _, r in B.iterrows():
    k = r['_nt']
    m = meta.get(k, {})
    f = k2f.get(str(m.get('Key', '')))
    if not f:
        continue
    p = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'), f)
    if not os.path.exists(p):
        continue
    try:
        doc = pymupdf.open(p)
        txt = re.sub(r'\s+', ' ', '\n'.join(pg.get_text() for pg in doc[:30]))
        doc.close()
    except Exception:
        continue
    wins, seen = [], set()

    def add(mo):
        s = max(0, mo.start() - 320)
        e = min(len(txt), mo.end() + 320)
        key = (s // 200,)
        if key in seen:
            return
        seen.add(key)
        wins.append(txt[s:e])

    for mo in NAME_RX.finditer(txt):
        add(mo)
        if len(wins) >= 5:
            break
    if len(wins) < 5:
        for mo in GEN_RX.finditer(txt):
            add(mo)
            if len(wins) >= 7:
                break
    if not wins:
        continue
    rows.append({'Title': m.get('Key') and r['Title'] or r['Title'], '_nt': k,
                 '期刊': m.get('Publication Title'), 'Item Type': m.get('Item Type'),
                 'Key': m.get('Key'), '摘要': m.get('Abstract'),
                 '证据片段': ' ||| '.join(wins)[:6000], 'PDF': f,
                 'PassA': '', 'PassB': r['判定']})

out = pd.DataFrame(rows)
out.to_pickle(os.path.join(ANA, 'final_pass', 'candidates_all.pkl'))
print('全部候选：%d 条' % len(out))

# 合并已裁决结果，只保留尚未裁决的
fp = os.path.join(ANA, 'final_pass', 'final_parsed.csv')
done = set()
if os.path.exists(fp):
    done = set(pd.read_csv(fp, low_memory=False)['_nt'].astype(str))
todo = out[~out['_nt'].isin(done)]
todo.to_pickle(os.path.join(ANA, 'final_pass', 'candidates_todo.pkl'))
print('已裁决 %d ；待补裁决 %d' % (len(done & set(out['_nt'])), len(todo)))
