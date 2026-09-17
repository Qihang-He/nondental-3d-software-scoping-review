# -*- coding: utf-8 -*-
"""Verify reference [11] (Int J Comput Dent) and the two official documents."""
import json
import os
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
UA = 'nondental-review-reference-check/1.0 (mailto:qihanghe05@foxmail.com)'


def txt(u):
    req = urllib.request.Request(u, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode('utf-8', 'replace')


TITLE = 'First steps of a digital workflow to build up a virtual articulator'

print('--- OpenAlex ---')
try:
    d = json.loads(txt('https://api.openalex.org/works?per-page=5&search=' + urllib.parse.quote(TITLE)))
    for w in d.get('results', []):
        src = ((w.get('primary_location') or {}).get('source') or {}).get('display_name')
        bib = w.get('biblio') or {}
        print('  -', (w.get('title') or '')[:95])
        print('    %s | %s | vol %s | p %s-%s | DOI %s'
              % (src, w.get('publication_year'), bib.get('volume'),
                 bib.get('first_page'), bib.get('last_page'), w.get('doi')))
except Exception as e:
    print('  ERROR', e)
time.sleep(0.4)

print()
print('--- PubMed: journal + Meshmixer ---')
q = '"Int J Comput Dent"[Journal] AND Meshmixer'
try:
    s = json.loads(txt('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
                       '?db=pubmed&retmode=json&retmax=5&term=' + urllib.parse.quote(q)))
    ids = s['esearchresult'].get('idlist') or []
    print('  ids:', ids or 'none')
    if ids:
        ss = json.loads(txt('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
                            '?db=pubmed&retmode=json&id=' + ','.join(ids)))
        for k, v in ss['result'].items():
            if k == 'uids':
                continue
            print('  - %s | %s %s | vol %s | p %s'
                  % (v.get('title', '')[:85], v.get('source'), v.get('pubdate'),
                     v.get('volume'), v.get('pages')))
except Exception as e:
    print('  ERROR', e)
time.sleep(0.4)

print()
print('--- PubMed: journal indexed at all? ---')
q2 = '"Int J Comput Dent"[Journal] AND 2022[dp]'
try:
    s = json.loads(txt('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
                       '?db=pubmed&retmode=json&retmax=3&term=' + urllib.parse.quote(q2)))
    print('  count:', s['esearchresult'].get('count'))
except Exception as e:
    print('  ERROR', e)

print()
print('--- official documents ---')
for label, url in [
        ('EUR-Lex MDR', 'https://eur-lex.europa.eu/eli/reg/2017/745/oj'),
        ('FDA SaMD guidance',
         'https://www.fda.gov/regulatory-information/search-fda-guidance-documents/'
         'software-medical-device-samd-clinical-evaluation')]:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read().decode('utf-8', 'replace')
        print('  [%s] HTTP %s, %d bytes' % (label, r.status, len(body)))
    except Exception as e:
        print('  [%s] ERROR %s' % (label, e))
    time.sleep(0.4)
