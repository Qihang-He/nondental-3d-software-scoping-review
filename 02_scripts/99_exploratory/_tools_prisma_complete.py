# -*- coding: utf-8 -*-
"""
_tools_prisma_complete.py
1) 在规范语料（2,556 条唯一记录）上核对 AI 三轮复筛覆盖度；
   未覆盖记录用**完全相同的提示词/参数**补跑三轮，逐条保存原始返回。
2) 对"筛查阶段排除"的记录（2,556 - 613 = 1,943 条）执行**排除原因单选**归类，
   逐条保存原始返回，用于 PRISMA 按原因报告排除数（回应 R3-12）。
输出目录：03_数据/08_分析用/prisma_pass/
"""
import os
import re
import json
import time
import hashlib
import argparse
from datetime import datetime
import pandas as pd
import requests

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
OUT = os.path.join(ANA, 'prisma_pass')
os.makedirs(OUT, exist_ok=True)

MODEL = 'deepseek-chat'
TEMPERATURE = 0.1
MAX_TOKENS = 500
API_URL = 'https://api.deepseek.com/v1/chat/completions'

SCREEN_SYSTEM = open(os.path.join(ROOT, '07_AI重跑原始记录', 'system_prompt.txt'),
                     encoding='utf-8').read()

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


def nt(s):
    s = re.sub(r'<[^>]+>', ' ', str(s))
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


def load_key():
    with open(os.path.join(ROOT, '07_AI重跑原始记录', 'config.local.json'), encoding='utf-8') as f:
        return json.load(f)['deepseek_api_key'].strip()


def call(headers, system, user, tag, raw_fp):
    payload = {'model': MODEL,
               'messages': [{'role': 'system', 'content': system},
                            {'role': 'user', 'content': user}],
               'temperature': TEMPERATURE, 'max_tokens': MAX_TOKENS, 'stream': False}
    t0 = time.time()
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        j = r.json()
        content = j['choices'][0]['message']['content']
        rec = {'tag': tag, 'request_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
               'model_returned': j.get('model'), 'response_id': j.get('id'),
               'latency_s': round(time.time() - t0, 2), 'content': content}
        with open(raw_fp, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        return content, j.get('model')
    except Exception as e:
        with open(raw_fp, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'tag': tag, 'error': str(e)}, ensure_ascii=False) + '\n')
        return None, None


def parse_screen(c):
    def g(t):
        m = re.search(r'【%s】\s*[:：]\s*(.*)' % t, c or '')
        return m.group(1).strip() if m else ''
    return g('分类结果')


def parse_reason(c):
    m = re.search(r'【原因代码】\s*[:：]\s*([1-5])', c or '')
    return int(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--task', choices=['cover', 'reason', 'all'], default='all')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--interval', type=float, default=0.5)
    args = ap.parse_args()

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + load_key()}

    corpus = pd.read_csv(os.path.join(ROOT, '03_数据', '02_清洗后',
                                      '筛选语料_唯一记录_2556.csv'), low_memory=False)
    corpus['_nt'] = corpus['Title'].map(nt)
    f613 = pd.read_excel(os.path.join(ROOT, '03_数据', '04_最终表', '最终表.xlsx'))
    tc = [x for x in f613.columns if 'Title' in str(x) or '标题' in str(x)][0]
    f613['_nt'] = f613[tc].map(nt)
    in613 = set(f613['_nt'])

    # ---------- 任务 A：补齐三轮复筛覆盖 ----------
    if args.task in ('cover', 'all'):
        run_fps = {i: os.path.join(ROOT, '07_AI重跑原始记录', 'run%d' % i,
                                   'classification_parsed.csv') for i in (1, 2, 3)}
        have = set()
        for i, fp in run_fps.items():
            t = pd.read_csv(fp, low_memory=False)
            t['_nt'] = t['文献标题'].map(nt)
            have |= set(t['_nt'])
        todo = corpus[~corpus['_nt'].isin(have)]
        print('[覆盖] 语料 %d ；已有三轮结果 %d ；待补 %d'
              % (len(corpus), len(corpus) - len(todo), len(todo)))
        raw_fp = os.path.join(OUT, 'run_extra_raw.jsonl')
        parsed_fp = os.path.join(OUT, 'run_extra_parsed.csv')
        done = set()
        if os.path.exists(parsed_fp):
            done = set(pd.read_csv(parsed_fp, low_memory=False)['_nt'])
        rows = []
        n = 0
        for _, r in todo.iterrows():
            if args.limit and n >= args.limit:
                break
            for run in (1, 2, 3):
                key = r['_nt']
                if (key, run) in done:
                    continue
                user = '【标题】\n%s\n\n【摘要】\n%s\n\n请根据系统指令中的纳入排除标准，对这篇文献进行分类。' \
                       % (r.get('Title', ''), r.get('Abstract Note', ''))
                c, _ = call(headers, SCREEN_SYSTEM, user, 'cover|run%d|%s' % (run, key[:40]), raw_fp)
                rows.append({'_nt': key, 'run': run, '分类结果': parse_screen(c),
                             '原始返回': c})
                time.sleep(args.interval)
            n += 1
        if rows:
            pd.DataFrame(rows).to_csv(parsed_fp, index=False, encoding='utf-8-sig')
            print('[覆盖] 补跑完成 %d 条记录（%d 次调用）' % (n, len(rows)))

    # ---------- 任务 B：排除原因单选 ----------
    if args.task in ('reason', 'all'):
        ex = corpus[~corpus['_nt'].isin(in613)].copy()
        print('[原因] 筛查阶段排除 %d 条（2,556 - 613 = %d）' % (len(ex), len(corpus) - 613))
        raw_fp = os.path.join(OUT, 'reason_raw.jsonl')
        parsed_fp = os.path.join(OUT, 'reason_parsed.csv')
        done = set()
        if os.path.exists(parsed_fp):
            d = pd.read_csv(parsed_fp, low_memory=False)
            done = set(d['_nt'])
        rows = []
        n = 0
        for _, r in ex.iterrows():
            if r['_nt'] in done:
                continue
            if args.limit and n >= args.limit:
                break
            user = '【标题】\n%s\n\n【摘要】\n%s' % (r.get('Title', ''),
                                                    r.get('Abstract Note', ''))
            c, _ = call(headers, REASON_SYSTEM, user, 'reason|%s' % r['_nt'][:40], raw_fp)
            rows.append({'_nt': r['_nt'], 'Key': r.get('Key'), 'Title': r.get('Title'),
                         '原因代码': parse_reason(c), '原始返回': c})
            n += 1
            time.sleep(args.interval)
            if n % 100 == 0:
                pd.DataFrame(rows).to_csv(parsed_fp, index=False, encoding='utf-8-sig')
                print('   进度 %d / %d' % (n, len(ex) - len(done)), flush=True)
        if rows:
            old = pd.read_csv(parsed_fp, low_memory=False) if os.path.exists(parsed_fp) else None
            new = pd.DataFrame(rows)
            allr = pd.concat([old, new], ignore_index=True) if old is not None else new
            allr.to_csv(parsed_fp, index=False, encoding='utf-8-sig')
            print('[原因] 完成 %d 条' % len(allr))


if __name__ == '__main__':
    main()
