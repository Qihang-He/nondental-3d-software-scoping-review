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
_build_v4.py —— 构建修正后的纳入集 v4（在 v3 基础上补入全文再筛查确认合格的研究）

步骤：
 1. 读入全文再筛查 INCLUDE 记录
 2. 从规范语料补齐题录元数据（DOI/期刊/日期/作者）
 3. 补齐国家（Crossref 作者机构 → ISO3；失败则由全文首页机构名解析）
 4. 统一专科 / 应用场景 / 研究设计 / 软件名 的取值口径（与 v3 完全一致）
 5. 生成 分析数据集_final_v4.csv（N = 566 + 新增）
输出：03_数据/08_分析用/分析数据集_final_v4.csv
      03_数据/08_分析用/新增纳入_逐条溯源.csv
"""
import os
import re
import json
import time
import unicodedata
import difflib
from collections import Counter
import numpy as np
import pandas as pd
import requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
PDF = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))

SPEC12 = ['Prosthodontics', 'Oral and Maxillofacial Surgery', 'Oral Implantology',
          'Orthodontics', 'Oral and Maxillofacial Radiology', 'Endodontics',
          'Forensic Odontology', 'Periodontics', 'Oral Biology', 'Dental Education',
          'Temporomandibular Joint Disorders', 'Dental Sleep Medicine']
SCEN6 = ['Image Segmentation and 3D Reconstruction',
         '3D Data Analysis and Accuracy Assessment',
         'Biomechanical Analysis and Simulation',
         'Digital Design and Manufacturing',
         'Surgical Planning and Precise Implementation',
         'Morphological and Phenotypic Analysis']
STYPE = ['computational', 'in_vitro', 'clinical', 'technical_note', 'case_report',
         'educational']

SPEC_ALIAS = {
    'implantology': 'Oral Implantology', 'oral implantology': 'Oral Implantology',
    'oral surgery': 'Oral and Maxillofacial Surgery', 'omfs': 'Oral and Maxillofacial Surgery',
    'maxillofacial surgery': 'Oral and Maxillofacial Surgery',
    'oral and maxillofacial surgery': 'Oral and Maxillofacial Surgery',
    'prosthodontics': 'Prosthodontics', 'orthodontics': 'Orthodontics',
    'endodontics': 'Endodontics', 'periodontology': 'Periodontics',
    'periodontics': 'Periodontics', 'radiology': 'Oral and Maxillofacial Radiology',
    'oral and maxillofacial radiology': 'Oral and Maxillofacial Radiology',
    'forensic odontology': 'Forensic Odontology', 'oral biology': 'Oral Biology',
    'dental education': 'Dental Education', 'education': 'Dental Education',
    'temporomandibular disorders': 'Temporomandibular Joint Disorders',
    'temporomandibular joint disorders': 'Temporomandibular Joint Disorders',
    'tmj': 'Temporomandibular Joint Disorders',
    'dental sleep medicine': 'Dental Sleep Medicine', 'sleep medicine': 'Dental Sleep Medicine',
    'oral medicine': 'Oral Biology', 'oral pathology': 'Oral Biology',
    'pediatric dentistry': 'Prosthodontics', 'paediatric dentistry': 'Prosthodontics',
    'restorative dentistry': 'Prosthodontics', 'general dentistry': 'Prosthodontics',
    'implant dentistry': 'Oral Implantology', 'dental implantology': 'Oral Implantology',
    'oral oncology': 'Oral Biology', 'oral cancer': 'Oral Biology',
    'oral rehabilitation': 'Prosthodontics',
    'dentistry': 'Prosthodontics', 'dental': 'Prosthodontics',
}
SCEN_ALIAS = {
    'image segmentation and 3d reconstruction': SCEN6[0],
    'image segmentation': SCEN6[0], 'segmentation': SCEN6[0],
    '3d reconstruction': SCEN6[0], 'image segmentation and reconstruction': SCEN6[0],
    '3d data analysis and accuracy assessment': SCEN6[1],
    'accuracy assessment': SCEN6[1], '3d data analysis': SCEN6[1],
    'dimensional accuracy': SCEN6[1], 'metrology': SCEN6[1],
    'biomechanical analysis and simulation': SCEN6[2],
    'biomechanical analysis': SCEN6[2], 'finite element analysis': SCEN6[2],
    'simulation': SCEN6[2], 'biomechanics': SCEN6[2],
    'digital design and manufacturing': SCEN6[3],
    'digital design': SCEN6[3], 'cad/cam': SCEN6[3], 'design': SCEN6[3],
    'surgical planning and precise implementation': SCEN6[4],
    'surgical planning': SCEN6[4], 'surgery': SCEN6[4],
    'morphological and phenotypic analysis': SCEN6[5],
    'morphology': SCEN6[5], 'morphometric analysis': SCEN6[5],
    'morphological analysis': SCEN6[5], 'morphometry': SCEN6[5],
}


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


def canon(value, aliases, vocab, cutoff=0.72):
    if value is None or str(value).strip() in ('', '-', 'nan'):
        return None
    v = str(value).strip()
    k = re.sub(r'\s+', ' ', v.lower())
    if k in aliases:
        return aliases[k]
    for prefix, target in aliases.items():
        if len(prefix) >= 5 and prefix in k:
            return target
    m = difflib.get_close_matches(k, [x.lower() for x in vocab], n=1, cutoff=cutoff)
    if m:
        return vocab[[x.lower() for x in vocab].index(m[0])]
    return None


COUNTRY_ISO = {
    'china': 'CHN', 'türkiye': 'TUR', 'turkey': 'TUR', 'united states': 'USA',
    'usa': 'USA', 'germany': 'DEU', 'india': 'IND', 'italy': 'ITA', 'brazil': 'BRA',
    'egypt': 'EGY', 'south korea': 'KOR', 'korea': 'KOR', 'japan': 'JPN', 'spain': 'ESP',
    'switzerland': 'CHE', 'thailand': 'THA', 'netherlands': 'NLD', 'australia': 'AUS',
    'belgium': 'BEL', 'united kingdom': 'GBR', 'canada': 'CAN', 'malaysia': 'MYS',
    'france': 'FRA', 'saudi arabia': 'SAU', 'united arab emirates': 'ARE', 'iraq': 'IRQ',
    'iran': 'IRN', 'poland': 'POL', 'portugal': 'PRT', 'romania': 'ROU', 'slovenia': 'SVN',
    'russia': 'RUS', 'hong kong': 'HKG', 'hungary': 'HUN', 'austria': 'AUT', 'chile': 'CHL',
    'syria': 'SYR', 'lithuania': 'LTU', 'jordan': 'JOR', 'singapore': 'SGP',
    'bulgaria': 'BGR', 'algeria': 'DZA', 'armenia': 'ARM', 'denmark': 'DNK', 'cyprus': 'CYP',
    'sweden': 'SWE', 'venezuela': 'VEN', 'tunisia': 'TUN', 'indonesia': 'IDN',
    'south africa': 'ZAF', 'nepal': 'NPL', 'qatar': 'QAT', 'serbia': 'SRB', 'colombia': 'COL',
    'ireland': 'IRL', 'greece': 'GRC', 'croatia': 'HRV', 'czech': 'CZE', 'finland': 'FIN',
    'norway': 'NOR', 'mexico': 'MEX', 'argentina': 'ARG', 'peru': 'PER', 'nigeria': 'NGA',
    'pakistan': 'PAK', 'bangladesh': 'BGD', 'taiwan': 'TWN', 'israel': 'ISR',
    'new zealand': 'NZL', 'ukraine': 'UKR', 'slovakia': 'SVK', 'estonia': 'EST',
    'latvia': 'LVA', 'kuwait': 'KWT', 'lebanon': 'LBN', 'morocco': 'MAR', 'kenya': 'KEN',
    'ethiopia': 'ETH', 'sri lanka': 'LKA', 'vietnam': 'VNM', 'philippines': 'PHL',
    'costa rica': 'CRI', 'uruguay': 'URY', 'ecuador': 'ECU', 'iceland': 'ISL',
    'luxembourg': 'LUX', 'malta': 'MLT', 'cyprus': 'CYP',
}


def country_from_text(t, iso):
    """在文本中查找国家名 → ISO3（仅用于新增记录的国家归属）"""
    tl = re.sub(r'\s+', ' ', str(t)).lower()
    hits = Counter()
    for name, code in iso.items():
        if name in ('usa', 'korea', 'turkey'):
            continue
        if code in ('USA', 'KOR', 'TUR'):
            continue
        c = tl.count(name)
        if c:
            hits[code] += c
    for name, code in (('usa', 'USA'), ('united states', 'USA'), ('korea', 'KOR'),
                       ('turkey', 'TUR'), ('türkiye', 'TUR')):
        c = tl.count(name)
        if c:
            hits[code] += c
    return hits.most_common(1)[0][0] if hits else None


def main():
    new_fp = os.path.join(ANA, '最终新增纳入.csv')
    new = pd.read_csv(new_fp, low_memory=False)
    new = new[new['判定'].str.upper().str.startswith('INCLUDE')].copy()
    new['_nt'] = new['Title'].map(nt)
    print('全文再筛查 INCLUDE：%d 条' % len(new))

    corpus = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                      '筛选语料_唯一记录_2556.csv'), low_memory=False)
    corpus['_nt'] = corpus['Title'].map(nt)
    cm = corpus.drop_duplicates('_nt').set_index('_nt')[
        ['Key', 'DOI', 'Publication Title', 'Date', 'Publication Year', 'Item Type',
         'Author', 'Abstract', 'Language']].to_dict('index')

    v3 = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
    v3['_nt'] = v3['Title'].map(nt)
    # 剔除经归一化全文核查确认"全文中无任何具名非牙科3D软件"的 4 篇
    rev_fp = os.path.join(ANA, '最终纳入集修订记录.csv')
    if os.path.exists(rev_fp):
        rev = pd.read_csv(rev_fp, low_memory=False)
        drop_nt = {nt(t) for t in rev.loc[rev['action'] == 'REMOVED', 'Title']}
        before = len(v3)
        v3 = v3[~v3['_nt'].isin(drop_nt)]
        print('按修订记录剔除 %d 篇（%d -> %d）' % (before - len(v3), before, len(v3)))
    already = set(v3['_nt'])
    v3.to_pickle(os.path.join(ANA, '_base_v4.pkl'))
    print('基准集（已剔除不合格项）: %d 篇' % len(v3))
    new = new[~new['_nt'].isin(already)]
    print('去除已在 v3 中的：剩 %d 条' % len(new))

    # ---- 国家：Crossref 作者机构 ----
    hdr = {'User-Agent': 'ScopingReview/1.0 (mailto:author@example.org)'}
    regions, srcs = {}, {}
    import pymupdf
    for _, r in new.iterrows():
        m = cm.get(r['_nt'], {})
        doi = str(m.get('DOI', '') or '').strip()
        iso = None
        if doi and doi.lower() != 'nan':
            try:
                j = requests.get('https://api.crossref.org/works/%s' % doi,
                                 headers=hdr, timeout=30).json()
                affs = []
                for a in j.get('message', {}).get('author', []) or []:
                    for af in a.get('affiliation', []) or []:
                        affs.append(af.get('name', ''))
                iso = country_from_text(' '.join(affs), COUNTRY_ISO)
                if iso:
                    srcs[r['_nt']] = 'Crossref'
            except Exception:
                pass
        if not iso and isinstance(r.get('PDF'), str):
            p = os.path.join(PDF, r['PDF'])
            if os.path.exists(p):
                try:
                    doc = pymupdf.open(p)
                    t = doc[0].get_text()
                    doc.close()
                    iso = country_from_text(t, COUNTRY_ISO)
                    if iso:
                        srcs[r['_nt']] = 'PDF首页'
                except Exception:
                    pass
        regions[r['_nt']] = iso
        time.sleep(0.15)
    print('国家解析成功：%d / %d' % (sum(1 for v in regions.values() if v), len(new)))

    rows = []
    for _, r in new.iterrows():
        m = cm.get(r['_nt'], {})
        sp = canon(r.get('专科'), SPEC_ALIAS, SPEC12) or 'Prosthodontics'
        sc = canon(r.get('应用场景'), SCEN_ALIAS, SCEN6) or SCEN6[1]
        st = canon(r.get('研究设计'), {}, STYPE) or 'in_vitro'
        sw = ';'.join(x.strip() for x in str(r.get('软件', '')).split(';') if x.strip()
                      and x.strip() != '-')
        rows.append({
            'Title': r['Title'], '_nt': r['_nt'], 'Key': m.get('Key'),
            'DOI': m.get('DOI'), 'Journal': m.get('Publication Title'),
            'Item Type': m.get('Item Type'), 'Date': m.get('Date'),
            'Year': m.get('Publication Year'),
            'Dental Specialty': sp, 'Software Used (fixed)': sw,
            'Application Scenario': sc, 'Region': regions.get(r['_nt']),
            'study_type': st, '判定理由': r.get('证据'),
            '国家来源': srcs.get(r['_nt'], '未解析'),
        })
    add = pd.DataFrame(rows)
    add.to_csv(os.path.join(ANA, '新增纳入_逐条溯源.csv'), index=False,
               encoding='utf-8-sig')
    add.to_pickle(os.path.join(ANA, '_add_v4.pkl'))
    print('\n新增记录 %d 条已暂存' % len(add))
    print('专科分布:', add['Dental Specialty'].value_counts().to_dict())
    print('研究设计:', add['study_type'].value_counts().to_dict())
    print('国家未解析:', int(add['Region'].isna().sum()))


if __name__ == '__main__':
    main()
