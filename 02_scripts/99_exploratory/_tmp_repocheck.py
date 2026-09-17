# -*- coding: utf-8 -*-
"""Verify the rebuilt public repository: filenames, counts and content conventions."""
import os
import re
import json
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
REPO = os.path.join('06_公共仓库')
OUT = os.path.join('04_代码', '07_文档', '_tmp_repocheck.txt')
L = []

bad_cn, bad_ver, files = [], [], []
VER = re.compile(r'(_v\d+|_v\d+\.\d+|_R\d+|_r\d+)(?=[._]|$)', re.I)
for root, dirs, fs in os.walk(REPO):
    for f in fs:
        p = os.path.relpath(os.path.join(root, f), REPO)
        files.append(p)
        if re.search(r'[\u4e00-\u9fff]', p):
            bad_cn.append(p)
        if VER.search(os.path.splitext(f)[0]):
            bad_ver.append(p)

L.append('total files: %d' % len(files))
L.append('filenames with Chinese characters: %d' % len(bad_cn))
for p in bad_cn[:20]:
    L.append('   ' + p)
L.append('filenames containing a version tag: %d' % len(bad_ver))
for p in bad_ver[:20]:
    L.append('   ' + p)

L.append('')
L.append('=== 06_data ===')
for f in sorted(os.listdir(os.path.join(REPO, '06_data'))):
    p = os.path.join(REPO, '06_data', f)
    if f.endswith('.csv'):
        d = pd.read_csv(p, low_memory=False)
        L.append('   %-40s %s rows=%d cols=%d' % (f, d.shape, len(d), len(d.columns)))
        if 'record_id' in d.columns and len(d) == 853:
            L.append('       record_id 1..%d ; first=%s last=%s'
                     % (d['record_id'].max(), d['record_id'].min(), d['record_id'].max()))
        if 'category' in d.columns:
            L.append('       distinct software = %d' % d['canonical_name'].nunique())
            L.append('       categories = %s' % sorted(d['category'].unique()))
    else:
        L.append('   %s' % f)

L.append('')
L.append('=== 05_results ===')
for f in sorted(os.listdir(os.path.join(REPO, '05_results'))):
    L.append('   ' + f)

L.append('')
S = json.load(open(os.path.join(REPO, '05_results', 'statistics_core.json'), encoding='utf-8'))
L.append('statistics_core: N=%d packages=%d assignments=%d'
         % (S['N'], S['n_software_packages'], S['software_assignments']))
P = json.load(open(os.path.join(REPO, '05_results', 'prisma_flow.json'), encoding='utf-8'))
L.append('prisma_flow: included=%d' % P['included'])
E = json.load(open(os.path.join(REPO, '05_results', 'supplementary_statistics.json'),
                   encoding='utf-8'))
L.append('supplementary: chi2=%.3f dof=%d V=%.4f'
         % (E['contingency_full']['chi2'], E['contingency_full']['dof'],
            E['contingency_full']['cramers_v']))

L.append('')
L.append('=== README / CITATION key lines ===')
for f in ('README.md', 'CITATION.cff'):
    p = os.path.join(REPO, f)
    txt = open(p, encoding='utf-8').read()
    for line in txt.splitlines():
        if re.search(r'\b853\b|\b861\b|\b100\b|\b110\b|10\.6084|figshare|GitHub', line):
            L.append('   [%s] %s' % (f, line.strip()[:150]))

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
