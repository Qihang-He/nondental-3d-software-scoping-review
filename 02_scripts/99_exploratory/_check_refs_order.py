# -*- coding: utf-8 -*-
"""Check reference numbering order against citation order, and measure manuscript length."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')
MS = open(os.path.join(D, 'Revised_manuscript_R2.md'), encoding='utf-8').read()
REF = open(os.path.join(D, 'References_R2.md'), encoding='utf-8').read()

body = MS[:MS.index('## Figure legends')]
legends = MS[MS.index('## Figure legends'):]

# --- citation order (body only; legends cite nothing)
cites = []
for m in re.finditer(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\]', body):
    for part in re.split(r'\s*,\s*', m.group(1)):
        part = part.strip()
        if re.match(r'^\d+$', part):
            cites.append(int(part))
        elif re.match(r'^\d+\s*[–-]\s*\d+$', part):
            a, b = re.split(r'\s*[–-]\s*', part)
            cites.extend(range(int(a), int(b) + 1))

first_seen, order = set(), []
for c in cites:
    if c not in first_seen:
        first_seen.add(c)
        order.append(c)

listed = [int(m.group(1)) for m in re.finditer(r'^\[(\d+)\]', REF, re.M)]
print('citations in body           : %d occurrences, %d distinct' % (len(cites), len(order)))
print('references listed           : %d' % len(listed))
print()
print('first-citation order        :', order)
print('reference list order        :', listed)
print()
print('list already in citation order:', order == listed)
if order != listed:
    print()
    print('position-by-position comparison (citation order -> currently at that number):')
    for i, want in enumerate(order, 1):
        have = listed[i - 1] if i <= len(listed) else None
        flag = '' if have == want else '   <-- MISMATCH'
        if have != want:
            print('   position %-4d should be [%d]%s' % (i, want, flag))

missing = [c for c in sorted(first_seen) if c not in listed]
never = [c for c in listed if c not in first_seen]
print()
print('cited but not listed        :', missing)
print('listed but never cited      :', never)

# --- Word-style word counts (whitespace tokens, citations intact)
def wordish(s):
    s = re.sub(r'[#*_`>|]', ' ', s)
    return len([w for w in s.split() if re.search(r'\w', w)])


print()
print('=== length, Word-style counting (brackets counted as words) ===')
print('   title + abstract + body + legends : %d' % wordish(MS))
print('   body only (Introduction..Conclusions): %d'
      % wordish(MS[MS.index('## Introduction'):MS.index('## Figure legends')]))
print('   figure legends                    : %d' % wordish(legends))
print('   references file                   : %d' % wordish(REF))
