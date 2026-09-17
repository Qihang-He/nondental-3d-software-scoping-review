# -*- coding: utf-8 -*-
"""Authoritative check: references numbered strictly in order of first citation."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')
md = open(os.path.join(D, 'Revised_manuscript_R2.md'), encoding='utf-8').read()
ref = open(os.path.join(D, 'References_R2.md'), encoding='utf-8').read()
body = md[:md.index('## Figure legends')]
legends = md[md.index('## Figure legends'):]


def nums_of(bracket):
    inner = bracket.strip('[]')
    out = []
    for part in re.split(r'\s*,\s*', inner):
        part = part.strip()
        if re.fullmatch(r'\d+', part):
            out.append(int(part))
        elif re.fullmatch(r'\d+\s*[-\u2013]\s*\d+', part):
            a, b = re.split(r'\s*[-\u2013]\s*', part)
            out.extend(range(int(a), int(b) + 1))
    return out


brackets = [m.group(0) for m in re.finditer(r'\[[\d,\u2013-]+\]', body)]
first, seen = [], set()
for b in brackets:
    for n in nums_of(b):
        if n not in seen:
            seen.add(n)
            first.append(n)

listed = [int(m.group(1)) for m in re.finditer(r'^\[(\d+)\]', ref, re.M)]

print('brackets in body            :', len(brackets))
print('distinct references cited   :', len(first))
print('references listed           :', len(listed))
print()
print('first-citation order strictly 1..N :', first == list(range(1, len(first) + 1)))
print('reference list == citation order   :', listed == first == list(range(1, len(listed) + 1)))
print()
print('bracket sequence as printed:')
print('   ' + ' '.join(brackets))
print()
dup = [n for n in set(first) if first.count(n) > 1]
print('references cited more than once (expected: many):', len(dup))
ungrouped = [b for b in brackets if nums_of(b) != sorted(nums_of(b))]
print('brackets whose numbers are not ascending :', len(ungrouped), ungrouped[:5])
print()
print('legends cite nothing                    :',
      len(re.findall(r'\[[\d,\u2013-]+\]', legends)) == 0)
