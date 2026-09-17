# -*- coding: utf-8 -*-
"""Record the software-scope exclusion stage in the PRISMA chain (861 -> 853)."""
import os
import json
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
ANA = os.path.join('03_数据', '08_分析用')
P = os.path.join(ANA, 'PRISMA_链路_v2.json')
BAK = os.path.join(ANA, 'PRISMA_链路_v2_backup_pre_scope.json')

if not os.path.exists(BAK):
    shutil.copy2(P, BAK)
    print('backup created:', BAK)

d = json.load(open(P, encoding='utf-8'))

REMOVED = 8
d['included'] = 853
d['final_included'] = 853
d['excluded_after_fulltext_assessment'] = d['excluded_after_fulltext_assessment'] + REMOVED
d['previous_set_removals'] = d['previous_set_removals'] + REMOVED
d['exclusion_breakdown']['software_scope_not_a_nondental_3d_package'] = REMOVED
d['removals_reason'] = (
    d['removals_reason'] +
    ' A final software-scope audit applied the definition of nondental 3D software literally: '
    'eight further studies were removed because the only named tool was a general-purpose '
    'programming, numerical-computing or machine-learning platform (MATLAB, Python, GNU Octave, '
    'TensorFlow, Keras) used to implement a custom in-house algorithm, which is not a third-party '
    '3D software package and which the eligibility criterion explicitly does not accept.'
)
d['software_scope_note'] = (
    'Ten entries were removed from the software list because they failed the definition: MATLAB, '
    'Python, GNU Octave, TensorFlow and Keras (not 3D software packages), Open3D, Trimesh and '
    'Iso2mesh (programming libraries rather than software packages), and R2 Gate and Viewbox '
    '(developed specifically for dentistry). CreatWare, Midas FX+ and Scalismo Lab were retained '
    'after full-text verification confirmed their nondental origin.'
)

assert d['assessed_for_eligibility_full_text'] - d['excluded_after_fulltext_assessment'] == 853, \
    'PRISMA arithmetic does not reconcile to N = 853'

json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('included =', d['included'])
print('excluded_after_fulltext =', d['excluded_after_fulltext_assessment'])
print('reconciles to N =',
      d['assessed_for_eligibility_full_text'] - d['excluded_after_fulltext_assessment'])
