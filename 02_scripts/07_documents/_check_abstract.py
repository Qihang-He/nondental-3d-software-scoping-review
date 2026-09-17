# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_check_abstract.py —— 检查摘要字数与关键数字一致性"""
import os
import re
import json

ROOT = _ROOTP
MS = os.path.join(ROOT, '01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
t = open(MS, encoding='utf-8').read()

ab = t[t.index('## Abstract'):t.index('**Keywords:**')]
body = ab[ab.index('**Objective.**'):]
for label in ('Objective', 'Methods', 'Results', 'Conclusions', 'Clinical significance'):
    seg = re.search(r'\*\*%s\.\*\*(.*?)(?=\*\*[A-Z]|\Z)' % label, ab, re.S)
    if seg:
        n = len(seg.group(1).split())
        print('%-22s %3d words' % (label, n))
main = re.search(r'\*\*Objective\.\*\*(.*?)\*\*Clinical significance', ab, re.S).group(1)
print('--- 摘要正文（不含 clinical significance）: %d words' % len(main.split()))

S = json.load(open(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用', '统计核心.json'), encoding='utf-8'))
N = S['N']
checks = {
    'N = %d' % N: N,
    '325': N and 1,
}
print('\n关键数字出现在正文中：')
for kw in ['863', '3,726', '1,170', '2,556', '1,943', '1,168', '304', '1,781', '918',
           '232', '8 conference', '58 countries', '110 nondental', '1,378', '337',
           '349', '240', '181', '0.229', '0.712', '47.4', '656']:
    c = t.count(kw)
    print('   %-16s 出现 %d 次' % (kw, c))

print('\n旧数字残留检查：')
for kw in ['566 studies', 'n = 566', '3,631', '1,075', '917 software', '783 study', '755 scenario',
           'k = 5', '0.64 ', 'Eighty-five', '188 journals']:
    c = t.count(kw)
    print('   %-16s 出现 %d 次%s' % (kw, c, '  <-- 需处理' if c else ''))
