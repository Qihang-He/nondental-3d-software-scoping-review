# -*- coding: utf-8 -*-
"""检查脚本中残留的旧路径字面量"""
import os

ROOT = r'd:\Desktop\v8 for JD'
PATS = ["'pdf'", 'pdf_dir', 'PDF_DIR', '检索式', '06_仓库归档', '05_图表_v',
        '00_总览与留痕', '05_AI重跑', '05_公共仓库_R2', 'R2_草稿']
found = False
for r, _, fs in os.walk(os.path.join(ROOT, '04_代码')):
    for f in fs:
        if not f.endswith('.py'):
            continue
        fp = os.path.join(r, f)
        t = open(fp, encoding='utf-8', errors='ignore').read()
        for p in PATS:
            if p in t:
                found = True
                for m in [i for i in range(len(t)) if t.startswith(p, i)][:2]:
                    s = max(0, m - 70)
                    print('%-34s %-14s %s' % (f, p, t[s:m + 70].replace('\n', ' ')))
if not found:
    print('未发现残留旧路径')
