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
_tools_rq3_extract.py
系统化提取纳入研究报告的"优势 / 挑战 / 缺口"（回应审稿人 R3-6：RQ3 必须由纳入研究回答）

方法：对 566 篇纳入研究的标题+摘要，用固定分类法做**多选**编码；
      分类法预设、编码规则固定、逐条保存原始返回；可脚本复现。
输出：03_数据/08_分析用/rq3_pass/rq3_parsed.csv 、rq3_raw.jsonl
      03_数据/08_分析用/RQ3_频次汇总.json
"""
import os
import re
import json
import time
import argparse
from datetime import datetime
from collections import Counter
import pandas as pd
import requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
OUT = os.path.join(ANA, 'rq3_pass')
os.makedirs(OUT, exist_ok=True)

MODEL = 'deepseek-chat'
TEMPERATURE = 0.1
MAX_TOKENS = 300
API_URL = 'https://api.deepseek.com/v1/chat/completions'

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

SYSTEM = """你是循证综述的数据提取助手。请阅读给出的口腔医学研究摘要，提取其中**明确报告**的三类信息，并只从下列预设代码中选择。

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


def load_key():
    with open(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'config.local.json'), encoding='utf-8') as f:
        return json.load(f)['deepseek_api_key'].strip()


def grab(c, tag):
    m = re.search(r'【%s】\s*[:：]\s*(.*)' % tag, c or '')
    if not m:
        return []
    return [x.strip().upper() for x in re.split(r'[,，;；\s]+', m.group(1)) if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--interval', type=float, default=0.4)
    args = ap.parse_args()

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + load_key()}
    d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
    uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                   '筛选语料_唯一记录_2556.csv'), low_memory=False)

    def nt(s):
        s = re.sub(r'<[^>]+>', ' ', str(s))
        s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
        return re.sub(r'\s+', ' ', s)

    uni['_nt'] = uni['Title'].map(nt)
    d['_nt'] = d['Title'].map(nt)
    abscol = 'Abstract' if 'Abstract' in uni.columns else 'Abstract Note'
    ab = dict(zip(uni['_nt'], uni[abscol]))
    d['_abs'] = d['_nt'].map(ab)

    raw_fp = os.path.join(OUT, 'rq3_raw.jsonl')
    parsed_fp = os.path.join(OUT, 'rq3_parsed.csv')
    done = set()
    if os.path.exists(parsed_fp):
        done = set(pd.read_csv(parsed_fp, low_memory=False)['序号'].astype(str))

    rows, n = [], 0
    for _, r in d.iterrows():
        if str(r['序号']) in done:
            continue
        if args.limit and n >= args.limit:
            break
        user = '【标题】\n%s\n\n【摘要】\n%s' % (r['Title'], r['_abs'] or '（无摘要）')
        payload = {'model': MODEL,
                   'messages': [{'role': 'system', 'content': SYSTEM},
                                {'role': 'user', 'content': user}],
                   'temperature': TEMPERATURE, 'max_tokens': MAX_TOKENS, 'stream': False}
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=90)
            j = resp.json()
            c = j['choices'][0]['message']['content']
            with open(raw_fp, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'tag': 'rq3|%s' % r['序号'],
                                    'request_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'model_returned': j.get('model'),
                                    'response_id': j.get('id'),
                                    'content': c}, ensure_ascii=False) + '\n')
            rows.append({'序号': r['序号'], 'Key': r.get('Key'), 'Title': r['Title'],
                         '优势': ','.join(grab(c, '优势')), '挑战': ','.join(grab(c, '挑战')),
                         '缺口': ','.join(grab(c, '缺口')), '原始返回': c})
        except Exception as e:
            rows.append({'序号': r['序号'], 'Key': r.get('Key'), 'Title': r['Title'],
                         '优势': '', '挑战': '', '缺口': '', '原始返回': 'ERROR: %s' % e})
        n += 1
        time.sleep(args.interval)
        if n % 50 == 0:
            print('   进度 %d' % n, flush=True)

    new = pd.DataFrame(rows)
    old = pd.read_csv(parsed_fp, low_memory=False) if os.path.exists(parsed_fp) else None
    allr = pd.concat([old, new], ignore_index=True) if old is not None else new
    allr.to_csv(parsed_fp, index=False, encoding='utf-8-sig')

    # 频次汇总
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
                      'pct': round(n2 / len(allr) * 100, 1)}
                     for k, n2 in c.most_common()]
    full['n_studies'] = int(len(allr))
    json.dump(full, open(os.path.join(ANA, 'RQ3_频次汇总.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print(json.dumps(full, ensure_ascii=False, indent=2)[:3000])


if __name__ == '__main__':
    main()
