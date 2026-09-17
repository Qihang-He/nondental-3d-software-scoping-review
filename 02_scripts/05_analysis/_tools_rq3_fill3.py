# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_tools_rq3_fill3.py —— 用同一代码本补齐 RQ3 未覆盖的少量记录"""
import os
import sys
import threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '00_lib'))
import _tools_parallel_pass as P

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')

d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)
d['Key'] = d['Key'].astype(str)
corpus = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                  '筛选语料_唯一记录_2556.csv'), low_memory=False)
corpus['_nt'] = corpus['Title'].map(P.nt)
ab = dict(zip(corpus['_nt'], corpus['Abstract']))

parsed_fp = os.path.join(ANA, 'rq3_pass', 'rq3_parsed.csv')
raw_fp = os.path.join(ANA, 'rq3_pass', 'rq3_raw.jsonl')
old = pd.read_csv(parsed_fp, low_memory=False)
old['Key'] = old['Key'].astype(str)

todo = d[~d['Key'].isin(set(old['Key']))].copy()
todo['_nt'] = todo['Title'].map(P.nt)
todo['_abs'] = todo['_nt'].map(ab)
print('待补：%d 条；其中可获摘要：%d' % (len(todo), int(todo['_abs'].notna().sum())))
for _, r in todo.iterrows():
    print('   - %s | 摘要:%s | %s' % (r['Key'], 'Y' if pd.notna(r['_abs']) else 'N',
                                     str(r['Title'])[:66]))

todo = todo[todo['_abs'].notna()]
if len(todo) == 0:
    raise SystemExit('无待补记录')

lock = threading.RLock()
buf = []
start = len(old)


def work(i, row):
    user = '【标题】\n%s\n\n【摘要】\n%s' % (row['Title'], row['_abs'])
    c = P.call(P.RQ3_SYSTEM, user, 'rq3fill|%d' % (start + i), raw_fp)
    buf.append({'序号': start + i, 'Key': row['Key'], 'Title': row['Title'],
                '优势': ','.join(P.grab(c, '优势')), '挑战': ','.join(P.grab(c, '挑战')),
                '缺口': ','.join(P.grab(c, '缺口')), '原始返回': c})


with ThreadPoolExecutor(max_workers=4) as ex:
    futs = [ex.submit(work, i, r) for i, (_, r) in enumerate(todo.iterrows())]
    for f in as_completed(futs):
        pass

allr = pd.concat([old, pd.DataFrame(buf)], ignore_index=True)
allr.to_csv(parsed_fp, index=False, encoding='utf-8-sig')
print('完成，rq3_parsed.csv 现共 %d 行' % len(allr))
for b in buf:
    print('   %s  A=%s C=%s G=%s' % (b['Key'], b['优势'], b['挑战'], b['缺口']))
