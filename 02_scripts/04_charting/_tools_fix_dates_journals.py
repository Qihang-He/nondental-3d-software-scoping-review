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
_tools_fix_dates_journals.py —— 修正 v4 的日期解析与期刊名规范化

问题1：新增记录的 Date 取值形如 "23-Oct"、"26-Feb"、"2026/4/30"、"2026"，
       原解析器仅识别 4 位年份与斜杠格式，导致 146 篇半年度为 unknown、并错分期间。
       修正：以 Year 字段为年份锚点，月份由月份缩写（Jan..Dec）或 YYYY/MM、YYYY-MM 解析；
             无法确定月份者标记 unknown，不计入半年度趋势。
问题2：同一期刊存在大小写变体（如 "BMC Oral Health" / "BMC ORAL HEALTH"）。
       修正：按"去符号小写"归并，展示名取出现次数最多且大小写最规范者。
"""
import os
import re
import json
from collections import Counter
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FP = os.path.join(ANA, '分析数据集_final_v4.csv')

MON = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}


def jkey(s):
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())

MON_FULL = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6, 'july': 7,
            'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'sept': 9, 'sep': 9, 'feb': 2, 'mar': 3, 'apr': 4, 'aug': 8,
            'oct': 10, 'nov': 11, 'dec': 12, 'jan': 1, 'may': 5, 'jun': 6, 'jul': 7}


def parse_month(s, year):
    s = str(s)
    if not s or s.lower() == 'nan':
        return None
    t = s.lower()
    # 1) 月份名
    for name, num in MON_FULL.items():
        if re.search(r'(?<![a-z])' + name + r'(?![a-z])', t):
            return num
    # 2) YYYY/MM 或 YYYY-MM-DD
    m = re.search(r'(?:19|20)\d{2}\s*[/\-. ]\s*(\d{1,2})(?![.\d])', t)
    if m:
        v = int(m.group(1))
        if 1 <= v <= 12:
            return v
    # 3) 纯数字且只有 4 位（如 2026）→ 无月份
    return None


def half_of(y, m):
    if y is None or (isinstance(y, float) and pd.isna(y)):
        return 'unknown'
    if m is None or (isinstance(m, float) and pd.isna(m)):
        m = None
    y = int(y)
    if y < 2020 or y > 2026:
        return 'unknown'
    if y == 2020:
        return '2020-H2'
    if m is None:
        return 'unknown'          # 仅有年份者一律不计入半年度趋势
    return '%d-H%d' % (y, 1 if int(m) <= 6 else 2)


d = pd.read_csv(FP, low_memory=False)

# ---- 年份锚点：优先 Year 字段，其次 Date 中的 4 位年份 ----
def year_of(r):
    y = r.get('Year')
    if pd.notna(y):
        try:
            y = int(y)
            if 1900 < y < 2100:
                return y
        except Exception:
            pass
    m = re.search(r'(19|20)\d{2}', str(r.get('Date', '')))
    return int(m.group(0)) if m else None


d['_year'] = d.apply(year_of, axis=1)
d['_month'] = [parse_month(r.get('Date'), r.get('_year')) for _, r in d.iterrows()]
d['Half2'] = [half_of(y, m) for y, m in zip(d['_year'], d['_month'])]

print('修正后 Half2 分布：')
print(d['Half2'].value_counts().to_string())
print('\n仅年份（未纳入趋势）：%d ；有月份：%d' %
      (int((d['Half2'] == 'unknown').sum()), int((d['Half2'] != 'unknown').sum())))
print('\n按来源：')
print(d.groupby('_来源')['Half2'].value_counts().unstack(fill_value=0).to_string())

# ---- 期刊名规范化（缩写↔全称）----
corpus = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                  '筛选语料_唯一记录_2556.csv'), low_memory=False)
p2a, a2p = {}, {}
for _, r in corpus.iterrows():
    t = str(r.get('Publication Title', '') or '').strip()
    a = str(r.get('Journal Abbreviation', '') or '').strip()
    if t and a and a.lower() != 'nan':
        p2a.setdefault(jkey(t), a)
        a2p.setdefault(jkey(a), t)


def norm_journal(x):
    x = str(x).strip()
    k = jkey(x)
    if k in p2a:
        return p2a[k]
    if k in a2p:
        return x
    return x


jc = Counter(d['Journal'].astype(str))
groups = {}
for name, n in jc.items():
    groups.setdefault(jkey(name), []).append((name, n))
best = {}
for k, v in groups.items():
    v = sorted(v, key=lambda x: (-x[1], not re.match(r'^[A-Z][a-z]', x[0])))
    best[k] = v[0][0]
d['Journal'] = d['Journal'].map(lambda x: best.get(jkey(x), x)).map(norm_journal)
print('\n规范后不同期刊名：%d（原 %d）' % (d['Journal'].nunique(), len(jc)))
print('Top 12：')
for k, n in Counter(d['Journal']).most_common(12):
    print('   %-42s %d' % (k[:40], n))

d.to_csv(FP, index=False, encoding='utf-8-sig')
print('\n已写回', FP)
