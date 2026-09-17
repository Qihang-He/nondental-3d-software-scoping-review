# -*- coding: utf-8 -*-
"""Pick replacement included studies for the 8 mismatched illustrative citations.

Numbers stay identical; only the reference-list entry content changes.
"""
import csv, re, sys, json, unicodedata

sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'd:\Desktop\v8 for JD'
DS = ROOT + r'\03_数据\08_分析用\分析数据集_final_v6.csv'
MS = ROOT + r'\01_投稿文件\R2_草稿\Revised_manuscript_R2.md'

with open(DS, encoding='utf-8-sig', newline='') as f:
    rows = list(csv.DictReader(f))

# --- parse current reference list ---
txt = open(MS, encoding='utf-8').read()
refs = {}
for m in re.finditer(r'^\[(\d+)\]\s+(.+)$', txt, re.M):
    refs[int(m.group(1))] = m.group(2).strip()
print('parsed refs:', len(refs))

def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()

# DOI lookup
by_doi = {}
for r in rows:
    d = (r.get('DOI') or '').strip().lower()
    d = re.sub(r'^https?://(dx\.)?doi\.org/', '', d)
    if d:
        by_doi[d] = r
by_title = {norm(r['Title']): r for r in rows}

used = set()
for n, text in sorted(refs.items()):
    dm = re.search(r'doi\.org/(10\.\S+)', text)
    key = dm.group(1).lower().rstrip('.,;)') if dm else None
    row = by_doi.get(key) if key else None
    if row:
        used.add(row['Title'])
print('refs mapped to dataset rows:', len(used))

TARGETS = {
    14: ['3D Data Analysis and Accuracy Assessment'],
    27: ['Image Segmentation and 3D Reconstruction'],
    34: ['Digital Design and Manufacturing'],
    36: ['Digital Design and Manufacturing'],
    43: ['Surgical Planning and Precise Implementation'],
    44: ['Surgical Planning and Precise Implementation'],
    49: ['Morphological and Phenotypic Analysis'],
    52: ['__educational_or_case__'],
}

def scen_list(r):
    return [s.strip() for s in (r.get('Application Scenario') or '').split('/') if s.strip()]

for slot, targets in TARGETS.items():
    print(f'\n=== slot [{slot}]  target={targets}')
    out = []
    for r in rows:
        if r['Title'] in used:
            continue
        if not (r.get('DOI') or '').strip():
            continue
        sty = (r.get('study_type') or '').lower()
        sc = scen_list(r)
        if targets == ['__educational_or_case__']:
            if sty not in ('educational', 'case_report'):
                continue
            if sty != 'educational':
                continue
        else:
            if sc != targets:            # unambiguous single-scenario studies only
                continue
        out.append(r)
    out.sort(key=lambda r: (-int(r.get('Year') or 0), r['Title']))
    for r in out[:14]:
        print(f"  {r.get('Year')}|{r.get('Journal','')[:26]:26s}|{r.get('study_type','')[:12]:12s}|"
              f"{(r.get('Dental Specialty') or '')[:34]:34s}|"
              f"{(r.get('Software Used (fixed)') or r.get('Software Used') or '')[:26]:26s}|"
              f"{(r.get('Region') or '')[:10]:10s}|{(r.get('DOI') or '')[:36]:36s}|{r['Title'][:64]}")
    print(f'  candidates: {len(out)}')
