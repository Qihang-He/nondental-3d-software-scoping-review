# -*- coding: utf-8 -*-
"""Pin down the full-text availability figures for the revised (v6) included set."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
ANA = os.path.join('03_数据', '08_分析用')
OUT = os.path.join('04_代码', '07_文档', '_tmp_fulltext.txt')

a = pd.read_csv(os.path.join('人工核验包', '无全文记录_摘要证据审计.csv'), low_memory=False)
d6 = pd.read_csv(os.path.join(ANA, '分析数据集_final_v6.csv'), low_memory=False)
log = pd.read_csv(os.path.join(ANA, '软件口径复核_修订记录.csv'), low_memory=False)

L = []
removed = set(log.loc[log['action'] == 'RECORD REMOVED', 'record_key'].astype(str))
L.append('scope-removed records: %d' % len(removed))

aud = a.copy()
aud['Key'] = aud['Key'].astype(str)
in_audit = aud[aud['Key'].isin(removed)]
L.append('')
L.append('=== scope-removed records that appear in the no-full-text audit ===')
for _, r in in_audit.iterrows():
    L.append('   %-10s status=%s' % (r['Key'], r['摘要状态']))
L.append('   --> %d of the 8 were in the audit list' % len(in_audit))

# the audit list after the scope revision
still = aud[aud['Key'].isin(set(d6['Key'].astype(str)))]
L.append('')
L.append('audit rows still in v6            : %d' % len(still))
L.append('  no abstract software evidence   : %d'
         % (still['摘要状态'] == '无摘要软件证据；无法全文核验').sum())
L.append('  abstract names software and use : %d'
         % (still['摘要状态'] == '摘要明确提及软件及其研究用途；可保留但标记“无全文”').sum())

# records known to have a full text even though they sit in the audit list
KNOWN_FT = {'Z5PYCCYC'}
n_no_ft = len(still) - len(KNOWN_FT & set(still['Key']))
L.append('')
L.append('records with a known full text inside the audit list: %s'
         % sorted(KNOWN_FT & set(still['Key'])))
L.append('=> records without a retrievable full text (v6) : %d' % n_no_ft)
L.append('=> records with a retrievable full text (v6)    : %d of %d (%.1f%%)'
         % (len(d6) - n_no_ft, len(d6), (len(d6) - n_no_ft) / len(d6) * 100))

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print('written', OUT)
