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
_rescreen_fulltext.py
对 E1 候选做**严格核验 + 逐条图表化编码**（一步完成）：
  · 输入：E1 候选（其全文已命中非牙科3D软件名）
  · 输入内容：题名 + 摘要 + 全文中软件名所在的方法学上下文（最多 5 段）
  · 输出：include/exclude 判定 + 纳入时的专科/应用场景/软件/研究设计
输出：03_数据/08_分析用/rescreen_pass/rescreen_parsed.csv
"""
import os
import re
import json
import time
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
PDF = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))
MODEL = 'deepseek-chat'
TEMPERATURE = 0.1
MAX_TOKENS = 400
API_URL = 'https://api.deepseek.com/v1/chat/completions'

SYSTEM = """你是范围综述的全文纳排核验员。

【纳入标准】
1) 主题属口腔医学任一学科；
2) 该研究**自身**在其方法中使用了一个**非牙科专用3D软件**（原始开发领域不在牙科，如 Mimics、3D Slicer、ANSYS、ABAQUS、Geomagic 系列、GOM Inspect、Blender、Meshmixer、CloudCompare、MeshLab、SolidWorks、MATLAB、ITK-SNAP、HyperMesh、COMSOL、3-Matic、Avizo 等）用于3D数据的处理/分析/建模；
3) 文献类型为原创研究、技术说明或病例报告（**排除**综述、系统综述、社论、评论、会议摘要、信件、方案）；
4) 英文，2020-07-01 至 2026-06-30。

【判定要求】只有当证据表明该研究**自己在方法中使用**了上述软件时才判 INCLUDE。
若软件名只出现在参考文献、被引他人研究、或仅在讨论中泛泛提及，判 EXCLUDE。

【输出格式】严格只输出以下各行：
【判定】: INCLUDE 或 EXCLUDE
【判定理由】: 一句话，引用具体证据
【专科】: 若 INCLUDE，填一个主要口腔专科（英文）；否则填 -
【应用场景】: 若 INCLUDE，填一个主要场景（Image segmentation and 3D reconstruction / 3D data analysis and accuracy assessment / Biomechanical analysis and simulation / Digital design and manufacturing / Surgical planning and precise implementation / Morphological and phenotypic analysis）；否则填 -
【软件】: 若 INCLUDE，列出该研究自己使用的非牙科3D软件（用 ; 分隔的规范名）；否则填 -
【研究设计】: 若 INCLUDE，填 computational / in_vitro / clinical / technical_note / case_report / educational 之一；否则填 -
"""


def nt(s):
    import unicodedata
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
            r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=150)
            j = r.json()
            c = j['choices'][0]['message']['content']
            with open(raw_fp, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'tag': tag, 'model': j.get('model'),
                                    'content': c}, ensure_ascii=False) + '\n')
            return c
        except Exception:
            if a == retries - 1:
                return ''
            time.sleep(2 + 3 * a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    out = os.path.join(ANA, 'rescreen_pass')
    os.makedirs(out, exist_ok=True)

    e1 = pd.read_csv(os.path.join(ANA, '漏排候选_E1.csv'), low_memory=False)
    e1['_nt'] = e1['_nt'].astype(str)
    cand = pd.read_pickle(os.path.join(ANA, 'triage_pass', 'candidates.pkl'))
    cand['_nt'] = cand['_nt'].astype(str)
    cols = [c for c in ['_nt', '摘要', '上下文'] if c in cand.columns]
    e1 = e1.merge(cand[cols], on='_nt', how='left')
    print('E1 候选 %d 条' % len(e1))

    parsed_fp = os.path.join(out, 'rescreen_parsed.csv')
    raw_fp = os.path.join(out, 'rescreen_raw.jsonl')
    done = set()
    if os.path.exists(parsed_fp):
        done = set(pd.read_csv(parsed_fp, low_memory=False)['_nt'].astype(str))
    todo = e1[~e1['_nt'].isin(done)]
    print('已完成 %d，待处理 %d' % (len(done), len(todo)))

    lock = threading.Lock()
    buf = []

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

    def g(c, tag):
        m = re.search(r'【%s】\s*[:：]\s*(.*)' % tag, c or '')
        return m.group(1).strip() if m else ''

    def work(row):
        user = ('【题名】%s\n\n【期刊】%s\n\n【摘要】\n%s\n\n'
                '【全文中出现非牙科3D软件的上下文片段】\n%s'
                % (row['Title'], row['期刊'], str(row['摘要'])[:1400],
                   str(row['上下文'])[:4000]))
        c = call(user, 'rescreen|%s' % str(row['_nt'])[:36], raw_fp)
        buf.append({'_nt': row['_nt'], 'Title': row['Title'], '期刊': row['期刊'],
                    'Item Type': row['Item Type'], '原流程原因': row['流程原因'],
                    '判定': g(c, '判定').upper(), '判定理由': g(c, '判定理由')[:300],
                    '专科': g(c, '专科'), '应用场景': g(c, '应用场景'),
                    '软件': g(c, '软件'), '研究设计': g(c, '研究设计'),
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
    flush()

    allr = pd.read_csv(parsed_fp, low_memory=False)
    inc = allr[allr['判定'].str.startswith('INCLUDE')]
    print('\n判定分布：')
    print(allr['判定'].value_counts().to_string())
    inc.to_csv(os.path.join(ANA, '新增纳入候选.csv'), index=False, encoding='utf-8-sig')
    print('\nINCLUDE %d 条' % len(inc))


if __name__ == '__main__':
    main()
