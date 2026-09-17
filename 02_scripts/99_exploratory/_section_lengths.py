# -*- coding: utf-8 -*-
"""Section word counts for the installed manuscript."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
P = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
md = open(P, encoding='utf-8').read()


def wc(s):
    s = re.sub(r'\[[\d,\u2013\-]+\]', ' ', s)
    s = re.sub(r'[*#_`>|]', ' ', s)
    return len([w for w in s.split() if re.search(r'\w', w)])


parts = re.split(r'^(#{1,3}\s+.*)$', md, flags=re.M)
name, buf = 'PREFACE', []
rows = []
for chunk in parts[1:]:
    if chunk.startswith('#'):
        rows.append((name, wc('\n'.join(buf))))
        name, buf = chunk.strip('# ').strip(), []
    else:
        buf.append(chunk)
rows.append((name, wc('\n'.join(buf))))

print('%-46s %6s' % ('SECTION', 'words'))
print('-' * 54)
for n, w in rows:
    print('%-46s %6d' % (n[:46], w))
main = sum(w for n, w in rows if n not in ('Abstract', 'Figure legends', 'PREFACE'))
print('-' * 54)
print('%-46s %6d' % ('MAIN TEXT (Introduction .. Conclusions)', main))
print('%-46s %6d' % ('whole file', wc(md)))
