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
_tools_parallel_pass.py —— 并发执行两类批量分类任务（可断点续跑，增量落盘）
  --task reason : 对"筛查阶段排除"的 1,943 条记录做单一排除原因归类（PRISMA 用）
  --task rq3    : 对 566 条纳入记录做优势/挑战/缺口多选编码（RQ3 用）
输出目录：03_数据/08_分析用/prisma_pass/ 与 03_数据/08_分析用/rq3_pass/
"""
import os
import re
import json
import time
import argparse
import threading
from datetime import datetime
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
MODEL = 'deepseek-chat'
TEMPERATURE = 0.1
API_URL = 'https://api.deepseek.com/v1/chat/completions'
LOCK = threading.RLock()

# ---------------- 提示词 ----------------
REASON_SYSTEM = """你是系统综述的筛选核对助手。

下面给出某条文献的标题与摘要。该记录在**标题/摘要筛选阶段未被纳入**一项关于
"非牙科专用3D软件在口腔医学中的应用"的范围综述。

请判断其**未被纳入的最主要单一原因**，只输出一个原因代码：

1 = 不属于口腔医学范畴
2 = 文献类型不符（综述、社论、评论、会议摘要、信件、研究方案、非原创研究等）
3 = 未使用非牙科专用3D软件（仅使用牙科专用软件，或未提及任何非牙科3D软件）
4 = 不在预设时间窗内（发表时间在 2020-07-01 至 2026-06-30 之外）
5 = 其他

输出格式（只输出一行）：
【原因代码】: <1-5 中的一个数字>
"""

RQ3_SYSTEM = """你是循证综述的数据提取助手。请阅读给出的口腔医学研究摘要，提取其中**明确报告**的三类信息，并只从下列预设代码中选择。

【优势 A】(可多选，用逗号分隔；未报告则填 A9)
A1 更大几何自由度/可定制性
A2 牙科专用平台不具备的分析功能
A3 成本节约/免费或开源
A4 更好的互操作性或数据交换
A5 自动化与效率提升
A6 精度或测量准确性提升
A9 未明确报告优势

【挑战 C】(可多选；未报告则填 C9)
C1 学习曲线陡峭/需要培训
C2 文件格式或互操作问题
C3 许可费用或获取限制
C4 验证证据有限
C5 流程耗时
C6 软件不稳定/报错
C7 硬件或算力要求高
C8 监管、审批或法律不确定性
C9 未明确报告挑战

【缺口 G】(可多选；未报告则填 G9)
G1 需要临床验证
G2 需要自动化或人工智能整合
G3 需要标准化与报告规范
G4 需要更大样本或多中心研究
G9 未明确报告缺口

只输出三行，不要任何其他文字：
【优势】: <代码>
【挑战】: <代码>
【缺口】: <代码>
"""


def nt(s):
    s = re.sub(r'<[^>]+>', ' ', str(s))
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


def load_key():
    with open(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'config.local.json'), encoding='utf-8') as f:
        return json.load(f)['deepseek_api_key'].strip()


HEADERS = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + load_key()}


def call(system, user, tag, raw_fp, max_tokens=300, retries=3):
    payload = {'model': MODEL, 'messages': [{'role': 'system', 'content': system},
                                            {'role': 'user', 'content': user}],
               'temperature': TEMPERATURE, 'max_tokens': max_tokens, 'stream': False}
    for attempt in range(retries):
        t0 = time.time()
        try:
            r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=120)
            j = r.json()
            c = j['choices'][0]['message']['content']
            with LOCK:
                with open(raw_fp, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({'tag': tag, 'model_returned': j.get('model'),
                                        'response_id': j.get('id'),
                                        'request_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        'latency_s': round(time.time() - t0, 2),
                                        'content': c}, ensure_ascii=False) + '\n')
            return c
        except Exception as e:
            if attempt == retries - 1:
                with LOCK:
                    with open(raw_fp, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({'tag': tag, 'error': str(e)},
                                           ensure_ascii=False) + '\n')
                return None
            time.sleep(2 + attempt * 3)


def parse_reason(c):
    m = re.search(r'【原因代码】\s*[:：]\s*([1-5])', c or '')
    return int(m.group(1)) if m else None


def grab(c, tag):
    m = re.search(r'【%s】\s*[:：]\s*(.*)' % tag, c or '')
    if not m:
        return []
    return [x.strip().upper() for x in re.split(r'[,，;；\s]+', m.group(1)) if x.strip()]


# ================= task: reason =================
def run_reason(workers):
    out = os.path.join(ANA, 'prisma_pass')
    os.makedirs(out, exist_ok=True)
    corpus = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                      '筛选语料_唯一记录_2556.csv'), low_memory=False)
    f613 = pd.read_excel(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '04_最终表', '最终表.xlsx'))
    tc = [x for x in f613.columns if 'Title' in str(x) or '标题' in str(x)][0]
    corpus['_nt'] = corpus['Title'].map(nt)
    f613['_nt'] = f613[tc].map(nt)
    in613 = set(f613['_nt'])
    ex = corpus[~corpus['_nt'].isin(in613)].copy()
    abs_col = 'Abstract' if 'Abstract' in ex.columns else 'Abstract Note'
    print('[reason] 目标 %d 条' % len(ex), flush=True)

    parsed_fp = os.path.join(out, 'reason_parsed.csv')
    raw_fp = os.path.join(out, 'reason_raw.jsonl')
    done = set()
    if os.path.exists(parsed_fp):
        done = set(pd.read_csv(parsed_fp, low_memory=False)['_nt'].astype(str))
    todo = ex[~ex['_nt'].astype(str).isin(done)]
    print('[reason] 已完成 %d，待处理 %d' % (len(done), len(todo)), flush=True)

    buf = []
    parsed_lock = threading.Lock()

    def flush():
        with parsed_lock:
            if not buf:
                return
            new = pd.DataFrame(buf)
            if os.path.exists(parsed_fp):
                old = pd.read_csv(parsed_fp, low_memory=False)
                new = pd.concat([old, new], ignore_index=True)
            new.to_csv(parsed_fp, index=False, encoding='utf-8-sig')
            buf.clear()

    def work(row):
        user = '【标题】\n%s\n\n【摘要】\n%s' % (row['Title'], row.get(abs_col) or '（无摘要）')
        c = call(REASON_SYSTEM, user, 'reason|%s' % str(row['_nt'])[:40], raw_fp)
        rec = {'_nt': row['_nt'], 'Key': row.get('Key'), 'Title': row['Title'],
               '原因代码': parse_reason(c), '原始返回': c}
        buf.append(rec)
        if len(buf) >= 25:
            flush()

    n = 0
    with ThreadPoolExecutor(max_workers=workers) as ex_:
        futs = [ex_.submit(work, r) for _, r in todo.iterrows()]
        for _ in as_completed(futs):
            n += 1
            if n % 100 == 0:
                flush()
                print('   [reason] %d / %d' % (n, len(todo)), flush=True)
    flush()
    print('[reason] 完成', flush=True)


# ================= task: rq3 =================
def run_rq3(workers):
    out = os.path.join(ANA, 'rq3_pass')
    os.makedirs(out, exist_ok=True)
    d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
    uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                   '筛选语料_唯一记录_2556.csv'), low_memory=False)
    uni['_nt'] = uni['Title'].map(nt)
    d['_nt'] = d['Title'].map(nt)
    ac = 'Abstract' if 'Abstract' in uni.columns else 'Abstract Note'
    ab = dict(zip(uni['_nt'], uni[ac]))
    d['_abs'] = d['_nt'].map(ab)
    print('[rq3] 目标 %d 条' % len(d), flush=True)

    parsed_fp = os.path.join(out, 'rq3_parsed.csv')
    raw_fp = os.path.join(out, 'rq3_raw.jsonl')
    done = set()
    if os.path.exists(parsed_fp):
        done = set(pd.read_csv(parsed_fp, low_memory=False)['序号'].astype(str))
    todo = d[~d['序号'].astype(str).isin(done)]
    print('[rq3] 已完成 %d，待处理 %d' % (len(done), len(todo)), flush=True)

    buf = []
    parsed_lock = threading.Lock()

    def flush():
        with parsed_lock:
            if not buf:
                return
            new = pd.DataFrame(buf)
            if os.path.exists(parsed_fp):
                old = pd.read_csv(parsed_fp, low_memory=False)
                new = pd.concat([old, new], ignore_index=True)
            new.to_csv(parsed_fp, index=False, encoding='utf-8-sig')
            buf.clear()

    def work(row):
        user = '【标题】\n%s\n\n【摘要】\n%s' % (row['Title'], row['_abs'] or '（无摘要）')
        c = call(RQ3_SYSTEM, user, 'rq3|%s' % row['序号'], raw_fp)
        buf.append({'序号': row['序号'], 'Key': row.get('Key'), 'Title': row['Title'],
                    '优势': ','.join(grab(c, '优势')), '挑战': ','.join(grab(c, '挑战')),
                    '缺口': ','.join(grab(c, '缺口')), '原始返回': c})
        if len(buf) >= 25:
            flush()

    n = 0
    with ThreadPoolExecutor(max_workers=workers) as ex_:
        futs = [ex_.submit(work, r) for _, r in todo.iterrows()]
        for _ in as_completed(futs):
            n += 1
            if n % 100 == 0:
                flush()
                print('   [rq3] %d / %d' % (n, len(todo)), flush=True)
    flush()
    print('[rq3] 完成', flush=True)


def summarize_rq3():
    fp = os.path.join(ANA, 'rq3_pass', 'rq3_parsed.csv')
    if not os.path.exists(fp):
        return
    allr = pd.read_csv(fp, low_memory=False)
    ADV = {'A1': 'Greater geometric freedom / customisation',
           'A2': 'Analysis functions unavailable in dental platforms',
           'A3': 'Cost savings / free or open-source access',
           'A4': 'Improved interoperability or data exchange',
           'A5': 'Automation and time efficiency',
           'A6': 'Improved accuracy or measurement precision',
           'A9': 'No advantage explicitly reported'}
    CHA = {'C1': 'Steep learning curve / training requirement',
           'C2': 'File-format or interoperability problems',
           'C3': 'Licence cost or access restrictions',
           'C4': 'Limited validation evidence',
           'C5': 'Time-consuming workflow',
           'C6': 'Software instability, bugs or errors',
           'C7': 'High hardware or computational demand',
           'C8': 'Regulatory, approval or medico-legal uncertainty',
           'C9': 'No challenge explicitly reported'}
    GAP = {'G1': 'Need for clinical validation',
           'G2': 'Need for automation or AI integration',
           'G3': 'Need for standardisation and reporting guidance',
           'G4': 'Need for larger or multi-centre samples',
           'G9': 'No gap explicitly reported'}
    full = {}
    for col, codes, key in [('优势', ADV, 'advantages'), ('挑战', CHA, 'challenges'),
                            ('缺口', GAP, 'gaps')]:
        c = Counter()
        for v in allr[col].dropna():
            for x in str(v).split(','):
                x = x.strip().upper()
                if x:
                    c[x] += 1
        full[key] = [{'code': k, 'label': codes.get(k, k), 'n': int(n2),
                      'pct': round(n2 / len(allr) * 100, 1)} for k, n2 in c.most_common()]
    full['n_studies'] = int(len(allr))
    json.dump(full, open(os.path.join(ANA, 'RQ3_频次汇总.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print(json.dumps(full, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--task', choices=['reason', 'rq3', 'summarize'], required=True)
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    if a.task == 'reason':
        run_reason(a.workers)
    elif a.task == 'rq3':
        run_rq3(a.workers)
    else:
        summarize_rq3()
