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
_tools_canon_software.py —— 软件名称规范化（统一大小写与别名），保证"软件包数"口径一致
规则：
 1) 已知别名映射到规范名（如 Geomagic Control -> Geomagic Control X；Slicer -> 3D Slicer）
 2) 其余按"去掉非字母数字并小写"后的键归并，展示名取出现次数最多/最规范者
 3) 输出更新后的 v4 数据集、规范名清单、以及需新增到软件词典的新包
"""
import os
import re
import ast
import json
from collections import Counter, defaultdict
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FP = os.path.join(ANA, '分析数据集_final_v4.csv')

ALIAS = {
    'geomagiccontrol': 'Geomagic Control X',
    'geomagic': 'Geomagic (unspecified)',
    'slicer': '3D Slicer',
    'ug': 'Siemens NX (UG)',
    'hyperworks': 'HyperWorks',
    'radiant': 'RadiAnt DICOM Viewer',
    'solid edge': 'Solid Edge',
    'mimics': 'Mimics',
    '3matic': '3-Matic',
    'meshlab': 'MeshLab',
    'cloudcompare': 'CloudCompare',
    'itksnap': 'ITK-SNAP',
    'gominsect': 'GOM Inspect',
    'gominspect': 'GOM Inspect',
    'solidworks': 'SolidWorks',
    'rhinoceros': 'Rhinoceros',
    'fusion360': 'Fusion 360',
    'pslice': 'PrusaSlicer',
    'prusaslicer': 'PrusaSlicer',
    'simplify3d': 'Simplify3D',
    'vgstudiomax': 'VGStudio MAX',
    'autocad': 'AutoCAD',
    'blender': 'Blender',
    'magics': 'Magics',
    'ansys': 'ANSYS',
    'abaqus': 'ABAQUS',
    'comsolmultiphysics': 'COMSOL Multiphysics',
    'hypermesh': 'HyperMesh',
    'algor': 'ALGOR',
    'creo': 'Creo',
    'catia': 'CATIA',
    'inventor': 'Inventor',
    'zbrush': 'ZBrush',
    'netfabb': 'Netfabb',
    'final surface': 'Final Surface',
    'finalsurface': 'Final Surface',
    'polyworks': 'PolyWorks',
    'simpleware': 'Simpleware',
    'avizo': 'Avizo',
    'amira': 'Amira',
    'osirix': 'OsiriX',
    'mitk': 'MITK',
    'brainlab': 'Brainlab',
    'brain lab': 'Brainlab',
    'mevislab': 'MeVisLab',
    'unity': 'Unity',
    'unrealengine': 'Unreal Engine',
    'meshmixer': 'Meshmixer',
    'geomagicwrap': 'Geomagic Wrap',
    'geomagicstudio': 'Geomagic Studio',
    'geomagicdesignx': 'Geomagic Design X',
    'geomagicfreeform': 'Geomagic Freeform',
    'geomagicqualify': 'Geomagic Qualify',
    '3dslicer': '3D Slicer',
    'invesalius': 'InVesalius',
    '3ddoctor': '3D-DOCTOR',
    '3d-doctor': '3D-DOCTOR',
    'vrmesh': 'VRMesh',
    'spaceclaim': 'SpaceClaim',
    'powershape': 'PowerShape',
    'camhypermill': 'Cam HyperMill',
    'ansyspolyflow': 'ANSYS Polyflow',
    'scalismo lab': 'Scalismo Lab',
    'scalismolab': 'Scalismo Lab',
    'realitycomposer': 'Reality Composer',
    'kirieddittngine': 'KIRI Engine',
    'kiriengine': 'KIRI Engine',
    'dragronfly': 'Dragonfly',
    'dragonfly': 'Dragonfly',
    'tinkercad': 'Tinkercad',
    'moi': 'MOI',
    'cliniface': 'Cliniface',
    'artisynth': 'Artisynth',
    'vectary': 'Vectary',
    'cura': 'Cura',
    'midas': 'Midas',
    'r2gate': 'R2 Gate',
    'polycam': 'Polycam',
    'calypso': 'Calypso',
    'sculptgl': 'SculptGL',
    'imfusion': 'ImFusion',
    'scaniverse': 'Scaniverse',
    'patran': 'PATRAN',
    'horos': 'Horos',
    'creatware': 'CreatWare',
    'digimizer': 'Digimizer',
    'matlab': 'MATLAB',
    'autodesk meshmixer': 'Meshmixer',
    'geomagic controlx': 'Geomagic Control X',
    'unigraphics': 'Siemens NX (UG)',
    'siemens nx': 'Siemens NX (UG)',
    'nx': 'Siemens NX (UG)',
    'preform': 'PreForm',
    'formlabsp reform': 'PreForm',
    'formlabs preform': 'PreForm',
}

d = pd.read_csv(FP, low_memory=False)
sw = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
GLOSS = set(sw['规范名称'].astype(str).str.strip())


def key(s):
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())


# 统计原始写法
cnt = Counter()
for v in d['_soft2'].fillna('[]'):
    try:
        for x in ast.literal_eval(v):
            x = str(x).strip()
            if x:
                cnt[x] += 1
    except Exception:
        pass
print('规范化前不同写法：%d' % len(cnt))

# 构建映射
key_best = {}
for name, n in cnt.most_common():
    k = key(name)
    if k in ALIAS:
        continue
    if k not in key_best:
        key_best[k] = name


def canon_name(x):
    x = str(x).strip()
    k = key(x)
    if k in ALIAS:
        return ALIAS[k]
    if x in GLOSS:
        return x
    return key_best.get(k, x)


def canon_list(v):
    try:
        lst = ast.literal_eval(v)
    except Exception:
        return []
    out = []
    for x in lst:
        c = canon_name(x)
        if c and c not in out:
            out.append(c)
    return out


d['_soft2'] = d['_soft2'].fillna('[]').map(lambda v: str(canon_list(v)))
d['_soft'] = d['_soft2']
d['_soft2'] = d['_soft2'].map(lambda v: str(canon_list(v)))     # 再保证唯一
d['Software Used (fixed)'] = d['_soft2'].map(
    lambda v: ';'.join(ast.literal_eval(v)))
d['Software Used'] = d['Software Used (fixed)']

newcnt = Counter()
for v in d['_soft2']:
    for x in ast.literal_eval(v):
        newcnt[x] += 1
print('规范化后不同写法：%d' % len(newcnt))
print('\nTop 20：')
for k, n in newcnt.most_common(20):
    print('   %-30s %d' % (k, n))
missing = [k for k in newcnt if k not in GLOSS]
print('\n不在软件词典中的新包（%d 个）：' % len(missing))
for k in sorted(missing):
    print('   %-30s %d 篇' % (k, newcnt[k]))

d.to_csv(FP, index=False, encoding='utf-8-sig')
pd.DataFrame(newcnt.most_common(), columns=['软件', '研究数']).to_csv(
    os.path.join(ANA, '软件规范名清单_v4.csv'), index=False, encoding='utf-8-sig')
print('\n已写回', FP)
