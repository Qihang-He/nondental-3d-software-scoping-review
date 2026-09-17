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
_excluded_fulltext_screen.py
系统筛查：在"筛查阶段被排除"的记录中，用可复现的全文文本匹配找出**全文确实提到
非牙科3D软件**的记录（与纳入集使用完全相同的匹配方法）。
目的：把抽样核验升级为全量系统核查，避免仅凭抽样估计漏排数。
输出：03_数据/08_分析用/排除集全文软件命中.csv + 汇总
"""
import os
import re
import json
import unicodedata
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
PDF = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


# 软件名集合：来自软件表（85 种）；使用词边界匹配，并剔除过短/易误命中的名字
sw = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
SKIP = {'Materials', 'Interface', 'Solid', 'Studio', 'Design', 'Control', 'Doctor',
        'Space', 'Tools', 'Model', 'Guide', 'ProPlan', 'Horos', 'InVesalius',
        'Cura', 'Marc', 'Algor', 'Inventor', 'Unity', 'MOI', 'Warp', 'Wrap',
        'Ansys', 'Abaqus', 'Slicer', 'Plasticity', 'FreeCAD', 'Rhinoceros'}
NAMES = set()
for c in ('规范名称', '原始名称'):
    for v in sw[c].dropna():
        v = str(v).strip()
        if len(v) >= 5 and v not in SKIP:
            NAMES.add(v)
# 少数短名用更具体的写法
NAMES |= {'Geomagic Wrap', 'Geomagic Studio', 'Geomagic Control X', 'Geomagic Design X',
          'Meshmixer', 'Magics', 'Mimics', 'Blender', 'CloudCompare', 'MeshLab',
          'SolidWorks', 'MATLAB', 'Rhinoceros', 'AutoCAD', 'Fusion 360', 'ZBrush'}
NAMES = sorted({n for n in NAMES if len(n) >= 5}, key=len, reverse=True)
PAT = re.compile(r'(?<![A-Za-z])(?:' + '|'.join(re.escape(n) for n in NAMES) +
                 r')(?![A-Za-z])', re.I)
print('用于匹配的软件名 %d 个' % len(NAMES))
print('示例:', NAMES[:12])

# 排除集
rz = pd.read_csv(os.path.join(ANA, 'prisma_pass', 'reason_parsed.csv'),
                 low_memory=False).drop_duplicates('_nt')
LBL = {1: 'Outside the scope of dentistry',
       2: 'Not an original research report',
       3: 'No non-dental 3D software identified',
       4: 'Outside the prespecified date window',
       5: 'Other / not classifiable'}
rz['原因'] = rz['原因代码'].map(LBL)

uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                               '筛选语料_唯一记录_2556.csv'), low_memory=False)
uni['_nt'] = uni['Title'].map(nt)
meta = uni.set_index('_nt')[['Item Type', 'Publication Title', 'Date', 'Key',
                             'Abstract']].to_dict('index')
rz['Item Type'] = rz['_nt'].map(lambda k: meta.get(k, {}).get('Item Type'))
rz['期刊'] = rz['_nt'].map(lambda k: meta.get(k, {}).get('Publication Title'))
rz['Key'] = rz['_nt'].map(lambda k: meta.get(k, {}).get('Key'))

pm = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '07_PDF与语料对照', 'pdf_match.csv'),
                 low_memory=False)
k2f = {}
for _, r in pm.iterrows():
    k = str(r.get('Key', '')).strip()
    if k and k != 'nan' and k not in k2f:
        k2f[k] = str(r['file'])
rz['PDF'] = rz['Key'].astype(str).map(k2f)

import pymupdf
rows = []
n_pdf = 0
for _, r in rz.iterrows():
    f = r['PDF']
    if not isinstance(f, str) or not f:
        continue
    fp = os.path.join(PDF, f)
    if not os.path.exists(fp):
        continue
    n_pdf += 1
    try:
        doc = pymupdf.open(fp)
        txt = '\n'.join(p.get_text() for p in doc[:40])
        doc.close()
    except Exception:
        continue
    hits = sorted(set(m.group(0) for m in PAT.finditer(txt)))
    if hits:
        rows.append({'Title': r['Title'], '期刊': r['期刊'], 'Item Type': r['Item Type'],
                     '流程原因': r['原因'], '命中软件': '; '.join(hits),
                     'PDF': f, '_nt': r['_nt']})

out = pd.DataFrame(rows)
out.to_csv(os.path.join(ANA, '排除集全文软件命中.csv'), index=False, encoding='utf-8-sig')
print('排除集 %d 条；其中 %d 条可匹配到 PDF；全文命中软件名的 %d 条'
      % (len(rz), n_pdf, len(out)))
print()
if len(out):
    print('按流程原因分布：')
    print(out['流程原因'].value_counts().to_string())
    print('\n前 40 条：')
    for _, r in out.head(40).iterrows():
        print('  [%s] %s | %s' % (r['流程原因'][:14], str(r['命中软件'])[:46],
                                  str(r['Title'])[:74]))
