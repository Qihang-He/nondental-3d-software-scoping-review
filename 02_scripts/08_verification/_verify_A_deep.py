# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""
_verify_A_deep.py
1) 读 23、33、137 的 PDF 首页，判断文献类型与所用软件
2) 检查纳入集（566）中是否含深度学习框架类"软件"（判断 157 的 nnU-Net 是否与纳入标准一致）
3) 输出 152 的完整信息
"""
import os
import re
import unicodedata
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
PDF = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


# ---------- 1. PDF 首页 ----------
import pymupdf
PDFS = {
    23: 'Claus 等 - 2026 - Efficacy of Ai Enabled Software in Automatic Segmentation for Orthognathic Surgery.pdf',
    33: 'Wu 等 - 2023 - Influence of different education approaches on the implantation performance of dental practitioners.pdf',
    137: 'Febvey 等 - 2023 - Root canal disinfection and maintenance of the remnant tooth tissues by using grape seed and cranber.pdf',
}
for n, f in PDFS.items():
    fp = os.path.join(PDF, f)
    print('=' * 96)
    print('编号 %s ｜ PDF: %s' % (n, f))
    if not os.path.exists(fp):
        print('  !! 文件不存在')
        continue
    doc = pymupdf.open(fp)
    t = doc[0].get_text()
    print('  ---- 首页前 1500 字符 ----')
    print(re.sub(r'\n{2,}', '\n', t)[:1500])
    doc.close()

# ---------- 2. 纳入集是否含深度学习框架类软件 ----------
print('=' * 96)
sw = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
names = sw['规范名称'].astype(str).tolist()
PAT = re.compile(r'nnU|PyTorch|TensorFlow|Keras|deep learn|YOLO|MATLAB|Python|ITK|'
                 r'SimpleITK|OpenCV|Unity|Unreal|Blender|CloudCompare|ParaView|'
                 r'MeshLab|Open3D|Cura|Slic3r|Python|scikit', re.I)
hits = [x for x in names if PAT.search(x)]
print('纳入集软件表中与深度学习/通用计算相关的条目：')
for h in hits:
    row = sw[sw['规范名称'] == h].iloc[0]
    print('   %-22s 类别=%-8s 研究数=%s' % (h, row['类别'], row['研究数']))
print('（共 %d 条）' % len(hits))

# ---------- 3. 152 完整信息 ----------
print('=' * 96)
sa = pd.read_csv(os.path.join(ANA, '核验抽样_样本A明细.csv'), low_memory=False)
sa['编号'] = sa.index + 1
uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                               '筛选语料_唯一记录_2556.csv'), low_memory=False)
uni['_nt'] = uni['Title'].map(nt)
meta = uni.set_index('_nt')[['Item Type', 'Publication Title', 'Date', 'Abstract']].to_dict('index')
for n in (152, 104, 153):
    r = sa[sa['编号'] == n].iloc[0]
    m = meta.get(r['_nt'], {})
    print('编号 %s ｜ 原因: %s' % (n, r['排除原因']))
    print('题名:', r['Title'])
    print('期刊:', m.get('Publication Title'), '｜日期:', m.get('Date'))
    print('摘要:', str(m.get('Abstract'))[:1200])
    print()

# ---------- 4. 原因标签整体审计 ----------
print('=' * 96)
rz = pd.read_csv(os.path.join(ANA, 'prisma_pass', 'reason_parsed.csv'), low_memory=False).drop_duplicates('_nt')
rz['_nt2'] = rz['Title'].map(nt)
it = dict(zip(uni['_nt'], uni['Item Type']))
rz['Item Type'] = rz['_nt'].map(it)
LBL = {1: 'Outside the scope of dentistry',
       2: 'Not an original research report',
       3: 'No non-dental 3D software identified',
       4: 'Outside the prespecified date window',
       5: 'Other / not classifiable'}
rz['原因'] = rz['原因代码'].map(LBL)
print('原因 × Item Type 交叉表（全部 1,943 条）：')
print(pd.crosstab(rz['原因'], rz['Item Type']).to_string())
