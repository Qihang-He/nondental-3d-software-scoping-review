# -*- coding: utf-8 -*-
"""Regenerate every submission docx from its Markdown source (journal format)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from _tools_md2docx import md_to_docx

ROOT = os.path.dirname(os.path.dirname(HERE))
D = os.path.join(ROOT, '01_投稿文件', 'R2_草稿')

FILES = [
    'Cover_Letter_R2',
    'Title_Page_R2',
    'Revised_manuscript_R2',
    'Response_to_reviewers_R2',
    'Declarations_R2',
    'Highlights_R2',
    'Supplementary_File_1_R2',
]

for stem in FILES:
    src = os.path.join(D, stem + '.md')
    dst = os.path.join(D, stem + '.docx')
    md_to_docx(src, dst)
print('done')
