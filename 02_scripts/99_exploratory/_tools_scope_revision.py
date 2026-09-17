# -*- coding: utf-8 -*-
"""
Scope revision v5 -> v6: enforce the review's nondental-3D-software definition
on the software list, and re-derive the included set accordingly.

Removed packages (fail the definition):
  Not "3D software" — general programming / numerical-computing / ML platforms:
      MATLAB, Python, GNU Octave, TensorFlow, Keras
  Not software packages — programming libraries:
      Open3D, Trimesh, Iso2mesh
  Dental origin (criterion 1 fails) — confirmed from full text:
      R2 Gate   (MegaGen implant planning software, dental-specific)
      Viewbox   (dHAL, cephalometric analysis = orthodontic/dental-specific)

Retained after full-text verification (previously flagged as suspicious):
  CreatWare   -> CreatWare v6.4.6 (CreatBot, Zhengzhou, China): print-preparation GUI software
  Midas       -> Midas FX+ (Brunleys, MK, UK): 2D/3D engineering CAD/CAE
  Scalismo Lab-> statistical shape-modelling software program (Univ. of Basel)

Outputs (nothing is overwritten without a backup):
  03_数据/08_分析用/分析数据集_final_v5_backup_pre_scope.csv   (backup)
  03_数据/08_分析用/分析数据集_final_v6.csv                    (revised locked set)
  03_数据/09_软件表/软件类别与来源表_backup_pre_scope.csv      (backup)
  03_数据/09_软件表/软件类别与来源表.csv                       (revised glossary, in place)
  03_数据/08_分析用/软件口径复核_修订记录.csv                  (per-record revision log)
"""
import os
import shutil
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
ANA = os.path.join('03_数据', '08_分析用')
SWD = os.path.join('03_数据', '09_软件表')

SRC = os.path.join(ANA, '分析数据集_final_v5.csv')
DST = os.path.join(ANA, '分析数据集_final_v6.csv')
BAK = os.path.join(ANA, '分析数据集_final_v5_backup_pre_scope.csv')
SWT = os.path.join(SWD, '软件类别与来源表.csv')
SWT_BAK = os.path.join(SWD, '软件类别与来源表_backup_pre_scope.csv')
LOG = os.path.join(ANA, '软件口径复核_修订记录.csv')

EXCL = {'MATLAB', 'Python', 'GNU Octave', 'TensorFlow', 'Keras',
        'Open3D', 'Trimesh', 'Iso2mesh', 'R2 Gate', 'Viewbox'}

REASON = {
    'MATLAB': 'Not a 3D software package: general numerical-computing platform',
    'Python': 'Not a 3D software package: general-purpose programming language',
    'GNU Octave': 'Not a 3D software package: general numerical-computing platform',
    'TensorFlow': 'Not a 3D software package: machine-learning framework',
    'Keras': 'Not a 3D software package: machine-learning framework',
    'Open3D': 'Not a software package: 3D programming library',
    'Trimesh': 'Not a software package: mesh-processing programming library',
    'Iso2mesh': 'Not a software package: mesh-generation programming library',
    'R2 Gate': 'Fails origin criterion: dental implant-planning software (MegaGen Implant)',
    'Viewbox': 'Fails origin criterion: cephalometric (orthodontic) analysis software (dHAL)',
}

# ---------------------------------------------------------------- dataset
if not os.path.exists(BAK):
    shutil.copy2(SRC, BAK)
    print('backup created:', BAK)

d = pd.read_csv(SRC, low_memory=False)


def parse(v):
    try:
        return list(eval(v)) if isinstance(v, str) else list(v or [])
    except Exception:
        return []


kept_rows, log_rows = [], []
for idx, r in d.iterrows():
    raw = parse(r['_soft2'])
    new = [s for s in raw if s not in EXCL]
    dropped = [s for s in raw if s in EXCL]
    if dropped:
        log_rows.append({
            'record_id': r.get('序号'),
            'record_key': r['Key'],
            'title': r['Title'],
            'software_before': ';'.join(raw),
            'software_after': ';'.join(new),
            'dropped_packages': ';'.join(dropped),
            'drop_reason': ' | '.join('%s: %s' % (s, REASON[s]) for s in dropped),
            'action': 'RECORD REMOVED' if not new else 'software list adjusted',
        })
    if not new:
        continue
    r = r.copy()
    r['_soft2'] = str(new)
    r['_soft'] = str([s for s in parse(r['_soft']) if s not in EXCL])
    r['Software Used (fixed)'] = ';'.join(new)
    kept_rows.append(r)

d6 = pd.DataFrame(kept_rows).reset_index(drop=True)

# canonical rename verified from full text: "Midas FX+ (Brunleys, MK, UK)" was
# named only as "Midas" in the annotation.
for _c in ['_soft2', 'Software Used (fixed)']:
    d6[_c] = d6[_c].astype(str).str.replace('Midas', 'Midas FX+', regex=False)

if '序号' in d6.columns:
    d6['序号'] = range(1, len(d6) + 1)
d6.to_csv(DST, index=False, encoding='utf-8-sig')

log = pd.DataFrame(log_rows)
log.to_csv(LOG, index=False, encoding='utf-8-sig')

print('v5 rows =', len(d), '-> v6 rows =', len(d6))
print('records removed =', len(d) - len(d6))
print('records with adjusted software list =', len(log) - (len(d) - len(d6)))

# ---------------------------------------------------------------- glossary
# make the step re-entrant: always rebuild from the pre-revision snapshot
if not os.path.exists(SWT_BAK):
    shutil.copy2(SWT, SWT_BAK)
    print('backup created:', SWT_BAK)
else:
    shutil.copy2(SWT_BAK, SWT)
    print('glossary restored from backup before revision')

g = pd.read_csv(SWT, low_memory=False)
g.columns = ['original_name', 'canonical_name', 'category', 'development_domain',
             'developer', 'source_url', 'url_status', 'n_studies']

# 1) drop packages that fail the definition
g = g[~g['canonical_name'].isin(EXCL)].copy()
# 2) drop exact duplicate rows
before = len(g)
g = g.drop_duplicates(subset=['original_name', 'canonical_name', 'category',
                              'development_domain', 'developer'], keep='first')
print('duplicate rows dropped =', before - len(g))

# 3) metadata corrections verified from full text (must run BEFORE the unused-entry filter)
def fix(name, **kw):
    m = g['canonical_name'] == name
    for k, v in kw.items():
        g.loc[m, k] = v


fix('Midas',
    original_name='Midas FX+', canonical_name='Midas FX+', category='CAD',
    development_domain='Engineering CAD/CAE (2D/3D design and analysis)',
    developer='Brunleys (Milton Keynes, UK)',
    source_url='https://doi.org/10.3390/jpm11090932',
    url_status='OK (verified in citing full text)')
fix('CreatWare',
    category='AM', development_domain='3D printing print-preparation (slicer)',
    developer='CreatBot (Zhengzhou, China)',
    source_url='https://doi.org/10.3390/ma15196890',
    url_status='OK (verified in citing full text)')

# 4) drop entries with no study in the revised locked set
before = len(g)
g = g[g['canonical_name'].isin(set([s for v in d6['_soft2'] for s in parse(v)]))].copy()
print('zero-study phantom rows dropped =', before - len(g))

# 5) recompute study counts from the revised locked dataset
from collections import Counter
cnt = Counter()
for v in d6['_soft2']:
    for s in set(parse(v)):
        cnt[s] += 1
g['n_studies'] = g['canonical_name'].map(lambda x: cnt.get(x, 0))
g = g[g['n_studies'] > 0].sort_values(['category', 'n_studies'],
                                      ascending=[True, False]).reset_index(drop=True)

# the workspace glossary keeps its Chinese headers; only the public repository copy
# is renamed to English (handled by the repository builder).
CN_COLS = ['原始名称', '规范名称', '类别', '原始开发领域', '开发商', '来源URL', 'URL状态', '研究数']
g.columns = CN_COLS
g.to_csv(SWT, index=False, encoding='utf-8-sig')

print('glossary rows (incl. alias rows) =', len(g))
print('distinct packages =', g['规范名称'].nunique())
print('assignments =', sum(cnt.values()))
print('DONE')
