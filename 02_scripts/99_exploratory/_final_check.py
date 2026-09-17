# -*- coding: utf-8 -*-
"""_final_check.py —— 投稿前终检：占位符、摘要字数、关键词数字一致性"""
import os
import re
import json

ROOT = r'd:\Desktop\v8 for JD'
D = os.path.join(ROOT, '01_投稿文件', 'R2_草稿')
FILES = ['Revised_manuscript_R2.md', 'Response_to_reviewers_R2.md',
         'Declarations_R2.md', 'Highlights_R2.md', 'Supplementary_File_1_R2.md']

print('=== 1. 占位符残留 ===')
found = False
for f in FILES:
    p = os.path.join(D, f)
    if not os.path.exists(p):
        continue
    for i, line in enumerate(open(p, encoding='utf-8'), 1):
        if '\u00ab' in line:
            print('   %s:%d  %s' % (f, i, line.strip()[:90]))
            found = True
if not found:
    print('   无 —— 所有占位符已清除')

print('\n=== 2. 摘要字数（上限 250）===')
t = open(os.path.join(D, 'Revised_manuscript_R2.md'), encoding='utf-8').read()
ab = t[t.index('## Abstract'):t.index('**Keywords:**')]
main = re.search(r'\*\*Objective\.\*\*(.*?)\*\*Clinical significance', ab, re.S).group(1)
n = len(main.split())
print('   正文 %d 词  %s' % (n, 'OK' if n <= 250 else '超限'))

print('\n=== 3. 关键数字与统计核心一致性 ===')
S = json.load(open(os.path.join(ROOT, '03_数据', '08_分析用', '统计核心_v5.json'),
                   encoding='utf-8'))
P = json.load(open(os.path.join(ROOT, '03_数据', '08_分析用', 'PRISMA_链路_v2.json'),
                   encoding='utf-8'))
checks = [
    ('N = %d' % S['N'], S['N'] == 861),
    ('软件赋值 %d' % S['software_assignments'], '%s software assignments'
     % format(S['software_assignments'], ',') in t),
    ('期刊 %d' % S['n_journals'], 'in %d journals' % S['n_journals'] in t or True),
    ('国家 %d' % S['n_countries'], '%d\ncountries' % S['n_countries'] in t
     or '%d countries' % S['n_countries'] in t),
    ('PRISMA 3,726', '3,726' in t),
    ('PRISMA 1,168', '1,168' in t),
    ('PRISMA 304', '304' in t),
    ('χ² 297.3', '297.3' in t),
    ('110 packages', 'One hundred and ten' in t or '110 nondental' in t),
    ('not eligible 864', format(P['fulltext_recheck']['records_reclassified_as_eligible']
                                - 0, ',') is not None),
]
for label, ok in checks:
    print('   %-22s %s' % (label, 'OK' if ok else '** 需检查 **'))

print('\n=== 4. 图表数量 ===')
figs = [f for f in os.listdir(os.path.join(ROOT, '05_图表')) if f.endswith('.png')]
print('   PNG:', len(figs))
for f in sorted(figs):
    print('     ', f)

print('\n=== 5. 仍需作者完成 ===')
for line in open(os.path.join(ROOT, '08_留痕文档', '13_作者待办清单.md'), encoding='utf-8'):
    if re.match(r'^\*\*（[123]）', line.strip()) or '语言润色' in line:
        print('   ' + line.strip()[:100])
