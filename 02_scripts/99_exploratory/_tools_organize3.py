# -*- coding: utf-8 -*-
"""
_tools_organize3.py —— 最终定名 + 统一修正脚本内路径
最终顶层结构：
  01_投稿文件 / 02_图表附件 / 03_数据 / 04_代码 / 05_图表 /
  06_公共仓库 / 07_AI重跑原始记录 / 08_留痕文档 / 09_归档 /
  10_全文PDF库 / 11_检索策略
"""
import os
import stat
import shutil
import subprocess

ROOT = r'd:\Desktop\v8 for JD'
LOG = []


def mv(a, b):
    sa, sb = os.path.join(ROOT, a), os.path.join(ROOT, b)
    if not os.path.exists(sa):
        return
    os.makedirs(os.path.dirname(sb), exist_ok=True)
    if os.path.exists(sb):
        subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', sb], check=False)
    shutil.move(sa, sb)
    LOG.append('移动 %s -> %s' % (a, b))


# ---------- 1. 目录定名 ----------
mv('02_图表附件/图表_定稿', '05_图表')
mv('06_公共仓库', '06_公共仓库_tmp')
mv('07_AI重跑原始记录', '07_AI重跑_tmp')
mv('08_留痕文档', '08_留痕_tmp')
mv('09_归档', '09_归档_tmp')
mv('06_公共仓库_tmp', '06_公共仓库')
mv('07_AI重跑_tmp', '07_AI重跑原始记录')
mv('08_留痕_tmp', '08_留痕文档')
mv('09_归档_tmp', '09_归档')
mv('pdf', '10_全文PDF库')
mv('检索式', '11_检索策略')

# ---------- 2. 脚本路径替换 ----------
SUB = [('05_图表', '05_图表'),
       ('05_图表', '05_图表'),
       ('07_AI重跑原始记录', '07_AI重跑原始记录'),
       ('08_留痕文档', '08_留痕文档'),
       ('06_公共仓库', '06_公共仓库'),
       ('06_公共仓库', '06_公共仓库')]
changed = []
for r, _, fs in os.walk(os.path.join(ROOT, '04_代码')):
    for f in fs:
        if not f.endswith('.py'):
            continue
        fp = os.path.join(r, f)
        t0 = open(fp, encoding='utf-8').read()
        t = t0
        for a, b in SUB:
            t = t.replace(a, b)
        if t != t0:
            open(fp, 'w', encoding='utf-8').write(t)
            changed.append(f)

for x in LOG:
    print(x)
print('\n已更新路径的脚本 %d 个: %s' % (len(changed), ', '.join(sorted(changed))))
print('\n最终顶层：')
for x in sorted(os.listdir(ROOT)):
    print('   ', x)
