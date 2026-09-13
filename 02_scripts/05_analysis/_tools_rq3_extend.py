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
_tools_rq3_extend.py —— 对新增纳入记录做与既有 566 篇完全相同的 RQ3 编码（优势/挑战/缺口）
沿用 _tools_parallel_pass.py 中同一套代码本与提示词，保证口径一致。
输出：03_数据/08_分析用/rq3_pass/rq3_parsed.csv（追加）
"""
import os
import sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '00_lib'))
import _tools_parallel_pass as P   # 复用同一提示词与解析函数

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')

add = pd.read_pickle(os.path.join(ANA, '_add_v4.pkl'))
corpus = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                  '筛选语料_唯一记录_2556.csv'), low_memory=False)
corpus['_nt'] = corpus['Title'].map(P.nt)
ab = dict(zip(corpus['_nt'], corpus['Abstract']))
add['_abs'] = add['_nt'].map(ab)
add = add[add['_abs'].notna()]
print('待编码新增记录：%d 条' % len(add))

out = os.path.join(ANA, 'rq3_pass')
os.makedirs(out, exist_ok=True)
parsed_fp = os.path.join(out, 'rq3_parsed.csv')
raw_fp = os.path.join(out, 'rq3_raw.jsonl')
old = pd.read_csv(parsed_fp, low_memory=False) if os.path.exists(parsed_fp) else None
start = len(old) if old is not None else 0

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
lock = threading.RLock()      # 可重入：flush() 在持锁时会被再次调用
buf, rows = [], []


def flush():
    with lock:
        if not buf:
            return
        new = pd.DataFrame(buf)
        base = pd.read_csv(parsed_fp, low_memory=False) if os.path.exists(parsed_fp) else None
        allr = pd.concat([base, new], ignore_index=True) if base is not None else new
        allr.to_csv(parsed_fp, index=False, encoding='utf-8-sig')
        buf.clear()


n = 0


def work(i, row):
    global n
    user = '【标题】\n%s\n\n【摘要】\n%s' % (row['Title'], row['_abs'])
    c = P.call(P.RQ3_SYSTEM, user, 'rq3add|%d' % (start + i), raw_fp)
    buf.append({'序号': start + i, 'Key': row.get('Key'), 'Title': row['Title'],
                '优势': ','.join(P.grab(c, '优势')), '挑战': ','.join(P.grab(c, '挑战')),
                '缺口': ','.join(P.grab(c, '缺口')), '原始返回': c})
    with lock:
        n += 1
    if n % 25 == 0:
        flush()
        print('   %d / %d' % (n, len(add)), flush=True)


with ThreadPoolExecutor(max_workers=8) as ex:
    futs = [ex.submit(work, i, r) for i, (_, r) in enumerate(add.iterrows())]
    for _ in as_completed(futs):
        pass
flush()
print('完成。rq3_parsed.csv 现共 %d 行'
      % len(pd.read_csv(parsed_fp, low_memory=False)))
