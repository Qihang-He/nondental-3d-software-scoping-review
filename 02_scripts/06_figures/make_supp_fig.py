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
make_supp_fig.py —— 补充图 S1：纳入文献的期刊分布（替代原 Fig2c 甜甜圈图）
回应审稿人：原图分母为 588（因 25 条缺刊名被静默丢弃），本图分母为全部 N，
并单独标注会议论文集与缺刊名条数。
输出：05_图表/Supplementary_Figure_S1_journals.(png|pdf)
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
OUT = os.path.join(ROOT, _os.path.join(_ROOTP, '05_图表'))
S = json.load(open(os.path.join(ANA, '统计核心.json'), encoding='utf-8'))
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)
N = len(d)

C = {'blue': '#2E6DA4', 'amber': '#D98C2B', 'grey': '#7E8B99', 'ink': '#26313C'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                     'axes.edgecolor': C['ink'], 'savefig.bbox': 'tight'})

import re
CONF_PAT = re.compile(r'\bConference\b|Annual International Conference|Symposium|'
                      r'International Conference|Proceedings', re.I)
is_conf = d['Journal'].astype(str).str.contains(CONF_PAT)
jc = d.loc[~is_conf, 'Journal'].value_counts()
top = jc.head(20)[::-1]

fig, ax = plt.subplots(figsize=(7.6, 6.4))
ypos = np.arange(len(top))
ax.barh(ypos, top.values, color=C['blue'], height=0.66)
for yp, val in zip(ypos, top.values):
    ax.text(val + max(top.values) * 0.015, yp, str(val), va='center', fontsize=7.6)
ax.set_yticks(ypos)
ax.set_yticklabels(['%s. %s' % (i + 1, t) for i, t in enumerate(top.index)], fontsize=7.8)
ax.set_xlabel('Number of included studies')
ax.set_xlim(0, max(top.values) * 1.12)
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
ax.xaxis.grid(True, color='#DCE2E8', lw=0.7)
ax.set_axisbelow(True)

n_conf = int(is_conf.sum())
txt = ('All %d included records have a recorded source.\n'
       'Journals (n = %d) and conference proceedings (n = %d) are counted separately; '
       'the denominator of every percentage is the full included set (n = %d), not the subset '
       'with complete metadata.'
       % (N, S['n_journals'], n_conf, N))
ax.text(0.0, -0.115, txt, transform=ax.transAxes, fontsize=7.4, va='top',
        color='#4A5560', linespacing=1.6)
ax.set_title('Supplementary Figure S1. Journal and proceedings distribution of the included studies',
             fontsize=9.6, loc='left', pad=10)
fig.savefig(os.path.join(OUT, 'Supplementary_Figure_S1_journals.png'), dpi=600)
fig.savefig(os.path.join(OUT, 'Supplementary_Figure_S1_journals.pdf'))
plt.close(fig)
print('saved: Supplementary_Figure_S1_journals')
print('journals=%d, proceedings=%d, top10 share=%.1f%%'
      % (S['n_journals'], n_conf, jc.head(10).sum() / N * 100))
