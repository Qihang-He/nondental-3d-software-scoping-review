# -*- coding: utf-8 -*-
"""Apply the v6 numbers to the response letter, declarations and highlights."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')

EDITS = {
    'Response_to_reviewers_R2.md': [
        ('(n = 861) produced by a single script', '(n = 853) produced by a single script'),
        ('changed from 566 to **861 studies**', 'changed from 566 to **853 studies**'),
        ('all 861 included', 'all 853 included'),
        ('(`locked_analysis_dataset.csv`, n = 861). All 861 records carry',
         '(`locked_analysis_dataset.csv`, n = 853). All 853 records carry'),
        ('χ² = 297.3, df = 28,', 'χ² = 296.4, df = 28,'),
        ('p = 8.43 × 10⁻⁴⁷,', 'p = 1.29 × 10⁻⁴⁶,'),
        ('χ² = 300.8, df = 32', 'χ² = 299.9, df = 32'),
        ('is the included set (n = 861)', 'is the included set (n = 853)'),
        ('1,075 study–speciality assignments across 861 studies',
         '1,067 study–speciality assignments across 853 studies'),
        ('1,377 software assignments', '1,354 software assignments'),
        ('to **861 studies**, and the PRISMA diagram', 'to **853 studies**, and the PRISMA diagram'),
        ('Each of the 861 included studies was coded', 'Each of the 853 included studies was coded'),
        ('stated explicitly in 514 studies (59.7%)', 'stated explicitly in 508 studies (59.6%)'),
        ('(409; 47.5%)', '(404; 47.4%)'),
        ('(298; 34.6%)', '(294; 34.5%)'),
        ('(113; 13.1%)', '(113; 13.2%)'),
        ('(107; 12.4%)', '(107; 12.5%)'),
        ('(87; 10.1%)', '(84; 9.8%)'),
        ('566 studies (65.7%) stated none, and among the 295 that did,',
         '561 studies (65.8%) stated none, and among the 292 that did,'),
        ('(272; 31.6%)', '(269; 31.5%)'),
        ('Gaps were stated by 601 studies (69.6%)', 'Gaps were stated by 594 studies (69.6%)'),
        ('(556; 64.4%)', '(550; 64.5%)'),
        ('(307; 35.6%)', '(301; 35.3%)'),
        ('(27; 3.1%)', '(27; 3.2%)'),
        ('349 studies (40.4%) were computational or simulation studies, 240 (27.8%) were in vitro, only 181',
         '343 studies (40.2%) were computational or simulation studies, 238 (27.9%) were in vitro, only 180'),
        ('(21.0%) were clinical, and 93 were technical notes',
         '(21.1%) were clinical, and 92 were technical notes'),
        ('for each of the 85 software\npackages', 'for each of the 100 software\npackages'),
        ('| Verification pack | Sampling script, seed, sampled records, per-record verification verdicts (evidence level and supporting passage) |',
         '| Verification pack | Sampling script, seed, sampled records, per-record verification verdicts (evidence level and supporting passage) |\n'
         '| Software list | Re-verified against the definition of nondental 3D software; ten non-conforming entries removed and eight records excluded (n = 853) |'),
    ],
    'Declarations_R2.md': [
        ('glossary of 110 software packages', 'glossary of 100 software packages'),
    ],
    'Highlights_R2.md': [
        ('1. 861 studies across 12 dental disciplines',
         '1. 853 studies across 12 dental disciplines'),
        ('3. 110 packages were recorded; 38.9% of studies (335/861) combined more than one.',
         '3. 100 packages were recorded; 38.5% of studies (328/853) combined more than one.'),
    ],
}

for fname, pairs in EDITS.items():
    p = os.path.join(D, fname)
    s = open(p, encoding='utf-8').read()
    missing = []
    for a, b in pairs:
        if a in s:
            s = s.replace(a, b)
        else:
            missing.append(a)
    open(p, 'w', encoding='utf-8').write(s)
    print('%-34s applied=%d  missing=%d' % (fname, len(pairs) - len(missing), len(missing)))
    for m in missing:
        print('    NOT FOUND:', m[:80])
