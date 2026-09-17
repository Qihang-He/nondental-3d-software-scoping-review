# -*- coding: utf-8 -*-
"""Point every reference at the new figshare article and finish the v6 sync."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)

OLD = '10.6084/m9.figshare.33886810'
NEW = '10.6084/m9.figshare.33891811'

TARGETS = [
    os.path.join('01_投稿文件', 'R2_草稿', 'Declarations_R2.md'),
    os.path.join('01_投稿文件', 'R2_草稿', 'Response_to_reviewers_R2.md'),
    os.path.join('04_代码', '07_文档', '_assemble_submission.py'),
    os.path.join('04_代码', '07_文档', '_tools_build_repo_v5.py'),
]

for p in TARGETS:
    s = open(p, encoding='utf-8').read()
    n = s.count(OLD)
    s = s.replace(OLD, NEW)
    open(p, 'w', encoding='utf-8').write(s)
    print('%-46s doi replaced x%d' % (os.path.basename(p), n))

# Declarations: remaining stale dataset size
p = os.path.join('01_投稿文件', 'R2_草稿', 'Declarations_R2.md')
s = open(p, encoding='utf-8').read()
before = s
s = s.replace('the locked dataset (n = 861)', 'the locked dataset (n = 853)')
if s != before:
    open(p, 'w', encoding='utf-8').write(s)
    print('Declarations: dataset size updated')
else:
    print('Declarations: no stale dataset size found')
