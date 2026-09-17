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
_tools_fix_journal_and_window.py
用途：
  1) 严格按时间窗（2020-07-01 ~ 2026-06-30）剔除窗口外记录（用户指令）。
  2) 为缺刊名记录补全 Journal：证据链优先级
        A. PDF 首页文本与数据集中已有刊名列表精确/归一化匹配（最强证据）
        B. Crossref DOI -> container-title
        C. Crossref 标题检索（标题相似度 >= 0.92）-> container-title
        D. 无可靠证据则留空
产出：
  03_数据/08_分析用/分析数据集_final_v3.csv        （窗口剔除后，N=566）
  03_数据/08_分析用/窗口外剔除_3条.csv
  03_数据/08_分析用/刊名补全_证据表.csv            （每条：来源、证据文本、置信度）
"""
import os, re, json, unicodedata, difflib, time
import pandas as pd

ROOT = _ROOTP
ANA  = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
MATCH_CSV = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '07_PDF与语料对照', 'pdf_match.csv')
PDF_DIR   = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))

WIN_S = pd.Timestamp('2020-07-01')
WIN_E = pd.Timestamp('2026-06-30')


def norm(s):
    if s is None:
        return ''
    s = unicodedata.normalize('NFKD', str(s))
    s = s.replace('&', ' and ')
    s = re.sub(r'[^0-9a-zA-Z]+', '', s).lower()
    return s


def norm_title(s):
    if s is None:
        return ''
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


def load_api_key():
    p = os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'config.local.json')
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    df = pd.read_csv(os.path.join(ANA, '分析数据集_final.csv'))
    n0 = len(df)

    # ---------- 1. 时间窗 ----------
    d = df['Date'].astype(str)
    parsed = pd.to_datetime(d, errors='coerce', format='mixed')
    # 仅有年份的记录不剔除（无非窗口证据）
    out_mask = (parsed < WIN_S) | (parsed > WIN_E)
    out = df[out_mask].copy()
    out['_窗判定'] = parsed[out_mask].dt.strftime('%Y-%m')
    kept = df[~out_mask].copy()
    print(f'[窗口] 原 N={n0} -> 剔除 {len(out)} -> N={len(kept)}')
    out[['序号', 'Key', 'Title', 'DOI', 'Journal', 'Date', '_窗判定']].to_csv(
        os.path.join(ANA, '窗口外剔除_3条.csv'), index=False, encoding='utf-8-sig')

    # ---------- 2. 刊名补全 ----------
    known = sorted({str(x).strip() for x in kept['Journal'].dropna()
                    if str(x).strip()})
    known_norm = {norm(x): x for x in known}

    pm = pd.read_csv(MATCH_CSV)
    pm = pm[pm['matched'] == True].copy()
    key2file = {}
    for _, r in pm.iterrows():
        k = str(r['Key']).strip()
        if k and k != 'nan' and k not in key2file:
            key2file[k] = str(r['file'])

    miss = kept[kept['Journal'].isna() |
                (kept['Journal'].astype(str).str.strip().isin(['', 'nan']))].copy()
    print(f'[刊名] 待补 {len(miss)} 条')

    try:
        import fitz  # pymupdf
    except Exception as e:
        fitz = None
        print('  !! pymupdf 不可用：', e)

    records = []
    for _, r in miss.iterrows():
        key = str(r['Key']).strip()
        title = str(r['Title'])
        doi = '' if pd.isna(r['DOI']) else str(r['DOI']).strip()
        rec = {'序号': r['序号'], 'Key': key, 'Title': title, 'DOI': doi,
               '补全刊名': '', '证据来源': '', '证据文本': '', '置信度': ''}

        # A. PDF 首页文本匹配已知刊名
        fn = key2file.get(key)
        if fn and fitz is not None:
            fp = os.path.join(PDF_DIR, fn)
            if os.path.exists(fp):
                try:
                    doc = fitz.open(fp)
                    txt = doc[0].get_text()
                    doc.close()
                    head = txt[:3000]
                    hit = None
                    for ln in head.splitlines():
                        nl = norm(ln)
                        if len(nl) < 6:
                            continue
                        if nl in known_norm:
                            hit = (known_norm[nl], ln.strip())
                            break
                    if hit is None:
                        # 长篇刊名（含 "Journal of ..." 等）整体归一化匹配
                        nn = norm(head)
                        for kn, orig in known_norm.items():
                            if len(kn) >= 8 and kn in nn:
                                hit = (orig, orig)
                                break
                    if hit:
                        rec.update({'补全刊名': hit[0], '证据来源': 'PDF首页',
                                    '证据文本': hit[1], '置信度': '高'})
                        records.append(rec)
                        continue
                except Exception:
                    pass

        # B/C. Crossref
        try:
            import requests
        except Exception:
            requests = None
        got = False
        if requests is not None:
            headers = {'User-Agent': 'ScopingReview/1.0 (mailto:author@example.org)'}
            try:
                if doi:
                    u = f'https://api.crossref.org/works/{doi}'
                    j = requests.get(u, headers=headers, timeout=25).json()
                    ct = (j.get('message', {}).get('container-title') or [''])
                    ct = ct[0] if ct else ''
                    if ct:
                        rec.update({'补全刊名': ct, '证据来源': 'Crossref-DOI',
                                    '证据文本': doi, '置信度': '高'})
                        records.append(rec)
                        got = True
                if not got:
                    u = 'https://api.crossref.org/works'
                    j = requests.get(u, headers=headers, timeout=30,
                                     params={'query.bibliographic': title[:200],
                                             'rows': 5}).json()
                    best, bs = None, 0.0
                    for it in j.get('message', {}).get('items', []):
                        cand = (it.get('title') or [''])
                        cand = cand[0] if cand else ''
                        s = difflib.SequenceMatcher(
                            None, norm_title(title), norm_title(cand)).ratio()
                        if s > bs:
                            bs, best = s, it
                    if best is not None and bs >= 0.92:
                        ct = (best.get('container-title') or [''])
                        ct = ct[0] if ct else ''
                        if ct:
                            rec.update({'补全刊名': ct, '证据来源': 'Crossref-标题',
                                        '证据文本': f'相似度={bs:.3f}',
                                        '置信度': '中'})
                            records.append(rec)
                            got = True
            except Exception:
                pass
            time.sleep(0.35)

        if not got:
            rec.update({'证据来源': '无可靠证据', '置信度': '留空'})
            records.append(rec)

    ev = pd.DataFrame(records)
    ev.to_csv(os.path.join(ANA, '刊名补全_证据表.csv'), index=False,
              encoding='utf-8-sig')

    # 应用补全
    fix = {r['序号']: r['补全刊名'] for _, r in ev.iterrows()
           if str(r['补全刊名']).strip()}
    kept['Journal'] = [fix.get(i, j) for i, j in zip(kept['序号'], kept['Journal'])]

    kept.drop(columns=[c for c in ['_d'] if c in kept.columns], inplace=True)
    kept.to_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), index=False,
                encoding='utf-8-sig')

    filled = sum(1 for v in fix.values() if str(v).strip())
    still = len(kept[kept['Journal'].isna() |
                     (kept['Journal'].astype(str).str.strip().isin(['', 'nan']))])
    print(f'[刊名] 补全 {filled} 条，仍缺 {still} 条')
    print(f'[输出] 分析数据集_final_v3.csv  N={len(kept)}')


if __name__ == '__main__':
    main()
