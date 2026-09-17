# -*- coding: utf-8 -*-
"""Reconcile the PRISMA exclusion counts against the deposited intermediate files."""
import csv, io, os, sys

sys.stdout.reconfigure(encoding='utf-8')
A = r'd:\Desktop\v8 for JD\03_数据\08_分析用'
B = r'd:\Desktop\v8 for JD\03_数据'
files = [
    os.path.join(B, '02_清洗后', '筛选语料_唯一记录_2556.csv'),
    os.path.join(B, '02_清洗后', '筛选语料_去重后.csv'),
    os.path.join(A, 'PRISMA_排除原因分类.csv'),
    os.path.join(A, 'PRISMA_未进入全文评估_1927.csv'),
    os.path.join(A, '全文再筛查_原纳入集复核.csv'),
    os.path.join(A, '全文再筛查_原纳入集复核_全量.csv'),
    os.path.join(A, '全文再筛查_新增纳入.csv'),
    os.path.join(A, '核验抽样_样本A明细.csv'),
    os.path.join(A, '核验抽样_样本B明细.csv'),
]
for f in files:
    if not os.path.exists(f):
        print(f'MISSING {f}')
        continue
    with io.open(f, encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.reader(fh))
    print(f'{os.path.basename(f):46s} rows(incl header)={len(rows):6d} cols={len(rows[0])}')
    print(f'      header: {", ".join(c[:20] for c in rows[0][:8])}')
