# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_update_prisma_v4.py —— 同步 PRISMA 链路到最终 N=863"""
import os
import json
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
FP = os.path.join(ANA, 'PRISMA_链路_v2.json')

d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v5.csv'), low_memory=False)
N = len(d)
n_assess = 613 + 1168

ch = json.load(open(FP, encoding='utf-8'))
ch['identified'] = {'PubMed': 1727, 'Web of Science': 1695, 'IEEE Xplore': 304}
ch['identified_total'] = 3726
ch['duplicates_removed'] = 1170
ch['screened_title_abstract'] = 2556
ch['excluded_at_title_abstract'] = 1639
ch['fulltext_recheck'] = {
    'excluded_records_with_full_text_available': 1168,
    'excluded_records_without_full_text': 775,
    'records_reclassified_as_eligible': 304,
}
ch['assessed_for_eligibility_full_text'] = n_assess
ch['included'] = N
ch['excluded_after_fulltext_assessment'] = n_assess - N
ch['exclusion_breakdown'] = {
    're_assessed_records_not_eligible': 1168 - 304,
    'excluded_at_full_text_screening': 47,
    'removed_from_previous_set_no_named_software': 4,
    'outside_prespecified_date_window': 3,
    'current_audit_narrative_review_or_unsupported_software': 2,
}
ch['previous_set_removals'] = 7
ch['removals_reason'] = ('4 studies retained in the previous dataset were removed because the '
                         'archived full text contains no named third-party non-dental 3D software; '
                         '3 further studies were removed because their publication date fell '
                         'outside the prespecified window (after 30 June 2026); two additional '
                         'records were excluded during the current audit because one was a narrative '
                         'or technical review and one had no full-text support for the recorded software.')
ch['final_included'] = N
json.dump(ch, open(FP, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

print(json.dumps(ch, ensure_ascii=False, indent=2))
cb = ch['exclusion_breakdown']
print('\n核验：%d + %d + %d + %d + %d = %d ?= %d' % (
    cb['re_assessed_records_not_eligible'], cb['excluded_at_full_text_screening'],
    cb['removed_from_previous_set_no_named_software'], cb['outside_prespecified_date_window'],
    cb['current_audit_narrative_review_or_unsupported_software'],
    sum(cb.values()), ch['excluded_after_fulltext_assessment']))
print('核验：%d - %d = %d ?= %d' % (ch['assessed_for_eligibility_full_text'],
                                    ch['excluded_after_fulltext_assessment'],
                                    ch['assessed_for_eligibility_full_text'] - ch['excluded_after_fulltext_assessment'],
                                    ch['included']))
