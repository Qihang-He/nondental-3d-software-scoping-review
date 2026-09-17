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
_newly_eligible_triage.py
对"排除集全文命中软件名"的候选记录做逐条判定：这些记录**是否本应纳入**。

输入：03_数据/08_分析用/排除集全文软件命中.csv（由 _excluded_fulltext_screen.py 生成）
      每条附带 PDF 中软件名出现的上下文片段（±350 字符，最多 4 段）
判定代码：
  E1 合格——口腔医学主题 + 原创研究/技术说明/病例报告 + 本研究**自身**使用了命名的非牙科3D软件
  X1 软件名仅出现在参考文献或泛泛描述中，并非本研究自身所用工具
  X2 主题不属于口腔医学
  X3 文献类型不符（综述/社论/会议摘要等）
  X4 其他（无法判定）
输出：03_数据/08_分析用/漏排候选判定.csv + 汇总
"""
import os
import re
import json
import time
import argparse
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
PDF = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))
MODEL = 'deepseek-chat'
TEMPERATURE = 0.1
MAX_TOKENS = 200
API_URL = 'https://api.deepseek.com/v1/chat/completions'

SYSTEM = """你是系统综述的纳排复核助手。下面给出：一条此前被排除的文献记录、它的期刊、它的摘要，
以及在该文献**全文**中检索到的非牙科3D软件名及其上下文片段。

请判断该文献**是否本应纳入**下面这项范围综述。

【纳入标准】
1. 主题属于口腔医学任一学科（修复、种植、正畸、颌面外科、牙体牙髓、牙周、口腔颌面放射、法医口腔、口腔生物学、口腔教育、颞下颌关节、口腔睡眠医学、口腔医学/口腔病理等）。
2. 该研究**自身**明确使用了**非牙科专用3D软件**（其原始开发领域不在牙科，例如 Mimics、3D Slicer、ANSYS、ABAQUS、Geomagic 系列、Blender、Meshmixer、CloudCompare、MeshLab、SolidWorks、MATLAB、ITK-SNAP、HyperMesh、COMSOL、3-Matic 等）用于3D数据处理、分析或建模。
3. 文献类型为同行评审的原创研究、技术说明或病例报告（**排除**综述、系统综述、社论、评论、会议摘要、信件、研究方案）。
4. 英文，发表于 2020-07-01 至 2026-06-30。

【判定代码】只输出一个：
E1 = 本应纳入
X1 = 命中的软件名仅出现在参考文献列表或泛泛介绍中，并非本研究自身使用的工具
X2 = 主题不属于口腔医学
X3 = 文献类型不符（综述/社论/会议摘要等）
X4 = 信息不足，无法判定

只输出一行：
【判定】: <代码>
【理由】: <一句话，引用具体证据>
"""


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


def load_key():
    with open(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'config.local.json'),
              encoding='utf-8') as f:
        return json.load(f)['deepseek_api_key'].strip()


HEADERS = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + load_key()}


def call(user, tag, raw_fp, retries=3):
    payload = {'model': MODEL, 'messages': [{'role': 'system', 'content': SYSTEM},
                                            {'role': 'user', 'content': user}],
               'temperature': TEMPERATURE, 'max_tokens': MAX_TOKENS, 'stream': False}
    for a in range(retries):
        try:
            r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=120)
            j = r.json()
            c = j['choices'][0]['message']['content']
            with open(raw_fp, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'tag': tag, 'model_returned': j.get('model'),
                                    'content': c}, ensure_ascii=False) + '\n')
            return c
        except Exception as e:
            if a == retries - 1:
                return None
            time.sleep(2 + 3 * a)


def build_candidates():
    """重新生成候选并附带上下文片段"""
    src = pd.read_csv(os.path.join(ANA, '排除集全文软件命中.csv'), low_memory=False)
    uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                   '筛选语料_唯一记录_2556.csv'), low_memory=False)
    uni['_nt'] = uni['Title'].map(nt)
    ab = uni.set_index('_nt')['Abstract'].to_dict()
    import pymupdf
    sw = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'))
    names = sorted({str(v).strip() for c in ('规范名称', '原始名称')
                    for v in sw[c].dropna() if len(str(v).strip()) >= 5},
                   key=len, reverse=True)
    PAT = re.compile(r'(?<![A-Za-z])(?:' + '|'.join(re.escape(n) for n in names) +
                     r')(?![A-Za-z])', re.I)
    out = []
    for _, r in src.iterrows():
        fp = os.path.join(PDF, r['PDF'])
        if not os.path.exists(fp):
            continue
        try:
            doc = pymupdf.open(fp)
            txt = '\n'.join(p.get_text() for p in doc[:40])
            doc.close()
        except Exception:
            continue
        ctx = []
        for m in PAT.finditer(txt):
            s = max(0, m.start() - 350)
            ctx.append(re.sub(r'\s+', ' ', txt[s:m.end() + 350]))
            if len(ctx) >= 4:
                break
        out.append({'Title': r['Title'], '期刊': r['期刊'], 'Item Type': r['Item Type'],
                    '流程原因': r['流程原因'], '命中软件': r['命中软件'],
                    '摘要': ab.get(r['_nt'], ''), '上下文': ' ||| '.join(ctx),
                    '_nt': r['_nt']})
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    os.makedirs(os.path.join(ANA, 'triage_pass'), exist_ok=True)
    fp = os.path.join(ANA, 'triage_pass', 'candidates.pkl')
    if os.path.exists(fp):
        cand = pd.read_pickle(fp)
    else:
        cand = build_candidates()
        cand.to_pickle(fp)
    print('候选记录 %d 条' % len(cand))

    parsed_fp = os.path.join(ANA, 'triage_pass', 'triage_parsed.csv')
    raw_fp = os.path.join(ANA, 'triage_pass', 'triage_raw.jsonl')
    done = set()
    if os.path.exists(parsed_fp):
        done = set(pd.read_csv(parsed_fp, low_memory=False)['_nt'].astype(str))
    todo = cand[~cand['_nt'].astype(str).isin(done)]
    print('已完成 %d，待处理 %d' % (len(done), len(todo)))

    import threading
    lock = threading.Lock()
    buf = []

    def flush():
        with lock:
            if not buf:
                return
            new = pd.DataFrame(buf)
            if os.path.exists(parsed_fp):
                old = pd.read_csv(parsed_fp, low_memory=False)
                new = pd.concat([old, new], ignore_index=True)
            new.to_csv(parsed_fp, index=False, encoding='utf-8-sig')
            buf.clear()

    def work(row):
        user = ('【题名】\n%s\n\n【期刊】%s\n\n【摘要】\n%s\n\n'
                '【全文中命中的非牙科3D软件名】%s\n\n【全文上下文片段】\n%s'
                % (row['Title'], row['期刊'], str(row['摘要'])[:1500],
                   row['命中软件'], str(row['上下文'])[:2600]))
        c = call(user, 'triage|%s' % str(row['_nt'])[:36], raw_fp) or ''
        code = ''
        m = re.search(r'【判定】\s*[:：]\s*(E1|X1|X2|X3|X4)', c)
        if m:
            code = m.group(1)
        why = ''
        m2 = re.search(r'【理由】\s*[:：]\s*(.*)', c)
        if m2:
            why = m2.group(1).strip()[:300]
        buf.append({'_nt': row['_nt'], 'Title': row['Title'], '期刊': row['期刊'],
                    'Item Type': row['Item Type'], '流程原因': row['流程原因'],
                    '命中软件': row['命中软件'], '判定': code, '理由': why,
                    '原始返回': c})
        if len(buf) >= 20:
            flush()

    n = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(work, r) for _, r in todo.iterrows()]
        for _ in as_completed(futs):
            n += 1
            if n % 50 == 0:
                flush()
                print('   %d / %d' % (n, len(todo)), flush=True)
            if a.limit and n >= a.limit:
                break
    flush()

    allr = pd.read_csv(parsed_fp, low_memory=False)
    print('\n判定分布：')
    print(allr['判定'].value_counts().to_string())
    e1 = allr[allr['判定'] == 'E1']
    e1.to_csv(os.path.join(ANA, '漏排候选_E1.csv'), index=False, encoding='utf-8-sig')
    print('\nE1（本应纳入）候选 %d 条：' % len(e1))
    for _, r in e1.iterrows():
        print('  [%s] %s' % (str(r['命中软件'])[:40], str(r['Title'])[:78]))


if __name__ == '__main__':
    main()
