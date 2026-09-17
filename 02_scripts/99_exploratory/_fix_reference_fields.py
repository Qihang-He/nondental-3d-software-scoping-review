# -*- coding: utf-8 -*-
"""Correct the two wrong publication years and add URLs/access dates to the official documents."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
P = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
s = open(P, encoding='utf-8').read()

FIX = [
    # [10] Crossref: published-print November 2025, volume 134
    ('J Prosthet Dent 134 (2024) 1508–1513', 'J Prosthet Dent 134 (2025) 1508–1513'),
    # [36] PubMed: J Prosthet Dent 2026 Feb;135:230-235
    ('Jaw motion tracking with open-source tools: A dental technique, J Prosthet Dent 135 (2025) 230–235.',
     'Jaw motion tracking with open-source tools: A dental technique, J Prosthet Dent 135 (2026) 230–235.'),
    # [56] traceable URL for the regulation
    ('Regulation (EU) 2017/745 of the European Parliament and of the Council of 5 April 2017 on medical '
     'devices, Off. J. Eur. Union L 117 (2017) 1–175.',
     'Regulation (EU) 2017/745 of the European Parliament and of the Council of 5 April 2017 on medical '
     'devices, Off. J. Eur. Union L 117 (2017) 1–175. '
     'https://eur-lex.europa.eu/eli/reg/2017/745/oj (accessed 17 September 2026).'),
    # [57] web document: URL and access date are required
    ('U.S. Food and Drug Administration, Software as a Medical Device (SaMD): Clinical Evaluation — '
     'Guidance for Industry and Food and Drug Administration Staff, FDA, Silver Spring, MD, 2017.',
     'U.S. Food and Drug Administration, Software as a Medical Device (SaMD): Clinical Evaluation — '
     'Guidance for Industry and Food and Drug Administration Staff, FDA, Silver Spring, MD, 2017. '
     'https://www.fda.gov/regulatory-information/search-fda-guidance-documents/'
     'software-medical-device-samd-clinical-evaluation (accessed 17 September 2026).'),
]

for old, new in FIX:
    if old in s:
        s = s.replace(old, new, 1)
        print('fixed   :', old[:80])
    else:
        print('NOT FOUND:', old[:80])

open(P, 'w', encoding='utf-8').write(s)
print()
for n in (10, 36, 56, 57):
    m = re.search(r'^\[%d\]\s*(.*)$' % n, s[s.index('## References'):], re.M)
    print('[%d] %s' % (n, m.group(1)))
    print()
