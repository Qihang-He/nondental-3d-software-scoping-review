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
_check_7_normalized.py —— 用**归一化字符串匹配**（去空格/连字符/大小写）重做确定性核查
解决 "Fusion360" vs "Fusion 360"、"AVIEW" vs "Avizo" 之类的写法差异导致的漏检。
匹配词表在软件表之外，补充常见逆向/建模/仿真/影像处理产品名。
"""
import os
import re
import pandas as pd
import pymupdf

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')

EXTRA = ['Rapidform', 'Fusion360', 'AVIEW', 'AVIEW Modeler', 'Solid Edge', 'RapidForm',
         'GeomagicDesignX', 'Geomagic Control X', 'Geomagic Studio', 'Geomagic Wrap',
         'Meshmixer', 'Magics', 'Blender', 'Rhinoceros', 'ANSYS', 'ABAQUS', 'Mimics',
         '3D Slicer', '3DSlicer', 'ITK-SNAP', 'ITKSNP', 'InVesalius', 'CloudCompare',
         'MeshLab', 'Avizo', 'Amira', 'VGStudio', 'MATLAB', 'COMSOL', 'HyperMesh',
         'ALGOR', 'SolidWorks', 'Solid Works', 'CATIA', 'Creo', 'Siemens NX', 'Inventor',
         'AutoCAD', 'ZBrush', 'Netfabb', 'Final Surface', 'PolyWorks', 'Geomagic',
         'Simpleware', 'Mimics Innovation Suite', '3-Matic', '3matic', 'OsiriX', 'MITK',
         'Brainlab', 'MeVisLab', 'Unity', 'Unreal', 'Open3D', 'Meshroom', 'GOM Inspect',
         'Cura', 'Simplify3D', 'PrusaSlicer', 'Formlabs Preform', 'Tinkercad',
         'PowerShape', 'SpaceClaim', 'Dragonfly', 'Scaniverse', 'Polycam', 'KIRI Engine']


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())


sw = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
NAMES = set(EXTRA)
for c in ('规范名称', '原始名称'):
    for v in sw[c].dropna():
        if len(str(v).strip()) >= 5:
            NAMES.add(str(v).strip())
NAMES_N = {n: norm(n) for n in NAMES if len(norm(n)) >= 6}

chk = pd.read_csv(os.path.join(ANA, '纳入集复核_确定性核查.csv'), low_memory=False)
sub = chk[chk['结论'].str.startswith('C_')].copy()
print('待重新核查：%d 篇\n' % len(sub))

verdict = []
for _, r in sub.iterrows():
    p = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'), str(r['PDF']))
    if not os.path.exists(p):
        verdict.append((r['Title'], r['原标注软件'], '无全文', ''))
        continue
    doc = pymupdf.open(p)
    txt = norm('\n'.join(pg.get_text() for pg in doc))
    doc.close()
    hits = [n for n, nn in NAMES_N.items() if nn in txt]
    verdict.append((r['Title'], r['原标注软件'],
                    '合格（全文含非牙科3D软件名）' if hits else '不合格（全文无任何非牙科3D软件名）',
                    '; '.join(sorted(set(hits))[:10])))

v = pd.DataFrame(verdict, columns=['Title', '原标注软件', '归一化核查结论', '全文出现的软件名'])
v.to_csv(os.path.join(ANA, '7篇归一化核查.csv'), index=False, encoding='utf-8-sig')
for _, r in v.iterrows():
    print('%-78s' % str(r['Title'])[:76])
    print('   原标注: %-26s 结论: %s' % (r['原标注软件'], r['归一化核查结论']))
    print('   全文软件名: %s' % r['全文出现的软件名'])
    print()
print(v['归一化核查结论'].value_counts().to_string())
