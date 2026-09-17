# -*- coding: utf-8 -*-
"""Apply the v6 (software-scope revised) numbers to the R2 manuscript."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
P = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
s = open(P, encoding='utf-8').read()
orig = s

# ---- global denominator changes -------------------------------------------
GLOBAL = [
    ('861', '853'),
    ('1,075', '1,067'),
    ('1,046', '1,038'),
    ('1,377', '1,354'),
    ('31.6%', '31.5%'),
    ('35.7%', '35.3%'),
    ('64.6%', '64.5%'),
    ('38.4%', '38.1%'),
    ('12.4%', '12.5%'),
    ('20.7%', '20.9%'),
    ('817', '810'),
    ('the remaining 44 records', 'the remaining 43 records'),
    ('(298, 34.6%)', '(294, 34.5%)'),
    ('(409 studies, 47.5%)', '(404 studies, 47.4%)'),
    ('(113, 13.1%)', '(113, 13.2%)'),
    ('(272 studies,', '(269 studies,'),
    ('(307, 35.3%)', '(301, 35.3%)'),
    ('(556, 64.5%)', '(550, 64.5%)'),
    ('556 studies', '550 studies'),
    ('335 studies (38.9%)', '328 studies (38.5%)'),
    ('601 studies (69.8%)', '594 studies (69.6%)'),
    ('566 (65.7%)', '561 (65.8%)'),
]

# ---- targeted changes ------------------------------------------------------
SPECIFIC = [
    # abstract
    ('2020-H2 to 98 in 2025-H2', '2020-H2 to 96 in 2025-H2'),
    ('(257) and oral implantology', '(253) and oral implantology'),
    ('A total of 110 nondental packages were recorded, 335',
     'A total of 100 nondental packages were recorded, 328'),
    ('Computational (349) and in vitro (239) studies outnumbered clinical studies (181)',
     'Computational (343) and in vitro (238) studies outnumbered clinical studies (180)'),
    ('(47.5%) and efficiency (34.6%)', '(47.4%) and efficiency (34.5%)'),
    # 2.4
    ('807 (93.7%)', '799 (93.7%)'),
    # 2.6
    ('added 304 studies and removed seven, so that the included set changed from',
     'added 304 studies and removed fifteen, so that the included set changed from'),
    # 3.1
    ('and 920 were excluded', 'and 928 were excluded'),
    ('the current audit. The final scoping review therefore comprises **853 studies**',
     'the current audit, and eight removed because the only named tool was a general-purpose '
     'programming, numerical-computing or machine-learning platform rather than a third-party '
     '3D software package. The final scoping review therefore comprises **853 studies**'),
    # 3.2
    ('332 studies (38.6%)', '331 studies (38.8%)'),
    ('Turkey (81) and the United States (68)', 'Turkey (80) and the United States (67)'),
    ('6.02 additional studies per half-year', '5.95 additional studies per half-year'),
    ('4.99 excluding', '4.93 excluding'),
    ('(147) and oral', '(144) and oral'),
    ('maxillofacial radiology (82)', 'maxillofacial radiology (81)'),
    ('349 studies (40.5%) were computational', '343 studies (40.2%) were computational'),
    ('239 (27.8%) were in vitro', '238 (27.9%) were in vitro'),
    ('181 (21.0%) were clinical', '180 (21.1%) were clinical'),
    ('accuracy assessment (263 studies)', 'accuracy assessment (261 studies)'),
    ('(204) [6,16,17,34]', '(203) [6,16,17,34]'),
    ('surgical planning and implementation (124)', 'surgical planning and implementation (122)'),
    ('phenotypic analysis (114)', 'phenotypic analysis (111)'),
    # 3.3
    ('One hundred and ten nondental packages', 'One hundred nondental packages'),
    ('(439 studies) and reverse engineering or 3D', '(371 studies) and reverse engineering or 3D'),
    ('reconstruction (309) were the software families',
     'reconstruction (294) were the software families'),
    ('modelling (226), engineering simulation (168) and computer-aided design (133)',
     'modelling (208), engineering simulation (150) and computer-aided design (128)'),
    ('and 526 (61.1%)', 'and 525 (61.5%)'),
    # 3.4
    ('(331 studies, 38.1%)', '(325 studies, 38.1%)'),
    ('(245 studies, 28.5%)', '(243 studies, 28.5%)'),
    ('(178 studies, 20.9%)', '(178 studies, 20.9%)'),
    ('(n = 331,', '(n = 325,'),
    ('(n = 245, 28.5%)', '(n = 243, 28.5%)'),
    # 3.5
    ('χ² = 297.3, df = 28, p = 8.43 × 10⁻⁴⁷', 'χ² = 296.4, df = 28, p = 1.29 × 10⁻⁴⁶'),
    ('χ² = 300.8, df = 32', 'χ² = 299.9, df = 32'),
    # 3.6
    ('514 of the 853 studies (59.7%)', '508 of the 853 studies (59.6%)'),
    ('(87, 10.1%)', '(84, 9.8%)'),
    ('295 studies (34.3%) stated at least one', '292 studies (34.2%) stated at least one'),
    ('(15, 1.7%)', '(15, 1.8%)'),
    ('reporting guidance (27, 3.1%)', 'reporting guidance (27, 3.2%)'),
    # 4
    ('349 of 853 studies were simulation', '343 of 853 studies were simulation'),
    ('239 were laboratory studies, against 181 clinical studies',
     '238 were laboratory studies, against 180 clinical studies'),
    # figure 6 legend
    ('347 studies (40.3%)', '345 studies (40.4%)'),
    ('gap by 260 (30.2%)', 'gap by 259 (30.4%)'),
]

missing = []
for a, b in GLOBAL + SPECIFIC:
    if a in s:
        s = s.replace(a, b)
    else:
        missing.append(a)

open(P, 'w', encoding='utf-8').write(s)
print('changed:', s != orig)
print('NOT FOUND (%d):' % len(missing))
for m in missing:
    print('   ', m)
