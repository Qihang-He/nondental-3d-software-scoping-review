# -*- coding: utf-8 -*-
"""Cross-check every in-text citation against the locked dataset.

For each reference, locate the corresponding included study (by DOI, then by title) and report the
discipline, scenario and software that the dataset records for it. Where a citation is used to
illustrate a particular claim (a scenario, a class of software, a study design), the recorded values
show whether the example actually supports that claim.
"""
import json
import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')
ANA = os.path.join('03_数据', '08_分析用')
OUT = os.path.join('04_代码', '07_文档', '_citation_fit.txt')

md = open(os.path.join(D, 'Revised_manuscript_R2.md'), encoding='utf-8').read()
body = md[md.index('## Introduction'):md.index('## References')]
ref_block = md[md.index('## References'):]

ents = {}
for line in ref_block.splitlines():
    m = re.match(r'^\[(\d+)\]\s*(.*)$', line)
    if m:
        ents[int(m.group(1))] = m.group(2).strip()

d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v6.csv'), low_memory=False)


def norm(s):
    s = re.sub(r'<[^>]+>', ' ', str(s or ''))
    s = s.replace('&amp;', '&').lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


d['_t'] = d['Title'].map(norm)
d['_doi'] = d['DOI'].astype(str).str.lower().str.replace(r'^https?://(dx\.)?doi\.org/', '',
                                                          regex=True).str.strip()
titles = list(zip(d['_t'], d.index))


def find(ref):
    m = re.search(r'10\.\d{4,9}/[^\s]+', ref)
    if m:
        doi = m.group(0).rstrip('.').rstrip(')').lower()
        hit = d.index[d['_doi'] == doi]
        if len(hit):
            return int(hit[0]), 'doi'
    n = norm(ref)
    best = None
    for t, i in titles:
        if len(t) > 25 and t in n:
            if best is None or len(t) > len(d.at[best, '_t']):
                best = i
    if best is not None:
        return int(best), 'title'
    return None, None


def parse(v):
    try:
        return list(eval(v)) if isinstance(v, str) else list(v or [])
    except Exception:
        return []


rows, unmatched = {}, []
for n in sorted(ents):
    i, how = find(ents[n])
    if i is None:
        unmatched.append(n)
        rows[n] = None
        continue
    r = d.loc[i]
    rows[n] = {
        'Key': r['Key'], 'title': str(r['Title'])[:95], 'how': how,
        'specialty': '; '.join(parse(r['_spec'])),
        'scenario': '; '.join(parse(r['_scen'])),
        'software': '; '.join(parse(r['_soft2']))[:80],
        'design': r['study_type'],
    }

lines = ['references citing an included study:', str(sum(1 for v in rows.values() if v)),
         'references not matched to an included study: %d %s' % (len(unmatched), unmatched), '']
for n in sorted(rows):
    v = rows[n]
    lines.append('[%d] %s' % (n, ents[n][:100]))
    if v:
        lines.append('     -> %s | %s' % (v['Key'], v['title']))
        lines.append('        specialty: %s' % v['specialty'])
        lines.append('        scenario : %s' % v['scenario'])
        lines.append('        software : %s' % v['software'])
        lines.append('        design   : %s' % v['design'])
    else:
        lines.append('        (not an included study: guideline, regulation or methodological source)')
    lines.append('')

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('\n'.join(lines[:3]))
print('written', OUT)
