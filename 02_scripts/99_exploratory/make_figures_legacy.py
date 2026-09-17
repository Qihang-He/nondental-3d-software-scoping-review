# -*- coding: utf-8 -*-
"""
v2 图表生成（基于锁定数据集 N=572）
输出：05_图表/
  Figure1_PRISMA.(png|pdf)
  Figure2_composite.(png|pdf)   a 半年度趋势 / b 世界地图 / c 期刊 / d 专科×半年度
  Figure3_specialty_scenario.(png|pdf)
  Figure5_contingency.(png|pdf)  标准化残差 + Cramér's V
"""
import os, ast, json, itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import matplotlib.gridspec as gridspec

ROOT = r"d:\Desktop\v8 for JD"
ANA = os.path.join(ROOT, "03_数据", "08_分析用")
OUT = os.path.join(ROOT, "05_图表")
os.makedirs(OUT, exist_ok=True)
df = pd.read_csv(os.path.join(ANA, "分析数据集_final.csv"), encoding="utf-8-sig")
N = len(df)

def pl(x):
    if isinstance(x, list): return x
    try: return ast.literal_eval(x) if isinstance(x, str) else []
    except Exception: return []
for c in ("_spec", "_scen", "_soft"):
    df[c] = df[c].map(pl)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.linewidth": 0.8,
                     "savefig.bbox": "tight"})

def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=600)
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    plt.close(fig)
    print("saved:", name)

# ==================== Figure 1: PRISMA ====================
def fig1():
    fig, ax = plt.subplots(figsize=(8.6, 10.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 14); ax.axis("off")

    def box(x, y, w, h, text, fc="#eef3fa", ec="#1F4E78", fs=8.4, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                    fc=fc, ec=ec, lw=1.0))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                fontweight=("bold" if bold else "normal"), linespacing=1.35)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=11, color="#1F4E78", lw=1.0))

    ax.text(5, 13.6, "Identification", fontsize=9.5, fontweight="bold", ha="center", color="#1F4E78")
    box(0.3, 11.7, 5.2, 1.5, "Records identified from databases\n(n = 3,631)\n"
        "PubMed (n = 1,727)\nWeb of Science (n = 1,605)\nIEEE Xplore (n = 299)", fc="#dbe7f5")
    box(6.1, 11.7, 3.6, 1.5, "Records removed before\nscreening (n = 1,091)\n"
        "Duplicates (n = 1,077)\nRetracted (n = 4)\nNon-journal (n = 10)", fc="#f5e6e6")

    box(0.3, 9.9, 5.2, 1.3, "Records screened at title/abstract\n(n = 2,540)\n"
        "AI-assisted triage (3 runs; Fleiss' κ = 0.936)", fc="#dbe7f5")
    box(6.1, 9.9, 3.6, 1.3, "Records excluded\n(n = 793)", fc="#f5e6e6")

    ax.text(5, 9.3, "Screening", fontsize=9.5, fontweight="bold", ha="center", color="#1F4E78")
    box(0.3, 8.0, 5.2, 1.1, "Full-text files retrieved or available\nfor verification (n = 1,747)", fc="#dbe7f5")
    box(6.1, 8.0, 3.6, 1.6, "Eligibility outcome\nnot fully reconstructable\nfrom archived human logs\nFinal included set: n = {:,}".format(N), fc="#f5e6e6")

    ax.text(5, 7.4, "Eligibility", fontsize=9.5, fontweight="bold", ha="center", color="#1F4E78")
    box(0.3, 5.9, 5.2, 1.1, f"Studies included in the scoping review\n(n = {N})", fc="#d9f0e1", ec="#1e7a45", bold=True)
    ax.text(5, 5.3, "Included", fontsize=9.5, fontweight="bold", ha="center", color="#1e7a45")

    for (x1, y1), (x2, y2) in [((2.9, 11.7), (2.9, 11.2)),
                               ((2.9, 9.9), (2.9, 9.1)),
                               ((2.9, 8.0), (2.9, 7.0))]:
        arrow(x1, y1, x2, y2)
    arrow(7.9, 11.7, 7.9, 11.2); arrow(7.9, 9.9, 7.9, 9.6); arrow(7.9, 8.0, 7.9, 7.6)

    ax.text(0.3, 4.8, "English-language and date restrictions were applied at the database-search level, not delegated to the LLM.\n"
            "Title/abstract screening was AI-assisted. Full-text files were retrieved or available for verification for 1,747 records;\n"
            "the archived human-verification log was incomplete, so this number is not presented as a count of documented human assessments.",
            fontsize=7.4, va="top", color="#444")
    fig.suptitle("Figure 1. PRISMA flow diagram of study selection", fontsize=11, y=0.995, fontweight="bold")
    save(fig, "Figure1_PRISMA")

# ==================== Figure 2 ====================
def fig2():
    order = ["2020-H2", "2021-H1", "2021-H2", "2022-H1", "2022-H2", "2023-H1", "2023-H2",
             "2024-H1", "2024-H2", "2025-H1", "2025-H2", "2026-H1"]
    tr = df[df["Half2"] != "unknown"]["Half2"].value_counts().reindex(order).fillna(0).astype(int)

    fig = plt.figure(figsize=(15, 11))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.32, wspace=0.24)

    # (a) trend
    ax = fig.add_subplot(gs[0, 0])
    x = np.arange(len(tr))
    ax.bar(x, tr.values, color="#7aa7d1", edgecolor="#1F4E78", lw=0.6, width=0.68)
    ax.plot(x, tr.values, color="#1F4E78", lw=1.6, marker="o", ms=4)
    ax.set_xticks(x); ax.set_xticklabels(tr.index, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Number of publications"); ax.set_title("(a) Semi-annual publication trend", fontsize=10, loc="left")
    for i, v in enumerate(tr.values):
        ax.text(i, v + 1.2, str(v), ha="center", fontsize=7.6)
    ax.set_ylim(0, tr.max() * 1.34)
    ax.annotate("2026-H1 incomplete\n(search ended 30 Jun 2026;\nindexing lag)", xy=(11, tr.values[-1]),
                xytext=(7.6, tr.max() * 1.12), fontsize=7.0, color="#a33",
                arrowprops=dict(arrowstyle="->", color="#a33", lw=0.9))
    ax.text(0.02, 0.965, f"n = {int(tr.sum())} records with month-level date", transform=ax.transAxes,
            fontsize=7.2, va="top", color="#555")

    # (b) world map (fallback to bar if geopandas/naturalearth unavailable)
    ax = fig.add_subplot(gs[0, 1])
    reg = df["Region"].value_counts()
    try:
        import geopandas as gpd, requests
        bdir = os.path.join(OUT, "_basemap"); os.makedirs(bdir, exist_ok=True)
        gp = os.path.join(bdir, "ne_110m_admin_0_countries.geojson")
        if not os.path.exists(gp):
            r = requests.get("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson", timeout=90)
            r.raise_for_status(); open(gp, "wb").write(r.content)
        w = gpd.read_file(gp)
        col = "ADM0_A3" if "ADM0_A3" in w.columns else "ISO_A3"
        w["n"] = w[col].map(reg).fillna(0)
        w.plot(column="n", cmap="OrRd", linewidth=0.3, edgecolor="0.6", ax=ax,
               legend=True, legend_kwds={"label": "Number of studies", "shrink": 0.6})
        top = reg.head(8)
        for code, n in top.items():
            try:
                c = w[w[col] == code]
                if len(c):
                    p = c.geometry.representative_point().iloc[0]
                    ax.annotate(f"{code}\n{n}", (p.x, p.y), fontsize=6.4, ha="center",
                                color="#7a1f1f", fontweight="bold")
            except Exception:
                pass
        ax.set_axis_off(); ax.set_title("(b) Geographic distribution", fontsize=10, loc="left")
    except Exception as e:
        print("map fallback:", e)
        t = reg.head(15)[::-1]
        ax.barh(t.index, t.values, color="#e0a06a", edgecolor="#8a4b1f", lw=0.5)
        ax.set_xlabel("Number of studies"); ax.set_title("(b) Geographic distribution (top 15)", fontsize=10, loc="left")

    # (c) journal donut
    ax = fig.add_subplot(gs[1, 0])
    jc = df["Journal"].dropna().value_counts()
    top = jc.head(10); other = jc.iloc[10:].sum()
    labels = list(top.index) + ([f"Other journals (n={other})"] if other else [])
    vals = list(top.values) + ([other] if other else [])
    cmap = plt.get_cmap("tab20")
    cols = [cmap(i % 20) for i in range(len(labels))]; cols[-1] = (0.85, 0.85, 0.85, 1.0)
    ax.pie(vals, labels=None, colors=cols, startangle=90, counterclock=False, radius=0.92,
           wedgeprops=dict(width=0.42, edgecolor="w", lw=0.8))
    ax.text(0, 0, f"Total\n{N}\n\nJournals\n{df['Journal'].nunique()}", ha="center", va="center", fontsize=10, fontweight="bold")
    ax.legend(labels, loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=6.6,
              frameon=False, ncol=2, handlelength=1.1, columnspacing=1.0)
    ax.set_title("(c) Journal distribution (top 10)", fontsize=10, loc="left")
    ax.text(-1.42, 1.06, f"{int(df['Journal'].isna().sum())} records lack journal metadata", fontsize=6.8, color="#a33")

    # (d) specialty x half heatmap
    ax = fig.add_subplot(gs[1, 1])
    rows = []
    for _, r in df.iterrows():
        if r["Half2"] == "unknown": continue
        for s in set(r["_spec"]):
            rows.append((r["Half2"], s, r["ID"]))
    hh = pd.DataFrame(rows, columns=["Half", "Spec", "ID"])
    ct = hh.groupby(["Spec", "Half"])["ID"].nunique().unstack(fill_value=0).reindex(columns=order, fill_value=0)
    ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).index]
    im = ax.imshow(ct.values, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(order))); ax.set_xticklabels(order, rotation=45, ha="right", fontsize=7.4)
    ax.set_yticks(range(len(ct))); ax.set_yticklabels(ct.index, fontsize=7.6)
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            v = ct.values[i, j]
            if v: ax.text(j, i, str(v), ha="center", va="center", fontsize=6.6,
                          color="white" if v > ct.values.max() * 0.6 else "#333")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Study–speciality assignments", fontsize=8)
    ax.set_title("(d) Speciality × half-year (multi-label assignments)", fontsize=10, loc="left")

    fig.suptitle(f"Figure 2. Trends and distributions of nondental 3D software use in dentistry (N = {N}; 2020-H2 to 2026-H1)",
                 fontsize=11.5, y=0.985, fontweight="bold")
    save(fig, "Figure2_composite")

# ==================== Figure 3 ====================
def fig3():
    rows = []
    for _, r in df.iterrows():
        for s in set(r["_spec"]):
            for sc in set(r["_scen"]):
                rows.append((s, sc, r["ID"]))
    t = pd.DataFrame(rows, columns=["Spec", "Scen", "ID"])
    ct = t.groupby(["Spec", "Scen"])["ID"].nunique().unstack(fill_value=0)
    spec_order = ct.sum(axis=1).sort_values().index
    scen_order = ct.sum(axis=0).sort_values(ascending=False).index
    ct = ct.loc[spec_order, scen_order]
    uniq = df.explode("_spec").groupby("_spec")["ID"].nunique()

    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    bottom = np.zeros(len(ct))
    cmap = plt.get_cmap("tab20")
    for i, sc in enumerate(ct.columns):
        ax.bar(range(len(ct)), ct[sc].values, bottom=bottom, label=sc, color=cmap(i % 20), edgecolor="w", lw=0.5)
        bottom += ct[sc].values
    ax.set_xticks(range(len(ct))); ax.set_xticklabels(ct.index, rotation=28, ha="right", fontsize=8.4)
    ax.set_ylabel("Study–speciality assignments")
    for i, s in enumerate(ct.index):
        ax.text(i, bottom[i] + 1.5, f"total {int(bottom[i])}\n(unique studies {int(uniq.get(s, 0))})",
                ha="center", fontsize=6.8, color="#333")
    ax.legend(title="Application scenario", fontsize=7.2, title_fontsize=7.6,
              loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)
    ax.set_ylim(0, bottom.max() * 1.22)
    ax.set_title(f"Figure 3. Application scenarios by dental speciality (N = {N})", fontsize=11, loc="left", fontweight="bold")
    ax.text(0, -0.24, "Bars are study–speciality–scenario assignments (multi-label); unique study counts are annotated above each bar.",
            transform=ax.transAxes, fontsize=7.4, color="#555")
    save(fig, "Figure3_specialty_scenario")

# ==================== Figure 5: contingency ====================
def fig5():
    from scipy.stats import chi2_contingency
    top_soft = df.explode("_soft").groupby("_soft")["ID"].nunique().sort_values(ascending=False).head(10).index.tolist()
    specs = df.explode("_spec").groupby("_spec")["ID"].nunique().sort_values(ascending=False).index.tolist()
    rows = []
    for _, r in df.iterrows():
        for s in set(r["_soft"]):
            if s not in top_soft: continue
            for sp in set(r["_spec"]):
                rows.append((s, sp, r["ID"]))
    t = pd.DataFrame(rows, columns=["Soft", "Spec", "ID"])
    ct = t.groupby(["Soft", "Spec"])["ID"].nunique().unstack(fill_value=0).reindex(index=top_soft, columns=specs, fill_value=0)
    O = ct.values
    chi2, p, dof, E = chi2_contingency(O)
    V = np.sqrt(chi2 / (O.sum() * min(O.shape[0] - 1, O.shape[1] - 1)))
    R = (O - E) / np.sqrt(E)
    # 蒙特卡洛 p（固定边际），应对稀疏格子
    # 稳健性：合并稀有专科（列合计<20 → Other）后重算
    colsum = O.sum(axis=0)
    keepj = [j for j in range(O.shape[1]) if colsum[j] >= 20]
    if len(keepj) < O.shape[1]:
        O2 = np.column_stack([O[:, keepj], O[:, [j for j in range(O.shape[1]) if j not in keepj]].sum(axis=1)])
    else:
        O2 = O
    chi2b, pb, dofb, Eb = chi2_contingency(O2)
    Vb = np.sqrt(chi2b / (O2.sum() * min(O2.shape[0] - 1, O2.shape[1] - 1)))

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 6.2), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    vmax = np.nanmax(np.abs(R))
    im = ax.imshow(R, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(specs))); ax.set_xticklabels(specs, rotation=45, ha="right", fontsize=7.8)
    ax.set_yticks(range(len(top_soft))); ax.set_yticklabels(top_soft, fontsize=8)
    for i in range(R.shape[0]):
        for j in range(R.shape[1]):
            ax.text(j, i, f"{R[i,j]:.1f}", ha="center", va="center", fontsize=6.4,
                    color="white" if abs(R[i, j]) > vmax * 0.62 else "#222")
    cb = fig.colorbar(im, ax=ax, fraction=0.036, pad=0.02)
    cb.set_label("Standardized residual", fontsize=8)
    ax.set_title(f"(a) Standardized residuals (χ² = {chi2:.1f}, df = {dof}, p = {p:.2g}; Cramér's V = {V:.2f})",
                 fontsize=9.4, loc="left")

    ax2 = axes[1]
    prop = O / O.sum(axis=1, keepdims=True) * 100
    im2 = ax2.imshow(prop, cmap="Blues", aspect="auto")
    ax2.set_xticks(range(len(specs))); ax2.set_xticklabels(specs, rotation=45, ha="right", fontsize=7.8)
    ax2.set_yticks(range(len(top_soft))); ax2.set_yticklabels(top_soft, fontsize=8)
    for i in range(prop.shape[0]):
        for j in range(prop.shape[1]):
            if O[i, j]:
                ax2.text(j, i, f"{prop[i,j]:.0f}%", ha="center", va="center", fontsize=6.4,
                         color="white" if prop[i, j] > prop.max() * 0.65 else "#222")
    cb2 = fig.colorbar(im2, ax=ax2, fraction=0.036, pad=0.02); cb2.set_label("Row %", fontsize=8)
    ax2.set_title("(b) Row-normalised distribution of each software across specialities", fontsize=9.6, loc="left")
    fig.suptitle("Figure 5. Association between nondental 3D software and dental specialities "
                 "(contingency analysis on study–software–speciality assignments)", fontsize=11, y=0.995, fontweight="bold")
    fig.text(0.01, -0.02, f"Cells show number of unique studies. χ² test on the contingency table of {len(top_soft)} software × {len(specs)} specialities; "
             f"standardized residuals highlight over-/under-representation. Sparse cells are frequent ({float((E<5).mean()*100):.0f}% of expected counts < 5), "
             f"so a sensitivity analysis merging rare specialities (< 20 studies) into 'Other' was performed "
             f"(merged table: χ² = {chi2b:.1f}, df = {dofb}, p = {pb:.2g}, Cramér's V = {Vb:.2f}; {float((Eb<5).mean()*100):.0f}% expected < 5).",
             fontsize=7.2, color="#555")
    save(fig, "Figure5_contingency")

    out = {"chi2": float(chi2), "dof": int(dof), "p": float(p), "cramers_v": float(V),
           "table_shape": list(O.shape), "min_expected": float(E.min()),
           "pct_expected_lt5": float((E < 5).mean() * 100),
           "merged": {"chi2": float(chi2b), "dof": int(dofb), "p": float(pb), "cramers_v": float(Vb),
                      "shape": list(O2.shape), "pct_expected_lt5": float((Eb < 5).mean() * 100)}}
    json.dump(out, open(os.path.join(OUT, "fig5_stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False))

fig1(); fig2(); fig3(); fig5()
print("\n全部图表已生成 ->", OUT)
