# -*- coding: utf-8 -*-
"""Accurate word counts for the manuscript revision (main text = Introduction .. Conclusions)."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
OLD = os.path.join('01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
NEW = os.path.join('04_代码', '07_文档', '_manuscript_revision.md')


def wc(s):
    s = re.sub(r'\[[\d,\u2013\-]+\]', ' ', s)
    s = re.sub(r'[*#_`>|]', ' ', s)
    return len([w for w in s.split() if re.search(r'\w', w)])


def counts(path):
    md = open(path, encoding='utf-8').read()

    def pos(pattern):
        m = re.search(pattern, md, re.M)
        if not m:
            raise SystemExit('heading not found: %s in %s' % (pattern, path))
        return m.start()

    def between(pa, pb):
        i, j = pos(pa), pos(pb)
        return md[i:j]

    abstract = between(r'^##\s+(?:\d+\.\s+)?Abstract', r'^##\s+(?:\d+\.\s+)?Introduction')
    main = between(r'^##\s+(?:\d+\.\s+)?Introduction', r'^##\s+Figure legends')
    legends = md[pos(r'^##\s+Figure legends'):]
    return {
        'abstract': wc(abstract),
        'main text (Introduction .. Conclusions)': wc(main),
        'figure legends': wc(legends),
        'whole file': wc(md),
    }


o, n = counts(OLD), counts(NEW)
print('%-42s %9s %9s %9s' % ('', 'current', 'revised', 'delta'))
print('-' * 72)
for k in o:
    print('%-42s %9d %9d %+9d' % (k, o[k], n[k], n[k] - o[k]))
print()
print('main text + legends + abstract (what counts towards the page allowance)')
print('  current  : %d' % (o['main text (Introduction .. Conclusions)'] + o['figure legends'] + o['abstract']))
print('  revised  : %d' % (n['main text (Introduction .. Conclusions)'] + n['figure legends'] + n['abstract']))
print()
print('journal allowance: Original Research Report = ~6 printed pages / ~20 word-processed pages')
print('  at ~250 words per double-spaced page that is roughly 5,000 words in total.')
