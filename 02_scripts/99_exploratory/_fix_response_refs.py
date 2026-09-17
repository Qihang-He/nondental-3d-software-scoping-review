# -*- coding: utf-8 -*-
"""Replace numbered section references in the response letter with the new heading names."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
P = os.path.join('01_投稿文件', 'R2_草稿', 'Response_to_reviewers_R2.md')
s = open(P, encoding='utf-8').read()

REPL = [
    ('Methods §2.3', 'Methods, Information sources and search strategy'),
    ('Methods §2.4', 'Methods, Study selection'),
    ('Methods §2.5–2.6', 'Methods, Data charting and synthesis'),
    ('Methods §2.5', 'Methods, Data charting and synthesis'),
    ('Results §3.1–3.2', 'Results, Study selection and Characteristics of the included studies'),
    ('Results §3.2–3.3', 'Results, Characteristics of the included studies and Software'),
    ('Results §3.1', 'Results, Study selection'),
    ('Results §3.2', 'Results, Characteristics of the included studies'),
    ('Results §3.3', 'Results, Software'),
    ('Results §3.4', 'Results, Workflow patterns'),
    ('Results §3.5', 'Results, Discipline and software family'),
    ('Results §3.6', 'Results, Advantages, challenges and gaps'),
]

for a, b in REPL:
    s = s.replace(a, b)

open(P, 'w', encoding='utf-8').write(s)

left = re.findall(r'.{0,60}(?:§\s*\d|Section\s+\d).{0,60}', s)
print('remaining numbered references:', len(left))
for x in left:
    print('   ', x.strip())
print()
print('occurrences of the word "Section":', len(re.findall(r'\bSection\b', s)))
