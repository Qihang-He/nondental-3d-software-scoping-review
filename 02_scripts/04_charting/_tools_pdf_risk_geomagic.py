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
PDF 复核：
(A) 4 篇"仅用归属不明软件"的研究——提取上下文，判断是否牙科专用
(B) Geomagic 系列混标修正——从全文检测实际使用的 Geomagic 产品
输出：03_数据/11_PDF核验/
"""
import os, re, ast, json
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "08_分析用")
PDFDIR = os.path.join(ROOT, "pdf")
MATCH = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "07_PDF与语料对照", "pdf_match.csv")
FULL = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "01_原始", "完整文献信息.csv")
OUTD = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "11_PDF核验")
os.makedirs(OUTD, exist_ok=True)
import fitz

def nt(s): return re.sub(r"[^a-z0-9]+", "", str(s).lower())
def pl(x):
    try: return ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
    except Exception: return []

d = pd.read_csv(os.path.join(ANA, "分析数据集_572_定稿.csv"), encoding="utf-8-sig")
d["_n"] = d["Title"].map(nt); d["_soft"] = d["_soft"].map(pl)

full = pd.read_csv(FULL, encoding="gbk"); full["_n"] = full["Title"].map(nt)
idx2n = dict(zip(range(1, len(full) + 1), full["_n"]))
pm = pd.read_csv(MATCH); pm = pm[pm["match_idx"].notna()]
n2file = {}
for _, r in pm.iterrows():
    k = idx2n.get(int(r["match_idx"]))
    if k and k not in n2file: n2file[k] = r["file"]

def text_of(k):
    f = n2file.get(k)
    if not f: return "", ""
    try:
        doc = fitz.open(os.path.join(PDFDIR, f))
        t = " ".join(pg.get_text() for pg in doc); doc.close()
        return re.sub(r"\s+", " ", t).lower(), f
    except Exception:
        return "", f

GEOM = {"Geomagic Wrap": "geomagic wrap", "Geomagic Design X": ["geomagic design x", "geomagic designx", "geomagic design"],
        "Geomagic Control X": ["geomagic control x", "geomagic controlx", "geomagic control"],
        "Geomagic Studio": "geomagic studio", "Geomagic Freeform": "geomagic freeform",
        "Geomagic Qualify": "geomagic qualify", "Geomagic Sculpt": "geomagic sculpt"}

# ---------- (A) 4 篇高危 ----------
RISK = {0: None}
risk_titles = ["splinted complete arch implant", "Modelling growth curves of the normal infant",
               "Accuracy of dynamic computer-assisted implant surgery", "Novel Digital Technique for Measuring the Accuracy",
               "Virtual Planned-Orthodontic-Surgical Approach"]
print("=" * 70)
print("(A) 高危文献 PDF 复核")
print("=" * 70)
for _, r in d.iterrows():
    if any(t.lower() in str(r["Title"]).lower() for t in risk_titles):
        txt, f = text_of(r["_n"])
        print(f"\n### {str(r['Title'])[:80]}")
        print(f"    标注软件: {';'.join(r['_soft'])} | PDF: {f[:60] if f else '无'}")
        if not txt:
            print("    (无全文，需人工)")
            continue
        for term in ["evalunav", "evalu nav", "nemofab", "nemo fab", "robins", "midas"]:
            for m in re.finditer(re.escape(term), txt):
                s = max(0, m.start() - 150); e = min(len(txt), m.end() + 200)
                print(f"    [{term}] ...{txt[s:e]}...")
                break
        # 是否还提到其他已知非牙科软件
        known = ["blender", "3d slicer", "mimics", "ansys", "meshmixer", "geomagic", "cloudcompare",
                 "meshlab", "solidworks", "abaqus", "rhinoceros", "itk-snap", "gom inspect", "magics"]
        found = sorted({k for k in known if k in txt})
        print("    全文中提到的其他已知软件:", found if found else "无")

# ---------- (B) Geomagic 混标 ----------
print("\n" + "=" * 70)
print("(B) Geomagic 系列：以全文为准的重新判定")
print("=" * 70)
rows = []
for _, r in d.iterrows():
    cur = [s for s in r["_soft"] if "geomagic" in s.lower()]
    if not cur: continue
    txt, f = text_of(r["_n"])
    det = {}
    if txt:
        for name, pats in GEOM.items():
            pats = [pats] if isinstance(pats, str) else pats
            det[name] = sum(txt.count(p) for p in pats)
        det["Geomagic (generic only)"] = max(0, txt.count("geomagic") - sum(det.values()))
    found = [k for k, v in det.items() if v > 0]
    rows.append({"ID": r["ID"], "Title": str(r["Title"])[:80], "PDF": bool(f),
                 "标注": ";".join(cur), "全文检出": ";".join(found), "明细": json.dumps(det, ensure_ascii=False)})
g = pd.DataFrame(rows)
g.to_csv(os.path.join(OUTD, "Geomagic_重判定.csv"), index=False, encoding="utf-8-sig")
sub = g[g["PDF"]]
match = sub.apply(lambda r: set(x.strip() for x in str(r["标注"]).split(";")) & set(x.strip() for x in str(r["全文检出"]).split(";") if x.strip()), axis=1)
print("含 Geomagic 标注的研究:", len(g), "| 有 PDF 可比对:", len(sub))
print("标注与全文一致:", int(match.map(bool).sum()), "| 不一致:", int((~match.map(bool)).sum()))
print("\n不一致样例:")
print(sub[~match.map(bool)][["标注", "全文检出"]].head(20).to_string(max_colwidth=48))
print("\n全文检出分布:")
allf = {}
for v in g["全文检出"]:
    for x in str(v).split(";"):
        if x: allf[x] = allf.get(x, 0) + 1
print(pd.Series(allf).sort_values(ascending=False).to_string())
