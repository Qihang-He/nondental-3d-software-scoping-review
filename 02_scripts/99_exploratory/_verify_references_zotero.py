# -*- coding: utf-8 -*-
"""Match every reference against the author's Zotero library and compare the printed fields.

Zotero is read through its local API (Zotero must be running). The library is cached to
_reference_zotero_cache.json so the check can be repeated without re-fetching 5,000 items.
"""
import json
import os
import re
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
MS = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
CACHE = os.path.join('04_代码', '07_文档', '_reference_zotero_cache.json')
OUT = os.path.join('04_代码', '07_文档', '_reference_audit_zotero.json')

# ---------------------------------------------------------------- fetch library
if not os.path.exists(CACHE):
    items, start = [], 0
    while True:
        url = ('http://localhost:23119/api/users/0/items?limit=100&start=%d'
               '&itemType=-attachment' % start)
        req = urllib.request.Request(url, headers={'Zotero-API-Version': '3'})
        with urllib.request.urlopen(req, timeout=90) as r:
            batch = json.loads(r.read().decode('utf-8', 'replace'))
        if not batch:
            break
        items.extend(batch)
        start += len(batch)
        if start % 1000 == 0:
            print('  fetched %d' % start)
        time.sleep(0.05)
    json.dump(items, open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    print('cached %d Zotero items' % len(items))
else:
    items = json.load(open(CACHE, encoding='utf-8'))
    print('using cached Zotero library: %d items' % len(items))

# ---------------------------------------------------------------- build indexes
def norm(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = s.replace('&amp;', '&').lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


by_doi, by_title = {}, {}
for it in items:
    d = it.get('data') or {}
    doi = (d.get('DOI') or '').strip().lower()
    if doi:
        by_doi.setdefault(re.sub(r'^https?://(dx\.)?doi\.org/', '', doi), d)
    t = norm(d.get('title'))
    if t:
        by_title.setdefault(t, d)

# ---------------------------------------------------------------- our references
md = open(MS, encoding='utf-8').read()
ref_block = md[md.index('## References'):]
entries = {}
for line in ref_block.splitlines():
    m = re.match(r'^\[(\d+)\]\s*(.*)$', line)
    if m:
        entries[int(m.group(1))] = m.group(2).strip()


def year_of(date):
    m = re.search(r'(19|20)\d{2}', date or '')
    return m.group(0) if m else ''


def first_family(d):
    for c in (d.get('creators') or []):
        if c.get('family'):
            return c.get('family')
    for c in (d.get('creators') or []):
        if c.get('name'):
            return c.get('name')
    return ''


rows = []
for n in sorted(entries):
    raw = entries[n]
    doi_m = re.search(r'10\.\d{4,9}/[^\s]+', raw)
    doi = doi_m.group(0).rstrip('.').rstrip(')').lower() if doi_m else ''
    z = by_doi.get(re.sub(r'^https?://(dx\.)?doi\.org/', '', doi)) if doi else None
    how = 'DOI'
    if z is None:
        # fall back on a title match: first 8 words of the title, letters only
        head = norm(raw)[:60]
        cand = [v for k, v in by_title.items() if head and k[:40] == head[:40]]
        if cand:
            z = cand[0]
            how = 'title'
    row = {'n': n, 'raw': raw, 'doi': doi, 'matched': bool(z), 'how': how, 'notes': []}
    if z:
        row['zotero'] = {
            'title': z.get('title', ''),
            'publicationTitle': z.get('publicationTitle', ''),
            'journalAbbreviation': z.get('journalAbbreviation', ''),
            'volume': z.get('volume', ''),
            'pages': z.get('pages', ''),
            'date': z.get('date', ''),
            'year': year_of(z.get('date')),
            'first_author': first_family(z),
            'itemType': z.get('itemType', ''),
        }
        zz = row['zotero']
        rn = norm(raw)
        if zz['first_author'] and norm(zz['first_author']).split()[0] not in rn:
            row['notes'].append('first author differs: Zotero has %r' % zz['first_author'])
        if zz['year'] and zz['year'] not in raw:
            row['notes'].append('year differs: Zotero has %s' % zz['year'])
        if zz['volume'] and not re.search(r'\b%s\b\s*\(' % re.escape(zz['volume']), raw):
            row['notes'].append('volume differs: Zotero has %s' % zz['volume'])
        if zz['pages']:
            p = re.split(r'[-\u2013]', zz['pages'])[0].strip()
            if p and p not in raw:
                row['notes'].append('first page differs: Zotero has %s' % zz['pages'])
    else:
        row['notes'].append('not found in Zotero')
    rows.append(row)

json.dump(rows, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

matched = [r for r in rows if r['matched'] and not r['notes']]
diff = [r for r in rows if r['matched'] and r['notes']]
miss = [r for r in rows if not r['matched']]
print()
print('references            : %d' % len(rows))
print('matched to Zotero     : %d' % sum(1 for r in rows if r['matched']))
print('  identical fields    : %d' % len(matched))
print('  field differences   : %d' % len(diff))
print('not in Zotero         : %d' % len(miss))
print()
for r in diff + miss:
    print('[%d] %s' % (r['n'], r['raw'][:110]))
    for x in r['notes']:
        print('      - %s' % x)
