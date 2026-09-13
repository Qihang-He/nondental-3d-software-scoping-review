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
_tools_prisma_reason_pass.py
为"筛查阶段未进入全文评估"的记录（约 1,927 条）分配**预设的单一排除原因**，
以便按审稿人 R3-12 的要求在 PRISMA 图中按原因报告排除数。

- 不改动任何纳入决定，仅对"未纳入"记录附加原因标签（纯增量）
- 规则阶段：先用确定性规则从**已归档的原始 AI 初筛理由文本**归类
- 模型阶段：规则无法归类的记录，用同模型同参数做一次强制单选，逐条保存原始返回
输出：03_数据/08_分析用/PRISMA_排除原因_pass1.csv 、
      03_数据/08_分析用/PRISMA_原因_原始日志.jsonl
"""
import os
import re
import json
import time
import hashlib
import unicodedata
from datetime import datetime
import pandas as pd
import requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
CORPUS = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后', '筛选语料_去重后.csv')
FINAL613 = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '04_最终表', '最终表.xlsx')

MODEL = 'deepseek-chat'
TEMPERATURE = 0.1
MAX_TOKENS = 300
API_URL = 'https://api.deepseek.com/v1/chat/completions'

SYSTEM = """你是系统综述的文献筛选核对助手。

下面给出的是某条文献记录。该记录在标题/摘要筛选阶段**未被纳入**一项关于"非牙科专用3D软件在口腔医学中的应用"的范围综述。

请判断该记录**未被纳入的最主要单一原因**，并输出原因代码（只能选一个）：

1 = 不属于口腔医学范畴（研究内容与口腔医学无关）
2 = 文献类型不符（综述、系统综述、社论、评论、会议摘要、信件、研究方案、非原创研究等）
3 = 未使用非牙科专用3D软件（仅使用牙科专用软件，或摘要未提及任何非牙科3D软件）
4 = 不在预设时间窗内（发表于 2020-07-01 至 2026-06-30 之外）
5 = 其他（无法归入以上任一类）

输出格式（只输出一行，不要任何额外文字）：
【原因代码】: <1-5 中的一个数字>
"""


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


def load_key():
    with open(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'config.local.json'), encoding='utf-8') as f:
        return json.load(f)['deepseek_api_key'].strip()


def build_screen_set():
    c = pd.read_csv(CORPUS, low_memory=False)
    f = pd.read_excel(FINAL613)
    tc = [x for x in f.columns if 'Title' in str(x) or '标题' in str(x)][0]
    c['_nt'] = c['Title'].map(nt)
    f['_nt'] = f[tc].map(nt)
    s613 = set(f['_nt'])
    c['_in613'] = c['_nt'].isin(s613)
    if 'DOI' in f.columns and 'DOI' in c.columns:
        d613 = {str(x).strip().lower() for x in f['DOI'].dropna()
                if str(x).strip() and str(x).strip().lower() != 'nan'}
        c['_in613'] = c['_in613'] | c['DOI'].astype(str).str.strip().str.lower().isin(d613)
    un = f.loc[~f['_nt'].isin(set(c.loc[c['_in613'], '_nt'])), '_nt']
    print('613 中未匹配到语料的条目:', len(un))
    for u in un:
        print('   UNMATCHED:', u[:90])
    return c, c[~c['_in613']].copy()


def main():
    c, out = build_screen_set()
    print('语料 %d ；进入资格评估 %d ；筛查阶段未进入 %d' % (len(c), int(c['_in613'].sum()), len(out)))

    ai = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '03_AI初筛原始', '完整文献信息_AI筛选结果.csv'))
    ai['_nt'] = ai['文献标题'].map(nt)
    rmap = dict(zip(ai['_nt'], ai['AI分类理由']))
    out['原AI理由'] = out['_nt'].map(rmap)

    out[['_nt', 'Key', 'Title', 'Abstract Note', '原AI理由']].to_csv(
        os.path.join(ANA, 'PRISMA_未进入全文评估_1927.csv'), index=False, encoding='utf-8-sig')
    print('[saved] PRISMA_未进入全文评估_1927.csv')

    os.makedirs(os.path.join(ANA, 'prisma_pass'), exist_ok=True)
    out.to_pickle(os.path.join(ANA, 'prisma_pass', '_screen_set.pkl'))


if __name__ == '__main__':
    main()
