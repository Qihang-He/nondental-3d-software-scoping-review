# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_final_adjudicate2.py —— 对补裁决的 855 条运行与 _final_adjudicate.py 完全相同的判定"""
import os
import sys
import re
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import _final_adjudicate as FA

ANA = _os.path.join(_ROOTP, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
out = os.path.join(ANA, 'final_pass')
cand = pd.read_pickle(os.path.join(out, 'candidates_todo.pkl'))
parsed_fp = os.path.join(out, 'final_parsed.csv')
raw_fp = os.path.join(out, 'final_raw2.jsonl')
print('待补裁决 %d 条' % len(cand))

lock, buf = threading.Lock(), []


def flush():
    with lock:
        if not buf:
            return
        new = pd.DataFrame(buf)
        if os.path.exists(parsed_fp):
            new = pd.concat([pd.read_csv(parsed_fp, low_memory=False), new],
                            ignore_index=True)
        new.to_csv(parsed_fp, index=False, encoding='utf-8-sig')
        buf.clear()


def g(c, t):
    m = re.search(r'【%s】\s*[:：]\s*(.*)' % t, c or '')
    return m.group(1).strip() if m else ''


def work(row):
    user = ('【题名】%s\n\n【期刊】%s\n\n【摘要】\n%s\n\n【方法学证据片段】\n%s'
            % (row['Title'], row['期刊'], str(row['摘要'])[:1200],
               str(row['证据片段'])[:6000]))
    c = FA.call(user, 'final2|%s' % str(row['_nt'])[:36], raw_fp)
    buf.append({'_nt': row['_nt'], 'Title': row['Title'], '期刊': row['期刊'],
                'Item Type': row['Item Type'], 'Key': row['Key'],
                'PassA': row.get('PassA', ''), 'PassB': row.get('PassB', ''),
                '判定': g(c, '判定').upper(), '证据': g(c, '证据')[:500],
                '软件': g(c, '软件'), '专科': g(c, '专科'),
                '应用场景': g(c, '应用场景'), '研究设计': g(c, '研究设计'),
                '原始返回': c})
    if len(buf) >= 20:
        flush()


n = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = [ex.submit(work, r) for _, r in cand.iterrows()]
    for _ in as_completed(futs):
        n += 1
        if n % 50 == 0:
            flush()
            print('   %d / %d' % (n, len(cand)), flush=True)
flush()

allr = pd.read_csv(parsed_fp, low_memory=False)
print('\n全部已裁决：%d 条' % len(allr))
print(allr['判定'].value_counts().to_string())
inc = allr[allr['判定'].str.upper().str.startswith('INCLUDE')]
inc.to_csv(_os.path.join(_ROOTP, _os.path.join(_ROOTP, '03_数据'), '08_分析用', '最终新增纳入.csv'), index=False,
           encoding='utf-8-sig')
print('\n最终 INCLUDE %d 条' % len(inc))
