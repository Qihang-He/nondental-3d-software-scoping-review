# -*- coding: utf-8 -*-
"""Bump active pipeline scripts from the v5 artifacts to the v6 (scope-revised) artifacts."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

FILES = [
    os.path.join('04_代码', '05_分析', '_tools_stats_core.py'),
    os.path.join('04_代码', '05_分析', '_rq3_summarize_v4.py'),
    os.path.join('04_代码', '05_分析', '_tools_archetype_derive_v5.py'),
    os.path.join('04_代码', '05_分析', '_tools_extra_stats_v3.py'),
    os.path.join('04_代码', '06_新图', 'make_figures_v3.py'),
    os.path.join('04_代码', '06_新图', 'make_supp_fig.py'),
    os.path.join('04_代码', '07_文档', '_tools_supp2_v2.py'),
    os.path.join('04_代码', '07_文档', '_tools_supp3_v2.py'),
    os.path.join('04_代码', '07_文档', '_tools_provenance_v4.py'),
    os.path.join('04_代码', '07_文档', '_final_check.py'),
    os.path.join('04_代码', '07_文档', '_tools_build_repo_v5.py'),
]

REPL = [
    ('分析数据集_final_v5.csv', '分析数据集_final_v6.csv'),
    ('统计核心_v5.json', '统计核心_v6.json'),
    ('补充统计_v3.json', '补充统计_v4.json'),
    ('RQ3_编码明细_v5.csv', 'RQ3_编码明细_v6.csv'),
    ('软件规范名清单_v5.csv', '软件规范名清单_v6.csv'),
]

for p in FILES:
    if not os.path.exists(p):
        print('MISSING', p)
        continue
    s = open(p, encoding='utf-8').read()
    orig = s
    hits = []
    for a, b in REPL:
        n = s.count(a)
        if n:
            hits.append('%s->%s x%d' % (a, b, n))
            s = s.replace(a, b)
    if s != orig:
        open(p, 'w', encoding='utf-8').write(s)
        print('patched %-46s %s' % (os.path.basename(p), '; '.join(hits)))
    else:
        print('no change %-45s' % os.path.basename(p))
