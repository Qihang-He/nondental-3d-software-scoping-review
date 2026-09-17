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
_tools_prisma_corpus.py
重建可复现的 PRISMA 语料定义：
  2,572（Zotero 去重后） -> 按归一化标题去重 -> 唯一记录集（预期 2,556）
校验：最终纳入 566 是否全部落在该唯一集内；613 是否全部落在其内。
输出：03_数据/02_清洗后/筛选语料_唯一记录_2556.csv
      03_数据/08_分析用/PRISMA_语料定义校验.json
"""
import os
import re
import json
import unicodedata
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


full = pd.read_csv(ROOT + r'\03_数据\01_原始\完整文献信息.csv', encoding='gbk',
                   low_memory=False)
full['_nt'] = full['Title'].map(nt)
uniq = full.drop_duplicates('_nt', keep='first').copy()
print('2572 -> 唯一标题 %d（移除组内重复 %d 行）' % (len(uniq), len(full) - len(uniq)))

v3 = pd.read_csv(ANA + r'\分析数据集_final_v3.csv', low_memory=False)
f613 = pd.read_excel(ROOT + r'\03_数据\04_最终表\最终表.xlsx')
tc = [x for x in f613.columns if 'Title' in str(x) or '标题' in str(x)][0]
v3['_nt'] = v3['Title'].map(nt)
f613['_nt'] = f613[tc].map(nt)

U = set(uniq['_nt'])
in_u_566 = v3['_nt'].isin(U).sum()
in_u_613 = f613['_nt'].isin(U).sum()
print('最终 566 中落在唯一集的比例: %d/%d' % (in_u_566, len(v3)))
print('613 中落在唯一集的比例: %d/%d' % (in_u_613, len(f613)))

missing566 = v3.loc[~v3['_nt'].isin(U), 'Title'].tolist()
if missing566:
    print('\n566 中仍不在唯一集的标题：')
    for t in missing566[:20]:
        print('   -', str(t)[:100])

uniq.to_csv(ROOT + r'\03_数据\02_清洗后\筛选语料_唯一记录_2556.csv',
            index=False, encoding='utf-8-sig')
json.dump({'records_after_zotero_dedup': int(len(full)),
           'records_after_title_dedup': int(len(uniq)),
           'duplicate_rows_removed': int(len(full) - len(uniq)),
           'final_566_within_universe': int(in_u_566),
           'preaudit_613_within_universe': int(in_u_613)},
          open(os.path.join(ANA, 'PRISMA_语料定义校验.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
