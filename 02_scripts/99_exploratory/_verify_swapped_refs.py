# -*- coding: utf-8 -*-
"""Three-way check for the 8 swapped reference entries:
manuscript entry  <->  locked dataset record  <->  Crossref record.
"""
import csv, json, re, sys, unicodedata, urllib.request, urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'd:\Desktop\v8 for JD'
DS = ROOT + r'\03_数据\08_分析用\分析数据集_final_v6.csv'
MS = ROOT + r'\01_投稿文件\R2_草稿\Revised_manuscript_R2.md'
UA = 'nondental-review-ref-crosscheck/1.0 (mailto:qihanghe05@foxmail.com)'

SLOTS = [14, 27, 34, 36, 43, 44, 49, 52]


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


with open(DS, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))
by_doi = {}
for r in rows:
    d = re.sub(r'^https?://(dx\.)?doi\.org/', '', (r.get('DOI') or '').strip().lower()).rstrip('.,;')
    if d:
        by_doi[d] = r

txt = open(MS, encoding='utf-8').read()
ok = True
for slot in SLOTS:
    m = re.search(r'^\[%d\]\s+(.+)$' % slot, txt, re.M)
    entry = m.group(1).strip()
    doi = re.search(r'doi\.org/(10\.\S+?)\.?$', entry).group(1)
    ds = by_doi.get(doi)
    req = urllib.request.Request('https://api.crossref.org/works/' + urllib.parse.quote(doi),
                                 headers={'User-Agent': UA})
    cr = json.load(urllib.request.urlopen(req, timeout=40))['message']
    cr_title = cr['title'][0]
    ds_title = ds['Title'] if ds else '(NOT IN DATASET)'
    # the entry text sits between the author list and the journal
    body = entry.split('. https://doi.org')[0]
    entry_title = body
    match_ds = ds and norm(ds_title)[:40] in norm(entry)
    match_cr = norm(cr_title)[:40] in norm(entry)
    flag = 'OK ' if (ds and match_ds and match_cr) else 'CHECK'
    if flag != 'OK ':
        ok = False
    print(f'{flag} [{slot}] doi={doi}')
    print(f'      dataset : {ds_title[:100]}')
    print(f'      crossref: {cr_title[:100]}')
    print(f'      scn/type: {(ds or {}).get("Application Scenario","")} | {(ds or {}).get("study_type","")}')
    print(f'      entry   : {body[-90:]}')
print()
print('ALL CONSISTENT' if ok else 'REVIEW NEEDED')
