# -*- coding: utf-8 -*-
"""Precise abstract word counts under both plausible journal conventions."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
P = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
md = open(P, encoding='utf-8').read()
ab = md[md.index('## Abstract'):md.index('## Introduction')]
ab_no_kw = ab[:ab.index('**Keywords:**')]


def wc(s):
    s = re.sub(r'[*#_`>|]', ' ', s)
    return len([w for w in s.split() if re.search(r'\w', w)])


body = ab_no_kw[ab_no_kw.index('**Objective.**'):]
cs = body[body.index('**Clinical significance.**'):]
main = body[:body.index('**Clinical significance.**')]
print('Objective..Conclusions                  : %d words' % wc(main))
print('Clinical significance                   : %d words' % wc(cs))
print('Objective..Clinical significance        : %d words   <- likely journal limit applies here' % wc(body))
print('including the Keywords line             : %d words' % wc(ab_no_kw))
print('limit                                   : 250 words')
print()
if wc(body) > 250:
    print('OVER by %d words' % (wc(body) - 250))
else:
    print('within limit (margin %d)' % (250 - wc(body)))
