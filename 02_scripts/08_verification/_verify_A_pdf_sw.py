# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_verify_A_pdf_sw.py —— 在 23、33 的 PDF 全文中查找被命名的第三方软件"""
import os
import re
import pymupdf

PDF = _os.path.join(_ROOTP, _os.path.join(_ROOTP, '10_全文PDF库'))
FILES = {
    23: 'Claus 等 - 2026 - Efficacy of Ai Enabled Software in Automatic Segmentation for Orthognathic Surgery.pdf',
    33: 'Wu 等 - 2023 - Influence of different education approaches on the implantation performance of dental practitioners.pdf',
}
SW = re.compile(r'\b(?:Mimics|3D\s?Slicer|Materialise|Meshmixer|Blender|Geomagic|GOM|'
                r'ANSYS|ABAQUS|SolidWorks|Rhinoceros|3-Matic|Simpleware|ITK-?SNAP|MITK|'
                r'CloudCompare|MeshLab|Amira|Avizo|Dolphin|ProPlan|SimPlant|Nobel|'
                r'coDiagnostiX|Exoplan|Blue\s?Sky|Romexis|RealGuid|Implant\s?Studio|'
                r'OnDemand3D|InVivo|Anatomage|Cybermed|Relu|Diagnocat|Overjet|Pearl|'
                r'Dentrix|Trios|iTero|Cura|Slic3r|PrusaSlicer|Chitubox|Magics|Netfabb|'
                r'MOI|Unity|Unreal|MATLAB|Python|PyTorch|TensorFlow|Keras|nnU-?Net|'
                r'U-?Net|YOLO|OpenCV|AutoCAD|Fusion\s?360|SketchUp|ZBrush|Photoshop)\b', re.I)
for n, f in FILES.items():
    fp = os.path.join(PDF, f)
    print('=' * 96)
    print('编号', n, '|', f)
    if not os.path.exists(fp):
        print('  文件不存在')
        continue
    doc = pymupdf.open(fp)
    txt = '\n'.join(p.get_text() for p in doc)
    doc.close()
    hits = sorted(set(m.group(0) for m in SW.finditer(txt)))
    print('  全文命中候选软件名:', hits if hits else '（无）')
    for h in hits:
        for m in list(SW.finditer(txt))[:0]:
            pass
        for m in re.finditer(re.escape(h), txt, re.I):
            s = max(0, m.start() - 110)
            print('   [%s] ...%s...' % (h, re.sub(r'\s+', ' ', txt[s:m.end() + 110])))
            break
    print('  全文长度: %d 字符' % len(txt))
