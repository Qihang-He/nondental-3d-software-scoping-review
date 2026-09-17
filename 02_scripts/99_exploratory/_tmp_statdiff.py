# -*- coding: utf-8 -*-
"""Diff the v5 and v6 statistics cores to drive document updates."""
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
ANA = os.path.join('03_数据', '08_分析用')
OUT = os.path.join('04_代码', '07_文档', '_tmp_statdiff.txt')

a = json.load(open(os.path.join(ANA, '统计核心_v5.json'), encoding='utf-8'))
b = json.load(open(os.path.join(ANA, '统计核心_v6.json'), encoding='utf-8'))

L = []


def flat(d, pre=''):
    r = {}
    for k, v in d.items():
        key = '%s.%s' % (pre, k) if pre else k
        if isinstance(v, dict):
            r.update(flat(v, key))
        elif isinstance(v, list):
            r[key] = json.dumps(v, ensure_ascii=False)
        else:
            r[key] = v
    return r


fa, fb = flat(a), flat(b)
keys = [k for k in sorted(set(fa) | set(fb)) if not k.startswith('archetype_method')]
L.append('%-46s %-14s %-14s' % ('KEY', 'v5 (861)', 'v6 (853)'))
L.append('-' * 80)
for k in keys:
    va, vb = fa.get(k, '-'), fb.get(k, '-')
    mark = '  <-- CHANGED' if va != vb else ''
    L.append('%-46s %-14s %-14s%s' % (k[:46], str(va)[:14], str(vb)[:14], mark))

L.append('')
L.append('=== values present in v5 but missing in v6 ===')
for k in sorted(set(fa) - set(fb)):
    L.append('   %s = %s' % (k, fa[k]))
L.append('=== values present in v6 but missing in v5 ===')
for k in sorted(set(fb) - set(fa)):
    L.append('   %s = %s' % (k, fb[k]))

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
print('changed keys:', sum(1 for k in keys if fa.get(k, '-') != fb.get(k, '-')))
