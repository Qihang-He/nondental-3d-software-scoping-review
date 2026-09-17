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
_rescreen_all_pdf.py  —— 对"筛查阶段被排除"记录中**所有可获取全文**的文献做全文纳排判定

科学要点（宁可保守，不可虚增）：
  · 不依赖软件表名单：从全文自动抽取"软件/程序/版本/建模/逆向/有限元/配准/叠加/分割"
    等关键词周边窗口作为证据片段，交由同一模型判定；
  · 只有当证据表明**该研究自身在方法中使用了一个具名的第三方非牙科3D软件**时才判 INCLUDE；
    仅出现在参考文献、他人研究、讨论泛述、或使用自研代码/牙科专用软件，一律 EXCLUDE；
  · 每条逐条保存原始返回，可复核可复现。
输出：03_数据/08_分析用/fulltext_pass/{fulltext_parsed.csv, fulltext_raw.jsonl}
"""
import os
import re
import json
import time
import argparse
import unicodedata
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

KEY = re.compile(
    r'(?:software|program\b|programme|version\s*[\d.]|reverse[- ]engineer|'
    r'finite[- ]element|finite element analysis|FEA\b|CAD\b|computer-aided|'
    r'segmentation|reconstruct|registration|superimpos|STL\b|DICOM|'
    r'three[- ]dimensional software|3D software|modell?ing|mesh\b|point cloud|'
    r'Geomagic|Mimics|Slicer|ANSYS|ABAQUS|Mimics|Meshmixer|Blender|GOM|'
    r'SolidWorks|MATLAB|Rhinoceros|3-Matic|ITK|HyperMesh|COMSOL|Avizo|'
    r'Mimics|CloudCompare|MeshLab|Magics|ZBrush|Fusion 360|InVesalius|VGStudio|'
    r'Simpleware|Amira|OsiriX|MITK|PolyWorks|AutoCAD|CATIA|Creo|NX\b|Inventor)',
    re.I)

SYSTEM = """你是范围综述的全文纳排核验员。下面给出：一条文献的题名、期刊、摘要，以及从该文献**全文**中
自动抽取的、与"使用什么软件/程序"有关的证据片段。

【本题的纳入标准】
1) 主题属于口腔医学任一学科。
2) 该研究**自身**在其材料与方法中使用了**一个具名的第三方非牙科三维（3D）软件**
   （其原始开发领域不在牙科，例如 Mimics、3D Slicer、ITK-SNAP、InVesalius、Brainlab、
   ANSYS、ABAQUS、COMSOL、HyperMesh、ALGOR、Geomagic 系列、GOM Inspect、PolyWorks、
   CloudCompare、MeshLab、Avizo、Amira、VGStudio、Blender、Meshmixer、ZBrush、
   SolidWorks、Rhinoceros、3-Matic、Solid Edge、CATIA、Creo、NX、Inventor、AutoCAD、
   Fusion 360、MATLAB、Magics、Netfabb 等），用于3D数据的处理、分析、建模或测量。
3) 文献类型为原创研究、技术说明或病例报告（**排除**综述、系统综述、社论、评论、
   会议摘要、信件、研究方案、撤稿）。
4) 英文，发表于 2020-07-01 至 2026-06-30。

【判为 EXCLUDE 的情形（务必严格执行）】
· 软件名只出现在参考文献、被引他人研究、或仅在讨论/引言中泛泛提及；
· 该研究只使用自研算法/代码（如自建 U-Net、深度学习模型、自编程序），没有使用具名第三方软件；
· 该研究只使用牙科专用软件（如 exocad、3Shape、coDiagnostiX、Implant Studio、Romexis 等）；
· 证据片段中没有任何一个**具名的第三方非牙科3D软件**被该研究自己使用；
· 主题不属于口腔医学；或为综述/社论/会议摘要等非原创类型。

【输出格式】严格只输出以下各行，不要任何多余文字：
【判定】: INCLUDE 或 EXCLUDE
【判定理由】: 一到两句，必须引用证据片段中的具体原文
【软件】: 若 INCLUDE，列出该研究自己使用的非牙科3D软件（用 ; 分隔）；否则填 -
【专科】: 若 INCLUDE，填一个主要口腔专科（英文）；否则填 -
【应用场景】: 若 INCLUDE，填一个（Image segmentation and 3D reconstruction / 3D data analysis and accuracy assessment / Biomechanical analysis and simulation / Digital design and manufacturing / Surgical planning and precise implementation / Morphological and phenotypic analysis）；否则填 -
【研究设计】: 若 INCLUDE，填 computational / in_vitro / clinical / technical_note / case_report / educational 之一；否则填 -
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
            r = requests.post(API_URL, headers=HEADERS, json=payload, timeout=180)
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


def build_excerpts(which='excluded'):
    """which='excluded' 处理排除集；'included' 处理现有纳入集（一致性复核）"""
    fp = os.path.join(ANA, 'fulltext_pass', 'excerpts_%s.pkl' % which)
    if os.path.exists(fp):
        return pd.read_pickle(fp)
    import pymupdf
    uni = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                   '筛选语料_唯一记录_2556.csv'), low_memory=False)
    uni['_nt'] = uni['Title'].map(nt)
    meta = uni.set_index('_nt')[['Item Type', 'Publication Title', 'Date', 'Key',
                                 'Abstract']].to_dict('index')
    pm = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '07_PDF与语料对照', 'pdf_match.csv'),
                     low_memory=False)
    k2f = {}
    for _, r in pm.iterrows():
        k = str(r.get('Key', '')).strip()
        if k and k != 'nan' and k not in k2f:
            k2f[k] = str(r['file'])

    if which == 'excluded':
        src = pd.read_csv(os.path.join(ANA, 'prisma_pass', 'reason_parsed.csv'),
                          low_memory=False).drop_duplicates('_nt')
        src = src[['_nt', 'Title']]
        src['_orig'] = None
    else:
        v = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
        v['_nt'] = v['Title'].map(nt)
        src = v[['_nt', 'Title']].copy()
        src['_orig'] = None

    rows = []
    for _, r in src.iterrows():
        m = meta.get(r['_nt'], {})
        f = k2f.get(str(m.get('Key', '')))
        if not f:
            continue
        p = os.path.join(PDF, f)
        if not os.path.exists(p):
            continue
        try:
            doc = pymupdf.open(p)
            txt = '\n'.join(pg.get_text() for pg in doc[:30])
            doc.close()
        except Exception:
            continue
        txt = re.sub(r'\s+', ' ', txt)
        wins, seen = [], set()
        for mm in KEY.finditer(txt):
            s = max(0, mm.start() - 300)
            e = min(len(txt), mm.end() + 300)
            key = (s // 250,)
            if key in seen:
                continue
            seen.add(key)
            wins.append(txt[s:e])
            if len(wins) >= 7:
                break
        if not wins:
            continue
        rows.append({'Title': r['Title'], '_nt': r['_nt'],
                     '期刊': m.get('Publication Title'), 'Item Type': m.get('Item Type'),
                     '摘要': m.get('Abstract'), '证据片段': ' ||| '.join(wins)[:5200],
                     'PDF': f, 'Key': m.get('Key')})
    df = pd.DataFrame(rows)
    df.to_pickle(fp)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--which', choices=['excluded', 'included'], default='excluded')
    a = ap.parse_args()
    out = os.path.join(ANA, 'fulltext_pass')
    os.makedirs(out, exist_ok=True)
    cand = build_excerpts(a.which)
    print('[%s] 可获取全文并抽取到证据片段的记录：%d 条' % (a.which, len(cand)))

    parsed_fp = os.path.join(out, 'fulltext_%s_parsed.csv' % a.which)
    raw_fp = os.path.join(out, 'fulltext_%s_raw.jsonl' % a.which)
    done = set()
    if os.path.exists(parsed_fp):
        done = set(pd.read_csv(parsed_fp, low_memory=False)['_nt'].astype(str))
    todo = cand[~cand['_nt'].astype(str).isin(done)]
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
        user = ('【题名】%s\n\n【期刊】%s\n\n【摘要】\n%s\n\n【全文中抽取的软件相关证据片段】\n%s'
                % (row['Title'], row['期刊'], str(row['摘要'])[:1200],
                   str(row['证据片段'])[:5200]))
        c = call(user, 'ft|%s' % str(row['_nt'])[:36], raw_fp)
        buf.append({'_nt': row['_nt'], 'Title': row['Title'], '期刊': row['期刊'],
                    'Item Type': row['Item Type'], 'Key': row['Key'], 'PDF': row['PDF'],
                    '判定': g(c, '判定').upper(), '判定理由': g(c, '判定理由')[:400],
                    '软件': g(c, '软件'), '专科': g(c, '专科'),
                    '应用场景': g(c, '应用场景'), '研究设计': g(c, '研究设计'),
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
    print('\n判定分布：')
    print(allr['判定'].value_counts().to_string())
    inc = allr[allr['判定'].str.startswith('INCLUDE')]
    tag = '新增纳入' if a.which == 'excluded' else '原纳入集复核'
    inc.to_csv(os.path.join(ANA, '全文再筛查_%s.csv' % tag), index=False,
               encoding='utf-8-sig')
    allr.to_csv(os.path.join(ANA, '全文再筛查_%s_全量.csv' % tag), index=False,
                encoding='utf-8-sig')
    print('\nINCLUDE %d 条' % len(inc))


if __name__ == '__main__':
    main()
