# -*- coding: utf-8 -*-
"""Fix the remaining awkward section reference in the response letter."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
P = os.path.join('01_投稿文件', 'R2_草稿', 'Response_to_reviewers_R2.md')
s = open(P, encoding='utf-8').read()

new = ('**Changes:** new Figure 1; the Information sources and search strategy and Study selection '
       'sections of the Methods; the Study selection section of the Results.')
pat = re.compile(r'\*\*Changes:\*\*\s*new Figure 1; Methods, Information sources and search '
                 r'strategy\s*[–—\-]\s*2\.4;\s*Results, Study selection\.')
if pat.search(s):
    s = pat.sub(lambda _m: new, s, count=1)
    open(P, 'w', encoding='utf-8').write(s)
    print('fixed the Information sources reference')
else:
    print('PATTERN NOT FOUND')

left = re.findall(r'.{0,50}(?:§\s*\d|Section\s+\d|Methods, |Results, ).{0,50}', s)
print('remaining mechanical section references:', len(left))
for x in left:
    print('   ', x.strip())
