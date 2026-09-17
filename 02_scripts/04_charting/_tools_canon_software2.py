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
_tools_canon_software2.py —— 软件名规范化（第二版，更强）
问题：模型返回的软件名常带版本号与厂商前缀（"3-matic 13.0"、"ALTAIR HyperMesh"、
      "Autodesk Meshmixer"、"Geomagic Studio 12"），导致"软件包数"虚高。
做法：
  1) 去版本号、去厂商前缀、统一大小写与符号
  2) 以"规范产品清单"（软件词典 + 常见补充）为对齐目标，按最长优先包含匹配
  3) 未匹配者保留原名并单列，供人工确认后并入词典
"""
import os
import re
import ast
from collections import Counter
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FP = os.path.join(ANA, '分析数据集_final_v4.csv')

sw = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
CANON = sorted({str(x).strip() for x in sw['规范名称'].dropna()} |
               {'RapidForm', 'AVIEW Modeler', 'Fusion 360', 'Tinkercad', 'PreForm',
                'ImageJ', 'Artec Studio', 'FreeCAD', 'Geomagic Verify',
                'ALTAIR OptiStruct', 'ANSYS Workbench', 'ANSYS SpaceClaim',
                'Solid Edge', 'RapidForm XOR', 'Rhino', 'ZBrush', 'Geomagic Control',
                'Geomagic Design X', 'Geomagic (unspecified)'},
               key=len, reverse=True)

VENDOR = ['Autodesk', 'ALTAIR', 'Altair', 'ANSYS', 'Ansys', 'Geomagic', '3D Systems',
          'Materialise', 'Brainlab', 'BrainLAB', 'Dassault', 'Siemens', 'Carl Zeiss',
          'GOM', 'Thermo Fisher', 'Coreline', 'Bruker', 'Amira', 'FEI']
VER = re.compile(r'\b(v|version)?\s*20\d\d(\.\d+)*\b|\b(v|version)?\s*\d+(\.\d+)+\b'
                 r'|\b(v|Version)\s*\d+\b', re.I)


def key(s):
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())


CANON_KEY = [(c, key(c)) for c in CANON]


def strip_noise(x):
    x = str(x).strip()
    x = VER.sub(' ', x)
    x = re.sub(r'[\(（][^)）]*[\)）]', ' ', x)      # 去括号补充（含厂商/版本）
    for v in VENDOR:
        x = re.sub(r'^\s*' + re.escape(v) + r'\s+', '', x, flags=re.I)
    return re.sub(r'\s+', ' ', x).strip(' -_,;')


ALIAS = {'geomagiccontrol': 'Geomagic Control X', 'geomagic': 'Geomagic (unspecified)',
         'slicer': '3D Slicer', 'ug': 'Siemens NX (UG)', 'nx': 'Siemens NX (UG)',
         'hyperworks': 'HyperWorks', 'hypermesh': 'HyperMesh', 'radiant': 'RadiAnt DICOM Viewer',
         '3matic': '3-Matic', 'meshlab': 'MeshLab', 'cloudcompare': 'CloudCompare',
         'gominsect': 'GOM Inspect', 'gominspect': 'GOM Inspect', 'rhino': 'Rhinoceros',
         'rhinoceros': 'Rhinoceros', 'fusion360': 'Fusion 360',
         'autodeskfusion360': 'Fusion 360', 'autodeskfusion': 'Fusion 360',
         'meshmixer': 'Meshmixer', 'rapidform': 'RapidForm', 'aviewmodeler': 'AVIEW Modeler',
         'fijiimagej': 'ImageJ', 'fiji': 'ImageJ', 'imagej': 'ImageJ',
         'altairhypermesh': 'HyperMesh', 'altairoptistruct': 'ALTAIR OptiStruct',
         'ansysworkbench': 'ANSYS Workbench', 'ansysspaceclaim': 'ANSYS SpaceClaim',
         'spaceclaim': 'SpaceClaim', 'creoparametric': 'Creo', 'freecad': 'FreeCAD',
         'artecstudio': 'Artec Studio', 'analyse': 'Analyze'}


def canon(x):
    raw = str(x).strip()
    s = strip_noise(raw)
    k = key(s)
    if k in ALIAS:
        return ALIAS[k]
    if k in dict((key(c), c) for c in CANON):
        return dict((key(c), c) for c in CANON)[k]
    # 最长优先的包含匹配
    for c, ck in CANON_KEY:
        if len(ck) >= 4 and (ck in k or k in ck):
            return c
    return s if s else raw


d = pd.read_csv(FP, low_memory=False)
before = Counter()
for v in d['_soft2'].fillna('[]'):
    for x in ast.literal_eval(v):
        before[str(x).strip()] += 1
print('规范化前：%d 种写法' % len(before))

lists = []
after = Counter()
for v in d['_soft2'].fillna('[]'):
    out = []
    for x in ast.literal_eval(v):
        c = canon(x)
        if c and c not in out:
            out.append(c)
    lists.append(out)
    for c in out:
        after[c] += 1
d['_soft2'] = [str(l) for l in lists]
d['_soft'] = d['_soft2']
d['Software Used (fixed)'] = [';'.join(l) for l in lists]
d['Software Used'] = d['Software Used (fixed)']

print('规范化后：%d 种写法' % len(after))
print('\nTop 25：')
for k, n in after.most_common(25):
    print('   %-32s %d' % (k, n))
GL = set(sw['规范名称'].astype(str).str.strip())
miss = sorted([k for k in after if k not in GL], key=lambda x: -after[x])
print('\n仍不在词典中的（%d 种，多为厂商专有平台或需人工合并）：' % len(miss))
for k in miss:
    print('   %-36s %d' % (k, after[k]))

d.to_csv(FP, index=False, encoding='utf-8-sig')
pd.DataFrame(after.most_common(), columns=['软件', '研究数']).to_csv(
    os.path.join(ANA, '软件规范名清单_v4.csv'), index=False, encoding='utf-8-sig')
print('\n已写回', FP)
