# -*- coding: utf-8 -*-
"""
_tools_author_verify_build.py —— 生成作者人工核验工作表。

设计（固定种子，可复现）：
  工作表 1：从最终纳入集（863）中简单随机抽取 100 条，作者逐条核对
            （a）是否确实使用了具名的非牙科专用 3D 软件；（b）学科归属是否正确。
  工作表 2：从"经全文复评确认不符合纳入标准"的 864 条中简单随机抽取 50 条，
            作者逐条核对是否存在"应纳入而漏纳"（假阴性）。

每条均附：已抽取的原文证据片段 + 全文 PDF 文件名，便于快速定位；
核验列留空供作者填写。

输出：02_图表附件/R2_补充材料/作者人工核验工作表.xlsx
      03_数据/08_分析用/作者核验_纳入抽样100.csv
      03_数据/08_分析用/作者核验_排除抽样50.csv
"""
import os, re, sys
import pandas as pd

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

ROOT = (os.environ.get('SCOPING_ROOT')
        or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = os.path.join(ROOT, '03_数据')
ANA = os.path.join(D, '08_分析用')
PDFDIR = os.path.join(ROOT, '10_全文PDF库')
SUP = os.path.join(ROOT, '02_图表附件', 'R2_补充材料')

SEED = 20260915
N_INC = 100
N_EXC = 50

sw = pd.read_csv(os.path.join(D, '09_软件表', '软件类别与来源表.csv'), encoding='utf-8-sig')
NAMES = sorted(set(sw['原始名称'].astype(str)) | set(sw['规范名称'].astype(str)), key=len, reverse=True)
NAMES = [n for n in NAMES if len(n) >= 3 and n.lower() not in ('ug', 'nx', 'moi')]
CTX = re.compile(r'software|version|\bv\.?\s?\d|package|toolkit|program(?:me)?\b|platform|'
                 r'developed (?:in|with|using)|using|modelling|modeling|simulation', re.I)


def rx(nm):
    return re.compile(r'(?<![A-Za-z0-9])' + re.escape(nm) + r'(?![A-Za-z0-9])', re.I)


def pdf_path(fn):
    for d, _, fs in os.walk(PDFDIR):
        if fn in fs:
            return os.path.join(d, fn)
    return None


def evidence(p, names):
    if not p:
        return ''
    try:
        doc = pymupdf.open(p)
        txt = re.sub(r'[ \t]+', ' ', '\n'.join(pg.get_text() for pg in doc))
        doc.close()
    except Exception:
        return ''
    out = []
    for nm in names:
        m = rx(nm).search(txt)
        if not m:
            continue
        s, e = max(0, m.start() - 300), min(len(txt), m.end() + 300)
        w = txt[s:e].replace('\n', ' ')
        out.append((2 if CTX.search(w) else 1, nm, w))
    if not out:
        return ''
    out.sort(key=lambda x: -x[0])
    return ' || '.join('%s :: %s' % (nm, w[:380]) for _, nm, w in out[:2])


def main():
    fin = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'),
                      encoding='utf-8-sig', low_memory=False)
    pm = pd.read_csv(os.path.join(D, '07_PDF与语料对照', 'pdf_match.csv'),
                     encoding='utf-8-sig', low_memory=False).dropna(subset=['file'])
    fmap = dict(zip(pm.Key, pm.file))
    rec = pd.read_csv(os.path.join(ANA, '最终新增纳入.csv'), encoding='utf-8-sig', low_memory=False)
    ft = pd.read_csv(os.path.join(ANA, 'fulltext_pass', 'fulltext_parsed.csv'),
                     encoding='utf-8-sig', low_memory=False)

    # ---- 工作表 1：纳入集 100 条 ----
    s1 = fin.sample(n=N_INC, random_state=SEED).copy()
    rows = []
    for i, (_, r) in enumerate(s1.iterrows(), 1):
        fn = fmap.get(r['Key'])
        ev = evidence(pdf_path(fn) if fn else None, NAMES)
        rows.append({
            '编号': i, 'Key': r['Key'], '标题': r['Title'], '期刊': r.get('Journal', ''),
            '年份': r.get('Year', ''), '全文PDF': fn or '（未定位到全文）',
            '数据集标注的软件': r.get('Software Used (fixed)', r.get('Software Used', '')),
            '数据集标注的学科': r.get('Dental Specialty', ''),
            '数据集标注的应用场景': r.get('Application Scenario', ''),
            '原文证据片段（供快速定位）': ev[:900],
            '【作者填写】软件使用是否属实（是/否）': '',
            '【作者填写】正确的软件名（如不符请填）': '',
            '【作者填写】学科归属是否正确（是/否）': '',
            '【作者填写】正确的学科（如不符请填）': '',
            '【作者填写】备注': '',
        })
    v1 = pd.DataFrame(rows)

    # ---- 工作表 2：确认排除中 50 条（假阴性检查） ----
    exc_keys = set(ft.Key.dropna()) - set(rec.Key.dropna())
    pop = ft[ft.Key.isin(exc_keys)].dropna(subset=['Key']).copy()
    pop = pop.drop_duplicates('Key')
    s2 = pop.sample(n=min(N_EXC, len(pop)), random_state=SEED + 1).copy()
    rows = []
    for i, (_, r) in enumerate(s2.iterrows(), 1):
        fn = fmap.get(r['Key'])
        ev = evidence(pdf_path(fn) if fn else None, NAMES)
        rows.append({
            '编号': i, 'Key': r['Key'], '标题': r['Title'], '期刊': r.get('期刊', ''),
            '文献类型': r.get('Item Type', ''),
            '全文复评时的判定理由': str(r.get('判定理由', ''))[:300],
            '全文PDF': fn or '（未定位到全文）',
            '原文证据片段（供快速定位）': ev[:900],
            '【作者填写】是否同意排除（同意/不同意）': '',
            '【作者填写】如不同意，应纳入的理由与软件名': '',
            '【作者填写】备注': '',
        })
    v2 = pd.DataFrame(rows)

    os.makedirs(SUP, exist_ok=True)
    # Excel 不接受控制字符（PDF 抽取文本常带 \x0b 等）
    ILLEGAL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

    def clean(v):
        if isinstance(v, str):
            v = ILLEGAL.sub(' ', v)
            v = re.sub(r'\s+', ' ', v).strip()
        return v

    v1 = v1.map(clean) if hasattr(v1, 'map') else v1.applymap(clean)
    v2 = v2.map(clean) if hasattr(v2, 'map') else v2.applymap(clean)

    xp = os.path.join(SUP, '作者人工核验工作表.xlsx')
    with pd.ExcelWriter(xp, engine='openpyxl') as w:
        pd.DataFrame({
            '项目': ['核验目的', '抽样种子', '核验方式', '工作表 1 说明', '工作表 2 说明',
                     '填写要求', '证据片段的作用', '完成后', '说明'],
            '内容': [
                '对数据集中最关键的两个字段（软件使用、学科归属）进行人工核验，'
                '并对"确认排除"的记录做假阴性抽查。',
                str(SEED) + '（简单随机抽样，可由脚本复现）',
                '由作者本人逐条查看原文证据与全文，独立作出判断；本表由作者填写。',
                '从最终纳入集（n = 863）中简单随机抽取 100 条。核对：'
                '(a) 该研究是否确实使用了具名的非牙科专用 3D 软件；(b) 学科归属是否正确。',
                '从"经全文复评判定为不符合纳入标准"的记录（n = 864）中简单随机抽取 50 条。'
                '核对：是否存在"本应纳入而漏纳"的情况（假阴性）。',
                '只填写【作者填写】列；同意则填"是/同意"，不同意请填正确内容。'
                '留空视为未核验，会在统计时单独列出。',
                '已在数据集中自动抽取一段包含软件名的原文作为定位线索，'
                '作者仍应以全文为准；如片段不足，请打开该条 PDF 查看。',
                '填写完成后运行 _tools_author_verify_collect.py，'
                '自动生成核验汇总与可写入论文的句段。',
                '本表用于人工核验，不用于独立双人盲核，也不用于估计筛查的敏感度。',
            ],
        }).to_excel(w, sheet_name='0_说明', index=False)
        v1.to_excel(w, sheet_name='1_纳入抽样核验（100条）', index=False)
        v2.to_excel(w, sheet_name='2_排除抽样核验（50条）', index=False)

    v1.to_csv(os.path.join(ANA, '作者核验_纳入抽样100.csv'), index=False, encoding='utf-8-sig')
    v2.to_csv(os.path.join(ANA, '作者核验_排除抽样50.csv'), index=False, encoding='utf-8-sig')

    print('已生成 %s' % xp)
    print('  工作表1 纳入抽样 %d 条；其中有全文 %d 条'
          % (len(v1), (v1['全文PDF'] != '（未定位到全文）').sum()))
    print('  工作表2 排除抽样 %d 条；其中有全文 %d 条'
          % (len(v2), (v2['全文PDF'] != '（未定位到全文）').sum()))


if __name__ == '__main__':
    main()
