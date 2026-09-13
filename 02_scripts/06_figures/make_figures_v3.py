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
make_figures_v3.py  —— R2 定稿图（N = 566）
设计原则：简洁、直观、全图统一配色与字号；去图表垃圾；直接标注数值。
唯一数字来源：03_数据/08_分析用/统计核心.json + 分析数据集_final_v3.csv
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

S = json.load(open(os.path.join(ANA, '统计核心.json'), encoding='utf-8'))
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)
SW = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
N = len(d)

# ---------------- 统一视觉系统 ----------------
C = {'blue': '#2E6DA4', 'blue_l': '#A8C4DE', 'teal': '#3F9C9C', 'teal_l': '#B2DBDB',
     'amber': '#D98C2B', 'amber_l': '#F2D6AE', 'coral': '#C0553F', 'coral_l': '#EBC4BA',
     'purple': '#6E5EA8', 'purple_l': '#CFC7E6', 'green': '#4C9366', 'green_l': '#BFDCCB',
     'grey': '#7E8B99', 'grey_l': '#DCE2E8', 'ink': '#26313C'}
SEQ = [C['blue'], C['teal'], C['amber'], C['purple'], C['green'], C['coral']]
SEQ_L = [C['blue_l'], C['teal_l'], C['amber_l'], C['purple_l'], C['green_l'], C['coral_l']]

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.edgecolor': C['ink'], 'axes.linewidth': 0.8,
    'axes.labelcolor': C['ink'], 'text.color': C['ink'],
    'xtick.color': C['ink'], 'ytick.color': C['ink'],
    'xtick.major.size': 3, 'ytick.major.size': 3,
    'savefig.bbox': 'tight', 'figure.dpi': 120,
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

    fig, ax = plt.subplots(figsize=(8.8, 10.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13.4)
    ax.axis('off')

    def box(x, y, w, h, txt, fc, ec, fs=8.2, bold=False, align='center'):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05',
                                    fc=fc, ec=ec, lw=0.9))
        ha = 'center' if align == 'center' else 'left'
        tx = x + w / 2 if align == 'center' else x + 0.16
        ax.text(tx, y + h / 2, txt, ha=ha, va='center', fontsize=fs,
                fontweight='bold' if bold else 'normal', linespacing=1.45)

    def arrow(x1, y1, x2, y2, color=None, ls='-'):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                                     mutation_scale=10, color=color or C['ink'],
                                     lw=0.9, linestyle=ls))

    LX, LW = 0.35, 5.4
    RX, RW = 6.3, 3.35
    stag = dict(fontsize=8.6, fontweight='bold', ha='center', color=C['blue'])

    ax.text(5, 13.1, 'Identification', **stag)
    box(LX, 11.55, LW, 1.25,
        'Records identified from databases\n(n = %s)\n'
        'PubMed (n = 1,727)  ·  Web of Science (n = 1,695)  ·  IEEE Xplore (n = 304)'
        % format(n_ident, ','), C['blue_l'], C['blue'])
    box(RX, 11.55, RW, 1.25,
        'Duplicate records removed\nbefore screening (n = %s)' % format(n_dup, ','),
        C['grey_l'], C['grey'], fs=7.9)
    arrow(5.75, 12.18, 6.3, 12.18)

    ax.text(5, 10.95, 'Screening', **stag)
    box(LX, 9.05, LW, 1.55,
        'Records screened at title/abstract level\n(n = %s)\n'
        'Topic, article type, language and date criteria;\nLLM-assisted, three independent runs '
        '(Fleiss\u2019 \u03ba = 0.936)' % format(n_scr, ','), C['blue_l'], C['blue'])
    arrow(3.05, 11.55, 3.05, 10.6)
    box(RX, 8.55, RW, 2.05,
        'Records excluded at title/abstract\nscreening (n = %s)\n\n'
        'Full text available and re-assessed: %s\nNo full text available: %s'
        % (format(n_excl, ','), format(n_ft, ','), format(n_noft, ',')),
        C['grey_l'], C['grey'], fs=7.4, align='left')
    arrow(5.75, 9.8, 6.3, 9.8)

    ax.text(5, 8.15, 'Eligibility', **stag)
    box(LX, 6.35, LW, 1.4,
        'Records assessed for eligibility\nat full text (n = %s)\n'
        '613 progressed from title/abstract screening\n'
        '+ %s excluded records re-assessed in full text'
        % (format(n_assess, ','), format(n_ft, ',')), C['blue_l'], C['blue'])
    arrow(3.05, 9.05, 3.05, 7.75)
    box(RX, 6.35, RW, 1.4,
        'Records excluded after\nfull-text assessment (n = %s)\n\n'
        'Not eligible on full-text review: %s\n'
        'Excluded at full-text screening: 47\n'
        'Removed from the previous set: 4\n'
        'Outside the date window: 3'
        % (format(n_ft_excl, ','), format(n_ft - n_new, ',')),
        C['grey_l'], C['grey'], fs=7.4, align='left')
    arrow(5.75, 7.05, 6.3, 7.05)

    ax.text(5, 5.55, 'Included', **stag)
    box(LX, 4.3, LW, 1.3,
        'Studies included in the scoping review\n(n = %s)' % format(N, ','),
        C['green_l'], C['green'], bold=True, fs=9.6)
    arrow(3.05, 6.35, 3.05, 5.6)

    box(LX, 2.35, LW, 1.55,
        'Full-text re-assessment of excluded records\n\n'
        '%s records re-assessed in full text\n'
        '\u2192 %s met the eligibility criteria \n'
        '    and were added to the review'
        % (format(n_ft, ','), format(n_new, ',')),
        C['amber_l'], C['amber'], fs=7.4, align='left')
    arrow(LX + LW / 2, 6.35, LX + LW / 2, 3.9, color=C['amber'], ls='--')

    ax.text(LX, 2.05,
            'Screening was performed with large-language-model assistance and is fully logged '
            '(prompts, raw API responses, decoding parameters and dates).\n'
            'The requirement for explicit use of a non-dental 3D software cannot be evaluated '
            'reliably at abstract level, because the software is\nusually named only in the methods '
            'section; every excluded record with a retrievable full text was therefore re-assessed '
            'in full text.\n'
            'Language and date limits were applied at the database-search level and were not '
            'delegated to the model.',
            fontsize=6.9, va='top', color='#4A5560', linespacing=1.55)

    fig.suptitle('Figure 1. PRISMA flow diagram of study selection',
                 fontsize=11.5, y=0.988, fontweight='bold')
    save(fig, 'Figure1_PRISMA')


# ==================================================================
# Figure 2 — 领域全景（趋势 / 地图 / 研究设计 / 专科）
# ==================================================================
def fig2():
    tr = S['trend']
    x = np.arange(len(HALF))
    v = [tr[h] for h in HALF]

    fig = plt.figure(figsize=(13.6, 9.2))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.40, wspace=0.22,
                           left=0.07, right=0.98, top=0.90, bottom=0.09)

    # (a) 趋势
    ax = fig.add_subplot(gs[0, 0])
    ax.bar(x, v, color=C['blue_l'], edgecolor=C['blue'], lw=0.7, width=0.7, zorder=2)
    for i, val in enumerate(v):
        ax.text(i, val + 1.0, str(val), ha='center', fontsize=7.4, color=C['ink'])
    ax.set_xticks(x)
    ax.set_xticklabels(HALF, rotation=45, ha='right', fontsize=7.6)
    ax.set_ylabel('Number of publications')
    ax.set_ylim(0, max(v) * 1.30)
    ax.set_title('(a)  Semi-annual publication trend', fontsize=10, loc='left', pad=8)
    tidy(ax)
    ax.patches[-1].set_facecolor(C['amber_l'])
    ax.patches[-1].set_edgecolor(C['amber'])
    ax.annotate('2026-H1 incomplete\n(search closed 30 Jun 2026)',
                xy=(11, v[-1]), xytext=(7.3, max(v) * 1.11), fontsize=6.9,
                color=C['amber'], ha='left',
                arrowprops=dict(arrowstyle='->', color=C['amber'], lw=0.9))

    # (b) 世界地图
    ax = fig.add_subplot(gs[0, 1])
    try:
        import geopandas as gpd
        import warnings
        warnings.filterwarnings('ignore', 'Geometry is in a geographic CRS')
        bdir = os.path.join(OUT, '_basemap')
        os.makedirs(bdir, exist_ok=True)
        gp = os.path.join(bdir, 'ne_110m_admin_0_countries.geojson')
        world = gpd.read_file(gp)
        key = 'ISO_A3' if 'ISO_A3' in world.columns else world.columns[0]
        world[key] = world[key].astype(str)
        reg = d['Region'].astype(str).value_counts()
        world['n'] = world[key].map(reg).fillna(0)
        world.plot(column='n', ax=ax, cmap='Blues', edgecolor='white', lw=0.35,
                   legend=True, missing_kwds={'color': '#F0F2F4'},
                   legend_kwds={'shrink': 0.5, 'label': 'Studies (n)', 'pad': 0.012})
        ax.set_axis_off()
        top5 = reg.head(5)
        ax.set_title('(b)  Geographic distribution of included studies', fontsize=10,
                     loc='left', pad=8)
        ax.text(0.01, -0.02, 'Leading contributors: ' + ', '.join(
            '%s (%d)' % (k, v) for k, v in top5.items()),
            transform=ax.transAxes, fontsize=6.9, va='top', color=C['grey'])
    except Exception as e:
        print('  map fallback:', e)
        reg = d['Region'].value_counts().head(12)[::-1]
        ax.barh(range(len(reg)), reg.values, color=C['teal'], height=0.65)
        ax.set_yticks(range(len(reg)))
        ax.set_yticklabels(reg.index, fontsize=7.6)
        ax.set_xlabel('Number of studies')
        ax.set_title('(b)  Geographic distribution (top 12)', fontsize=10, loc='left', pad=8)
        tidy(ax, grid='x')

    # (c) 研究设计
    ax = fig.add_subplot(gs[1, 0])
    st = S['study_type']
    lblmap = {'computational': 'Computational /\nsimulation', 'in_vitro': 'In vitro',
              'clinical': 'Clinical', 'technical_note': 'Technical note',
              'case_report': 'Case report', 'educational': 'Educational'}
    ks = list(st.keys())
    vals = [st[k] for k in ks]
    ypos = np.arange(len(ks))[::-1]
    ax.barh(ypos, vals, color=[SEQ[i % len(SEQ)] for i in range(len(ks))], height=0.62)
    for yp, val, k in zip(ypos, vals, ks):
        ax.text(val + max(vals) * 0.015, yp, '%d (%.1f%%)' % (val, val / N * 100),
                va='center', fontsize=7.8)
    ax.set_yticks(ypos)
    ax.set_yticklabels([lblmap.get(k, k) for k in ks], fontsize=8)
    ax.set_xlabel('Number of studies')
    ax.set_xlim(0, max(vals) * 1.24)
    ax.set_title('(c)  Study design', fontsize=10, loc='left', pad=8)
    tidy(ax, grid='x')

    # (d) 专科
    ax = fig.add_subplot(gs[1, 1])
    sp = S['speciality']
    ks = list(sp.keys())[:8][::-1]
    vals = [sp[k] for k in ks]
    ypos = np.arange(len(ks))
    ax.barh(ypos, vals, color=C['teal'], height=0.62)
    for yp, val in zip(ypos, vals):
        ax.text(val + max(vals) * 0.015, yp, str(val), va='center', fontsize=7.8)
    ax.set_yticks(ypos)
    ax.set_yticklabels([k.replace('Oral and Maxillofacial', 'OMF') for k in ks], fontsize=8)
    ax.set_xlabel('Study\u2013speciality assignments')
    ax.set_xlim(0, max(vals) * 1.16)
    ax.set_title('(d)  Dental specialities (multi-label)', fontsize=10, loc='left', pad=8)
    tidy(ax, grid='x')

    fig.suptitle('Figure 2. Landscape of the included literature (n = %d)' % N,
                 fontsize=11.5, y=0.965, fontweight='bold')
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

    fig = plt.figure(figsize=(13.6, 4.6))
    gs = gridspec.GridSpec(1, 3, figure=fig, wspace=0.30,
                           left=0.06, right=0.985, top=0.84, bottom=0.16,
                           width_ratios=[1.0, 1.35, 0.85])

    # (a) 软件功能族
    ax = fig.add_subplot(gs[0])
    items = sorted(fam_n.items(), key=lambda x: -x[1])[:6]
    labs = [FAMILY[k].replace('\n', ' ') for k, _ in items]
    vals = [v for _, v in items]
    ypos = np.arange(len(items))[::-1]
    ax.barh(ypos, vals, color=[SEQ_L[i] for i in range(len(items))],
            edgecolor=[SEQ[i] for i in range(len(items))], lw=0.8, height=0.62)
    for yp, val in zip(ypos, vals):
        ax.text(val + max(vals) * 0.02, yp, '%d (%.0f%%)' % (val, val / N * 100),
                va='center', fontsize=7.6)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labs, fontsize=7.8)
    ax.set_xlabel('Number of studies')
    ax.set_xlim(0, max(vals) * 1.26)
    ax.set_title('(a)  Software families used', fontsize=9.8, loc='left', pad=8)
    tidy(ax, grid='x')

    # (b) Top 15 软件包
    ax = fig.add_subplot(gs[1])
    top = list(S['software_top'].items())[:12][::-1]
    labs = [k for k, _ in top]
    vals = [v for _, v in top]
    ypos = np.arange(len(top))
    ax.barh(ypos, vals, color=C['blue'], height=0.66)
    for yp, val in zip(ypos, vals):
        ax.text(val + max(vals) * 0.018, yp, str(val), va='center', fontsize=7.4)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labs, fontsize=7.8)
    ax.set_xlabel('Number of studies')
    ax.set_xlim(0, max(vals) * 1.12)
    ax.set_title('(b)  Most frequently reported software packages',
                 fontsize=9.8, loc='left', pad=8)
    tidy(ax, grid='x')

    # (c) 每篇研究使用的软件包数
    ax = fig.add_subplot(gs[2])
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
    ax.set_title('(c)  Breadth of software use', fontsize=9.8, loc='left', pad=8)
    tidy(ax)
    ax.text(0.98, 0.94, '%d studies (%.1f%%) used\nmore than one package'
            % (S['n_studies_multi_software'], S['pct_multi_software']),
            transform=ax.transAxes, fontsize=7.0, ha='right', va='top', color=C['amber'])

    fig.suptitle('Figure 3. Software landscape across %d studies' % N,
                 fontsize=11.5, y=0.975, fontweight='bold')
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
    fig, axes = plt.subplots(1, nk, figsize=(2.9 * nk, 4.3), sharey=True,
                             gridspec_kw={'wspace': 0.15, 'left': 0.05,
                                          'right': 0.995, 'top': 0.79, 'bottom': 0.23})
    if nk == 1:
        axes = [axes]
    ypos = np.arange(len(SCEN))[::-1]
    for ax, a in zip(axes, ks):
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
        ax.set_title('%s\nn = %d (%.1f%%)' % (title_of(a, desc), sizes[a],
                                              sizes[a] / N * 100),
                     fontsize=8.4, pad=7)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        ax.xaxis.grid(True, color=C['grey_l'], lw=0.7)
        ax.set_axisbelow(True)
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels([SCEN_FULL[s] for s in SCEN], fontsize=7.2)
    for ax in axes:
        ax.set_xlabel('% of scenario\nassignments in archetype', fontsize=7.0)
    fig.text(0.5, 0.055,
             'Workflow archetypes were derived by unsupervised clustering of structured '
             'metadata (six application scenarios and seven software families; Jaccard distance, '
             'average-linkage hierarchical clustering, k = %d by silhouette; '
             'bootstrap ARI = %.2f across 100 resamples).\n'
             'Archetypes are data-driven groupings, not predefined or manually coded categories.'
             % (mp['k'], mp['bootstrap_ARI_mean']),
             ha='center', fontsize=6.9, color='#4A5560', linespacing=1.6)
    fig.suptitle('Figure 4. Data-driven workflow archetypes of non-dental 3D software use',
                 fontsize=11.2, y=0.965, fontweight='bold')
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

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 4.9),
                                   gridspec_kw={'wspace': 0.30, 'left': 0.155,
                                                'right': 0.99, 'top': 0.80, 'bottom': 0.30})
    labels_y = [s.replace('Oral and Maxillofacial', 'OMF') for s in spec_list]
    labels_x = [FAMILY[f].replace('\n', ' ') for f in fam_list]

    for ax, data, title, cmap, fmt in [
            (ax1, M, '(a)  Co-occurrence counts', 'Blues', '%d'),
            (ax2, resid, '(b)  Adjusted standardised residuals', 'RdBu_r', '%.1f')]:
        vmax = np.abs(data).max()
        im = ax.imshow(data, cmap=cmap, vmin=(-vmax if 'RdBu' in cmap else 0), vmax=vmax)
        ax.set_xticks(range(len(labels_x)))
        ax.set_xticklabels(labels_x, rotation=32, ha='right', fontsize=7.4)
        ax.set_yticks(range(len(labels_y)))
        ax.set_yticklabels(labels_y, fontsize=7.8)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                dark = abs(val) > (vmax * 0.55)
                ax.text(j, i, fmt % val, ha='center', va='center', fontsize=7.0,
                        color=('white' if dark else C['ink']),
                        fontweight='bold' if abs(val) >= 2 else 'normal')
        ax.set_title(title, fontsize=9.8, loc='left', pad=8)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=0)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
        cb.outline.set_visible(False)
        cb.ax.tick_params(labelsize=7)

    ax2.text(0.995, -0.42, '\u03c7\u00b2 = %.1f, df = %d, p %s; Cram\u00e9r\u2019s V = %.3f\n'
             'Cells with |residual| \u2265 2 are shown in bold.'
             % (chi2, dof, ('< 0.001' if p < 0.001 else '= %.3f' % p), cramers_v),
             transform=ax2.transAxes, fontsize=7.2, ha='right', va='top', color='#4A5560')
    fig.suptitle('Figure 5. Association between dental speciality and software family',
                 fontsize=11.2, y=0.965, fontweight='bold')
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

    panels = [('advantages', '(a)  Reported advantages', C['green']),
              ('challenges', '(b)  Reported challenges', C['coral']),
              ('gaps', '(c)  Reported gaps', C['purple'])]

    NONE_CODE = {'advantages': 'A9', 'challenges': 'C9', 'gaps': 'G9'}
    NONE_TEXT = {'advantages': 'no advantage stated', 'challenges': 'no challenge stated',
                 'gaps': 'no gap stated'}

    fig, axes = plt.subplots(1, 3, figsize=(14.6, 5.2),
                             gridspec_kw={'wspace': 0.55, 'left': 0.02,
                                          'right': 0.99, 'top': 0.78, 'bottom': 0.20})
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
        ax.set_yticklabels([l.replace(' / ', ' /\n') for l in labels], fontsize=7.4)
        ax.set_xlabel('Number of studies')
        ax.set_xlim(0, max(vals) * 1.34)
        ax.set_title('%s\n%s in %d studies (%.1f%%)'
                     % (title, NONE_TEXT[key], none_n, none_pct),
                     fontsize=9.6, loc='left', pad=8)
        tidy(ax, grid='x')

    fig.suptitle('Figure 6. Advantages, challenges and gaps reported by the included studies '
                 '(n = %d)' % n, fontsize=11.2, y=0.965, fontweight='bold')
    fig.text(0.5, 0.035,
             'Categories were coded from the title and abstract of each included study against a '
             'prespecified multi-select scheme; codes are not mutually exclusive and the denominator '
             'is all %d included studies. Studies that did not report the corresponding element are '
             'not plotted.' % n,
             ha='center', fontsize=7.0, color='#4A5560')
    save(fig, 'Figure6_rq3')


if __name__ == '__main__':
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
    print('done ->', OUT)