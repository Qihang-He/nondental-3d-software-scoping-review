# -*- coding: utf-8 -*-
"""
_scrub_keys.py —— 清除项目内硬编码的 API 密钥（全部替换为占位符）

只改写 *.py / *.txt / *.md / *.json / *.ipynb，不改动数据文件。
运行前会打印命中位置，运行后再次扫描确认清零。
"""
import os
import re

ROOT = r'd:\Desktop\v8 for JD'
EXTS = {'.py', '.txt', '.md', '.json', '.ipynb', '.cfg', '.ini', '.yaml', '.yml'}
KEY_RE = re.compile(r'sk-[A-Za-z0-9]{20,}')
PLACEHOLDER = 'sk-REPLACE-WITH-YOUR-OWN-KEY'
SKIP_DIRS = {'.git', '__pycache__', 'node_modules'}


def scan():
    hits = []
    for d, dirs, fs in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in fs:
            if os.path.splitext(f)[1].lower() not in EXTS:
                continue
            p = os.path.join(d, f)
            try:
                txt = open(p, encoding='utf-8', errors='ignore').read()
            except Exception:
                continue
            for m in KEY_RE.finditer(txt):
                hits.append((p, m.group(0)))
    return hits


before = scan()
print('发现 %d 处硬编码密钥：' % len(before))
seen = {}
for p, k in before:
    seen.setdefault(p, 0)
    seen[p] += 1
for p, n in seen.items():
    print('   %-72s %d 处  %s' % (os.path.relpath(p, ROOT), n, KEY_RE.search(
        open(p, encoding='utf-8', errors='ignore').read()).group(0)[:14] + '...'))

if not before:
    raise SystemExit(0)

changed = 0
for p in seen:
    txt = open(p, encoding='utf-8', errors='ignore').read()
    new = KEY_RE.sub(PLACEHOLDER, txt)
    if new != txt:
        open(p, 'w', encoding='utf-8').write(new)
        changed += 1

print('\n已改写 %d 个文件。' % changed)
after = scan()
print('复扫结果：%d 处' % len(after))
if after:
    for p, k in after:
        print('   ! 残留:', os.path.relpath(p, ROOT))
else:
    print('OK：项目内已无硬编码密钥。')
