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
_check_135_by_fulltext.py —— 对"同标准复核未通过"的纳入记录做确定性核查
不依赖模型：直接在整个 PDF（全部页）中检索
  (a) 该记录原先标注的软件名（来自 Software Used (fixed)）
  (b) 软件表中的全部规范名
判定：
  A 原标注软件名在全文出现  → 记录成立，模型只是未捕捉到
  B 仅出现其他非牙科3D软件  → 记录成立
  C 全文均未出现任何非牙科3D软件名 → 无法核实，需逐条裁决
输出：03_数据/08_分析用/纳入集复核_确定性核查.csv
"""
import os
import re
import pandas as pd
import pymupdf

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')

d = pd.read_csv(os.path.join(ANA, 'fulltext_pass',
                             'fulltext_included_parsed.csv'), low_memory=False)
ex = d[d['判定'].astype(str).str.upper().str.startswith('EXCLUDE')].copy()
print('待核查（模型判 EXCLUDE）:', len(ex))

v3 = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)


def nt(s):
    import unicodedata
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


v3['_nt'] = v3['Title'].map(nt)
ann = dict(zip(v3['_nt'], v3['Software Used (fixed)']))
pm = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '07_PDF与语料对照', 'pdf_match.csv'),
                 low_memory=False)
k2f = {}
for _, r in pm.iterrows():
    k = str(r.get('Key', '')).strip()
    if k and k != 'nan' and k not in k2f:
        k2f[k] = str(r['file'])
key2 = dict(zip(v3['_nt'], v3['Key']))

sw = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
ALLNAME = sorted({str(v).strip() for c in ('规范名称', '原始名称')
                  for v in sw[c].dropna() if len(str(v).strip()) >= 5},
                 key=len, reverse=True)
ALLRX = re.compile(r'(?<![A-Za-z])(?:' + '|'.join(re.escape(n) for n in ALLNAME) +
                   r')(?![A-Za-z])', re.I)

rows = []
for _, r in ex.iterrows():
    k = r['_nt']
    f = k2f.get(str(key2.get(k, '')))
    a = str(ann.get(k, '') or '')
    rec = {'Title': r['Title'], '_nt': k, '原标注软件': a, 'PDF': f}
    if not f:
        rec.update({'结论': 'C_无全文', '全文中出现的非牙科3D软件': ''})
        rows.append(rec)
        continue
    p = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'), f)
    if not os.path.exists(p):
        rec.update({'结论': 'C_文件缺失', '全文中出现的非牙科3D软件': ''})
        rows.append(rec)
        continue
    try:
        doc = pymupdf.open(p)
        txt = re.sub(r'\s+', ' ', '\n'.join(pg.get_text() for pg in doc))
        doc.close()
    except Exception:
        rec.update({'结论': 'C_读取失败', '全文中出现的非牙科3D软件': ''})
        rows.append(rec)
        continue
    found_all = sorted(set(m.group(0) for m in ALLRX.finditer(txt)))
    ann_names = [x.strip() for x in a.split(';') if x.strip()]
    hit_ann = [x for x in ann_names
               if re.search(r'(?<![A-Za-z])' + re.escape(x) + r'(?![A-Za-z])', txt, re.I)]
    if hit_ann:
        concl = 'A_原标注软件在全文出现'
    elif found_all:
        concl = 'B_全文出现其他非牙科3D软件'
    else:
        concl = 'C_全文未出现任何非牙科3D软件名'
    rec.update({'结论': concl, '全文中出现的非牙科3D软件': '; '.join(found_all[:12])})
    rows.append(rec)

out = pd.DataFrame(rows)
out.to_csv(os.path.join(ANA, '纳入集复核_确定性核查.csv'), index=False,
           encoding='utf-8-sig')
print(out['结论'].value_counts().to_string())
print('\nC 类（全文中确无任何非牙科3D软件名）：')
for _, r in out[out['结论'].str.startswith('C_全文未出现')].iterrows():
    print('   %-86s 原标注=%s' % (str(r['Title'])[:84], r['原标注软件']))
