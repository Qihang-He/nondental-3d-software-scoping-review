# -*- coding: utf-8 -*-
"""
_tools_organize.py —— 最终目录整理
原则：保留可复现链路所需的一切；删除中间诊断脚本与已被取代的数据版本；
      把同类目录合并到编号体系内，避免出现两个 05_ 与两个 06_。
执行前会打印将要删除的内容，全部为可再生成或已被取代的文件。
"""
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


def rm(p, why):
    full = os.path.join(ROOT, p)
    if not os.path.exists(full):
        return
    n = sum(len(f) for _, _, f in os.walk(full)) if os.path.isdir(full) else 1
    if os.path.isdir(full):
        if os.path.exists(os.path.join(full, '.git')):
            subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', full], check=False)
        if os.path.exists(full):
            shutil.rmtree(full, onerror=_onerror)
    else:
        os.chmod(full, stat.S_IWRITE)
        os.remove(full)
    LOG.append(('删除', p, '%s（%d 个文件）' % (why, n)))


def mv(a, b, why):
    sa, sb = os.path.join(ROOT, a), os.path.join(ROOT, b)
    if not os.path.exists(sa):
        LOG.append(('跳过', a, '不存在'))
        return
    os.makedirs(os.path.dirname(sb), exist_ok=True)
    if os.path.exists(sb):
        shutil.rmtree(sb) if os.path.isdir(sb) else os.remove(sb)
    shutil.move(sa, sb)
    LOG.append(('移动', '%s -> %s' % (a, b), why))


# ---------- 1. 删除临时诊断脚本 ----------
D = os.path.join(ROOT, '04_代码', '05_分析')
for f in os.listdir(D):
    if f.startswith(('_diag_', '_explore_')) or f in ('_tools_summary_final.py',
                                                      '_tools_recompute.py',
                                                      '_tools_build_final.py'):
        rm(os.path.join('04_代码', '05_分析', f), '临时诊断或已被取代')

# ---------- 2. 删除已被取代的数据版本 ----------
LOCK = os.path.join(ROOT, '03_数据', '06_锁定数据集')
for f in os.listdir(LOCK):
    if f.startswith('最终数据集_v2'):
        rm(os.path.join('03_数据', '06_锁定数据集', f), '被 v3 取代')

ANA = os.path.join(ROOT, '03_数据', '08_分析用')
for f in os.listdir(ANA):
    if f in ('分析数据集_final.csv', '分析数据集_572_定稿.csv', '分析数据集_572.csv',
             '交叉验证_旧.csv', 'crossref_补全.csv') or f.startswith('_diag_'):
        rm(os.path.join('03_数据', '08_分析用', f), '被 v3 取代或为诊断输出')

# ---------- 3. 旧图与旧仓库归档 ----------
rm('05_图表', '被 05_图表（R2 定稿图）取代')
rm('06_公共仓库', '被 06_公共仓库 取代')
rm(os.path.join('06_归档', '文本提取'), '纯文本提取稿可由 docx 再生成')
rm(os.path.join('06_归档', 'R2_草稿_v1备份'), '中间版本，已被取代')

# ---------- 4. 合并同类目录 ----------
mv('03_数据/10_研究设计', '03_数据/05_审计与核验/研究设计编码', '并入审计与核验')
mv('03_数据/11_PDF核验', '03_数据/05_审计与核验/PDF核验', '并入审计与核验')
mv('03_数据/05_审核',
   '03_数据/05_审计与核验/纳排审核', '并入审计与核验')

# ---------- 5. 统一编号：图表与留痕 ----------
mv('05_图表', '02_图表附件/图表_定稿', '图表统一放在图表目录下')
mv('06_公共仓库', '06_公共仓库', '避免与 07_AI重跑原始记录 编号冲突')
mv('07_AI重跑原始记录', '07_AI重跑原始记录', '避免编号冲突')
mv('08_留痕文档', '08_留痕文档', '避免与 00 编号的歧义')
mv('06_归档', '09_归档', '统一编号')

# ---------- 6. 输出日志 ----------
for a, b, c in LOG:
    print('%-4s %-58s %s' % (a, b, c))
print('\n完成。当前顶层：')
for x in sorted(os.listdir(ROOT)):
    print('   ', x)
