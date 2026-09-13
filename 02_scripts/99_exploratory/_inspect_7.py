# -*- coding: utf-8 -*-
"""_inspect_7.py —— 对全文确无非牙科3D软件名的 7 篇，抽取含 software/program/version 的段落供判读"""
import os
import re
import pandas as pd
import pymupdf

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
chk = pd.read_csv(os.path.join(ANA, '纳入集复核_确定性核查.csv'), low_memory=False)
sub = chk[chk['结论'].str.startswith('C_全文未出现')]
print('待判读：%d 篇\n' % len(sub))
RX = re.compile(r'(software|program(?:me)?\b|version\s*[\d.]|V\s?[\d.]+\s*\(|'
                r'were (?:analysed|analyzed|measured|designed|processed)|'
                r'using (?:the )?[A-Z][A-Za-z]+\s|Geomagic|Rhinoceros|Fusion|Magics|'
                r'Solid Edge|Avizo|Blender|ANSYS|Mimics)', re.I)
for _, r in sub.iterrows():
    print('=' * 100)
    print('题名:', r['Title'])
    print('原标注软件:', r['原标注软件'], '| PDF:', r['PDF'])
    p = os.path.join(ROOT, '10_全文PDF库', str(r['PDF']))
    if not os.path.exists(p):
        print('  （文件缺失）')
        continue
    doc = pymupdf.open(p)
    txt = re.sub(r'\s+', ' ', '\n'.join(pg.get_text() for pg in doc))
    doc.close()
    seen, n = set(), 0
    for m in RX.finditer(txt):
        s = max(0, m.start() - 200)
        e = min(len(txt), m.end() + 200)
        k = s // 250
        if k in seen:
            continue
        seen.add(k)
        print('   ...%s...' % txt[s:e])
        n += 1
        if n >= 8:
            break
    if n == 0:
        print('   （未见 software/program 相关表述；全文长度 %d）' % len(txt))
    print()
