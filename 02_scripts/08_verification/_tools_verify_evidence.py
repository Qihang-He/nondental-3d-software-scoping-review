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
构建核验样本（A 200 条 / B 100 条）的复核证据包。

对每条样本：
  1. 若能在 10_全文PDF库 定位到全文，抽取全文并对软件词表做检索；
  2. 抽取命中软件名及其上下文片段（作为复评依据）；
  3. 若无法定位全文，仅保留摘要，证据等级记为 "摘要"。

输出:
  03_数据/08_分析用/核验复核_证据包.csv
  03_数据/08_分析用/核验复核_证据包.json   (逐条，含更长片段，供复核用)

本脚本只做证据采集，不做判定；判定在复核环节逐条给出。
"""
import os, re, json, glob, sys
import pandas as pd

try:
    import pymupdf
except ImportError:  # pragma: no cover
    import fitz as pymupdf

ROOT = (os.environ.get('SCOPING_ROOT')
        or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'))
OUT = os.path.join(D, '08_分析用')
PDFDIR = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))

# ---------- 1. 软件词表 ----------
# 只保留真正的软件名；剔除长度过短或与常用词冲突而无法可靠匹配的条目
DROP = {'ug', 'nx', 'moi', 'cura', 'unity'}
sw = pd.read_csv(os.path.join(D, '09_软件表', '软件类别与来源表.csv'), encoding='utf-8-sig')
LEX = {}
for _, r in sw.iterrows():
    for nm in (r['原始名称'], r['规范名称']):
        nm = str(nm).strip()
        if len(nm) < 3 or nm.lower() in DROP:
            continue
        LEX.setdefault(nm, r['规范名称'])
LEX.pop('ug', None)
LEX.pop('MOI', None)
# 补充常见但可能未进入词表的非牙科软件
EXTRA = ['Blender', 'MeshLab', 'CloudCompare', 'Rhinoceros', 'SolidWorks', 'Fusion 360',
         'AutoCAD', 'Inventor', 'CATIA', 'NX', 'Creo', 'FreeCAD', 'ZBrush', 'SketchUp',
         'ANSYS', 'ABAQUS', 'COMSOL', 'Mimics', '3D Slicer', 'ITK-SNAP', 'Seg3D', 'MITK',
         'Avizo', 'Amira', 'Dragonfly', 'ImageJ', 'Fiji', 'Meshroom', 'Agisoft', 'ReCap',
         'Geomagic', 'GOM', 'PolyWorks', 'FARO', 'Artec', 'Meshmixer', 'Netfabb', 'Magics',
         '3-Matic', 'Simpleware', 'ScanIP', 'Dolphin', 'OpenFOAM', 'MSC', 'LS-DYNA',
         'Autodesk', 'Materialise', 'Python', 'MATLAB', 'VMTK', 'ITK', 'VTK', 'Paraview']
for nm in EXTRA:
    LEX.setdefault(nm, nm)
# 按长度倒序，优先匹配长名（Geomagic Control X 先于 Geomagic）
NAMES = sorted(LEX.keys(), key=len, reverse=True)

# 牙科专用软件（用于说明"命中的不是非牙科软件"）
DENTAL = ['exocad', '3Shape', 'Dental System', 'DentalCAD', 'CEREC', 'inLab', 'Dolphin 3D',
          'Dolphin Imaging', 'Romexis', 'Planmeca', 'coDiagnostiX', 'NobelClinician',
          'Simplant', 'OnDemand3D', 'Blue Sky Plan', 'ProPlan', 'Mimics Dental']


def pdf_text(path, limit=400000):
    try:
        doc = pymupdf.open(path)
        buf = []
        n = 0
        for pg in doc:
            t = pg.get_text()
            buf.append(t)
            n += len(t)
            if n > limit:
                break
        doc.close()
        return re.sub(r'[ \t]+', ' ', '\n'.join(buf))
    except Exception as e:
        return ''


def _rx(nm):
    """词边界匹配，避免 algorithm 命中 ALGOR、accuracy 命中 Cura 之类误报。"""
    return re.compile(r'(?<![A-Za-z0-9])' + re.escape(nm) + r'(?![A-Za-z0-9])', re.I)


# 软件语境词：命中处附近出现这些词，说明该软件是被实际使用而非仅被提及
CTX = re.compile(r'software|softwares|version|\bv\.?\s?\d|package|toolkit|program(?:me)?\b|'
                 r'platform|developed (?:in|with|using)|using|performed (?:in|with)|'
                 r'analysis (?:in|with)|modell?ing|simulation|open-source|module|plug-?in', re.I)


def snippets(txt, names, width=300, maxhits=3):
    """返回命中软件名及其上下文；优先保留带软件语境的片段。"""
    cands = []
    for nm in names:
        m = _rx(nm).search(txt)
        if not m:
            continue
        s, e = max(0, m.start() - width), min(len(txt), m.end() + width)
        win = txt[s:e].replace('\n', ' ')
        score = 2 if CTX.search(win) else 1
        if nm.isupper() or nm in ('3D Slicer', 'ITK-SNAP'):
            score += 1  # 全大写缩写更可能指软件本体
        cands.append((score, m.start(), nm, win))
    if not cands:
        return [], []
    cands.sort(key=lambda x: (-x[0], x[1]))
    # 同一软件名只保留一次；位置过于接近的片段合并（避免重复上下文）
    picked, used_nm, spans = [], set(), []
    for sc, pos, nm, win in cands:
        if nm.lower() in used_nm:
            continue
        if any(abs(pos - p) < 400 for p in spans):
            continue
        used_nm.add(nm.lower())
        spans.append(pos)
        picked.append((nm, win))
        if len(picked) >= maxhits:
            break
    names_seen = [p[0] for p in picked]
    allnames = []
    for nm in names:
        if _rx(nm).search(txt):
            allnames.append(nm)
    return allnames[:15], picked


def main():
    A = pd.read_csv(os.path.join(OUT, '核验抽样_样本A明细.csv'), encoding='utf-8-sig')
    B = pd.read_csv(os.path.join(OUT, '核验抽样_样本B明细.csv'), encoding='utf-8-sig')
    A['样本'] = 'A_排除抽样'
    B['样本'] = 'B_纳入抽样'
    A['流程记录原因'] = A['排除原因']
    B['流程记录原因'] = ''
    S = pd.concat([A, B], ignore_index=True)
    S['编号'] = range(1, len(S) + 1)

    pm = pd.read_csv(os.path.join(D, '07_PDF与语料对照', 'pdf_match.csv'),
                     encoding='utf-8-sig', low_memory=False).dropna(subset=['file'])
    fmap = dict(zip(pm.Key, pm.file))
    # 建立文件名 -> 实际路径索引
    idx = {}
    for tdir, _, files in os.walk(PDFDIR):
        for f in files:
            if f.lower().endswith('.pdf'):
                idx.setdefault(f, os.path.join(tdir, f))

    # 摘要来源
    ex = {}
    for pk in ['fulltext_pass/excerpts.pkl', 'fulltext_pass/excerpts_included.pkl']:
        p = os.path.join(OUT, pk)
        if os.path.exists(p):
            d = pd.read_pickle(p)
            for _, r in d.iterrows():
                ex.setdefault(r['Key'], r.get('摘要', '') or '')

    rows, detail = [], []
    for i, r in S.iterrows():
        key = r['Key']
        row = {'样本': r['样本'], '编号': r['编号'], 'Key': key, 'Title': r['Title'],
               '流程记录原因': r['流程记录原因']}
        fn = fmap.get(key)
        path = idx.get(fn) if fn else None
        txt = pdf_text(path) if path else ''
        abst = str(ex.get(key, '') or r.get('摘要', '') or '')
        if txt:
            names, snips = snippets(txt, NAMES)
            dent = [d for d in DENTAL if d.lower() in txt.lower()]
            row.update({'证据等级': '全文', 'PDF': os.path.basename(path),
                        '命中非牙科软件': '；'.join(names), '命中牙科专用软件': '；'.join(dent),
                        '全文长度': len(txt)})
            ev = ' || '.join('%s :: %s' % (n, s) for n, s in snips)
            detail.append({'Key': key, '样本': r['样本'], '证据等级': '全文',
                           '命中': names, '牙科专用命中': dent, '证据': ev, '摘要': abst[:1200]})
            row['证据片段'] = ev[:900]
        else:
            row.update({'证据等级': '摘要', 'PDF': '', '命中非牙科软件': '',
                        '命中牙科专用软件': '', '全文长度': 0,
                        '证据片段': ''})
            detail.append({'Key': key, '样本': r['样本'], '证据等级': '摘要',
                           '命中': [], '牙科专用命中': [], '证据': '', '摘要': abst[:1200]})
        row['摘要'] = abst[:900]
        rows.append(row)
        if (i + 1) % 50 == 0:
            print('  已处理 %d/%d' % (i + 1, len(S)))

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, '核验复核_证据包.csv'), index=False, encoding='utf-8-sig')
    with open(os.path.join(OUT, '核验复核_证据包.json'), 'w', encoding='utf-8') as f:
        json.dump(detail, f, ensure_ascii=False, indent=1)

    print('\n证据包构建完成')
    for lab, g in df.groupby('样本'):
        print('  %s: 全文 %d, 仅摘要 %d' % (lab, (g.证据等级 == '全文').sum(), (g.证据等级 == '摘要').sum()))
    print('  有非牙科软件命中的样本数: %d' % (df['命中非牙科软件'] != '').sum())
    print('  -> 核验复核_证据包.csv / .json')


if __name__ == '__main__':
    main()
