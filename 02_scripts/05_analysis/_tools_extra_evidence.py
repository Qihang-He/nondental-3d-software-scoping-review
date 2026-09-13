# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""为回复审稿人补充两项科学证据：软件共现（工作流经验支撑）+ 趋势斜率（含/不含 2026-H1）"""
import os, ast, json, itertools
import numpy as np, pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "08_分析用")
df = pd.read_csv(os.path.join(ANA, "分析数据集_572_定稿.csv"), encoding="utf-8-sig")
def pl(x):
    try: return ast.literal_eval(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
    except Exception: return []
for c in ("_soft", "_spec", "_scen"):
    df[c] = df[c].map(pl)

# 1) 软件共现（同一研究同时使用两种软件）
pairs = {}
multi = 0
for l in df["_soft"]:
    if len(l) >= 2: multi += 1
    for a, b in itertools.combinations(sorted(set(l)), 2):
        pairs[(a, b)] = pairs.get((a, b), 0) + 1
top_pairs = sorted(pairs.items(), key=lambda kv: -kv[1])[:15]
print("多软件研究数:", multi, "/", len(df), f"({multi/len(df)*100:.1f}%)")
print("Top 软件共现对:")
for (a, b), n in top_pairs:
    print(f"  {n:3d}  {a} + {b}")

# 2) 趋势斜率（半年度）
order = ["2020-H2", "2021-H1", "2021-H2", "2022-H1", "2022-H2", "2023-H1", "2023-H2",
         "2024-H1", "2024-H2", "2025-H1", "2025-H2", "2026-H1"]
tr = df[df["Half2"] != "unknown"]["Half2"].value_counts().reindex(order).fillna(0).astype(int)
x = np.arange(len(tr))
s_all = np.polyfit(x, tr.values, 1)[0]
s_no26 = np.polyfit(x[:-1], tr.values[:-1], 1)[0]
# 仅用完整期（排除 2020-H2 起点不完整与 2026-H1）
idx = list(range(1, len(tr) - 1))
s_full = np.polyfit(idx, tr.values[idx], 1)[0]
r_all = np.corrcoef(x, tr.values)[0, 1]
print(f"\n斜率(全部12期): {s_all:.2f} 篇/半年 | 排除2026-H1: {s_no26:.2f} | 仅完整期(2021-H1~2025-H2): {s_full:.2f}")
print("Pearson r(全部):", round(float(r_all), 3))

json.dump({"multi_software_studies": multi, "n": len(df),
           "top_pairs": [[a, b, n] for (a, b), n in top_pairs],
           "slope_all": float(s_all), "slope_excl_2026H1": float(s_no26),
           "slope_complete_only": float(s_full), "pearson_r": float(r_all),
           "trend": tr.to_dict()},
          open(os.path.join(ANA, "extra_evidence.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("\n已保存 extra_evidence.json")
