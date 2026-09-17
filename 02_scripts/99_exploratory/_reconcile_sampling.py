# -*- coding: utf-8 -*-
"""Reconcile the sampling-frame number (1939) with the PRISMA exclusion count (1943)."""
import csv, json, os, sys, glob, re

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'd:\Desktop\v8 for JD'

pr = json.load(open(os.path.join(ROOT, '03_数据', '08_分析用', 'PRISMA_链路_v2.json'), encoding='utf-8'))
print('PRISMA keys/values:')
for k, v in pr.items():
    if not isinstance(v, (list, dict)):
        print(f'   {k} = {v}')

# look for sampling artefacts
hits = []
for pat in ('**/*sampl*', '**/*抽样*', '**/*抽样*', '**/*sample*'):
    for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
        hits.append(p)
print('\nsampling-related files:')
for h in sorted(set(hits))[:25]:
    print('   ', h)
