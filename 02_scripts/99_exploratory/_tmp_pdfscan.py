# -*- coding: utf-8 -*-
"""Full-text scan of the PDF library for every borderline software term."""
import os
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OUT = os.path.join('04_代码', '07_文档', '_tmp_pdfscan.txt')

TERMS = ['CreatWare', 'Creatware', 'CREATWARE',
         'R2 Gate', 'R2GATE', 'R2gate',
         'Viewbox', 'ViewBox',
         'Midas', 'MIDAS',
         'Scalismo',
         'MATLAB', 'Python', 'TensorFlow', 'Keras', 'Octave',
         'Open3D', 'Trimesh', 'Iso2mesh',
         'ImageJ', 'Digimizer']

import pymupdf
pdfs = []
for root, dirs, files in os.walk('10_全文PDF库'):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdfs.append(os.path.join(root, f))

L = ['PDF library: %d files' % len(pdfs), '']
for t in TERMS:
    found = []
    for p in pdfs:
        try:
            doc = pymupdf.open(p)
            txt = '\n'.join(pg.get_text() for pg in doc)
            doc.close()
        except Exception:
            continue
        i = txt.find(t)
        if i >= 0:
            seg = txt[max(0, i - 200):i + 300].replace('\n', ' ')
            found.append((os.path.basename(p), seg))
    L.append('=== [%s]  %d hit(s)' % (t, len(found)))
    for fn, seg in found[:6]:
        L.append('   FILE: ' + fn)
        L.append('        ...%s...' % seg)
    L.append('')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT, 'pdfs', len(pdfs))
