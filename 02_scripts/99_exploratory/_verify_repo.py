# -*- coding: utf-8 -*-
"""Verify the rebuilt public repository: naming rules and headline data consistency."""
import json
import os
import re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
REPO = os.path.join('06_公共仓库')
files = []
for root, dirs, fs in os.walk(REPO):
    dirs[:] = [x for x in dirs if x != '.git']
    for f in fs:
        files.append(os.path.relpath(os.path.join(root, f), REPO))

VER = re.compile(r'(_v\d+(\.\d+)?|_R\d+)(?=[._]|$)', re.I)
cn = [p for p in files if re.search(r'[\u4e00-\u9fff]', p)]
ver = [p for p in files if VER.search(os.path.splitext(os.path.basename(p))[0])]
print('files                          : %d' % len(files))
print('Chinese characters in filenames: %d %s' % (len(cn), cn[:5]))
print('version tags in filenames      : %d %s' % (len(ver), ver[:5]))

S = json.load(open(os.path.join(REPO, '05_results', 'statistics_core.json'), encoding='utf-8'))
P = json.load(open(os.path.join(REPO, '05_results', 'prisma_flow.json'), encoding='utf-8'))
E = json.load(open(os.path.join(REPO, '05_results', 'supplementary_statistics.json'),
                   encoding='utf-8'))
R = json.load(open(os.path.join(REPO, '05_results', 'rq3_frequencies.json'), encoding='utf-8'))
D = pd.read_csv(os.path.join(REPO, '06_data', 'locked_analysis_dataset.csv'), low_memory=False)
G = pd.read_csv(os.path.join(REPO, '06_data', 'software_glossary.csv'), low_memory=False)
N = S['N']

checks = [
    ('locked dataset rows == N', len(D) == N == 853),
    ('record_id is 1..N', list(D['record_id']) == list(range(1, N + 1))),
    ('statistics_core packages == glossary packages',
     S['n_software_packages'] == G['canonical_name'].nunique() == 100),
    ('prisma included == N', P['included'] == N),
    ('prisma breakdown sums to excluded',
     sum(P['exclusion_breakdown'].values()) == P['excluded_after_fulltext_assessment']),
    ('prisma early stages reconcile',
     P['assessed_for_eligibility_full_text'] - P['excluded_after_fulltext_assessment'] == N),
    ('multi-software share consistent',
     S['n_studies_multi_software'] + S['n_studies_single_software'] == N),
    ('RQ3 denominator == N', R['N_analysed'] == N),
    ('contingency chi2 is the v6 value', abs(E['contingency_full']['chi2'] - 296.358) < 0.01),
    ('no software_scope revision rows missing',
     os.path.exists(os.path.join(REPO, '05_results', 'software_scope_revision.csv'))),
    ('glossary has no programming platforms',
     not set(['MATLAB', 'Python', 'GNU Octave', 'TensorFlow', 'Keras', 'Open3D', 'Trimesh',
              'Iso2mesh', 'R2 Gate', 'Viewbox']) & set(G['canonical_name'])),
    ('README cites the current figshare DOI',
     '10.6084/m9.figshare.33900364' in open(os.path.join(REPO, 'README.md'),
                                            encoding='utf-8').read()),
    ('CITATION cites the current figshare DOI',
     '10.6084/m9.figshare.33900364' in open(os.path.join(REPO, 'CITATION.cff'),
                                            encoding='utf-8').read()),]
print()
bad = 0
for label, ok in checks:
    print('%-52s %s' % (label, 'OK' if ok else '** FAIL **'))
    bad += 0 if ok else 1
print()
print('repository verification: %s' % ('PASS' if (bad == 0 and not cn and not ver) else 'FAILED'))
