# -*- coding: utf-8 -*-
"""Final QA of the submission Word files, and removal of scratch scripts."""
import os
import re
from docx import Document
from docx.shared import Pt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
SUB = os.path.join('01_投稿文件', 'R2_Submission')

print('=== Word formatting QA ===')
for f in sorted(os.listdir(SUB)):
    if not f.endswith('.docx'):
        continue
    doc = Document(os.path.join(SUB, f))
    xml = doc.element.xml
    pars = doc.paragraphs
    body = '\n'.join(p.text for p in pars)
    sizes = {r.font.size for p in pars for r in p.runs if r.font.size}
    fonts = {r.font.name for p in pars for r in p.runs if r.font.name}
    spacing = {p.paragraph_format.line_spacing for p in pars if p.paragraph_format.line_spacing}
    indents = {p.paragraph_format.first_line_indent for p in pars
               if p.paragraph_format.first_line_indent}
    print('--- %s' % f)
    print('    paragraphs=%d  runs=%d' % (len(pars), sum(len(p.runs) for p in pars)))
    print('    fonts=%s  sizes=%s' % (sorted(fonts)[:3], sorted(str(s) for s in sizes)[:4]))
    print('    line_spacing=%s  first_line_indent=%s'
          % (sorted(str(s) for s in spacing)[:3], sorted(str(i) for i in indents)[:3]))
    print('    line numbers in sectPr: %s' % ('w:lnNumType' in xml))
    issues = []
    if re.search(r'[\u4e00-\u9fff]', body):
        issues.append('Chinese text')
    if '---' in body:
        issues.append('horizontal rule')
    if re.search(r'\bR2\b(?!\s+Gate)', body):
        issues.append('version tag "R2"')
    if '«' in body or '»' in body:
        issues.append('placeholder markers')
    if re.search(r'\bv5\b|\bv6\b|\bv4\b|861 included|110 software|1,377|297\.3', body):
        issues.append('stale dataset reference')
    print('    issues: %s' % (issues or 'none'))
    # first non-empty lines
    shown = [p.text for p in pars if p.text.strip()][:2]
    print('    head: %s' % ' | '.join(s[:70] for s in shown))
print()

print('=== scratch file cleanup ===')
removed = 0
for root, dirs, files in os.walk('04_代码'):
    if '__pycache__' in root:
        continue
    for f in files:
        if f.startswith('_tmp_') or f in ('_migrate_v6.py', '_apply_v6_manuscript.py',
                                          '_apply_v6_docs.py', '_run_pipeline_v6.py',
                                          '_apply_new_doi.py'):
            os.remove(os.path.join(root, f))
            removed += 1
print('removed %d scratch scripts' % removed)
