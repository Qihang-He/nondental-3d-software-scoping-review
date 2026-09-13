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
_tools_prisma_v2.py —— 生成修正后的 PRISMA 链路（含全文再筛查步骤）

修正点：
  1) "识别记录数"改为可从留痕导出文件复现的数字：PubMed 1,727 + WoS 1,695 + IEEE 304 = 3,726
  2) 新增"对筛查阶段被排除记录做全文再核查"这一步骤，并给出由此补入的研究数
  3) 排除原因在补入后重新计算
输出：03_数据/08_分析用/PRISMA_链路_v2.json
"""
import os
import json
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FULLTEXT = os.path.join(ROOT, _os.path.join(_ROOTP, '10_全文PDF库'))

# --- 识别数（可由 11_检索策略 的导出文件复现）---
IDENT = {'PubMed': 1727, 'Web of Science': 1695, 'IEEE Xplore': 304}
TOTAL_IDENT = sum(IDENT.values())

rz = pd.read_csv(os.path.join(ANA, 'prisma_pass', 'reason_parsed.csv'),
                 low_memory=False).drop_duplicates('_nt')
n_excluded_ta = len(rz)

ft = pd.read_csv(os.path.join(ANA, 'fulltext_pass', 'fulltext_parsed.csv'),
                 low_memory=False)
ft = ft.drop_duplicates('_nt')
n_ft = len(ft)
n_new = int(ft['判定'].astype(str).str.upper().str.startswith('INCLUDE').sum())

newfp = os.path.join(ANA, '最终新增纳入.csv')
if os.path.exists(newfp):
    n_new = len(pd.read_csv(newfp, low_memory=False).drop_duplicates('_nt'))
    print('以最终裁决结果为准，新增纳入 = %d' % n_new)

v4 = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)
n_prev = len(v4) - n_new
N = len(v4)

SCREENED = 2556
# 补入后，筛查阶段排除数减少
excl_ta = n_excluded_ta - n_new
# 未能获取全文、无法用全文核验的被排除记录
no_ft = n_excluded_ta - n_ft

chain = {
    'identified': IDENT,
    'identified_total': TOTAL_IDENT,
    'duplicates_removed': TOTAL_IDENT - SCREENED,
    'screened_title_abstract': SCREENED,
    'excluded_at_title_abstract': excl_ta,
    'fulltext_recheck': {
        'excluded_records_with_full_text_available': n_ft,
        'excluded_records_without_full_text': no_ft,
        'records_reclassified_as_eligible': n_new,
    },
    'assessed_for_eligibility_full_text': (n_prev + 47) + n_ft,
    'excluded_after_fulltext_assessment': (n_prev + 47 + n_ft) - N,
    'included': N,
    'v3_to_v4_removals': 4,
    'removals_reason': ('4 studies retained in the previous dataset were removed because the archived '
                        'full text contains no named third-party non-dental 3D software'),
    'note': ('Title/abstract screening applied the topic, article-type, language and date '
             'criteria; because the software criterion cannot be evaluated reliably at '
             'abstract level, every excluded record for which a full text could be obtained '
             'was re-assessed at full text and %d additional eligible studies were identified.'
             % n_new),
}
json.dump(chain, open(os.path.join(ANA, 'PRISMA_链路_v2.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print(json.dumps(chain, ensure_ascii=False, indent=2))
