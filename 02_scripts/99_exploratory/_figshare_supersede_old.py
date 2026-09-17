# -*- coding: utf-8 -*-
"""Mark the previous figshare deposit as superseded by the revised deposit."""
import os
import json
import requests

BASE = 'https://api.figshare.com/v2'
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD_ID = 33886810
NEW_DOI = '10.6084/m9.figshare.33891811'

TOKEN = os.environ.get('FIGSHARE_TOKEN', '').strip()
if not TOKEN:
    raise SystemExit('FIGSHARE_TOKEN not set')
H = {'Authorization': 'token ' + TOKEN, 'Content-Type': 'application/json'}

r = requests.get('%s/account/articles/%d' % (BASE, OLD_ID), headers=H, timeout=120)
r.raise_for_status()
a = r.json()
old_title = a['title']
old_desc = a.get('description') or ''

note = ('SUPERSEDED. This deposit contains an earlier version of the dataset (861 included '
        'studies, 110 software packages) and is retained for transparency only. The dataset was '
        'subsequently revised after every recorded software package was re-verified against the '
        'review definition of nondental 3D software: ten non-conforming entries were removed and '
        'eight studies were excluded, giving 853 included studies and 100 software packages. ')
new_desc = note + 'The current version is available at https://doi.org/' + NEW_DOI + '\n\n' + old_desc

title = old_title
if not title.startswith('[SUPERSEDED]'):
    title = '[SUPERSEDED] ' + title

payload = {'title': title[:300], 'description': new_desc}
r2 = requests.put('%s/account/articles/%d' % (BASE, OLD_ID), headers=H,
                  data=json.dumps(payload), timeout=120)
print('PUT status:', r2.status_code)
if r2.status_code not in (200, 205):
    print(r2.text[:400])
else:
    r3 = requests.get('%s/account/articles/%d' % (BASE, OLD_ID), headers=H, timeout=120)
    b = r3.json()
    print('title now:', b['title'])
    print('description starts:', (b.get('description') or '')[:120])
