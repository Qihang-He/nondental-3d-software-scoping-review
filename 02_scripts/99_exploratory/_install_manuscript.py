# -*- coding: utf-8 -*-
"""Install the restyled manuscript (backing up the previous version)."""
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')
SRC = os.path.join('04_代码', '07_文档', '_manuscript_revision.md')
DST = os.path.join(D, 'Revised_manuscript_R2.md')
BAK = os.path.join('09_归档', 'Revised_manuscript_R2_pre_style_edit.md')

shutil.copy2(DST, BAK)
print('backup:', BAK)

new = open(SRC, encoding='utf-8').read()
open(DST, 'w', encoding='utf-8').write(new)

heads = re.findall(r'^#{1,4}\s+.*$', new, re.M)
print()
print('headings in the installed manuscript:')
for h in heads:
    print('   ', h)
numbered = [h for h in heads if re.match(r'^#{1,4}\s+\d', h)]
print()
print('numbered headings remaining:', len(numbered))
print('bold run-in labels:', len(re.findall(r'^\*\*[A-Z][^*]{5,60}\.\*\*', new, re.M)))
