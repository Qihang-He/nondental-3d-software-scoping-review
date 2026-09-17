# -*- coding: utf-8 -*-
"""
_assemble_submission.py —— 组装最终英文投稿包（R2_Submission）。

从 R2_草稿（docx）、05_图表（图件）、R2_补充材料（补充材料）复制到统一目录。
版本号只在目录名（R2_Submission）标注，内部文件按期刊规范使用干净英文名（不带 R2）。
"""
import os
import shutil

ROOT = os.environ.get('SCOPING_ROOT') or r'd:\Desktop\v8 for JD'
SRC_DOC = os.path.join(ROOT, '01_投稿文件', 'R2_草稿')
SRC_FIG = os.path.join(ROOT, '05_图表')
SRC_SUP = os.path.join(ROOT, '02_图表附件', 'R2_补充材料')
OUT = os.path.join(ROOT, '01_投稿文件', 'R2_Submission')

os.makedirs(OUT, exist_ok=True)

# 源文件名 -> 干净英文名（去掉 R2 后缀）
DOC_MAP = {
    'Revised_manuscript_R2.docx': 'Manuscript.docx',
    'Response_to_reviewers_R2.docx': 'Response_to_Reviewers.docx',
    'Declarations_R2.docx': 'Declarations.docx',
    'Highlights_R2.docx': 'Highlights.docx',
    'References_R2.docx': 'References.docx',
    'Supplementary_File_1_R2.docx': 'Supplementary_File_1.docx',
}

FIG_MAP = {
    'Figure1_PRISMA': 'Figure_1_PRISMA',
    'Figure2_landscape': 'Figure_2_Landscape',
    'Figure3_software': 'Figure_3_Software',
    'Figure4_workflows': 'Figure_4_Workflows',
    'Figure5_contingency': 'Figure_5_Contingency',
    'Figure6_rq3': 'Figure_6_RQ3',
    'Supplementary_Figure_S1_journals': 'Supplementary_Figure_S1_Journals',
}

SUP_MAP = {
    'Supplementary_File_2_R2.xlsx': 'Supplementary_File_2.xlsx',
    'Supplementary_File_3.xlsx': 'Supplementary_File_3.xlsx',
    'Supplementary_File_4_Author_verification.xlsx': 'Supplementary_File_4.xlsx',
}

manifest = []

for old, new in DOC_MAP.items():
    src = os.path.join(SRC_DOC, old)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(OUT, new))
        manifest.append(new)

for old, new in FIG_MAP.items():
    for ext in ('.png', '.pdf'):
        src = os.path.join(SRC_FIG, old + ext)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(OUT, new + ext))
            manifest.append(new + ext)

for old, new in SUP_MAP.items():
    src = os.path.join(SRC_SUP, old)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(OUT, new))
        manifest.append(new)

# 清单
with open(os.path.join(OUT, 'MANIFEST.txt'), 'w', encoding='utf-8') as f:
    f.write('R2 final submission package (English filenames)\n')
    f.write('Generated 2026-09-17\n\n')
    f.write('Manuscript and supporting documents:\n')
    for m in manifest:
        f.write('  - %s\n' % m)
    f.write('\nData archive:\n')
    f.write('  - figshare DOI 10.6084/m9.figshare.33870937.v1\n')
    f.write('  - GitHub https://github.com/Qihang-He/nondental-3d-software-scoping-review (release v2.0)\n')

print('已组装 %d 个文件 ->' % len(manifest), OUT)
for m in manifest:
    print('  ', m)
