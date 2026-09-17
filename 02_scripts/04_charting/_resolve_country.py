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
_resolve_country.py —— 为新增记录补齐国家（ISO3）
 步骤1：Crossref 作者机构 → 国家
 步骤2：全文前 3 页机构文字 → 国家（扩充国家写法表）
 步骤3：仍未解析的，用同一模型阅读机构文字判定国家
输出：更新 03_数据/08_分析用/_add_v4.pkl 与 新增纳入_逐条溯源.csv
"""
import os
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
import pymupdf

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
PDF = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))
API_URL = 'https://api.deepseek.com/v1/chat/completions'

COUNTRY_ISO = {
    'china': 'CHN', 'taiwan': 'TWN', 'hong kong': 'HKG', 'türkiye': 'TUR', 'turkey': 'TUR',
    'united states': 'USA', 'usa': 'USA', 'u.s.a': 'USA', 'germany': 'DEU', 'india': 'IND',
    'italy': 'ITA', 'brazil': 'BRA', 'egypt': 'EGY', 'south korea': 'KOR', 'korea': 'KOR',
    'japan': 'JPN', 'spain': 'ESP', 'switzerland': 'CHE', 'thailand': 'THA',
    'netherlands': 'NLD', 'the netherlands': 'NLD', 'australia': 'AUS', 'belgium': 'BEL',
    'united kingdom': 'GBR', 'england': 'GBR', 'scotland': 'GBR', 'wales': 'GBR',
    'canada': 'CAN', 'malaysia': 'MYS', 'france': 'FRA', 'saudi arabia': 'SAU',
    'united arab emirates': 'ARE', 'iraq': 'IRQ', 'iran': 'IRN', 'poland': 'POL',
    'portugal': 'PRT', 'romania': 'ROU', 'slovenia': 'SVN', 'russia': 'RUS',
    'hungary': 'HUN', 'austria': 'AUT', 'chile': 'CHL', 'syria': 'SYR', 'lithuania': 'LTU',
    'jordan': 'JOR', 'singapore': 'SGP', 'bulgaria': 'BGR', 'algeria': 'DZA',
    'armenia': 'ARM', 'denmark': 'DNK', 'cyprus': 'CYP', 'sweden': 'SWE',
    'venezuela': 'VEN', 'tunisia': 'TUN', 'indonesia': 'IDN', 'south africa': 'ZAF',
    'nepal': 'NPL', 'qatar': 'QAT', 'serbia': 'SRB', 'colombia': 'COL', 'ireland': 'IRL',
    'greece': 'GRC', 'croatia': 'HRV', 'czech': 'CZE', 'finland': 'FIN', 'norway': 'NOR',
    'mexico': 'MEX', 'argentina': 'ARG', 'peru': 'PER', 'nigeria': 'NGA',
    'pakistan': 'PAK', 'bangladesh': 'BGD', 'israel': 'ISR', 'new zealand': 'NZL',
    'ukraine': 'UKR', 'slovakia': 'SVK', 'estonia': 'EST', 'latvia': 'LVA',
    'kuwait': 'KWT', 'lebanon': 'LBN', 'morocco': 'MAR', 'kenya': 'KEN',
    'ethiopia': 'ETH', 'sri lanka': 'LKA', 'vietnam': 'VIE', 'viet nam': 'VIE',
    'philippines': 'PHL', 'costa rica': 'CRI', 'uruguay': 'URY', 'ecuador': 'ECU',
    'iceland': 'ISL', 'luxembourg': 'LUX', 'malta': 'MLT', 'belarus': 'BLR',
    'kazakhstan': 'KAZ', 'uzbekistan': 'UZB', 'georgia': 'GEO', 'azerbaijan': 'AZE',
    'bosnia': 'BIH', 'north macedonia': 'MKD', 'albania': 'ALB', 'moldova': 'MDA',
    'cuba': 'CUB', 'panama': 'PAN', 'bolivia': 'BOL', 'paraguay': 'PRY',
    'ghana': 'GHA', 'tanzania': 'TZA', 'uganda': 'UGA', 'zimbabwe': 'ZWE',
    'cameroon': 'CMR', 'sudan': 'SDN', 'libya': 'LBY', 'yemen': 'YEM', 'oman': 'OMN',
    'bahrain': 'BHR', 'mongolia': 'MNG', 'myanmar': 'MMR', 'cambodia': 'KHM',
    'brunei': 'BRN', 'macau': 'MAC', 'macao': 'MAC', 'puerto rico': 'PRI',
    'kosovo': 'XKX', 'montenegro': 'MNE', 'monaco': 'MCO', 'bhutan': 'BTN',
    'maldives': 'MDV', 'afghanistan': 'AFG', 'senegal': 'SEN', 'ivory coast': 'CIV',
}


def pick(t):
    tl = re.sub(r'\s+', ' ', str(t)).lower()
    hits = {}
    for name, code in COUNTRY_ISO.items():
        n = len(re.findall(r'(?<![a-z])' + re.escape(name) + r'(?![a-z])', tl))
        if n:
            hits[code] = hits.get(code, 0) + n
    return max(hits, key=hits.get) if hits else None


def load_key():
    with open(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'config.local.json'),
              encoding='utf-8') as f:
        return json.load(f)['deepseek_api_key'].strip()


def llm_country(aff_text):
    prompt = ('下面是一篇期刊论文首页的作者单位信息。请判断第一作者所属国家，'
              '只输出三字母 ISO-3166-1 alpha-3 代码（如 CHN、USA、TUR），不要任何其他文字。\n\n'
              + aff_text[:2500])
    try:
        r = requests.post(API_URL,
                          headers={'Content-Type': 'application/json',
                                   'Authorization': 'Bearer ' + load_key()},
                          json={'model': 'deepseek-chat',
                                'messages': [{'role': 'user', 'content': prompt}],
                                'temperature': 0, 'max_tokens': 12, 'stream': False},
                          timeout=60)
        c = r.json()['choices'][0]['message']['content'].strip().upper()
        m = re.search(r'\b([A-Z]{3})\b', c)
        return m.group(1) if m else None
    except Exception:
        return None


add = pd.read_pickle(os.path.join(ANA, '_add_v4.pkl'))
todo = add[add['Region'].isna()].copy()
print('待补国家：%d 篇' % len(todo))

# PDF 通过 Key 从对照表取得
pm = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '07_PDF与语料对照', 'pdf_match.csv'),
                 low_memory=False)
k2f = {}
for _, r in pm.iterrows():
    k = str(r.get('Key', '')).strip()
    if k and k != 'nan' and k not in k2f:
        k2f[k] = str(r['file'])
todo['PDF'] = todo['Key'].astype(str).map(k2f)
print('其中可匹配到 PDF：%d' % int(todo['PDF'].notna().sum()))

hdr = {'User-Agent': 'ScopingReview/1.0 (mailto:author@example.org)'}
newreg, src = {}, {}
for _, r in todo.iterrows():
    iso, how = None, ''
    f = r.get('PDF')
    aff_txt = ''
    if isinstance(f, str) and f:
        p = os.path.join(PDF, f)
        if os.path.exists(p):
            try:
                doc = pymupdf.open(p)
                aff_txt = '\n'.join(pg.get_text() for pg in doc[:2])
                doc.close()
            except Exception:
                aff_txt = ''
    if aff_txt:
        iso = pick(aff_txt)
        if iso:
            how = '全文机构'
    if not iso and aff_txt:
        iso = llm_country(aff_txt)
        if iso:
            how = '模型判读机构'
    newreg[r['_nt']] = iso
    src[r['_nt']] = how
    if iso:
        print('  %-58s -> %s (%s)' % (str(r['Title'])[:56], iso, how))

add['Region'] = [newreg.get(k, v) for k, v in zip(add['_nt'], add['Region'])]
add['国家来源'] = [src.get(k, v) for k, v in zip(add['_nt'], add['国家来源'])]
add.to_pickle(os.path.join(ANA, '_add_v4.pkl'))
add.to_csv(os.path.join(ANA, '新增纳入_逐条溯源.csv'), index=False, encoding='utf-8-sig')
print('\n仍缺国家：%d' % int(add['Region'].isna().sum()))
print(add['国家来源'].value_counts().to_string())
