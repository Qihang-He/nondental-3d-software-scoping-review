# -*- coding: utf-8 -*-
"""Verify every reference against Crossref: does the DOI resolve, and do the author, year,
journal, volume and pages in our list match the registered record?"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
MS = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
OUT = os.path.join('04_代码', '07_文档', '_reference_audit.json')

md = open(MS, encoding='utf-8').read()
ref_block = md[md.index('## References'):]

entries = {}
for line in ref_block.splitlines():
    m = re.match(r'^\[(\d+)\]\s*(.*)$', line)
    if m:
        entries[int(m.group(1))] = m.group(2).strip()

UA = 'nondental-review-reference-check/1.0 (mailto:qihanghe05@foxmail.com)'
SLEEP = 0.4


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                               'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode('utf-8', 'replace'))


def norm(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    s = s.replace('&amp;', '&')
    s = re.sub(r'[^a-z0-9 ]', ' ', s.lower())
    return re.sub(r'\s+', ' ', s).strip()


def surname(a):
    return norm(a).split()[0] if a and norm(a) else ''


results = []
for n in sorted(entries):
    raw = entries[n]
    doi_m = re.search(r'10\.\d{4,9}/[^\s]+', raw)
    doi = doi_m.group(0).rstrip('.').rstrip(')') if doi_m else None
    rec = {'n': n, 'raw': raw, 'doi': doi, 'status': '', 'notes': []}
    if doi:
        try:
            data = get('https://api.crossref.org/works/' + urllib.parse.quote(doi))['message']
            rec['crossref'] = {
                'title': (data.get('title') or [''])[0],
                'container': (data.get('container-title') or [''])[0],
                'short': (data.get('short-container-title') or [''])[0],
                'year': str((data.get('issued', {}).get('date-parts') or [['']])[0][0]),
                'volume': data.get('volume', ''),
                'page': data.get('page', ''),
                'article': data.get('article-number', ''),
                'authors': [('%s %s' % (a.get('given', ''), a.get('family', ''))).strip()
                            for a in (data.get('author') or [])][:3],
                'type': data.get('type', ''),
            }
            rec['status'] = 'RESOLVED'

            # ---- compare the fields we print in the reference list
            cr = rec['crossref']
            if cr['authors']:
                fam = cr['authors'][0].split()[-1]
                if surname(fam) and surname(fam) not in norm(raw):
                    rec['notes'].append('first author %r not found in entry' % fam)
            if cr['year'] and cr['year'] not in raw:
                rec['notes'].append('year %s not found in entry' % cr['year'])
            if cr['volume'] and re.search(r'\(\s*%s\s*\)' % re.escape(cr['volume']), raw) is None:
                rec['notes'].append('volume %s not found in entry' % cr['volume'])
            if cr['page']:
                first_page = re.split(r'[-\u2013]', cr['page'])[0].strip()
                if first_page and first_page not in raw.replace(' ', '').replace('\u2013', '-'):
                    rec['notes'].append('page %s not found in entry' % cr['page'])
            if cr['article'] and cr['article'] not in raw:
                rec['notes'].append('article number %s not found in entry' % cr['article'])
            abbr = cr['short'] or cr['container']
            if abbr:
                head = norm(abbr).split()[0][:5]
                if head and head not in norm(raw):
                    rec['notes'].append('journal %r not matched in entry' % abbr)
        except Exception as e:
            code = getattr(e, 'code', None)
            rec['status'] = 'DOI UNRESOLVED (%s)' % (code or type(e).__name__)
            if n == min(entries):
                import traceback
                traceback.print_exc()
                rec['error'] = str(e)
    else:
        rec['status'] = 'NO DOI'
    results.append(rec)
    time.sleep(SLEEP)

json.dump(results, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

ok = sum(1 for r in results if r['status'] == 'RESOLVED' and not r['notes'])
flagged = [r for r in results if r['status'] == 'RESOLVED' and r['notes']]
bad = [r for r in results if r['status'] != 'RESOLVED']
print('references checked : %d' % len(results))
print('fully matched      : %d' % ok)
print('resolved w/ notes  : %d' % len(flagged))
print('unresolved / no DOI: %d' % len(bad))
print()
for r in flagged + bad:
    print('[%d] %s' % (r['n'], r['status']))
    for x in r['notes']:
        print('      - %s' % x)
