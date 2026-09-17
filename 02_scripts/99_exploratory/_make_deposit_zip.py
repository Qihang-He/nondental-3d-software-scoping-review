# -*- coding: utf-8 -*-
"""
_make_deposit_zip.py —— 为 figshare/OSF 存档生成跨平台可解压的 zip

要点：
  * 使用正斜杠作为 zip 内路径分隔符（Windows 的 Compress-Archive 用反斜杠，跨平台解压会出错）
  * 排除 .git、密钥文件、.pkl 中间文件
  * 打完后自检：条目数、路径分隔符、是否含敏感文件
"""
import os
import re
import zipfile

ROOT = r'd:\Desktop\v8 for JD'
SRC = os.path.join(ROOT, '06_公共仓库')
OUTDIR = os.path.join(ROOT, '02_图表附件', 'figshare_v2.0')
OUT = os.path.join(OUTDIR, 'nondental-3d-software-reproducibility-materials.zip')

EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules'}
EXCLUDE_FILES = {'config.local.json'}
EXCLUDE_EXT = {'.pkl', '.pyc', '.pyo'}
SECRET_RES = [
    re.compile(r'sk-[A-Za-z0-9]{20,}'),
    re.compile(r'ghp_[A-Za-z0-9]{20,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{20,}'),
]

os.makedirs(OUTDIR, exist_ok=True)
if os.path.exists(OUT):
    os.remove(OUT)

n = 0
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for d, dirs, fs in os.walk(SRC):
        dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
        for f in sorted(fs):
            if f in EXCLUDE_FILES or os.path.splitext(f)[1].lower() in EXCLUDE_EXT:
                continue
            p = os.path.join(d, f)
            rel = os.path.relpath(p, SRC).replace(os.sep, '/')
            z.write(p, rel)
            n += 1

print('已写入 %d 个文件 ->' % n, OUT)

# ---------------- 自检 ----------------
with zipfile.ZipFile(OUT) as z:
    names = z.namelist()
    bad_sep = [x for x in names if '\\' in x]
    bad_file = [x for x in names if x.startswith('.git/') or 'config.local' in x
                or x.endswith(('.pkl', '.pyc'))]
    secrets = []
    for x in names:
        info = z.getinfo(x)
        if info.file_size > 40 * 1024 * 1024:
            continue
        try:
            txt = z.read(x).decode('utf-8', 'ignore')
        except Exception:
            continue
        if any(p.search(txt) for p in SECRET_RES):
            secrets.append(x)

print('条目数          :', len(names))
print('含反斜杠的条目  :', len(bad_sep))
print('敏感/中间文件   :', bad_file or '无')
print('含密钥的文件    :', secrets or '无')
print('解压测试        :', 'OK' if not zipfile.ZipFile(OUT).testzip() else '损坏')
print('压缩包大小      : %.1f MB' % (os.path.getsize(OUT) / 1024 / 1024))
