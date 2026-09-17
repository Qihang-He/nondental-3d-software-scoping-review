# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""_tools_provenance_v4.py —— 重建数据集溯源表（v5；N=861）"""
import os
import json
import pandas as pd

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
OUT = os.path.join(ROOT, _os.path.join(_ROOTP, '02_图表附件'), 'R2_补充材料', 'Dataset_provenance_table.csv')

S = json.load(open(os.path.join(ANA, '统计核心_v6.json'), encoding='utf-8'))
P = json.load(open(os.path.join(ANA, 'PRISMA_链路_v2.json'), encoding='utf-8'))
N = S['N']

rows = [
    ('Figure 1 (PRISMA flow diagram)', 'v5 (n = %d)' % N,
     '%s records identified (PubMed 1,727; Web of Science 1,695; IEEE Xplore 304); '
     '%s duplicates removed; %s screened at title/abstract; %s excluded at that stage, of which '
     '%s had a retrievable full text and were re-assessed, %s had none; %s records assessed for '
     'eligibility at full text; %s excluded; %d included.'
     % ('{:,}'.format(P['identified_total']), '{:,}'.format(P['duplicates_removed']),
        '{:,}'.format(P['screened_title_abstract']), '{:,}'.format(P['excluded_at_title_abstract']),
        '{:,}'.format(P['fulltext_recheck']['excluded_records_with_full_text_available']),
        '{:,}'.format(P['fulltext_recheck']['excluded_records_without_full_text']),
        '{:,}'.format(P['assessed_for_eligibility_full_text']),
        '{:,}'.format(P['excluded_after_fulltext_assessment']), N)),
    ('Figure 2a (publication trend)', 'v5 (n = %d)' % N,
     '%d records with month-level dates; %d records with year only, not plotted; 2026-H1 incomplete '
     '(search closed 30 June 2026); slope %.2f studies per half-year over all periods, %.2f excluding '
     '2026-H1' % (S['trend_denominator'], S['n_year_only'],
                 json.load(open(os.path.join(ANA, '补充统计_v4.json'), encoding='utf-8'))['trend_all']['slope'],
                 json.load(open(os.path.join(ANA, '补充统计_v4.json'), encoding='utf-8'))['trend_excl_2026H1']['slope'])),
    ('Figure 2b (geographic distribution)', 'v5 (n = %d)' % N,
     '%d countries or territories; ISO-3 country codes; no missing values' % S['n_countries']),
    ('Figure 2c (study design)', 'v5 (n = %d)' % N,
     'Six mutually exclusive study designs; two repeated model-assisted coding passes, '
     'agreement 97.6%% (Cohen kappa = 0.966), reported as coding stability'),
    ('Figure 2d (dental disciplines)', 'v5 (n = %d)' % N,
     '%d study-speciality assignments across %d studies; %d studies in more than one discipline; '
     'multi-label' % (S['speciality_assignments'], N, S['n_studies_multispeciality'])),
    ('Figure 3 (software landscape)', 'v5 (n = %d)' % N,
     '%d software packages; %d software assignments; %d studies (%.1f%%) used more than one package'
     % (S['n_software_packages'], S['software_assignments'], S['n_studies_multi_software'],
        S['pct_multi_software'])),
    ('Figure 4 (workflow archetypes)', 'v5 (n = %d)' % N,
     'Unsupervised clustering of multi-hot scenario and software-family indicators; Jaccard distance; '
     'average linkage; k = 4 by silhouette (0.349); bootstrap ARI = 0.712 over 100 resamples'),
    ('Figure 5 (contingency analysis)', 'v5 (n = %d)' % N,
     'Chi-square test with adjusted standardised residuals; Cramer\u2019s V = 0.229; sensitivity '
     'analysis with merged disciplines V = 0.226; some expected cell counts below five'),
    ('Figure 6 (advantages, challenges, gaps)', 'v5 (n = %d)' % N,
     'Coded from titles and abstracts of all %d included studies against a prespecified multi-select '
     'scheme; %d studies analysed' % (N, N)),
    ('Supplementary File 1 (search strategy)', 'search conducted 30 June 2026',
     'Five conceptual blocks per database; language and date limits applied in the database fields'),
    ('Supplementary File 2 (screening and coding logs)', 'screening corpus (n = 2,556)',
     '%s title/abstract exclusions with a single assigned reason; %s included studies with outcome '
     'codes; three independent screening runs with raw JSON responses; model metadata'
     % ('{:,}'.format(P['excluded_at_title_abstract']), '{:,}'.format(N))),
    ('Supplementary File 3 (included studies and glossary)', 'v5 (n = %d)' % N,
     'Included studies with journal, year, discipline, software and design; software glossary with '
     'category and development-domain provenance; eligibility audit (47 records)'),
    ('Full-text re-assessment pass', 'excluded records, n = 1,168',
     'Every excluded record with a retrievable full text re-assessed against the same eligibility '
     'criteria by two reconciled routes (tabulated software-name matching; keyword-window extraction '
     'prioritising the methods section); %d studies met the criteria and were added; %s excluded '
     'records had no retrievable full text'
     % (P['fulltext_recheck']['records_reclassified_as_eligible'],
        '{:,}'.format(P['fulltext_recheck']['excluded_records_without_full_text']))),
    ('Reverse check and current eligibility audit', 'v4 to v5',
     'The same full-text standard applied to the previously included studies removed 4 records whose '
     'full text names no nondental package; 3 software annotations corrected; 3 further records '
    'removed because their publication date fell outside the prespecified window; I48 was removed as '
    'a narrative/technical review and Z5PYCCYC was removed because its recorded software lacked full-text support'),
    ('Eligibility audit', 'v4 to v5',
    'Current audit changes: I48 excluded by article type; Z5PYCCYC excluded because the recorded software '
    'was not supported in the full text; 88HUKGCR software list expanded with VRMesh Studio and Algor; '
    'final included set = %d' % N),
]

df = pd.DataFrame(rows, columns=['Output', 'Dataset version', 'Notes'])
df.to_csv(OUT, index=False, encoding='utf-8-sig')
print('已写出', OUT, df.shape)
print(df.to_string(max_colwidth=70))
