# -*- coding: utf-8 -*-
"""Style audit of the manuscript: LLM-flavoured wording, sentence length, punctuation habits."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
P = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
md = open(P, encoding='utf-8').read()
body = md[md.index('## Introduction'):md.index('## Figure legends')]

FLAGS = ['furthermore', 'moreover', 'additionally', 'notably', 'importantly',
         'it is worth noting', 'it is important to note', 'delve', 'underscore',
         'pivotal', 'crucial', 'robust', 'holistic', 'leverage', 'paradigm',
         'landscape', 'testament', 'realm', 'myriad', 'seamless', 'in conclusion',
         'plays a vital role', 'shed light', 'at the forefront', 'cutting-edge',
         'comprehensive understanding', 'in the realm of', 'significant strides']

print('=== LLM-flavoured wording ===')
total = 0
for f in FLAGS:
    n = len(re.findall(re.escape(f), body, re.I))
    if n:
        print('   %-32s %d' % (f, n))
        total += n
print('   total flagged terms: %d' % total)

print()
print('=== punctuation ===')
print('   em dashes (—)          : %d' % body.count('—'))
print('   en dashes (–)          : %d' % body.count('–'))
print('   semicolons             : %d' % body.count(';'))
print('   parenthetical dashes   : %d' % len(re.findall(r'\s—\s', body)))

print()
print('=== sentence length ===')
sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', re.sub(r'\s+', ' ', body))
         if len(s.split()) > 3]
lens = sorted((len(s.split()) for s in sents), reverse=True)
print('   sentences              : %d' % len(sents))
print('   mean words/sentence    : %.1f' % (sum(lens) / len(lens)))
print('   longest 8              : %s' % lens[:8])
print('   over 45 words          : %d' % sum(1 for x in lens if x > 45))
for s in sents:
    if len(s.split()) > 48:
        print('     [%d] %s' % (len(s.split()), s[:170]))

print()
print('=== sentence openings (repetition) ===')
from collections import Counter
firsts = Counter(' '.join(s.split()[:1]).lower() for s in sents)
for w, n in firsts.most_common(8):
    print('   %-14s %d' % (w, n))
