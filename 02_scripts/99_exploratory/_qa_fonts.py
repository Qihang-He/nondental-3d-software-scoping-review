# -*- coding: utf-8 -*-
"""Confirm the base font of the submission documents."""
import os
from docx import Document
from docx.shared import Pt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
SUB = os.path.join('01_投稿文件', 'R2_Submission')
for f in sorted(os.listdir(SUB)):
    if not f.endswith('.docx'):
        continue
    doc = Document(os.path.join(SUB, f))
    st = doc.styles['Normal']
    rpr = st.element.find(
        '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
    latin = east = None
    if rpr is not None:
        f_el = rpr.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts')
        if f_el is not None:
            latin = f_el.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii')
            east = f_el.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia')
    print('%-32s Normal: name=%s size=%s latin=%s eastAsia=%s'
          % (f, st.font.name, st.font.size, latin, east))
