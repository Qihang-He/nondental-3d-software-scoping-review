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
_reconcile_passes.py —— 比对两轮全文判定，统计分歧，构造最终裁决的候选并集
  Pass A：260 条（软件表名命中）→ 257 INCLUDE
  Pass B：1,180 条（关键词窗口）→ 134 INCLUDE
分歧原因：Pass B 的证据片段按文档顺序取前 7 个关键词窗口，可能被引言中的
          "software" 占满而未取到方法学中的具体软件名 → 需按"软件名优先"重建证据。
输出：03_数据/08_分析用/final_pass/candidates.pkl
"""
import os
import re
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FTP = os.path.join(ANA, 'fulltext_pass')

A = pd.read_csv(os.path.join(ANA, 'rescreen_pass', 'rescreen_parsed.csv'), low_memory=False)
A['_nt'] = A['_nt'].astype(str)
AIN = set(A.loc[A['判定'].str.upper().str.startswith('INCLUDE'), '_nt'])

B = pd.read_csv(os.path.join(FTP, 'fulltext_parsed.csv'), low_memory=False)
B['_nt'] = B['_nt'].astype(str)
BIN = set(B.loc[B['判定'].str.upper().str.startswith('INCLUDE'), '_nt'])
BEX = set(B.loc[B['判定'].str.upper().str.startswith('EXCLUDE'), '_nt'])

print('Pass A INCLUDE: %d' % len(AIN))
print('Pass B INCLUDE: %d' % len(BIN))
print('两者一致 INCLUDE: %d' % len(AIN & BIN))
print('A 纳入 / B 排除（需复核）: %d' % len(AIN & BEX))
print('B 纳入 / A 未判（B 独有）: %d' % len(BIN - AIN))
U = AIN | BIN
print('并集: %d' % len(U))

# 为并集重建"软件名优先"的证据片段
import pymupdf
uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                               '筛选语料_唯一记录_2556.csv'), low_memory=False)


def nt(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


uni['_nt'] = uni['Title'].map(nt)
meta = uni.set_index('_nt')[['Item Type', 'Publication Title', 'Key', 'Abstract']].to_dict('index')
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

titles = {}
for df in (A, B):
    for _, r in df.iterrows():
        titles.setdefault(r['_nt'], r['Title'])

rows = []
for k in U:
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

    def add(mo, before=320, after=320):
        s = max(0, mo.start() - before)
        e = min(len(txt), mo.end() + after)
        key = (s // 200,)
        if key in seen:
            return
        seen.add(key)
        wins.append(txt[s:e])

    for mo in NAME_RX.finditer(txt):          # 软件名优先，最多 5 段
        add(mo)
        if len(wins) >= 5:
            break
    if len(wins) < 5:
        for mo in GEN_RX.finditer(txt):       # 再补通用关键词，最多补到 7 段
            add(mo)
            if len(wins) >= 7:
                break
    if not wins:
        continue
    rows.append({'Title': titles[k], '_nt': k, '期刊': m.get('Publication Title'),
                 'Item Type': m.get('Item Type'), 'Key': m.get('Key'),
                 '摘要': m.get('Abstract'),
                 '证据片段': ' ||| '.join(wins)[:6000], 'PDF': f,
                 'PassA': 'INCLUDE' if k in AIN else '',
                 'PassB': 'INCLUDE' if k in BIN else 'EXCLUDE'})

out = pd.DataFrame(rows)
os.makedirs(os.path.join(ANA, 'final_pass'), exist_ok=True)
out.to_pickle(os.path.join(ANA, 'final_pass', 'candidates.pkl'))
print('\n最终裁决候选（有全文、有证据片段）：%d 条' % len(out))
print(out[['PassA', 'PassB']].value_counts().to_string())
