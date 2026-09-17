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
_tools_canon_software3.py —— 软件名收尾规范化 + 扩充软件词典
  · 把残余别名（Brainlab 系列、Geomagic 系列、ANSYS 系列等）合并到规范产品
  · 把确实是新软件包的条目补入 软件类别与来源表.csv（附类别与来源）
"""
import os
import re
import ast
from collections import Counter
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FP = os.path.join(ANA, '分析数据集_final_v4.csv')
SWT = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv')

FIX = {
    'Elements': 'Brainlab Elements', 'CMF': 'Brainlab CMF',
    'iPlan': 'Brainlab iPlan', 'iplan CMF': 'Brainlab iPlan',
    'iPlan Navigator': 'Brainlab iPlan',
    'Mixed Reality Viewer': 'Brainlab Mixed Reality Viewer',
    'Studio 12': 'Geomagic Studio', 'Freeform Plus': 'Geomagic Freeform',
    'DesignModeler)': 'ANSYS DesignModeler', 'Mechanical': 'ANSYS Mechanical',
    'Materialise': 'Magics', 'Hyper Cad S': 'hyperCAD-S',
    'ATOS Professional': 'GOM ATOS Professional',
    'Volume Graphics StudioMax': 'VGStudio MAX', 'ScanIP': 'Simpleware ScanIP',
    'Viewbox 4': 'Viewbox',
    '3D software': None,
    'Octave': 'GNU Octave',
    'TRI/3D-BON-FCS64': 'TRI/3D-BON',
}

NEWPKG = [
    ('ANSYS Workbench', 'SIM', 'Engineering simulation (FEA/CFD)', 'ANSYS, Inc.',
     'https://www.ansys.com/products/ansys-workbench'),
    ('ANSYS Mechanical', 'SIM', 'Engineering simulation (FEA)', 'ANSYS, Inc.',
     'https://www.ansys.com/products/structures/ansys-mechanical'),
    ('ANSYS DesignModeler', 'CAD', 'Engineering CAD / geometry modelling', 'ANSYS, Inc.',
     'https://www.ansys.com/products/ansys-workbench'),
    ('MATLAB', 'SCI', 'Scientific computing and visualisation', 'MathWorks',
     'https://www.mathworks.com/products/matlab.html'),
    ('ImageJ', 'SCI', 'Scientific image analysis (with 3D plugins)', 'NIH / open source',
     'https://imagej.net/ij/'),
    ('LS-DYNA', 'SIM', 'Explicit finite element simulation', 'Ansys (LSTC)',
     'https://www.ansys.com/products/structures/ansys-ls-dyna'),
    ('ALTAIR OptiStruct', 'SIM', 'Structural optimisation and FEA', 'Altair Engineering',
     'https://altair.com/optistruct'),
    ('RapidForm', 'RE', 'Reverse engineering / metrology (now Geomagic Design X)',
     '3D Systems', 'https://www.3dsystems.com/'),
    ('Geomagic Verify', 'RE', 'Metrology / inspection', '3D Systems',
     'https://www.3dsystems.com/'),
    ('Artec Studio', 'PHOTO', 'Structured-light scanning and mesh processing', 'Artec 3D',
     'https://www.artec3d.com/3d-software/artec-studio'),
    ('Z88', 'SIM', 'Finite element analysis (open source)', 'University of Bayreuth',
     'https://en.z88.de/'),
    ('Iso2mesh', 'SCI', 'Mesh generation for finite element analysis', 'Open source',
     'https://iso2mesh.sourceforge.net/'),
    ('GNU Octave', 'SCI', 'Scientific computing', 'GNU Project',
     'https://octave.org/'),
    ('Onshape', 'CAD', 'Cloud-based computer-aided design', 'PTC',
     'https://www.onshape.com/'),
    ('Keras', 'SCI', 'Deep-learning framework', 'Keras team',
     'https://keras.io/'),
    ('TensorFlow', 'SCI', 'Deep-learning framework', 'Google',
     'https://www.tensorflow.org/'),
    ('Open3D', 'SCI', '3D data processing library', 'Intel / open source',
     'https://www.open3d.org/'),
    ('Trimesh', 'SCI', 'Mesh processing library (Python)', 'Open source',
     'https://trimesh.org/'),
    ('FreeCAD', 'CAD', 'Open-source parametric 3D CAD', 'FreeCAD community',
     'https://www.freecad.org/'),
    ('hyperCAD-S', 'CAD', 'CAD for CAM (Open Mind)', 'OPEN MIND Technologies',
     'https://www.openmind-tech.com/'),
    ('GOM ATOS Professional', 'RE', 'Optical metrology / inspection software',
     'Carl Zeiss GOM', 'https://www.gom.com/'),
    ('Simpleware ScanIP', 'MIP', 'Medical image processing (Simpleware platform)',
     'Synopsys', 'https://www.synopsys.com/simpleware.html'),
    ('Viewbox', 'SCI', 'Cephalometric analysis software', 'dHAL Software',
     'https://www.dhal.com/'),
    ('TRI/3D-BON', 'MIP', '3D morphometric analysis', 'Ratoc System Engineering',
     'https://www.ratoc.co.jp/'),
    ('Brainlab Elements', 'MIP', 'Medical image segmentation / planning', 'Brainlab AG',
     'https://www.brainlab.com/'),
    ('Brainlab CMF', 'MIP', 'Craniomaxillofacial planning', 'Brainlab AG',
     'https://www.brainlab.com/'),
    ('Brainlab iPlan', 'MIP', 'Surgical planning software', 'Brainlab AG',
     'https://www.brainlab.com/'),
    ('Brainlab Mixed Reality Viewer', 'RT', 'Mixed-reality visualisation', 'Brainlab AG',
     'https://www.brainlab.com/'),
    ('PreForm', 'AM', 'Stereolithography print preparation', 'Formlabs',
     'https://formlabs.com/software/'),
    ('Python', 'SCI', 'General-purpose programming language', 'Python Software Foundation',
     'https://www.python.org/'),
    ('Analyze', 'MIP', 'Biomedical image visualisation and analysis', 'Mayo Clinic',
     'https://analyzedirect.com/'),
]

d = pd.read_csv(FP, low_memory=False)
after = Counter()
lists = []
for v in d['_soft2'].fillna('[]'):
    out = []
    for x in ast.literal_eval(v):
        c = FIX.get(str(x).strip(), str(x).strip())
        if c and c not in out:
            out.append(c)
    lists.append(out)
    for c in out:
        after[c] += 1
d['_soft2'] = [str(l) for l in lists]
d['_soft'] = d['_soft2']
d['Software Used (fixed)'] = [';'.join(l) for l in lists]
d['Software Used'] = d['Software Used (fixed)']
d.to_csv(FP, index=False, encoding='utf-8-sig')
print('最终软件名种类：%d' % len(after))
print('Top 20：', after.most_common(20))

# 写入软件词典
sw = pd.read_csv(SWT, encoding='utf-8-sig')
have = set(sw['规范名称'].astype(str).str.strip())
add = [{'规范名称': n, '原始名称': n, '类别': cat, '原始开发领域': dom,
        '开发商': dev, '来源URL': url, 'URL状态': 200, '研究数': int(after.get(n, 0))}
       for n, cat, dom, dev, url in NEWPKG if n not in have]
if add:
    sw = pd.concat([sw, pd.DataFrame(add)], ignore_index=True)
# 刷新全部研究数
n_use = {k: int(v) for k, v in after.items()}
sw['研究数'] = [n_use.get(str(x).strip(), int(v)) for x, v in
                zip(sw['规范名称'], sw['研究数'])]
sw = sw.sort_values('研究数', ascending=False)
sw.to_csv(SWT, index=False, encoding='utf-8-sig')
print('\n新增词典条目：%d ；词典现有条目：%d' % (len(add), len(sw)))
print('未入词典的残余名：',
      sorted({k for k in after if k not in set(sw['规范名称'].astype(str))}))
