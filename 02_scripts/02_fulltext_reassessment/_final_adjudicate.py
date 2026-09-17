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
_final_adjudicate.py —— 对 301 条候选做**最终裁决**（软件名优先抽取证据 + 严格判定）
输出：03_数据/08_分析用/final_pass/final_parsed.csv
"""
import os
import re
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
MODEL = 'deepseek-chat'
TEMPERATURE = 0.1
MAX_TOKENS = 400
API_URL = 'https://api.deepseek.com/v1/chat/completions'

SYSTEM = """你是范围综述的全文纳排核验员。下面给出：一条文献的题名、期刊、摘要，以及从该文献**方法学部分**
自动抽取的、包含具体软件名的原文片段。

【纳入标准】
1) 主题属于口腔医学任一学科；
2) 该研究**自身**在材料与方法中使用了**一个具名的第三方非牙科三维（3D）软件**
   （原始开发领域不在牙科，例如 Mimics、3D Slicer、ITK-SNAP、InVesalius、Brainlab、
   ANSYS、ABAQUS、COMSOL、HyperMesh、ALGOR、Geomagic 系列、GOM Inspect、PolyWorks、
   CloudCompare、MeshLab、Avizo、Amira、VGStudio、Blender、Meshmixer、ZBrush、
   SolidWorks、Rhinoceros、3-Matic、Solid Edge、CATIA、Creo、NX、Inventor、AutoCAD、
   Fusion 360、MATLAB、Magics、Netfabb 等），用于3D数据的处理、分析、建模或测量；
3) 类型为原创研究、技术说明或病例报告（排除综述、系统综述、社论、评论、会议摘要、
   信件、方案、撤稿）；
4) 英文，2020-07-01 至 2026-06-30。

【必须判 EXCLUDE 的情形】
· 证据片段中，该软件名只出现在参考文献列表、他文引用、或 "similar to previous studies" 之类泛述；
· 该研究只使用自研代码/自建深度学习模型，没有使用具名第三方软件；
· 该研究只使用牙科专用软件（exocad、3Shape、coDiagnostiX、Implant Studio、Romexis、
  DentalCAD、NemoScan 等）；
· 主题不属于口腔医学；或文献类型不符。
请特别核对：句中是否用 "we used / were analysed using / imported into / processed in"
等表述表明**本研究自己使用**了该软件。

【输出格式】严格只输出以下各行：
【判定】: INCLUDE 或 EXCLUDE
【证据】: 直接引用证据片段中表明本研究使用了该软件的原文（若 EXCLUDE 则说明缺失何种证据）
【软件】: 若 INCLUDE，列出该研究使用的非牙科3D软件（; 分隔）；否则填 -
【专科】: 若 INCLUDE，填一个主要口腔专科（英文）；否则填 -
【应用场景】: 若 INCLUDE，填一个（Image segmentation and 3D reconstruction / 3D data analysis and accuracy assessment / Biomechanical analysis and simulation / Digital design and manufacturing / Surgical planning and precise implementation / Morphological and phenotypic analysis）；否则填 -
【研究设计】: 若 INCLUDE，填 computational / in_vitro / clinical / technical_note / case_report / educational；否则填 -
"""


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
            r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=180)
            j = r.json()
            c = j['choices'][0]['message']['content']
            with open(raw_fp, 'a', encoding='utf-8') as f:
                f.write(json.dumps({'tag': tag, 'model': j.get('model'), 'content': c},
                                   ensure_ascii=False) + '\n')
            return c
        except Exception:
            if a == retries - 1:
                return ''
            time.sleep(2 + 3 * a)


def main():
    out = os.path.join(ANA, 'final_pass')
    cand = pd.read_pickle(os.path.join(out, 'candidates.pkl'))
    parsed_fp = os.path.join(out, 'final_parsed.csv')
    raw_fp = os.path.join(out, 'final_raw.jsonl')
    done = set()
    if os.path.exists(parsed_fp):
        done = set(pd.read_csv(parsed_fp, low_memory=False)['_nt'].astype(str))
    todo = cand[~cand['_nt'].astype(str).isin(done)]
    print('候选 %d ；待裁决 %d' % (len(cand), len(todo)))
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
        c = call(user, 'final|%s' % str(row['_nt'])[:36], raw_fp)
        buf.append({'_nt': row['_nt'], 'Title': row['Title'], '期刊': row['期刊'],
                    'Item Type': row['Item Type'], 'Key': row['Key'],
                    'PassA': row['PassA'], 'PassB': row['PassB'],
                    '判定': g(c, '判定').upper(), '证据': g(c, '证据')[:500],
                    '软件': g(c, '软件'), '专科': g(c, '专科'),
                    '应用场景': g(c, '应用场景'), '研究设计': g(c, '研究设计'),
                    '原始返回': c})
        if len(buf) >= 20:
            flush()

    n = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(work, r) for _, r in todo.iterrows()]
        for _ in as_completed(futs):
            n += 1
            if n % 50 == 0:
                flush()
                print('   %d / %d' % (n, len(todo)), flush=True)
    flush()
    allr = pd.read_csv(parsed_fp, low_memory=False)
    print('\n最终判定分布：')
    print(allr['判定'].value_counts().to_string())
    print('\n按两轮历史判定分层：')
    print(pd.crosstab([allr['PassA'], allr['PassB']], allr['判定']).to_string())
    inc = allr[allr['判定'].str.upper().str.startswith('INCLUDE')]
    inc.to_csv(os.path.join(ANA, '最终新增纳入.csv'), index=False, encoding='utf-8-sig')
    print('\n最终 INCLUDE %d 条' % len(inc))


if __name__ == '__main__':
    main()
