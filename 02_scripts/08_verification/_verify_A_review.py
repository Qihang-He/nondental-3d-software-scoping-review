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
_verify_A_review.py —— 对作者核验表中被质疑的 A 表条目做独立复核
输出：每条记录的 Item Type / 期刊 / 年份 / 原因 / 完整摘要 / 是否有 PDF / PDF 中是否出现软件名
"""
import os
import re
import json
import unicodedata
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')

FLAG = [104, 153, 157, 23, 33, 117, 137, 55, 119, 107, 160, 152]


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


# 样本 A 明细（脚本生成，按顺序即工作簿编号）
sa = pd.read_csv(os.path.join(ANA, '核验抽样_样本A明细.csv'), low_memory=False)
sa = sa.reset_index(drop=True)
sa['编号'] = sa.index + 1

uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                               '筛选语料_唯一记录_2556.csv'), low_memory=False)
uni['_nt'] = uni['Title'].map(nt)

pm = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '07_PDF与语料对照', 'pdf_match.csv'),
                 low_memory=False)
key2file = {}
for _, r in pm.iterrows():
    k = str(r.get('Key', '')).strip()
    if k and k != 'nan' and k not in key2file:
        key2file[k] = str(r['file'])

meta = uni.set_index('_nt')[['Item Type', 'Publication Title', 'Date', 'Publication Year',
                             'DOI', 'Abstract', 'Key']].to_dict('index')

for n in FLAG:
    row = sa[sa['编号'] == n]
    if not len(row):
        print('!! 编号 %s 不在样本 A 中' % n)
        continue
    row = row.iloc[0]
    m = meta.get(row['_nt'], {})
    print('=' * 100)
    print('编号 %s ｜ 流程原因: %s' % (n, row['排除原因']))
    print('题名:', row['Title'])
    print('Item Type:', m.get('Item Type'), '｜ 期刊:', m.get('Publication Title'),
          '｜ 日期:', m.get('Date'), '｜ DOI:', m.get('DOI'))
    k = str(m.get('Key', '')).strip()
    f = key2file.get(k)
    print('PDF:', f if f else '（无）')
    ab = m.get('Abstract')
    print('摘要:')
    print((str(ab) if ab is not None else '（无摘要）')[:1800])
    print()
