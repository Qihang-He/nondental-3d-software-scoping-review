# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_check_search_counts.py —— 从检索导出文件直接统计各库命中数，核实 3,631 的来源"""
import os
import re

ROOT = _os.path.join(_ROOTP, _os.path.join(_ROOTP, '11_检索策略'))


def count_bib(fp):
    t = open(fp, encoding='utf-8', errors='ignore').read()
    types = re.findall(r'@(\w+)\s*\{', t)
    types = [x.lower() for x in types if x.lower() not in
             ('comment', 'string', 'preamble')]
    from collections import Counter
    return len(types), Counter(types)


def count_medline(fp):
    t = open(fp, encoding='utf-8', errors='ignore').read()
    return len(re.findall(r'^PMID- ', t, re.M))


tot = {}
for f in sorted(os.listdir(ROOT)):
    fp = os.path.join(ROOT, f)
    if f.lower().endswith('.bib'):
        n, c = count_bib(fp)
        tot[f] = n
        print('%-26s %d 条  %s' % (f, n, dict(c)))
    elif f.lower().endswith('.txt') and 'set' in f.lower():
        n = count_medline(fp)
        tot[f] = n
        print('%-26s %d 条（MEDLINE 记录）' % (f, n))

ieee = sum(v for k, v in tot.items() if k.startswith('IEEE-AA'))
wos = sum(v for k, v in tot.items() if k.startswith('wos'))
pub = sum(v for k, v in tot.items() if 'pubmed-softwarewa' in k.lower())
print('\nIEEE 合计: %d' % ieee)
print('Web of Science 合计: %d' % wos)
print('PubMed: %d' % pub)
print('三库总计: %d' % (ieee + wos + pub))
print('\n（注：.bib 按条目计数，可能含少量重复；PubMed 文件按 PMID 计数）')
