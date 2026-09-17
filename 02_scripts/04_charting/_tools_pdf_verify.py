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
PDF 核验：检查锁定数据集中每篇文献所标注的软件名称是否真的出现在其全文 PDF 中
- 确定性字符串核验（可复现），输出逐篇/逐软件核验率
输出：03_数据/11_PDF核验/
"""
import os, re, ast, json, html
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "08_分析用")
PDFDIR = os.path.join(ROOT, "pdf")
MATCH = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "07_PDF与语料对照", "pdf_match.csv")
FULL = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "01_原始", "完整文献信息.csv")
OUTD = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "11_PDF核验")
os.makedirs(OUTD, exist_ok=True)

def nt(s): return re.sub(r"[^a-z0-9]+", "", str(s).lower())
def pl(x):
    try: return ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
    except Exception: return []

d = pd.read_csv(os.path.join(ANA, "分析数据集_572_定稿.csv"), encoding="utf-8-sig")
d["_n"] = d["Title"].map(nt); d["_soft"] = d["_soft"].map(pl)

# 完整文献信息.csv 行序 -> 标题（pdf_match 的 match_idx 即此序号）
full = pd.read_csv(FULL, encoding="gbk")
full["_n"] = full["Title"].map(nt)
idx2n = dict(zip(range(1, len(full) + 1), full["_n"]))

# PDF 文件 -> 语料序号
pm = pd.read_csv(MATCH)
pm = pm[pm["match_idx"].notna()]
n2file = {}
for _, r in pm.iterrows():
    k = idx2n.get(int(r["match_idx"]))
    if k and k not in n2file:
        n2file[k] = r["file"]
print("可用的 PDF 映射:", len(n2file))

# 软件名的检索别名（宽松匹配）
ALIAS = {
    "3D Slicer": ["3d slicer", "slicer", "slicer.org"], "Mimics": ["mimics", "materialise mimics"],
    "ANSYS": ["ansys", "workbench"], "Meshmixer": ["meshmixer"], "Geomagic Wrap": ["geomagic wrap", "geomagic"],
    "Geomagic Control X": ["geomagic control", "control x"], "Blender": ["blender"],
    "GOM Inspect": ["gom inspect", "gom "], "3-Matic": ["3-matic", "3matic", "3 matic"],
    "SolidWorks": ["solidworks", "solid works"], "Geomagic Design X": ["geomagic design", "design x"],
    "Rhinoceros": ["rhinoceros", "rhino3d", "rhino 3d", "rhino"], "ITK-SNAP": ["itk-snap", "itksnap", "itk snap"],
    "ABAQUS": ["abaqus"], "CloudCompare": ["cloudcompare", "cloud compare"], "MeshLab": ["meshlab"],
    "Magics": ["magics"], "HyperMesh": ["hypermesh"], "InVesalius": ["invesalius"], "CATIA": ["catia"],
    "SpaceClaim": ["spaceclaim"], "Fusion 360": ["fusion 360", "fusion360"], "Brainlab": ["brainlab"],
    "3D-DOCTOR": ["3d-doctor", "3d doctor"], "VRMesh": ["vrmesh"], "ZBrush": ["zbrush"],
    "Siemens NX (UG)": ["nx ", "unigraphics", "ug nx"], "Inventor": ["inventor"], "ALGOR": ["algor"],
    "Unity": ["unity"], "Simpleware": ["simpleware"], "Amira": ["amira"], "Geomagic Freeform": ["freeform"],
    "Solid Edge": ["solid edge"], "MeViSLab": ["mevislab"], "VGStudio MAX": ["vgstudio", "vg studio"],
    "Final Surface": ["final surface"], "Avizo": ["avizo"], "Netfabb": ["netfabb"], "MITK": ["mitk"],
    "OsiriX": ["osirix"], "COMSOL Multiphysics": ["comsol"], "AutoCAD": ["autocad"], "PolyWorks": ["polyworks"],
    "Meshroom": ["meshroom"], "HyperWorks": ["hyperworks"], "Cam HyperMill": ["hypermill"], "Marc": ["marc"],
    "ANSYS Polyflow": ["polyflow"], "Tinkercad": ["tinkercad"], "MOI": ["moi3d", "moi 3d"],
    "Cliniface": ["cliniface"], "ArtiSynth": ["artisynth"], "Scalismo Lab": ["scalismo"],
    "RadiAnt DICOM Viewer": ["radiant"], "Vectary": ["vectary"], "Reality Composer": ["reality composer"],
    "PrusaSlicer": ["prusaslicer"], "Simplify3D": ["simplify3d"], "Cura": ["cura"], "Geomagic Studio": ["geomagic studio"],
    "PowerShape": ["powershape"], "nTop": ["ntop"], "Creo": ["creo"], "Polycam": ["polycam"], "Calypso": ["calypso"],
    "SculptGL": ["sculptgl"], "ImFusion": ["imfusion"], "Scaniverse": ["scaniverse"], "KIRI Engine": ["kiri"],
    "PATRAN": ["patran"], "Horos": ["horos"], "Dragonfly": ["dragonfly"], "Unreal Engine": ["unreal"],
    "Digimizer": ["digimizer"], "R2 Gate": ["r2gate", "r2 gate"], "Geomagic (suite)": ["geomagic"],
    "Robins 3D": ["robins"], "EvaluNav": ["evalunav", "evalu nav"], "Midas": ["midas"],
    "CreatWare": ["creatware"], "NEMOfab": ["nemofab"],
}
NORM = {"Slicer": "3D Slicer", "SOLID EDGE": "Solid Edge", "Geomagic Control": "Geomagic Control X",
        "Geomagic Design": "Geomagic Design X", "Radiant": "RadiAnt DICOM Viewer", "Hyperworks": "HyperWorks",
        "ug": "Siemens NX (UG)", "Geomagic": "Geomagic (suite)"}

import fitz
rows = []
for _, r in d.iterrows():
    k = r["_n"]; softs = sorted(set(NORM.get(s, s) for s in r["_soft"]))
    f = n2file.get(k)
    if not f:
        rows.append({"ID": r["ID"], "Title": r["Title"][:90], "PDF": "", "核验": "无PDF",
                     "软件数": len(softs), "命中数": 0, "命中": "", "未命中": ";".join(softs)})
        continue
    p = os.path.join(PDFDIR, f)
    try:
        doc = fitz.open(p)
        txt = " ".join(pg.get_text() for pg in doc).lower()
        doc.close()
    except Exception as e:
        rows.append({"ID": r["ID"], "Title": r["Title"][:90], "PDF": f, "核验": f"读取失败:{str(e)[:20]}",
                     "软件数": len(softs), "命中数": 0, "命中": "", "未命中": ";".join(softs)})
        continue
    hit, miss = [], []
    for s in softs:
        al = ALIAS.get(s, [s.lower()])
        (hit if any(a in txt for a in al) else miss).append(s)
    rows.append({"ID": r["ID"], "Title": r["Title"][:90], "PDF": f,
                 "核验": "通过" if not miss else ("部分" if hit else "未命中"),
                 "软件数": len(softs), "命中数": len(hit), "命中": ";".join(hit), "未命中": ";".join(miss)})
res = pd.DataFrame(rows)
res.to_csv(os.path.join(OUTD, "PDF软件核验_逐篇.csv"), index=False, encoding="utf-8-sig")

withpdf = res[res["PDF"] != ""]
summary = {
    "N": len(res), "有PDF": int((res["PDF"] != "").sum()),
    "完全命中": int((res["核验"] == "通过").sum()),
    "部分命中": int((res["核验"] == "部分").sum()),
    "完全未命中": int((res["核验"] == "未命中").sum()),
    "核验通过率(有PDF且全部命中)": round((res["核验"] == "通过").sum() / max(1, len(withpdf)), 4),
}
json.dump(summary, open(os.path.join(OUTD, "PDF软件核验_汇总.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n文本提取诊断（前5个有PDF的样本）:")
c = 0
for _, r in d.iterrows():
    f = n2file.get(r["_n"])
    if not f: continue
    try:
        doc = fitz.open(os.path.join(PDFDIR, f)); txt = "".join(pg.get_text() for pg in doc); doc.close()
        print(f"  {len(txt):7d} chars | {f[:60]}")
    except Exception as e:
        print("  ERR", str(e)[:40], f[:50])
    c += 1
    if c >= 5: break
print("\n未命中最多的软件:")
mm = {}
for v in res["未命中"]:
    for s in str(v).split(";"):
        if s: mm[s] = mm.get(s, 0) + 1
print(pd.Series(mm).sort_values(ascending=False).head(15).to_string())
