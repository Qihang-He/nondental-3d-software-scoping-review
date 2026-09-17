# -*- coding: utf-8 -*-
"""Resolve the flagged references against Crossref and PubMed."""
import json
import os
import re
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
UA = 'nondental-review-reference-check/1.0 (mailto:qihanghe05@foxmail.com)'


def get(url, accept='application/json'):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': accept})
    with urllib.request.urlopen(req, timeout=45) as r:
        body = r.read().decode('utf-8', 'replace')
    return json.loads(body) if accept == 'application/json' else body


CASES = {
    10: '10.1016/j.prosdent.2024.05.024',
    16: '10.1016/j.prosdent.2025.09.010',
    36: None,   # resolved by title
    48: '10.1097/SCS.0000000000007879',
}

print('=' * 78)
print('A. Crossref check of the four flagged entries')
print('=' * 78)
for n, doi in CASES.items():
    if not doi:
        continue
    try:
        m = get('https://api.crossref.org/works/' + urllib.parse.quote(doi))['message']
        print('\n[%d] %s' % (n, doi))
        print('    title      : %s' % (m.get('title') or [''])[0][:95])
        print('    container  : %s | short: %s' % ((m.get('container-title') or [''])[0],
                                                  (m.get('short-container-title') or [''])[0]))
        print('    issued     : %s' % (m.get('issued', {}).get('date-parts')))
        print('    published-print: %s | published-online: %s'
              % (m.get('published-print', {}).get('date-parts'),
                 m.get('published-online', {}).get('date-parts')))
        print('    volume/pages: %s / %s   article-number: %s'
              % (m.get('volume'), m.get('page'), m.get('article-number')))
    except Exception as e:
        print('\n[%d] %s -> ERROR %s' % (n, doi, e))
    time.sleep(0.4)

print()
print('=' * 78)
print('B. Title search for the entries without a DOI')
print('=' * 78)
TITLES = {
    11: 'First steps of a digital workflow to build up a virtual articulator using open-source Autodesk Meshmixer software',
    36: 'Jaw motion tracking with open-source tools',
    56: 'Regulation (EU) 2017/745 medical devices',
    57: 'Software as a Medical Device Clinical Evaluation Guidance',
}
for n, t in TITLES.items():
    print('\n[%d] %s' % (n, t[:90]))
    try:
        q = urllib.parse.quote(t)
        body = get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
                   '?db=pubmed&retmode=json&retmax=3&term=' + q, accept='text')
        ids = json.loads(body)['esearchresult'].get('idlist', [])
        print('    PubMed ids: %s' % (ids or 'none'))
        if ids:
            s = get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
                    '?db=pubmed&retmode=json&id=' + ','.join(ids), accept='text')
            for k, v in json.loads(s)['result'].items():
                if k == 'uids':
                    continue
                print('      - %s | %s | %s | vol %s | pages %s | %s'
                      % (v.get('title', '')[:70], v.get('source'), v.get('pubdate'),
                         v.get('volume'), v.get('pages'), v.get('elocationid', '')))
    except Exception as e:
        print('    PubMed ERROR %s' % e)
    time.sleep(0.4)
