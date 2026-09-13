# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_tools_check_ms.py —— 正文一致性检查：摘要字数、占位符、旧数字残留、图-表-文数字一致性"""
import os
import re
import json

ROOT = _ROOTP
fp = os.path.join(ROOT, '01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
txt = open(fp, encoding='utf-8').read()

# ---- 摘要字数 ----
m = re.search(r'## Abstract(.*?)\n---', txt, re.S)
abs_txt = m.group(1)
words = re.findall(r"[A-Za-z][A-Za-z'\-]*", abs_txt)
print('摘要词数（含小标题）:', len(words))

# ---- 占位符 ----
ph = re.findall(r'«[^»]+»', txt)
print('剩余占位符:', ph)

# ---- 旧数字残留 ----
bad = {
    '569': r'\b569\b', '572': r'\b572\b', '613': r'\b613\b', '2,540': r'2,540',
    '184 journals': r'184 journals', '185 journals': r'185 journals',
    'Fleiss 0.936 ok': r'κ = 0.936',
    '306.4': r'306\.4', 'Cramér 0.203': r'0\.203', '791': r'\b791\b', '758': r'\b758\b',
    '920': r'\b920\b', '39.4': r'39\.4', '1,747': r'1,747', '1,017': r'1,017',
    '2.23': r'2\.23', '202 studies': r'202 studies',
}
print('\n可疑旧数字:')
for k, pat in bad.items():
    hits = re.findall(pat, txt)
    if hits:
        print('  !!', k, '命中', len(hits), '次')

# ---- 关键新数字是否出现 ----
must = ['566', '2,556', '1,943', '3,631', '1,075', '224', '39.6', '216.2', '0.229',
        '2.17', '2.96', '85', '917', '783', '755', '188', '51']
print('\n关键新数字缺失检查:')
for k in must:
    if k not in txt:
        print('  !! 缺少', k)

S = json.load(open(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用', '统计核心.json'),
                   encoding='utf-8'))
print('\n统计核心复核: N=%s 期刊=%s 软件=%s 多软件=%s(%s%%) 专科赋值=%s 场景赋值=%s'
      % (S['N'], S['n_journals'], S['n_software_packages'], S['n_studies_multi_software'],
         S['pct_multi_software'], S['speciality_assignments'], S['scenario_assignments']))
