# -*- coding: utf-8 -*-
"""Verify the two decisive borderline cases: ZV568RJY (Midas/Geomagic) and EQ8LE4IL (Scalismo Lab)."""
import os
import glob
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OUT = os.path.join('04_代码', '07_文档', '_tmp_verify2.txt')
L = []

# 1) list the verification folder
vdir = os.path.join('03_数据', '05_审计与核验', 'PDF核验')
L.append('=== %s ===' % vdir)
for f in sorted(os.listdir(vdir)):
    L.append('   ' + f)

# 2) any PDF-software verification csv
for p in glob.glob(os.path.join('03_数据', '**', '*.csv'), recursive=True):
    if 'PDF' in os.path.basename(p) or '核验' in os.path.basename(p):
        try:
            x = pd.read_csv(p, low_memory=False)
        except Exception:
            continue
        keycols = [c for c in x.columns if x[c].dtype == object]
        m = pd.Series(False, index=x.index)
        for c in keycols:
            m |= x[c].astype(str).str.contains('ZV568RJY|EQ8LE4IL|Midas|Scalismo', na=False)
        if m.any():
            L.append('')
            L.append('=== %s  (%d hits) ===' % (p, int(m.sum())))
            for _, r in x[m].iterrows():
                L.append('   ----')
                for c in x.columns:
                    v = str(r[c])
                    if v in ('', 'nan'):
                        continue
                    L.append('   %s: %s' % (c, v))
        break

# 3) PDF text search
L.append('')
L.append('=== PDF TEXT SEARCH ===')
pdfs = glob.glob(os.path.join('人工核验包', 'PDF', '*.pdf')) + \
       glob.glob(os.path.join('10_全文PDF库', '**', '*.pdf'), recursive=True)
targets = {'ZV568RJY': ['Midas', 'GeoMagic', 'Geomagic'],
           'EQ8LE4IL': ['Scalismo', 'statistical shape']}
for key, terms in targets.items():
    hits = [p for p in pdfs if key.lower() in os.path.basename(p).lower()]
    L.append('--- %s : %d pdf file(s)' % (key, len(hits)))
    for p in hits:
        L.append('    file: ' + os.path.basename(p))
        try:
            import pymupdf
            doc = pymupdf.open(p)
            txt = '\n'.join(pg.get_text() for pg in doc)
        except Exception as e:
            L.append('    READ ERR ' + str(e))
            continue
        for t in terms:
            idx = 0
            n = 0
            while True:
                i = txt.find(t, idx)
                if i < 0 or n >= 4:
                    break
                seg = txt[max(0, i - 180):i + 220].replace('\n', ' ')
                L.append('    [%s] ...%s...' % (t, seg))
                idx = i + 1
                n += 1

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
