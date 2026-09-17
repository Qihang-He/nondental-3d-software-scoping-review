# -*- coding: utf-8 -*-
"""Repack the clean submission folder into R2_Submission.zip and show the manifest."""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
SUB = os.path.join('01_投稿文件', 'R2_Submission')
ZIP = os.path.join('01_投稿文件', 'R2_Submission.zip')

print('--- MANIFEST.txt ---')
print(open(os.path.join(SUB, 'MANIFEST.txt'), encoding='utf-8').read())

if os.path.exists(ZIP):
    os.remove(ZIP)
names = sorted(os.listdir(SUB))
with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
    for n in names:
        z.write(os.path.join(SUB, n), n)
with zipfile.ZipFile(ZIP) as z:
    entries = z.namelist()
print('--- %s ---' % ZIP)
print('entries =', len(entries), ' size = %.2f MB' % (os.path.getsize(ZIP) / 1024 / 1024))
for e in entries:
    print('   ', e)
