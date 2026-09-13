# -*- coding: utf-8 -*-
"""Figure 4：四个多软件工作流原型（含软件共现经验频次）"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = r"d:\Desktop\v8 for JD"
OUT = os.path.join(ROOT, "05_图表")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})

fig, axes = plt.subplots(2, 2, figsize=(14, 9.6))
for ax in axes.ravel():
    ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis("off")

C1, C2, C3, C4 = "#dbe7f5", "#dff0e2", "#fdeadb", "#ece3f5"

def box(ax, x, y, w, h, txt, fc=C1, fs=8.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06", fc=fc, ec="#33475b", lw=0.9))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, linespacing=1.3)

def ar(ax, p1, p2, style="-|>", rad=0.0, color="#33475b"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=10, lw=0.9,
                                 color=color, connectionstyle=f"arc3,rad={rad}"))

# A. Prosthesis design and mechanical verification
ax = axes[0, 0]
ax.set_title("A  Prosthesis design and mechanical verification", fontsize=9.5, loc="left", fontweight="bold")
box(ax, 0.3, 5.2, 4.2, 1.1, "Scan data / digital impressions\n(Geomagic Wrap, GOM Inspect)")
box(ax, 5.5, 5.2, 4.2, 1.1, "Model preparation &\nreverse engineering", C2)
box(ax, 0.3, 3.2, 4.2, 1.1, "Prosthesis design\n(Blender, Meshmixer, Rhinoceros)", C2)
box(ax, 5.5, 3.2, 4.2, 1.1, "Biomechanical evaluation\n(ANSYS, ABAQUS, SolidWorks)", C4)
box(ax, 0.3, 1.2, 4.2, 1.1, "CAM / additive manufacturing\n(3D printing or milling)", C3)
box(ax, 5.5, 1.2, 4.2, 1.1, "Accuracy / quality control\n(Geomagic Control X, GOM Inspect)")
ar(ax, (4.5, 5.75), (5.5, 5.75)); ar(ax, (7.6, 5.2), (7.6, 4.3))
ar(ax, (5.5, 3.75), (4.5, 3.75)); ar(ax, (2.4, 3.2), (2.4, 2.3))
ar(ax, (4.5, 1.75), (5.5, 1.75)); ar(ax, (7.6, 2.3), (7.6, 3.2), rad=-0.35, color="#b03a2e")
ax.text(8.6, 2.75, "iterate", fontsize=7, color="#b03a2e", rotation=90)
ax.text(0.3, 0.35, "Supported by co-occurrence: ANSYS+SolidWorks n=22; ANSYS+Rhinoceros n=12; ANSYS+Geomagic Wrap n=9",
        fontsize=6.8, color="#555")

# B. Surgical planning and guide fabrication
ax = axes[0, 1]
ax.set_title("B  Surgical planning and guide fabrication", fontsize=9.5, loc="left", fontweight="bold")
box(ax, 0.3, 5.2, 4.2, 1.1, "Medical image segmentation\n(Mimics, 3D Slicer, ITK-SNAP)")
box(ax, 5.5, 5.2, 4.2, 1.1, "3D reconstruction &\nmesh refinement (3-Matic, Meshmixer)", C2)
box(ax, 0.3, 3.2, 4.2, 1.1, "Virtual surgical planning\n(Geomagic, Blender)", C2)
box(ax, 5.5, 3.2, 4.2, 1.1, "Guide / implant design\n(Meshmixer, Rhinoceros, SolidWorks)", C2)
box(ax, 0.3, 1.2, 4.2, 1.1, "Additive manufacturing\n(3D printing)", C3)
box(ax, 5.5, 1.2, 4.2, 1.1, "Intraoperative use /\nnavigation & validation")
ar(ax, (4.5, 5.75), (5.5, 5.75)); ar(ax, (7.6, 5.2), (7.6, 4.3))
ar(ax, (5.5, 3.75), (4.5, 3.75)); ar(ax, (2.4, 3.2), (2.4, 2.3))
ar(ax, (4.5, 1.75), (5.5, 1.75))
ax.text(0.3, 0.35, "Supported by co-occurrence: 3-Matic+Mimics n=26; Geomagic Wrap+Mimics n=17; 3D Slicer+ITK-SNAP n=13",
        fontsize=6.8, color="#555")

# C. Morphological analysis and research
ax = axes[1, 0]
ax.set_title("C  Morphological analysis and quantitative research", fontsize=9.5, loc="left", fontweight="bold")
box(ax, 0.3, 5.2, 4.2, 1.1, "3D models from\nmultiple sources (CBCT, IOS, scans)")
box(ax, 5.5, 5.2, 4.2, 1.1, "Registration / alignment\n(CloudCompare, Geomagic Wrap)", C2)
box(ax, 0.3, 3.2, 4.2, 1.1, "Deviation & shape analysis\n(Geomagic Design X, MeshLab, ITK-SNAP)", C2)
box(ax, 5.5, 3.2, 4.2, 1.1, "Custom computation\n(MATLAB, Python, statistical shape models)", C4)
box(ax, 0.3, 1.2, 4.2, 1.1, "Statistical comparison /\nmeasurement error")
box(ax, 5.5, 1.2, 4.2, 1.1, "Visualisation & reporting", C3)
ar(ax, (4.5, 5.75), (5.5, 5.75)); ar(ax, (7.6, 5.2), (7.6, 4.3))
ar(ax, (5.5, 3.75), (4.5, 3.75)); ar(ax, (2.4, 3.2), (2.4, 2.3))
ar(ax, (4.5, 1.75), (5.5, 1.75))
ax.text(0.3, 0.35, "Supported by co-occurrence: Geomagic Design X+Geomagic Wrap n=26; 3D Slicer+ITK-SNAP n=13",
        fontsize=6.8, color="#555")

# D. Dynamic visualisation
ax = axes[1, 1]
ax.set_title("D  Dynamic visualisation and education", fontsize=9.5, loc="left", fontweight="bold")
box(ax, 0.3, 5.2, 4.2, 1.1, "Anatomical / dental models\n(CBCT, IOS, 3D scans)")
box(ax, 0.3 + 5.2, 5.2, 4.2, 1.1, "Mesh preparation\n(Blender, Meshmixer)", C2)
box(ax, 0.3, 3.2, 4.2, 1.1, "Animation & rendering\n(Blender, KeyShot-like pipelines)", C3)
box(ax, 5.5, 3.2, 4.2, 1.1, "Real-time / XR environment\n(Unity, Unreal Engine)", C4)
box(ax, 0.3, 1.2, 9.4, 1.1, "Educational videos, interactive demonstrations, procedural guidance,\n"
                            "patient communication and immersive training", C3)
ar(ax, (4.5, 5.75), (5.5, 5.75)); ar(ax, (2.4, 5.2), (2.4, 4.3))
ar(ax, (7.6, 5.2), (7.6, 4.3)); ar(ax, (2.4, 3.2), (2.4, 2.3))
ar(ax, (7.6, 3.2), (7.6, 2.3))
ax.text(0.3, 0.35, "Least frequent archetype; co-occurrence 3D Slicer+Blender n=8; 3D Slicer+Meshmixer n=7",
        fontsize=6.8, color="#555")

fig.suptitle("Figure 4. Recurring multi-software workflow archetypes of nondental 3D software in dentistry (N = 569)",
             fontsize=11.5, y=0.985, fontweight="bold")
fig.text(0.01, 0.01, "Archetypes were derived from the functional role and execution order of the software reported in the included studies; "
         "the frequencies below each panel give the number of studies in which the corresponding software pair co-occurred, "
         "and 224/569 studies (39.4%) used more than one software package.",
         fontsize=7.0, color="#555")
fig.savefig(os.path.join(OUT, "Figure4_workflows.png"), dpi=600, bbox_inches="tight")
fig.savefig(os.path.join(OUT, "Figure4_workflows.pdf"), bbox_inches="tight")
print("saved Figure4_workflows")
