# -*- coding: utf-8 -*-
"""Regenerate the canonical software-name list from the revised glossary, then run
the core statistics pipeline on the scope-revised (v6) locked dataset."""
import os
import subprocess
import sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
ANA = os.path.join('03_数据', '08_分析用')
SWD = os.path.join('03_数据', '09_软件表')

# ---- 1) canonical software-name list (alias -> canonical) from the revised glossary
g = pd.read_csv(os.path.join(SWD, '软件类别与来源表.csv'), low_memory=False)
g.columns = ['original_name', 'canonical_name', 'category', 'development_domain',
             'developer', 'source_url', 'url_status', 'n_studies']
out = g[['canonical_name', 'n_studies']].drop_duplicates('canonical_name').copy()
out.columns = ['软件', '研究数']
out = out.sort_values('研究数', ascending=False).reset_index(drop=True)
dst = os.path.join(ANA, '软件规范名清单_v6.csv')
out.to_csv(dst, index=False, encoding='utf-8-sig')
print('wrote %s  (%d packages)' % (dst, len(out)))

# ---- 2) core pipeline
STEPS = [
    os.path.join('04_代码', '05_分析', '_tools_stats_core.py'),
    os.path.join('04_代码', '05_分析', '_tools_archetype_derive_v5.py'),
    os.path.join('04_代码', '05_分析', '_rq3_summarize_v4.py'),
    os.path.join('04_代码', '05_分析', '_tools_extra_stats_v3.py'),
]
env = dict(os.environ, PYTHONIOENCODING='utf-8')
for s in STEPS:
    print('=== RUN', s)
    p = subprocess.run([sys.executable, s], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env=env)
    tail = (p.stdout or '').strip().splitlines()[-6:]
    for line in tail:
        print('    ' + line)
    if p.returncode != 0:
        print('    !! FAILED rc=%d' % p.returncode)
        print((p.stderr or '')[-2000:])
        break
print('DONE')
