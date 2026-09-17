# -*- coding: utf-8 -*-
"""Single-pass full-text scan of the PDF library for all borderline software terms."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OUT = os.path.join('04_代码', '07_文档', '_tmp_pdfscan2.txt')

TERMS = ['CreatWare', 'R2 Gate', 'R2GATE', 'Viewbox', 'Midas',
         'Scalismo', 'MATLAB', 'Python', 'TensorFlow', 'Keras', 'Octave',
         'Open3D', 'Trimesh', 'Iso2mesh', 'ImageJ', 'Digimizer']

import pymupdf
pdfs = []
for root, dirs, files in os.walk('10_全文PDF库'):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdfs.append(os.path.join(root, f))

res = {t: [] for t in TERMS}
print('scanning %d pdfs ...' % len(pdfs))
for n, p in enumerate(pdfs, 1):
    if n % 200 == 0:
        print('  %d/%d' % (n, len(pdfs)))
    try:
        doc = pymupdf.open(p)
        txt = '\n'.join(pg.get_text() for pg in doc)
        doc.close()
    except Exception:
        continue
    txt = txt.replace('\u00ad', '')
    low = txt.lower()
    for t in TERMS:
        i = low.find(t.lower())
        if i >= 0:
            seg = re.sub(r'\s+', ' ', txt[max(0, i - 220):i + 320])
            res[t].append((os.path.basename(p), seg))

L = ['PDF library: %d files scanned' % len(pdfs), '']
for t in TERMS:
    L.append('=== [%s]  %d hit(s)' % (t, len(res[t])))
    for fn, seg in res[t][:8]:
        L.append('   FILE: ' + fn)
        L.append('        ...%s...' % seg)
    L.append('')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
