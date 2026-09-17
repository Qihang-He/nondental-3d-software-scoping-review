# -*- coding: utf-8 -*-
"""Find which package disappeared from the revised glossary."""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
SWD = os.path.join('03_数据', '09_软件表')
old = pd.read_csv(os.path.join(SWD, '软件类别与来源表_backup_pre_scope.csv'), low_memory=False)
new = pd.read_csv(os.path.join(SWD, '软件类别与来源表.csv'), low_memory=False)
old.columns = new.columns = ['original_name', 'canonical_name', 'category', 'development_domain',
                             'developer', 'source_url', 'url_status', 'n_studies']
o = set(old['canonical_name'])
n = set(new['canonical_name'])
print('OLD distinct =', len(o), ' NEW distinct =', len(n))
print()
print('--- in OLD but not NEW ---')
for x in sorted(o - n):
    r = old[old['canonical_name'] == x].iloc[0]
    print('   %-26s n_studies=%s  %s' % (x, r['n_studies'], r['development_domain']))
print()
print('--- in NEW but not OLD ---')
for x in sorted(n - o):
    print('   ', x)
