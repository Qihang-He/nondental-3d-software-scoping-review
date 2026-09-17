# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_check_search_unique.py —— 按标题/DOI 去重后统计各库唯一记录数"""
import os
import re
from collections import Counter
import pandas as pd

ROOT = _os.path.join(_ROOTP, _os.path.join(_ROOTP, '11_检索策略'))


def parse_bib(fp):
    t = open(fp, encoding='utf-8', errors='ignore').read()
    entries = re.split(r'(?=@\w+\s*\{)', t)
    out = []
    for e in entries:
        if not e.strip().startswith('@'):
            continue
        ti = re.search(r'\btitle\s*=\s*[{"](.+?)[}"]\s*,?\s*\n', e, re.S | re.I)
        doi = re.search(r'\bdoi\s*=\s*[{"](.+?)[}"]', e, re.S | re.I)
        out.append((ti.group(1) if ti else '',
                    doi.group(1).strip().lower() if doi else ''))
    return out


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())


wos, ieee = [], []
for f in sorted(os.listdir(ROOT)):
    if not f.endswith('.bib'):
        continue
    rows = parse_bib(os.path.join(ROOT, f))
    if f.startswith('wos'):
        wos += rows
    else:
        ieee += rows
    print('%-26s %d 条' % (f, len(rows)))

pub = len(re.findall(r'^PMID- ', open(os.path.join(ROOT, 'pubmed-softwarewa-set.txt'),
                                      encoding='utf-8', errors='ignore').read(), re.M))


def uniq(rows):
    by_t = {norm(t) for t, d in rows if norm(t)}
    by_d = {d for t, d in rows if d}
    return len(by_t), len(by_t | set()) if not by_d else len({norm(t) for t, d in rows if norm(t)})


ut, _ = uniq(wos)
print('\nWeb of Science: 导出 %d 条，标题去重后 %d 条' % (len(wos), ut))
ut2, _ = uniq(ieee)
print('IEEE: 导出 %d 条，标题去重后 %d 条' % (len(ieee), ut2))
print('PubMed: %d 条' % pub)
print('\n按导出文件合计 = %d' % (len(wos) + len(ieee) + pub))
print('去重后合计 = %d' % (ut + ut2 + pub))
print('\n原稿采用：PubMed 1,727 + WoS 1,605 + IEEE 299 = 3,631')
print('差异：WoS %+d ；IEEE %+d' % (ut - 1605, ut2 - 299))
