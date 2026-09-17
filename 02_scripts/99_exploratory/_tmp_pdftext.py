# -*- coding: utf-8 -*-
"""Locate the two PDFs and extract the software sentences."""
import os
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OUT = os.path.join('04_代码', '07_文档', '_tmp_pdftext.txt')
L = []

stems = ['Faus-Matoses', 'Bannink']
for st in stems:
    hits = []
    for root, dirs, files in os.walk('.'):
        for f in files:
            if st.lower() in f.lower() and f.lower().endswith('.pdf'):
                hits.append(os.path.join(root, f))
    L.append('=== %s : %d pdf(s)' % (st, len(hits)))
    for p in hits:
        L.append('   ' + p)
        try:
            import pymupdf
            doc = pymupdf.open(p)
            txt = '\n'.join(pg.get_text() for pg in doc)
        except Exception as e:
            L.append('   ERR ' + str(e))
            continue
        L.append('   chars=%d pages=%d' % (len(txt), doc.page_count))
        for t in ['Midas', 'MIDAS', 'Geomagic', 'GeoMagic', 'GOM', 'Scalismo', 'Abaqus', 'ANSYS']:
            idx, n = 0, 0
            while n < 3:
                i = txt.find(t, idx)
                if i < 0:
                    break
                L.append('   [%s] ...%s...' % (t, txt[max(0, i - 250):i + 250].replace('\n', ' ')))
                idx = i + 1
                n += 1
    L.append('')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
