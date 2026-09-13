# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""核查归属不明的软件：出现在哪些研究、是否同时使用其他非牙科软件"""
import os, ast
import pandas as pd

ROOT = _ROOTP
d = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "08_分析用", "分析数据集_572_定稿.csv"), encoding="utf-8-sig")
def pl(x):
    try: return ast.literal_eval(x) if isinstance(x, str) else []
    except Exception: return []
d["_soft"] = d["_soft"].map(pl)

UNKNOWN = ["R2 Gate", "Robins 3D", "EvaluNav", "Midas", "CreatWare", "NEMOfab"]
KNOWN_NONDENTAL = {"Mimics", "3D Slicer", "ANSYS", "Meshmixer", "Geomagic Wrap", "Geomagic Control X",
                   "Blender", "GOM Inspect", "3-Matic", "SolidWorks", "Geomagic Design X", "Rhinoceros",
                   "ITK-SNAP", "ABAQUS", "CloudCompare", "MeshLab", "Magics", "HyperMesh", "InVesalius",
                   "CATIA", "SpaceClaim", "Fusion 360", "Brainlab", "3D-DOCTOR", "VRMesh", "ZBrush",
                   "Inventor", "Unity", "Simpleware", "Amira", "MITK", "OsiriX", "AutoCAD", "PolyWorks",
                   "Meshroom", "Tinkercad", "Voxel", "Avizo", "Netfabb", "Horos", "Dragonfly", "Unreal Engine",
                   "RadiAnt DICOM Viewer", "SculptGL", "Scaniverse", "KIRI Engine", "Polycam", "Vectary"}
for u in UNKNOWN:
    sub = d[d["_soft"].map(lambda l: u in l)]
    print(f"=== {u} : {len(sub)} 篇 ===")
    for _, r in sub.iterrows():
        others = [s for s in r["_soft"] if s != u]
        has_known = any(s in KNOWN_NONDENTAL for s in others)
        print(f"  [{'保留' if has_known else '⚠仅此软件'}] {str(r['Title'])[:66]}")
        print(f"        全部软件: {';'.join(r['_soft'])}")
    print()
