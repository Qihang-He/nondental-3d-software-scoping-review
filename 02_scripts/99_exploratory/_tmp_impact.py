# -*- coding: utf-8 -*-
"""Verify software-list conformance + compute impact of removing non-conforming packages."""
import os
from collections import Counter
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
DATA = os.path.join('03_数据', '08_分析用', '分析数据集_final_v5.csv')
OUT = os.path.join('04_代码', '07_文档', '_tmp_impact.txt')
d = pd.read_csv(DATA, low_memory=False)

softs = []
for v in d['_soft2']:
    try:
        s = set(eval(v)) if isinstance(v, str) else set(v or [])
    except Exception:
        s = set()
    softs.append(s)

# ---- audit verdicts -------------------------------------------------------
PROG = {'MATLAB', 'Python', 'GNU Octave', 'TensorFlow', 'Keras'}          # computing/ML platforms
LIB = {'Open3D', 'Trimesh', 'Iso2mesh', 'Scalismo Lab'}                    # programming libraries
DENTAL = {'R2 Gate'}                                                       # dental-specific origin
DENTAL_ORIENT = {'Viewbox'}                                                # dental-oriented (cephalometric)
UNVERIFIED = {'CreatWare', 'Midas'}                                        # cannot confirm

EXCL = PROG | LIB | DENTAL | DENTAL_ORIENT | UNVERIFIED

cnt = Counter()
for s in softs:
    for x in s:
        cnt[x] += 1

L = []
L.append('=== EXCLUDED PACKAGES AND THEIR STUDY COUNTS ===')
for grp, name in [(PROG, 'PROGRAMMING / NUMERICAL / ML PLATFORM'),
                  (LIB, 'PROGRAMMING LIBRARY (not an application)'),
                  (DENTAL, 'DENTAL-SPECIFIC ORIGIN'),
                  (DENTAL_ORIENT, 'DENTAL-ORIENTED (cephalometric)'),
                  (UNVERIFIED, 'UNVERIFIABLE (no source / no evidence)')]:
    L.append('')
    L.append('[%s]' % name)
    for s in sorted(grp, key=lambda x: -cnt.get(x, 0)):
        L.append('   %-16s assignments=%d' % (s, cnt.get(s, 0)))

L.append('')
L.append('=== STUDIES USING ONLY EXCLUDED PACKAGES (would be REMOVED) ===')
removed = []
for i, s in enumerate(softs):
    if s and s <= EXCL:
        removed.append(i)
        r = d.iloc[i]
        L.append('   %-10s | %-38s | %s' % (r['Key'], str(r['Software Used (fixed)'])[:38],
                                            str(r['Title'])[:95]))
L.append('   --> %d studies removed ; N = %d' % (len(removed), 861 - len(removed)))

L.append('')
L.append('=== STUDIES KEEPING EXCLUDED PACKAGES ALONGSIDE VALID ONES (software list shrinks only) ===')
for i, s in enumerate(softs):
    inter = s & EXCL
    if inter and not (s <= EXCL):
        r = d.iloc[i]
        L.append('   %-10s | drop=%-24s | keep=%s' % (
            r['Key'], ','.join(sorted(inter)), ','.join(sorted(s - EXCL))))

L.append('')
L.append('=== REMAINING PACKAGES AFTER EXCLUSION ===')
keepnames = sorted([k for k in cnt if k not in EXCL])
L.append('   %d packages, %d assignments' % (len(keepnames), sum(cnt[k] for k in keepnames)))

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written:', OUT)
print('removed studies =', len(removed), 'N =', 861 - len(removed))
print('remaining packages =', len(keepnames), 'assignments =', sum(cnt[k] for k in keepnames))
