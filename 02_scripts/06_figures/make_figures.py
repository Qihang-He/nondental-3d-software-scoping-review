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
make_figures_v3.py  —— R2 定稿图（v6；N = 853）
设计原则：简洁、直观、全图统一配色与字号；去图表垃圾；直接标注数值。
唯一数字来源：03_数据/08_分析用/统计核心_v6.json + 分析数据集_final_v6.csv
输出：05_图表/Figure1_PRISMA ~ Figure5_contingency (.png 600dpi + .pdf)
"""
import os
import ast
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import MaxNLocator
import matplotlib.gridspec as gridspec

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
OUT = os.path.join(ROOT, _os.path.join(_ROOTP, '05_图表'))
os.makedirs(OUT, exist_ok=True)

S = json.load(open(os.path.join(ANA, '统计核心_v6.json'), encoding='utf-8'))
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v6.csv'), low_memory=False)
SW = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
N = len(d)

# ---------------- 统一视觉系统 ----------------
C = {'blue': '#2E6DA4', 'blue_l': '#A8C4DE', 'teal': '#3F9C9C', 'teal_l': '#B2DBDB',
     'amber': '#D98C2B', 'amber_l': '#F2D6AE', 'coral': '#C0553F', 'coral_l': '#EBC4BA',
     'purple': '#6E5EA8', 'purple_l': '#CFC7E6', 'green': '#4C9366', 'green_l': '#BFDCCB',
     'grey': '#7E8B99', 'grey_l': '#DCE2E8', 'ink': '#26313C'}
SEQ = [C['blue'], C['teal'], C['amber'], C['purple'], C['green'], C['coral']]
SEQ_L = [C['blue_l'], C['teal_l'], C['amber_l'], C['purple_l'], C['green_l'], C['coral_l']]

# ---------------- 印刷尺寸与字号 ----------------
# Journal of Dentistry（Elsevier）：单栏 8.5 cm，通栏 17.5 cm。
# 图件一律按**最终印刷尺寸**绘制，故此处字号即为印刷字号；最小不低于 6 pt 以保证可读。
FIG_W = 6.9           # 通栏 17.5 cm
FIG_W2 = 3.35         # 单栏 8.5 cm
FS = {'panel': 8.5, 'lab': 8.0, 'tick': 7.2, 'val': 6.8, 'note': 6.5}

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': FS['tick'],
    'axes.edgecolor': C['ink'], 'axes.linewidth': 0.7,
    'axes.labelcolor': C['ink'], 'text.color': C['ink'],
    'xtick.color': C['ink'], 'ytick.color': C['ink'],
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'xtick.major.width': 0.7, 'ytick.major.width': 0.7,
    'axes.labelsize': FS['lab'],
    'savefig.bbox': 'tight', 'figure.dpi': 120, 'pdf.fonttype': 42,
})


def tidy(ax, grid='y', spines=('top', 'right')):
    """去图表垃圾：隐藏上/右边框、浅色网格、无标题背景"""
    for s in spines:
        ax.spines[s].set_visible(False)
    if grid in ('y', 'both'):
        ax.yaxis.grid(True, color=C['grey_l'], lw=0.7)
    if grid in ('x', 'both'):
        ax.xaxis.grid(True, color=C['grey_l'], lw=0.7)
    if grid == 'none':
        ax.grid(False)
    ax.set_axisbelow(True)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + '.png'), dpi=600)
    fig.savefig(os.path.join(OUT, name + '.pdf'))
    plt.close(fig)
    print('saved:', name)


def pl(x):
    if isinstance(x, list):
        return x
    try:
        return ast.literal_eval(x) if isinstance(x, str) else []
    except Exception:
        return []


d['_spec_l'] = d['_spec'].map(pl)
d['_soft_l'] = d['_soft2'].map(pl)
d['_scen_l'] = d['_scen'].map(pl)

HALF = ['2020-H2', '2021-H1', '2021-H2', '2022-H1', '2022-H2', '2023-H1', '2023-H2',
        '2024-H1', '2024-H2', '2025-H1', '2025-H2', '2026-H1']

name2cat = dict(zip(SW['规范名称'], SW['类别']))
FAMILY = {'MIP': 'Medical image\nprocessing', 'RE': 'Reverse engineering /\n3D reconstruction',
          'SIM': 'Engineering\nsimulation', 'GEN3D': 'General-purpose\n3D modelling',
          'CAD': 'Computer-aided\ndesign', 'AM': 'Additive\nmanufacturing',
          'SCI': 'Scientific computing\n/ visualisation', 'DICOM': 'DICOM\nviewers',
          'PHOTO': 'Photogrammetry', 'RT': 'Radiotherapy\nplanning',
          '???': 'Unclassified'}
FAM_ORDER = ['MIP', 'RE', 'SIM', 'GEN3D', 'CAD', 'AM', 'SCI', 'DICOM', 'PHOTO', 'RT', '???']


def fam_of(soft):
    c = name2cat.get(soft)
    return c if c in FAMILY else None


# ==================================================================
# Figure 1 — PRISMA 2020 流程图
# ==================================================================
def fig1():
    ch = json.load(open(os.path.join(ANA, 'PRISMA_链路_v2.json'), encoding='utf-8'))
    N = ch['included']
    n_ident = ch['identified_total']
    n_dup = ch['duplicates_removed']
    n_scr = ch['screened_title_abstract']
    n_excl = ch['excluded_at_title_abstract'] + ch['fulltext_recheck']['records_reclassified_as_eligible']
    n_ft = ch['fulltext_recheck']['excluded_records_with_full_text_available']
    n_noft = ch['fulltext_recheck']['excluded_records_without_full_text']
    n_new = ch['fulltext_recheck']['records_reclassified_as_eligible']
    n_prog = 613
    n_assess = n_prog + n_ft
    n_ft_excl = n_assess - N

    # PRISMA 为整页图；保持经典四阶段排版。文字全部经渲染测量，超框自动缩小字号。
    fig, ax = plt.subplots(figsize=(8.6, 9.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12.4)
    ax.axis('off')
    fig.canvas.draw()
    _rend = fig.canvas.get_renderer()
    _inv = ax.transData.inverted()

    def _measure(t):
        bb = t.get_window_extent(renderer=_rend)
        (x0, y0), (x1, y1) = _inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        return (x1 - x0), (y1 - y0)

    def box(x, y, w, h, txt, fc, ec, fs=8.2, bold=False, align='center'):
        """文本框：先量文字，超框则逐步缩小字号（下限 5.8 pt），确保文字始终在框内。"""
        ha = 'center' if align == 'center' else 'left'
        tx = x + w / 2 if align == 'center' else x + 0.18
        t = ax.text(tx, y + h / 2, txt, ha=ha, va='center', fontsize=fs,
                    fontweight='bold' if bold else 'normal', linespacing=1.42, zorder=3)
        cur = fs
        while cur > 5.8:
            tw, th = _measure(t)
            if tw <= w * 0.92 and th <= h * 0.88:
                break
            cur -= 0.15
            t.set_fontsize(cur)
        tw, th = _measure(t)
        if tw > w * 0.92 or th > h * 0.88:
            print('  [PRISMA 文本仍偏紧] %s' % txt.split('\n')[0][:44])
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.04',
                                    fc=fc, ec=ec, lw=0.9, zorder=2))
        return t

    def arrow(x1, y1, x2, y2, color=None, ls='-'):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                     mutation_scale=9, color=color or C['ink'],
                                     lw=0.9, linestyle=ls, zorder=1))

    LX, LW = 0.30, 5.45
    RX, RW = 6.15, 3.55
    CX = LX + LW / 2
    stag = dict(fontsize=8.4, fontweight='bold', ha='center', color=C['blue'])

    # ---- 阶段标签置于各阶段方框上方，不与方框重叠 ----
    ax.text(5.0, 11.95, 'Identification', **stag)
    box(LX, 10.35, LW, 1.35,
        'Records identified from databases\n(n = %s)\n'
        'PubMed (n = 1,727)   Web of Science (n = 1,695)   IEEE Xplore (n = 304)'
        % format(n_ident, ','), C['blue_l'], C['blue'])
    box(RX, 10.35, RW, 1.35,
        'Duplicate records removed\nbefore screening (n = %s)' % format(n_dup, ','),
        C['grey_l'], C['grey'], fs=7.9)
    arrow(5.83, 11.02, 6.15, 11.02)

    ax.text(5.0, 9.35, 'Screening', **stag)
    box(LX, 7.70, LW, 1.42,
        'Records screened at title/abstract level\n(n = %s)\n'
        'Topic, article type, language and date criteria;\n'
        'LLM-assisted, three independent runs (Fleiss\u2019 \u03ba = 0.936)'
        % format(n_scr, ','), C['blue_l'], C['blue'])
    box(RX, 7.70, RW, 1.42,
        'Records excluded at title/abstract\nscreening (n = %s)\n\n'
        'Full text available and re-assessed: %s\nNo full text available: %s'
        % (format(n_excl, ','), format(n_ft, ','), format(n_noft, ',')),
        C['grey_l'], C['grey'], fs=7.6, align='left')
    arrow(CX, 10.35, CX, 9.12)
    arrow(5.83, 8.41, 6.15, 8.41)

    ax.text(5.0, 6.95, 'Eligibility', **stag)
    box(LX, 5.20, LW, 1.52,
        'Records assessed for eligibility\nat full text (n = %s)\n'
        '613 progressed from title/abstract screening\n'
        '+ %s excluded records re-assessed in full text'
        % (format(n_assess, ','), format(n_ft, ',')), C['blue_l'], C['blue'])
    EB = ch['exclusion_breakdown']
    box(RX, 5.05, RW, 1.67,
        'Records excluded after\nfull-text assessment (n = %s)\n\n'
        'Not eligible on full-text review: %s\n'
        'Excluded at full-text screening: %s\n'
        'No eligible package in full text: %s\n'
        'Only named tool not 3D software: %s\n'
        'Outside the date window: %s\n'
        'Narrative review / software unsupported: %s'
        % (format(n_ft_excl, ','),
           format(n_ft - n_new, ','),
           EB['excluded_at_full_text_screening'],
           EB['removed_from_previous_set_no_named_software'],
           EB['software_scope_not_a_nondental_3d_package'],
           EB['outside_prespecified_date_window'],
           EB['current_audit_narrative_review_or_unsupported_software']),
        C['grey_l'], C['grey'], fs=7.6, align='left')
    arrow(CX, 7.70, CX, 6.72)
    arrow(5.83, 5.88, 6.15, 5.88)

    ax.text(5.0, 4.55, 'Included', **stag)
    box(LX, 3.05, LW, 1.25,
        'Studies included in the scoping review\n(n = %s)' % format(N, ','),
        C['green_l'], C['green'], bold=True, fs=9.4)
    arrow(CX, 5.20, CX, 4.30)

    # ---- 全文重评说明放在右栏（与 Included 同排），虚线不再穿过任何文本框 ----
    box(RX, 3.05, RW, 1.25,
        'Full-text re-assessment\nof the %s excluded records\n'
        '\u2192 %s met the eligibility criteria\n    and were added to the review'
        % (format(n_ft, ','), format(n_new, ',')),
        C['amber_l'], C['amber'], fs=7.6, align='left')
    arrow(RX + RW / 2, 5.05, RX + RW / 2, 4.30, color=C['amber'], ls='--')

    save(fig, 'Figure1_PRISMA')


# ==================================================================
# Figure 2 — 领域全景（趋势 / 地图 / 研究设计 / 专科）
# ==================================================================
def fig2():
    tr = S['trend']
    x = np.arange(len(HALF))
    v = [tr[h] for h in HALF]

    # 按最终印刷尺寸绘制（全幅 17.5 cm），字号即为印刷字号
    fig = plt.figure(figsize=(FIG_W, 9.9))
    gs = gridspec.GridSpec(3, 2, figure=fig, height_ratios=[1.0, 1.30, 1.02],
                           hspace=0.38, wspace=0.28,
                           left=0.095, right=0.985, top=0.982, bottom=0.062)

    # (a) 趋势 —— 通栏
    ax = fig.add_subplot(gs[0, :])
    ax.bar(x, v, color=C['blue_l'], edgecolor=C['blue'], lw=0.6, width=0.68, zorder=2)
    for i, val in enumerate(v):
        ax.text(i, val + max(v) * 0.022, str(val), ha='center', fontsize=FS['val'], color=C['ink'])
    ax.set_xticks(x)
    ax.set_xticklabels(HALF, rotation=40, ha='right', fontsize=FS['tick'])
    ax.set_ylabel('Publications', fontsize=FS['lab'])
    ax.set_ylim(0, max(v) * 1.22)
    ax.set_title('(a)', fontsize=FS['panel'], loc='left', pad=4, fontweight='bold')
    tidy(ax)

    # (b) 世界地图 —— 通栏，标注国名与数量
    ax = fig.add_subplot(gs[1, :])
    try:
        import geopandas as gpd
        import warnings
        from matplotlib.patheffects import withStroke
        warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS')
        bdir = os.path.join(OUT, '_basemap')
        os.makedirs(bdir, exist_ok=True)
        gp = os.path.join(bdir, 'ne_110m_admin_0_countries.geojson')
        world = gpd.read_file(gp)
        world['ISO_A3'] = world['ISO_A3'].astype(str)
        nm = dict(zip(world['ISO_A3'], world['NAME_EN'].astype(str)))
        reg = d['Region'].astype(str).value_counts()
        world['n'] = world['ISO_A3'].map(reg).fillna(0)
        world.plot(column='n', ax=ax, cmap='Blues', edgecolor='white', lw=0.3,
                   legend=True, missing_kwds={'color': '#F0F2F4'},
                   legend_kwds={'shrink': 0.55, 'label': 'Studies', 'pad': 0.008,
                                'aspect': 14})
        ax.set_axis_off()

        SHORT = {'United States of America': 'United States', 'Korea': 'South Korea',
                 'Republic of Korea': 'South Korea', 'Korea, Republic of': 'South Korea',
                 "People's Republic of China": 'China', 'Czechia': 'Czech Republic',
                 'Russian Federation': 'Russia', 'United Republic of Tanzania': 'Tanzania',
                 'Republic of Türkiye': 'Türkiye', 'Turkiye': 'Türkiye'}
        # 标签相对国土地理位置的偏移（度）。仅标注前 8 位；
        # 把标签推到大西洋、撒哈拉、太平洋等空白区，并靠不同纬度错开，杜绝叠字。
        NUDGE = {'USA': (-14, -10), 'BRA': (-11, -8), 'CHN': (-10, -6), 'TUR': (-22, -14),
                 'ITA': (-48, -6), 'DEU': (0, 12), 'KOR': (18, -12), 'EGY': (-14, -22),
                 'IND': (6, -12), 'ESP': (-30, -14), 'JPN': (16, 8), 'CHE': (-24, -2)}
        halo = [withStroke(linewidth=2.0, foreground='white')]
        inv = ax.transData.inverted()

        # 标注文献量最多的 3 个国家（正文点名的领先国家），分别放进
        # 东太平洋、非洲内陆、东南太平洋三片互不相邻的空白区，杜绝叠字。
        NUDGE5 = {'CHN': (40, -22), 'TUR': (-16, -24), 'USA': (-6, -28)}
        items = []
        for code, cnt in reg.head(3).items():
            sub = world[world['ISO_A3'] == code]
            if not len(sub):
                continue
            pt = sub.geometry.representative_point().iloc[0]
            nmv = SHORT.get(nm.get(code, code), nm.get(code, code))
            dx, dy = NUDGE5.get(code, (0, -14))
            items.append([code, pt, '%s (%d)' % (nmv, cnt),
                          ax.annotate('%s (%d)' % (nmv, cnt), xy=(pt.x, pt.y),
                                      xytext=(pt.x + dx, pt.y + dy),
                                      fontsize=FS['val'], color=C['ink'], ha='center',
                                      va='center', zorder=5, path_effects=halo,
                                      arrowprops=dict(arrowstyle='-', color=C['grey'],
                                                      lw=0.4, shrinkA=1, shrinkB=2))])

        def _bbox(t):
            bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
            (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
            return x0, y0, x1, y1

        fig.canvas.draw()
        _boxes = [_bbox(it[3]) for it in items]
        _ov = []
        for i in range(len(_boxes)):
            for j in range(i + 1, len(_boxes)):
                a, b = _boxes[i], _boxes[j]
                if not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]):
                    _ov.append('%s/%s' % (items[i][0], items[j][0]))
        print('  Fig2 国名标签：%d 个，%s'
              % (len(items), '无重叠' if not _ov else '重叠 %s' % ', '.join(_ov)))
        ax.set_title('(b)', fontsize=FS['panel'], loc='left', pad=4, fontweight='bold')
    except Exception as e:
        print('  map fallback:', e)
        reg = d['Region'].value_counts().head(12)[::-1]
        ax.barh(range(len(reg)), reg.values, color=C['teal'], height=0.65)
        ax.set_yticks(range(len(reg)))
        ax.set_yticklabels(reg.index, fontsize=FS['tick'])
        ax.set_xlabel('Number of studies', fontsize=FS['lab'])
        ax.set_title('(b)', fontsize=FS['panel'], loc='left', pad=4, fontweight='bold')
        tidy(ax, grid='x')

    # (c) 研究设计
    ax = fig.add_subplot(gs[2, 0])
    st = S['study_type']
    lblmap = {'computational': 'Computational /\nsimulation', 'in_vitro': 'In vitro',
              'clinical': 'Clinical', 'technical_note': 'Technical note',
              'case_report': 'Case report', 'educational': 'Educational'}
    ks = list(st.keys())
    vals = [st[k] for k in ks]
    ypos = np.arange(len(ks))[::-1]
    ax.barh(ypos, vals, color=[SEQ[i % len(SEQ)] for i in range(len(ks))], height=0.64)
    for yp, val in zip(ypos, vals):
        ax.text(val + max(vals) * 0.02, yp, '%d (%.1f%%)' % (val, val / N * 100),
                va='center', fontsize=FS['val'])
    ax.set_yticks(ypos)
    ax.set_yticklabels([lblmap.get(k, k) for k in ks], fontsize=FS['tick'])
    ax.set_xlabel('Studies', fontsize=FS['lab'])
    ax.set_xlim(0, max(vals) * 1.30)
    ax.set_title('(c)', fontsize=FS['panel'], loc='left', pad=4, fontweight='bold')
    tidy(ax, grid='x')

    # (d) 专科 —— 列出全部 12 个专科
    ax = fig.add_subplot(gs[2, 1])
    sp = S['speciality']
    ks = list(sp.keys())[::-1]
    vals = [sp[k] for k in ks]
    ypos = np.arange(len(ks))
    ax.barh(ypos, vals, color=C['teal'], height=0.68)
    for yp, val in zip(ypos, vals):
        ax.text(val + max(vals) * 0.02, yp, str(val), va='center', fontsize=FS['val'])
    SHORTSPEC = {'Oral and Maxillofacial Surgery': 'OMF surgery',
                 'Oral and Maxillofacial Radiology': 'OMF radiology',
                 'Temporomandibular Joint Disorders': 'TMD',
                 'Dental Sleep Medicine': 'Dental sleep med.'}
    ax.set_yticks(ypos)
    ax.set_yticklabels([SHORTSPEC.get(k, k) for k in ks], fontsize=FS['tick'])
    ax.set_xlabel('Study\u2013speciality assignments', fontsize=FS['lab'])
    ax.set_xlim(0, max(vals) * 1.18)
    ax.set_ylim(-0.6, len(ks) - 0.4)
    ax.set_title('(d)', fontsize=FS['panel'], loc='left', pad=4, fontweight='bold')
    tidy(ax, grid='x')

    save(fig, 'Figure2_landscape')


# ==================================================================
# Figure 3 — 软件格局
# ==================================================================
def fig3():
    fam = {}
    for soft, n in S['software_top'].items():
        pass
    for _, r in d.iterrows():
        for s in set(r['_soft_l']):
            f = fam_of(s)
            if f:
                fam.setdefault(f, set()).add(r['序号'])
    fam_n = {f: len(v) for f, v in fam.items()}

    fig = plt.figure(figsize=(FIG_W, 6.4))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.46, wspace=0.36,
                           left=0.135, right=0.985, top=0.965, bottom=0.085,
                           height_ratios=[1.30, 1.0])

    # (a) 软件功能族 —— 左下
    ax = fig.add_subplot(gs[1, 0])
    items = sorted(fam_n.items(), key=lambda x: -x[1])[:6]
    labs = [FAMILY[k] for k, _ in items]          # 保留换行，避免标签过长导致幅面变宽
    vals = [v for _, v in items]
    ypos = np.arange(len(items))[::-1]
    ax.barh(ypos, vals, color=[SEQ_L[i] for i in range(len(items))],
            edgecolor=[SEQ[i] for i in range(len(items))], lw=0.7, height=0.64)
    for yp, val in zip(ypos, vals):
        ax.text(val + max(vals) * 0.02, yp, '%d (%.0f%%)' % (val, val / N * 100),
                va='center', fontsize=FS['val'])
    ax.set_yticks(ypos)
    ax.set_yticklabels(labs, fontsize=FS['tick'])
    ax.set_xlabel('Number of studies', fontsize=FS['lab'])
    ax.set_xlim(0, max(vals) * 1.26)
    ax.set_title('(a)', fontsize=10.5, loc='left', pad=6, fontweight='bold')
    tidy(ax, grid='x')

    # (b) 最常报告的软件包 —— 通栏
    ax = fig.add_subplot(gs[0, :])
    top = list(S['software_top'].items())[:12][::-1]
    labs = [k for k, _ in top]
    vals = [v for _, v in top]
    ypos = np.arange(len(top))
    ax.barh(ypos, vals, color=C['blue'], height=0.66)
    for yp, val in zip(ypos, vals):
        ax.text(val + max(vals) * 0.018, yp, str(val), va='center', fontsize=FS['val'])
    ax.set_yticks(ypos)
    ax.set_yticklabels(labs, fontsize=FS['tick'])
    ax.set_xlabel('Number of studies', fontsize=FS['lab'])
    ax.set_xlim(0, max(vals) * 1.12)
    ax.set_title('(b)', fontsize=FS['panel'], loc='left', pad=6, fontweight='bold')
    tidy(ax, grid='x')

    # (c) 每篇研究使用的软件包数 —— 右下
    ax = fig.add_subplot(gs[1, 1])
    cnt = pd.Series([len(set(l)) for l in d['_soft_l']]).value_counts().sort_index()
    cnt = cnt[cnt.index > 0]
    bars = ax.bar(cnt.index, cnt.values,
                  color=[C['blue'] if i == 1 else C['amber'] for i in cnt.index],
                  width=0.62)
    for xx, yy in zip(cnt.index, cnt.values):
        ax.text(xx, yy + max(cnt.values) * 0.02, str(yy), ha='center', fontsize=7.2)
    ax.set_xlabel('Non-dental software packages per study')
    ax.set_ylabel('Number of studies')
    ax.set_ylim(0, max(cnt.values) * 1.18)
    ax.set_title('(c)', fontsize=10.5, loc='left', pad=6, fontweight='bold')
    tidy(ax)

    save(fig, 'Figure3_software')


# ==================================================================
# Figure 4 — 数据驱动工作流原型
# ==================================================================
def fig4():
    desc = pd.read_csv(os.path.join(ANA, '工作流分型_描述.csv'))
    mp = json.load(open(os.path.join(ANA, '工作流分型_方法参数.json'), encoding='utf-8'))

    TITLE = {
        1: 'Quantitative measurement and\naccuracy assessment',
        2: 'Computational biomechanical\nsimulation',
        3: 'Image segmentation and\n3D reconstruction',
        4: 'Digital design and\nmanufacturing',
        5: 'Surgical planning and\nprocedure execution',
        6: 'Morphometric and\nphenotypic analysis',
    }
    LABEL_FROM_SCEN = {
        'Analysis/Accuracy': 'Quantitative measurement and\naccuracy assessment',
        'Biomechanics': 'Computational biomechanical\nsimulation',
        'Segmentation/Reconstruction': 'Image segmentation and\n3D reconstruction',
        'Design/Manufacturing': 'Digital design and\nmanufacturing',
        'Surgical planning': 'Surgical planning and\nprocedure execution',
        'Morphology/Phenotype': 'Morphometric and\nphenotypic analysis',
    }

    def title_of(a, desc):
        row = desc[desc['Archetype'] == a]
        if len(row):
            s1 = str(row.iloc[0]['场景1'])
            if s1 in LABEL_FROM_SCEN:
                return LABEL_FROM_SCEN[s1]
        return TITLE.get(int(a), 'Archetype %s' % a)

    SCEN_FULL = {'Image Segmentation and 3D Reconstruction':
                     'Image segmentation &\n3D reconstruction',
                 '3D Data Analysis and Accuracy Assessment':
                     '3D data analysis &\naccuracy assessment',
                 'Biomechanical Analysis and Simulation':
                     'Biomechanical analysis &\nsimulation',
                 'Digital Design and Manufacturing':
                     'Digital design &\nmanufacturing',
                 'Surgical Planning and Precise Implementation':
                     'Surgical planning &\nprecise implementation',
                 'Morphological and Phenotypic Analysis':
                     'Morphological &\nphenotypic analysis'}
    SCEN = list(SCEN_FULL.keys())

    # 计算每个原型的场景构成
    comp, sizes = {}, {}
    for a in sorted(desc['Archetype']):
        sub = d[d['Archetype'] == a]
        sizes[a] = len(sub)
        cc = {s: 0 for s in SCEN}
        for lst in sub['_scen_l']:
            for s in set(lst):
                if s in cc:
                    cc[s] += 1
        tot = sum(cc.values())
        comp[a] = {s: (cc[s] / tot * 100 if tot else 0) for s in SCEN}

    ks = sorted(desc['Archetype'])
    nk = len(ks)
    fig, axes = plt.subplots(1, nk, figsize=(FIG_W, 4.3), sharey=True,
                             gridspec_kw={'wspace': 0.16, 'left': 0.20,
                                          'right': 0.995, 'top': 0.90, 'bottom': 0.22})
    if nk == 1:
        axes = [axes]
    ypos = np.arange(len(SCEN))[::-1]
    for ai, (ax, a) in enumerate(zip(axes, ks)):
        vals = [comp[a][s] for s in SCEN]
        imax = int(np.argmax(vals))
        colors = [C['coral'] if i == imax else C['grey_l'] for i in range(len(vals))]
        ax.barh(ypos, vals, color=colors, height=0.6)
        for yp, val in zip(ypos, vals):
            if val >= 8:
                ax.text(val + 3, yp, '%.0f' % val, va='center', fontsize=6.8,
                        color=C['ink'])
        ax.set_xlim(0, 118)
        ax.set_xticks([0, 50, 100])
        ax.set_xticklabels(['0', '50', '100'], fontsize=7)
        archetype_name = title_of(a, desc).replace('\n', ' ')
        ax.set_title('(%s) %s\nn = %d (%.1f%%)' %
                 (chr(ord('a') + ai), archetype_name, sizes[a], sizes[a] / N * 100),
                 fontsize=7.8, loc='left', pad=6, fontweight='bold',
                 linespacing=1.15)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        ax.xaxis.grid(True, color=C['grey_l'], lw=0.7)
        ax.set_axisbelow(True)
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels([SCEN_FULL[s] for s in SCEN], fontsize=7.2)
    for ax in axes:
        ax.set_xlabel('% of scenario\nassignments in archetype', fontsize=7.0)

    save(fig, 'Figure4_workflows')


# ==================================================================
# Figure 5 — 专科 × 软件功能族 列联分析（标准化残差）
# ==================================================================
def fig5():
    from scipy.stats import chi2_contingency
    from itertools import combinations

    SPEC_KEEP = 8
    spec_list = list(S['speciality'].keys())[:SPEC_KEEP]
    fam_list = [f for f, _ in sorted(
        {f: sum(1 for lst in d['_soft_l'] if any(fam_of(s) == f for s in lst))
         for f in ['MIP', 'RE', 'SIM', 'GEN3D', 'CAD']}.items(), key=lambda x: -x[1])]

    M = np.zeros((len(spec_list), len(fam_list)), dtype=int)
    for _, r in d.iterrows():
        sps = set(r['_spec_l'])
        fams = {fam_of(s) for s in r['_soft_l']}
        fams.discard(None)
        for i, sp in enumerate(spec_list):
            if sp in sps:
                for j, f in enumerate(fam_list):
                    if f in fams:
                        M[i, j] += 1
    chi2, p, dof, exp = chi2_contingency(M)
    cramers_v = float(np.sqrt(chi2 / (M.sum() * (min(M.shape) - 1))))
    resid = (M - exp) / np.sqrt(exp * (1 - M.sum(axis=1, keepdims=True) / M.sum())
                               * (1 - M.sum(axis=0, keepdims=True) / M.sum()))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FIG_W, 3.6),
                                   gridspec_kw={'wspace': 0.26, 'left': 0.215,
                                                'right': 0.975, 'top': 0.905, 'bottom': 0.185})
    # 轴标签用缩写（全称见图注），避免长字符串旋转后难以阅读
    SPEC_ABBR = {'Prosthodontics': 'Prosthodontics',
                 'Oral and Maxillofacial Surgery': 'OMF surgery',
                 'Oral Implantology': 'Implantology',
                 'Orthodontics': 'Orthodontics',
                 'Oral and Maxillofacial Radiology': 'OMF radiology',
                 'Endodontics': 'Endodontics',
                 'Periodontics': 'Periodontics',
                 'Forensic Odontology': 'Forensic odont.'}
    FAM_ABBR = {'MIP': 'MIP', 'RE': 'RE', 'SIM': 'SIM', 'GEN3D': 'GEN3D', 'CAD': 'CAD'}
    labels_y = [SPEC_ABBR.get(s, s) for s in spec_list]
    labels_x = [FAM_ABBR.get(f, f) for f in fam_list]

    for ax, data, ptag, cmap, fmt in [
            (ax1, M, '(a)', 'Blues', '%d'),
            (ax2, resid, '(b)', 'RdBu_r', '%.1f')]:
        vmax = np.abs(data).max()
        im = ax.imshow(data, cmap=cmap, vmin=(-vmax if 'RdBu' in cmap else 0), vmax=vmax)
        ax.set_xticks(range(len(labels_x)))
        ax.set_xticklabels(labels_x, fontsize=FS['tick'])
        ax.set_yticks(range(len(labels_y)))
        ax.set_yticklabels(labels_y, fontsize=FS['tick'])
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                dark = abs(val) > (vmax * 0.55)
                ax.text(j, i, fmt % val, ha='center', va='center', fontsize=FS['val'],
                        color=('white' if dark else C['ink']),
                        fontweight='bold' if abs(val) >= 2 else 'normal')
        ax.set_title(ptag, fontsize=FS['panel'], loc='left', pad=5, fontweight='bold')
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0)
        cb = fig.colorbar(im, ax=ax, fraction=0.042, pad=0.025)
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=FS['val'])

    save(fig, 'Figure5_contingency')

    json.dump({'chi2': float(chi2), 'df': int(dof), 'p': float(p),
               'cramers_v': cramers_v, 'n_cells': int(M.sum()),
               'spec': spec_list, 'fam': fam_list,
               'counts': M.tolist(), 'residuals': np.round(resid, 3).tolist()},
              open(os.path.join(OUT, 'fig5_stats.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)


# ==================================================================
# Figure 6 — 纳入研究报告的优势 / 挑战 / 缺口
# ==================================================================
def fig6():
    fp = os.path.join(ANA, 'RQ3_频次汇总.json')
    if not os.path.exists(fp):
        print('  RQ3_频次汇总.json 尚未生成，跳过 Figure 6')
        return
    R = json.load(open(fp, encoding='utf-8'))
    n = R['n_studies']

    panels = [('advantages', '(a)', C['green']),
              ('challenges', '(b)', C['coral']),
              ('gaps', '(c)', C['purple'])]

    NONE_CODE = {'advantages': 'A9', 'challenges': 'C9', 'gaps': 'G9'}
    NONE_TEXT = {'advantages': 'no advantage stated', 'challenges': 'no challenge stated',
                 'gaps': 'no gap stated'}

    fig, axes = plt.subplots(1, 3, figsize=(FIG_W, 4.5), sharey=True,
                             gridspec_kw={'wspace': 0.14, 'left': 0.30,
                                          'right': 0.99, 'top': 0.915, 'bottom': 0.16})
    for ax, (key, title, color) in zip(axes, panels):
        none_n = next((x['n'] for x in R[key] if x['code'] == NONE_CODE[key]), 0)
        none_pct = round(none_n / n * 100, 1)
        items = [x for x in R[key] if not x['code'].endswith('9')]
        items = items[::-1]
        if not items:
            continue
        labels = [x['label'] for x in items]
        vals = [x['n'] for x in items]
        ypos = np.arange(len(items))
        ax.barh(ypos, vals, color=color, height=0.6)
        for yp, x in zip(ypos, items):
            ax.text(x['n'] + max(vals) * 0.02, yp, '%d (%.0f%%)' % (x['n'], x['pct']),
                    va='center', fontsize=7.2)
        ax.set_yticks(ypos)
        ax.set_yticklabels([l.replace(' / ', ' /\n') for l in labels], fontsize=FS['tick'])
        if ax is not axes[0]:
            ax.tick_params(labelleft=False)
        ax.set_xlabel('Number of studies', fontsize=FS['lab'])
        ax.set_xlim(0, max(vals) * 1.34)
        ax.set_title(('(%s)' % chr(ord('a') + panels.index((key, title, color)))),
                     fontsize=10.5, loc='left', pad=6, fontweight='bold')
        tidy(ax, grid='x')

    save(fig, 'Figure6_rq3')


if __name__ == '__main__':
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
    print('done ->', OUT)