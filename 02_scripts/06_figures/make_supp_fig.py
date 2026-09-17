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
S = json.load(open(os.path.join(ANA, '统计核心_v5.json'), encoding='utf-8'))
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v5.csv'), low_memory=False)
N = len(d)

C = {'blue': '#2E6DA4', 'amber': '#D98C2B', 'grey': '#7E8B99', 'ink': '#26313C'}
# 按最终印刷尺寸绘制（全幅 17.5 cm），字号即为印刷字号
FIG_W = 6.9
FS = {'lab': 8.0, 'tick': 7.2, 'val': 6.8}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': FS['tick'],
                     'axes.edgecolor': C['ink'], 'axes.linewidth': 0.7,
                     'axes.labelsize': FS['lab'], 'savefig.bbox': 'tight',
                     'pdf.fonttype': 42})

import re
CONF_PAT = re.compile(r'\bConference\b|Annual International Conference|Symposium|'
                      r'International Conference|Proceedings', re.I)
is_conf = d['Journal'].astype(str).str.contains(CONF_PAT)
jc = d.loc[~is_conf, 'Journal'].value_counts()
top = jc.head(20)[::-1]


def _short(s, n=34):
    s = str(s)
    return s if len(s) <= n else s[:n - 1] + '\u2026'


fig, ax = plt.subplots(figsize=(FIG_W, 5.4),
                       gridspec_kw={'left': 0.34, 'right': 0.985,
                                    'top': 0.975, 'bottom': 0.10})
ypos = np.arange(len(top))
ax.barh(ypos, top.values, color=C['blue'], height=0.68)
for yp, val in zip(ypos, top.values):
    ax.text(val + max(top.values) * 0.02, yp, str(val), va='center', fontsize=FS['val'])
ax.set_yticks(ypos)
ax.set_yticklabels(['%d. %s' % (i + 1, _short(t)) for i, t in enumerate(top.index)],
                   fontsize=FS['tick'])
ax.set_xlabel('Number of included studies', fontsize=FS['lab'])
ax.set_xlim(0, max(top.values) * 1.16)
ax.set_ylim(-0.6, len(top) - 0.4)
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
ax.xaxis.grid(True, color='#DCE2E8', lw=0.7)
ax.set_axisbelow(True)

n_conf = int(is_conf.sum())
fig.savefig(os.path.join(OUT, 'Supplementary_Figure_S1_journals.png'), dpi=600)
fig.savefig(os.path.join(OUT, 'Supplementary_Figure_S1_journals.pdf'))
plt.close(fig)
print('saved: Supplementary_Figure_S1_journals')
print('journals=%d, proceedings=%d, top10 share=%.1f%%'
      % (S['n_journals'], n_conf, jc.head(10).sum() / N * 100))
