# -*- coding: utf-8 -*-
"""Probe specific reference rows inside the locked v6 dataset."""
import csv, io, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

DS = r'd:\Desktop\v8 for JD\03_数据\08_分析用\分析数据集_final_v6.csv'

with open(DS, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))

print('dataset rows:', len(rows))
print('columns:', list(rows[0].keys()))
print()

probes = {
    'bar clip / Elkhadem': r'bar[ -]?clip|Elkhadem',
    'VirtuEleDent / Wang': r'VirtuEleDent|tooth-cutting',
    'Loetzerich 19': r'Loetzerich|marginal and internal fit',
    'Merken 27': r'Merken|anthropomorphic phantom',
    'Ruggiero 36': r'Ruggiero|Jaw motion tracking',
    'Liu 43': r'osteotomy and root-end',
    'Ding 44': r'Semi-Autonomous',
    'Zhao 49': r'palatal rugae',
    'Zhang 14': r'thresholds and voxels',
    'Mancino 50': r'dens invaginatus',
    'Monaghesh 51': r'virtual reality simulation for dental implant',
}

for label, pat in probes.items():
    rx = re.compile(pat, re.I)
    hits = []
    for r in rows:
        blob = ' | '.join(str(v) for v in r.values())
        if rx.search(blob):
            hits.append(r)
    print(f'--- {label}: {len(hits)} hit(s)')
    for h in hits[:4]:
        keys = [k for k in ('study_id', 'Study_ID', 'id', '题目', 'title', 'Title') if k in h]
        ident = ' / '.join(f'{k}={h[k]}' for k in keys)
        for k in h:
            if re.search(r'scenario|场景|software|软件|design|设计|special|专业|领域', k, re.I):
                print(f'    [{k}] {h[k]}')
        print(f'    id: {ident}')
    print()
