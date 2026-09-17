# -*- coding: utf-8 -*-
"""_tools_organize2.py —— 第二轮整理：归档历史文件、清理失效脚本、生成根 README"""
import os
import stat
import shutil
import subprocess

ROOT = r'd:\Desktop\v8 for JD'
LOG = []


def _onerror(func, path, exc):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def mv(a, b, why=''):
    sa, sb = os.path.join(ROOT, a), os.path.join(ROOT, b)
    if not os.path.exists(sa):
        return
    os.makedirs(os.path.dirname(sb), exist_ok=True)
    if os.path.exists(sb):
        if os.path.isdir(sb):
            for f in os.listdir(sa):
                shutil.move(os.path.join(sa, f), os.path.join(sb, f))
            os.rmdir(sa)
        else:
            os.remove(sb)
            shutil.move(sa, sb)
    else:
        shutil.move(sa, sb)
    LOG.append(('移动', '%s -> %s' % (a, b), why))


def rm(p, why=''):
    full = os.path.join(ROOT, p)
    if not os.path.exists(full):
        return
    if os.path.isdir(full):
        subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', full], check=False)
        if os.path.exists(full):
            shutil.rmtree(full, onerror=_onerror)
    else:
        os.chmod(full, stat.S_IWRITE)
        os.remove(full)
    LOG.append(('删除', p, why))


ARCH = '09_归档'

# 1. R1 时代的代码与图件归档
mv('04_代码/01_绘图', os.path.join(ARCH, '原始代码_R1', '01_绘图'), 'R1 绘图脚本')
mv('04_代码/02_AI初筛', os.path.join(ARCH, '原始代码_R1', '02_AI初筛'), 'R1 AI 初筛脚本')
mv('04_代码/03_其它AI', os.path.join(ARCH, '原始代码_R1', '03_其它AI'), 'R1 其它 AI 脚本')
mv('04_代码/04_整合', os.path.join(ARCH, '原始代码_R1', '04_整合'), 'R1 数据整合脚本')
mv('02_图表附件/Figure_1.pdf', os.path.join(ARCH, 'R1_图件', 'Figure_1.pdf'))
mv('02_图表附件/Figure_2.pdf', os.path.join(ARCH, 'R1_图件', 'Figure_2.pdf'))
mv('02_图表附件/Figure_3.pdf', os.path.join(ARCH, 'R1_图件', 'Figure_3.pdf'))
mv('02_图表附件/Figure_4.pdf', os.path.join(ARCH, 'R1_图件', 'Figure_4.pdf'))
mv('02_图表附件/Figure_5.pdf', os.path.join(ARCH, 'R1_图件', 'Figure_5.pdf'))
mv('02_图表附件/Figure1.docx', os.path.join(ARCH, 'R1_图件', 'Figure1.docx'))
mv('02_图表附件/Supplementary_File_1.docx', os.path.join(ARCH, 'R1_补充材料', 'Supplementary_File_1.docx'))
mv('02_图表附件/Supplementary_File_2.docx', os.path.join(ARCH, 'R1_补充材料', 'Supplementary_File_2.docx'))
mv('02_图表附件/Supplementary_File_3.xlsx', os.path.join(ARCH, 'R1_补充材料', 'Supplementary_File_3.xlsx'))

# 2. R1 投稿文件归档
for f in ['Cover letter.docx', 'Declarations.docx', 'Highlights.docx',
          'Response to reviewers.docx', 'Revised manuscript .docx',
          'Title page with author details.docx']:
    mv(os.path.join('01_投稿文件', f), os.path.join(ARCH, 'R1_投稿文件', f), 'R1 原稿')

# 3. 失效脚本清理
for p in ['04_代码/05_分析/_tools_final_stats.py',
          '04_代码/05_分析/_tools_summary_final.py',
          '04_代码/07_文档/_tools_final_pack.py',
          '04_代码/07_文档/_tools_refs.py',
          '04_代码/07_文档/_tools_consistency.py',
          '04_代码/07_文档/_check_paths.py',
          '04_代码/07_文档/_check_supp1.py']:
    rm(p, '引用了已删除的旧目录，已被 v2/v3 脚本取代')

# 4. 过时留痕归档
mv('08_留痕文档/08_最终统计汇总_572.md', os.path.join(ARCH, '过时留痕', '08_最终统计汇总_572.md'), '被 12_最终统计汇总_566.md 取代')
mv('08_留痕文档/05_613纳排风险清单.csv', os.path.join(ARCH, '过时留痕', '05_613纳排风险清单.csv'), '反映 613 阶段的中间状态')
mv('08_留痕文档/05_613纳排风险汇总.json', os.path.join(ARCH, '过时留痕', '05_613纳排风险汇总.json'), '反映 613 阶段的中间状态')

for a, b, c in LOG:
    print('%-4s %-62s %s' % (a, b, c))
print('\n剩余顶层：')
for x in sorted(os.listdir(ROOT)):
    print('   ', x)
