# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""建立软件主表：规范化名称 + 类别 + 原始开发领域 + 来源(URL) + 校验"""
import os, json, ast, time
import pandas as pd, requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "08_分析用")
OUTD = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "09_软件表")
os.makedirs(OUTD, exist_ok=True)

d = pd.read_csv(os.path.join(ANA, "分析数据集_final.csv"), encoding="utf-8-sig")
def pl(x):
    try: return ast.literal_eval(x) if isinstance(x, str) else []
    except Exception: return []
cnt = {}
for l in d["_soft"].map(pl):
    for s in set(l): cnt[s] = cnt.get(s, 0) + 1

# 名称规范化（合并变体）
NORM = {"Slicer": "3D Slicer", "SOLID EDGE": "Solid Edge", "Geomagic Control": "Geomagic Control X",
        "Geomagic Design": "Geomagic Design X", "Radiant": "RadiAnt DICOM Viewer",
        "Hyperworks": "HyperWorks", "ug": "Siemens NX (UG)", "Geomagic": "Geomagic (suite)"}
# 类别 / 开发领域 / 开发商 / 来源URL
# 类别: MIP=医学影像处理, GEN3D=通用3D建模, CAD=工程CAD, SIM=工程仿真, RE=逆向工程与计量,
#       AM=增材制造/切片, PHOTO=摄影测量/扫描, RT=实时/XR引擎, SCI=科学计算与影像分析, DICOM=DICOM 阅片
SW = {
 "Mimics": ("MIP", "Medical image processing", "Materialise", "https://www.materialise.com/en/medical/mimics-innovation-suite/mimics"),
 "3D Slicer": ("MIP", "Medical image processing / academic", "Slicer Community (BWH/Harvard)", "https://www.slicer.org"),
 "ANSYS": ("SIM", "Engineering simulation (FEA/CFD)", "ANSYS, Inc.", "https://www.ansys.com"),
 "Meshmixer": ("GEN3D", "General-purpose 3D modeling", "Autodesk", "https://meshmixer.com"),
 "Geomagic Wrap": ("RE", "Reverse engineering & metrology", "3D Systems", "https://www.3dsystems.com/software/geomagic-wrap"),
 "Geomagic Control X": ("RE", "Reverse engineering & metrology", "3D Systems", "https://www.3dsystems.com/software/geomagic-control-x"),
 "Blender": ("GEN3D", "General-purpose 3D modeling / animation", "Blender Foundation", "https://www.blender.org"),
 "GOM Inspect": ("RE", "Industrial metrology / 3D inspection", "GOM GmbH (Zeiss)", "https://www.gom.com"),
 "3-Matic": ("MIP", "Medical image processing / design (Materialise)", "Materialise", "https://www.materialise.com/en/medical/software/3-matic"),
 "SolidWorks": ("CAD", "Engineering CAD", "Dassault Systemes", "https://www.solidworks.com"),
 "Geomagic Design X": ("RE", "Reverse engineering", "3D Systems", "https://www.3dsystems.com/software/geomagic-design-x"),
 "Rhinoceros": ("GEN3D", "General-purpose 3D NURBS modeling", "Robert McNeel & Associates", "https://www.rhino3d.com"),
 "ITK-SNAP": ("MIP", "Medical image processing / academic", "ITK-SNAP (Univ. of Pennsylvania)", "https://www.itksnap.org"),
 "ABAQUS": ("SIM", "Engineering simulation (FEA)", "Dassault Systemes (SIMULIA)", "https://www.3ds.com/products/simulia/abaqus"),
 "CloudCompare": ("RE", "Point-cloud / 3D processing (open source)", "CloudCompare / EDF R&D", "https://www.cloudcompare.org"),
 "MeshLab": ("GEN3D", "Mesh processing (open source)", "ISTI-CNR", "https://www.meshlab.net"),
 "Magics": ("AM", "Additive manufacturing data preparation", "Materialise", "https://www.materialise.com/en/industrial/software/magics"),
 "HyperMesh": ("SIM", "Engineering simulation pre-/post-processing", "Altair", "https://altair.com/hypermesh"),
 "InVesalius": ("MIP", "Medical image processing (open source)", "Renato Archer CTI", "https://invesalius.github.io"),
 "CATIA": ("CAD", "Engineering CAD", "Dassault Systemes", "https://www.3ds.com/products/catia"),
 "SpaceClaim": ("CAD", "Engineering direct modeling CAD", "ANSYS", "https://www.ansys.com/products/3d-design/ansys-spaceclaim"),
 "Fusion 360": ("CAD", "Engineering CAD/CAM", "Autodesk", "https://www.autodesk.com/products/fusion-360"),
 "Brainlab": ("MIP", "Medical navigation / planning", "Brainlab AG", "https://www.brainlab.com"),
 "3D-DOCTOR": ("MIP", "Medical image processing", "Able Software Corp.", "http://www.3d-doctor.com"),
 "VRMesh": ("RE", "Reverse engineering / mesh processing", "VirtualGrid", "https://www.vrmesh.com"),
 "ZBrush": ("GEN3D", "Digital sculpting", "Maxon (Pixologic)", "https://www.maxon.net/en/zbrush"),
 "Siemens NX (UG)": ("CAD", "Engineering CAD/CAM", "Siemens Digital Industries", "https://plm.sw.siemens.com/en-US/nx/"),
 "Inventor": ("CAD", "Engineering CAD", "Autodesk", "https://www.autodesk.com/products/inventor"),
 "ALGOR": ("SIM", "Engineering simulation (FEA)", "Autodesk (formerly ALGOR)", "https://www.autodesk.com"),
 "Unity": ("RT", "Real-time engine / XR", "Unity Technologies", "https://unity.com"),
 "Simpleware": ("MIP", "Medical image processing & FEA meshing", "Synopsys", "https://www.synopsys.com/simpleware.html"),
 "Amira": ("SCI", "Scientific/medical 3D visualization", "Thermo Fisher Scientific", "https://www.thermofisher.com/amira-avizo"),
 "Geomagic Freeform": ("RE", "Haptic 3D design / reverse engineering", "3D Systems", "https://www.3dsystems.com/software/geomagic-freeform"),
 "Solid Edge": ("CAD", "Engineering CAD", "Siemens Digital Industries", "https://solidedge.siemens.com"),
 "MeViSLab": ("MIP", "Medical image processing (open source)", "MeVis Medical Solutions / Fraunhofer MEVIS", "https://www.mevislab.de"),
 "VGStudio MAX": ("RE", "Industrial CT analysis & metrology", "Volume Graphics", "https://www.volumegraphics.com"),
 "Final Surface": ("RE", "Mesh processing / reverse engineering", "Final Surface", "https://www.final-surface.com"),
 "Avizo": ("SCI", "Scientific 3D imaging & analysis", "Thermo Fisher Scientific", "https://www.thermofisher.com/amira-avizo"),
 "Netfabb": ("AM", "Additive manufacturing preparation", "Autodesk", "https://www.autodesk.com/products/netfabb"),
 "MITK": ("MIP", "Medical image processing (open source)", "German Cancer Research Center (DKFZ)", "https://www.mitk.org"),
 "OsiriX": ("DICOM", "DICOM viewer / medical imaging", "Pixmeo SARL", "https://www.osirix-viewer.com"),
 "COMSOL Multiphysics": ("SIM", "Multiphysics simulation", "COMSOL, Inc.", "https://www.comsol.com"),
 "AutoCAD": ("CAD", "Engineering CAD", "Autodesk", "https://www.autodesk.com/products/autocad"),
 "PolyWorks": ("RE", "Industrial metrology", "InnovMetric", "https://www.innovmetric.com"),
 "Meshroom": ("PHOTO", "Photogrammetry (open source)", "AliceVision", "https://alicevision.org/#meshroom"),
 "HyperWorks": ("SIM", "Engineering simulation suite", "Altair", "https://altair.com"),
 "Cam HyperMill": ("CAD", "CAM / NC machining", "OPEN MIND Technologies", "https://www.openmind-tech.com"),
 "Marc": ("SIM", "Nonlinear FEA simulation", "MSC Software (Hexagon)", "https://www.mscsoftware.com/product/marc"),
 "ANSYS Polyflow": ("SIM", "CFD simulation", "ANSYS, Inc.", "https://www.ansys.com/products/fluids/ansys-polyflow"),
 "Tinkercad": ("GEN3D", "Web-based 3D modeling", "Autodesk", "https://www.tinkercad.com"),
 "MOI": ("GEN3D", "NURBS modeling (MoI 3D)", "Triple Squid Software Design", "https://moi3d.com"),
 "Cliniface": ("SCI", "3D facial image analysis (open source)", "Cliniface (Curtin University)", "https://cliniface.org"),
 "ArtiSynth": ("SIM", "Biomechanical simulation (open source)", "University of British Columbia", "https://www.artisynth.org"),
 "Scalismo Lab": ("SCI", "Statistical shape modeling (open source)", "University of Basel", "https://scalismo.org"),
 "RadiAnt DICOM Viewer": ("DICOM", "DICOM viewer", "Medixant", "https://www.radiantviewer.com"),
 "Vectary": ("GEN3D", "Web-based 3D modeling", "Vectary", "https://www.vectary.com"),
 "Reality Composer": ("RT", "Augmented reality authoring", "Apple Inc.", "https://developer.apple.com/augmented-reality/"),
 "PrusaSlicer": ("AM", "3D printing slicer (open source)", "Prusa Research", "https://www.prusa3d.com/prusaslicer/"),
 "Simplify3D": ("AM", "3D printing slicer", "Simplify3D", "https://www.simplify3d.com"),
 "Cura": ("AM", "3D printing slicer (open source)", "Ultimaker", "https://ultimaker.com/software/ultimaker-cura/"),
 "Geomagic (suite)": ("RE", "Reverse engineering & metrology (product family)", "3D Systems", "https://www.3dsystems.com/software"),
 "Geomagic Studio": ("RE", "Reverse engineering & metrology (legacy)", "3D Systems", "https://www.3dsystems.com/software"),
 "PowerShape": ("CAD", "CAM/CAD for toolmaking", "Autodesk", "https://www.autodesk.com/products/powershape"),
 "nTop": ("CAD", "Implicit modeling / engineering design", "nTopology", "https://www.ntop.com"),
 "Creo": ("CAD", "Engineering CAD", "PTC", "https://www.ptc.com/en/products/creo"),
 "Polycam": ("PHOTO", "Photogrammetry app", "Polycam", "https://poly.cam"),
 "Calypso": ("RE", "Coordinate metrology", "ZEISS", "https://www.zeiss.com/metrology"),
 "SculptGL": ("GEN3D", "Web-based digital sculpting (open source)", "Stephane Ginier", "https://stephaneginier.com/sculptgl/"),
 "ImFusion": ("MIP", "Medical imaging software", "ImFusion GmbH", "https://www.imfusion.com"),
 "Scaniverse": ("PHOTO", "3D scanning app", "Niantic", "https://scaniverse.com"),
 "KIRI Engine": ("PHOTO", "Photogrammetry app", "KIRI Innovation", "https://www.kiriengine.app"),
 "PATRAN": ("SIM", "FEA pre-/post-processing", "MSC Software (Hexagon)", "https://www.mscsoftware.com/product/patran"),
 "Horos": ("DICOM", "DICOM viewer (open source)", "Horos Project", "https://horosproject.org"),
 "Dragonfly": ("SCI", "CT/imaging analysis", "Object Research Systems (ORS)", "https://www.theobjects.com/dragonfly"),
 "Unreal Engine": ("RT", "Real-time engine / XR", "Epic Games", "https://www.unrealengine.com"),
 "Digimizer": ("SCI", "Image measurement & analysis", "MedCalc Software", "https://www.digimizer.com"),
 "Geomagic Qualify": ("RE", "Industrial 3D inspection / metrology (legacy)", "3D Systems", "https://www.3dsystems.com/software"),
 "Midas": ("SIM", "General-purpose finite element analysis (MIDAS FX+)", "MIDAS IT / Brunleys", "https://www.midasit.com"),
 "R2 Gate": ("DENTAL", "Dental implant surgical guide software (dental-specific; not counted as nondental)", "MegaGen Implant", "https://www.megagen.co.kr"),
 # 需人工核验（疑似牙科专用/工具不明）
 "R2 Gate": ("???", "TO VERIFY (suspected dental-specific implant guide software)", "MegaGen", "https://www.megagen.co.kr"),
 "Robins 3D": ("???", "TO VERIFY", "", ""),
 "EvaluNav": ("???", "TO VERIFY", "", ""),
 "Midas": ("???", "TO VERIFY (Midas NFX FEA or other)", "", ""),
 "CreatWare": ("???", "TO VERIFY", "", ""),
 "NEMOfab": ("???", "TO VERIFY", "", ""),
}

rows, session = [], requests.Session()
for name, n in sorted(cnt.items(), key=lambda x: -x[1]):
    canon = NORM.get(name, name)
    meta = SW.get(canon) or SW.get(name)
    if meta is None:                                  # 大小写不敏感回退
        low = {k.lower(): v for k, v in SW.items()}
        meta = low.get(str(canon).lower()) or low.get(str(name).lower())
    if meta is None and "unspecified" in str(canon).lower():
        meta = ("RE", "Geomagic product family (specific module not specified in full text)", "3D Systems", "https://www.3dsystems.com/software")
    if meta:
        cat, dom, dev, url = meta
    else:
        cat, dom, dev, url = "?", "MISSING ENTRY", "", ""
    status = ""
    if url:
        try:
            r = session.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
            status = r.status_code
        except Exception as e:
            status = f"ERR:{str(e)[:30]}"
    rows.append({"原始名称": name, "规范名称": canon, "类别": cat, "原始开发领域": dom,
                 "开发商": dev, "来源URL": url, "URL状态": status, "研究数": n})
t = pd.DataFrame(rows)
t.to_csv(os.path.join(OUTD, "软件类别与来源表.csv"), index=False, encoding="utf-8-sig")
print("软件数:", len(t))
print("类别分布:", t["类别"].value_counts().to_dict())
print("URL 校验:", pd.Series([str(s).split(":")[0] for s in t["URL状态"]]).value_counts().to_dict())
print("\n待核验/异常:")
print(t[(t["类别"] == "?") | (t["URL状态"] != 200)][["原始名称", "类别", "开发商", "URL状态"]].to_string(index=False))
