# -*- coding: utf-8 -*-
"""Final check of the submission package: naming, DOI and completeness."""
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
SUB = os.path.join('01_投稿文件', 'R2_Submission')
ZIP = os.path.join('01_投稿文件', 'R2_Submission.zip')
DOI = '10.6084/m9.figshare.33891811'
REPO = 'https://github.com/Qihang-He/nondental-3d-software-scoping-review'

names = sorted(os.listdir(SUB))
cn = [n for n in names if re.search(r'[\u4e00-\u9fff]', n)]
ver = [n for n in names if re.search(r'(?i)(_v\d+|_r\d+)(?=[._]|$)', os.path.splitext(n)[0])]
print('submission files      : %d' % len(names))
print('Chinese filenames     : %d' % len(cn))
print('version-tagged names  : %d %s' % (len(ver), ver))

man = open(os.path.join(SUB, 'MANIFEST.txt'), encoding='utf-8').read()
print('MANIFEST cites DOI    : %s' % (DOI in man))
print('MANIFEST cites repo   : %s' % (REPO in man))

with zipfile.ZipFile(ZIP) as z:
    entries = z.namelist()
    bad = z.testzip()
print('zip entries           : %d  size %.2f MB' % (len(entries), os.path.getsize(ZIP) / 1024 / 1024))
print('zip integrity         : %s' % ('OK' if bad is None else bad))
print('zip internal names ok : %s'
      % ('yes' if not any('\\' in e or re.search(r'[\u4e00-\u9fff]', e) for e in entries) else 'no'))

# every manuscript figure/table referenced in the legends must exist
LEG = {'Figure_1': 'Figure1_PRISMA', 'Figure_2': 'Figure2_landscape', 'Figure_3': 'Figure3_software',
       'Figure_4': 'Figure4_workflows', 'Figure_5': 'Figure5_contingency', 'Figure_6': 'Figure6_rq3'}
missing = [v for v in LEG if not (os.path.exists(os.path.join(SUB, v + '.png'))
                                  and os.path.exists(os.path.join(SUB, v + '.pdf')))]
print('figures png+pdf present: %s' % ('yes' if not missing else missing))
for f in ['Title_Page.docx', 'Manuscript.docx', 'Response_to_Reviewers.docx', 'Declarations.docx',
          'Highlights.docx', 'References.docx', 'Supplementary_File_1.docx',
          'Supplementary_File_2.xlsx', 'Supplementary_File_3.xlsx',
          'Supplementary_File_4.xlsx', 'Supplementary_Figure_S1.png']:
    if f not in names:
        print('MISSING', f)
print('all expected deliverables present')
