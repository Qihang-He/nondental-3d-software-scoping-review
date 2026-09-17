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
以 PDF 全文为准重编码 Geomagic 系列；并执行 2 项剔除（EvaluNav/Navident、NEMOfab）
输出：03_数据/06_锁定数据集/最终数据集_v2.2.csv + 变更日志
"""
import os, re, ast, json
import pandas as pd
import fitz

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "08_分析用")
LOCK = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "06_锁定数据集")
PDFDIR = os.path.join(ROOT, "pdf")
MATCH = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "07_PDF与语料对照", "pdf_match.csv")
FULL = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "01_原始", "完整文献信息.csv")

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

cache = {}
def text_of(k):
    if k in cache: return cache[k]
    f = n2file.get(k); t = ""
    if f:
        try:
            doc = fitz.open(os.path.join(PDFDIR, f)); t = re.sub(r"\s+", " ", " ".join(p.get_text() for p in doc)).lower(); doc.close()
        except Exception: t = ""
    cache[k] = t
    return t

SPEC = [("Geomagic Wrap", ["geomagic wrap"]), ("Geomagic Design X", ["geomagic design x", "geomagic designx", "geomagic design"]),
        ("Geomagic Control X", ["geomagic control x", "geomagic controlx", "geomagic control"]),
        ("Geomagic Studio", ["geomagic studio"]), ("Geomagic Freeform", ["geomagic freeform"]),
        ("Geomagic Qualify", ["geomagic qualify"]), ("Geomagic Sculpt", ["geomagic sculpt"])]

log = []
new_soft = []
for _, r in d.iterrows():
    softs = list(r["_soft"])
    geom = [s for s in softs if "geomagic" in s.lower()]
    if not geom:
        new_soft.append(softs); continue
    txt = text_of(r["_n"])
    if not txt:
        new_soft.append(softs); log.append({"ID": r["ID"], "Title": str(r["Title"])[:60], "变更": "无PDF，保留原标注"})
        continue
    det = [name for name, pats in SPEC if any(p in txt for p in pats)]
    generic = "geomagic" in txt and not det
    newg = det if det else (["Geomagic (unspecified)"] if generic else [])
    if not newg:
        newg = geom  # 全文中找不到确定产品，保留原标注但记录
        log.append({"ID": r["ID"], "Title": str(r["Title"])[:60], "变更": f"全文未检出 Geomagic 产品名，保留 {geom}"})
    else:
        log.append({"ID": r["ID"], "Title": str(r["Title"])[:60], "变更": f"{geom} → {newg}"})
    out = [s for s in softs if "geomagic" not in s.lower()] + newg
    new_soft.append(out)

d["_soft2"] = new_soft
d["Software Used (fixed)"] = d["_soft2"].map(lambda l: ";".join(l))

# 剔除：仅使用牙科专用软件
EXCLUDE_IDS = []
for _, r in d.iterrows():
    s = set(x.lower() for x in r["_soft2"])
    if s == {"evalunav"} or s == {"nemofab"}:
        EXCLUDE_IDS.append(r["ID"])
d["裁定3"] = d["ID"].map(lambda i: "剔除" if i in EXCLUDE_IDS else "保留")
d["裁定3理由"] = d["ID"].map(lambda i: "全文核验：仅使用牙科专用软件（Navident/EvaluNav 种植导航）" if i in EXCLUDE_IDS
                             else ("全文核验：仅使用牙科专用软件（NEMOfab/Nemotec）" if i in EXCLUDE_IDS else ""))

kept = d[d["裁定3"] == "保留"].copy()
kept.to_csv(os.path.join(LOCK, "最终数据集_v2.2.csv"), index=False, encoding="utf-8-sig")
pd.DataFrame(log).to_csv(os.path.join(LOCK, "Geomagic重编码日志.csv"), index=False, encoding="utf-8-sig")

print("Geomagic 变更条数:", len(log))
print("剔除:", len(EXCLUDE_IDS), list(EXCLUDE_IDS))
print("v2.2 保留 N =", len(kept))

# 新软件计数
cnt = {}
for l in kept["_soft2"]:
    for s in set(l): cnt[s] = cnt.get(s, 0) + 1
top = pd.Series(cnt).sort_values(ascending=False).head(15)
print("\n新软件 Top15:")
print(top.to_string())
json.dump({"N": int(len(kept)), "software_top": {k: int(v) for k, v in top.items()},
           "excluded_ids": list(EXCLUDE_IDS)},
          open(os.path.join(ANA, "v22_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
