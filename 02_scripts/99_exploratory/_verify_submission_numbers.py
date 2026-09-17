# -*- coding: utf-8 -*-
"""Cross-verify every headline number in the submission documents against the data sources.

Whitespace-normalised, so hard-wrapped markdown cannot cause false failures.
"""
import json
import os
import re
import pandas as pd
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')
ANA = os.path.join('03_数据', '08_分析用')

S = json.load(open(os.path.join(ANA, '统计核心_v6.json'), encoding='utf-8'))
E = json.load(open(os.path.join(ANA, '补充统计_v4.json'), encoding='utf-8'))
R = json.load(open(os.path.join(ANA, 'RQ3_频次汇总.json'), encoding='utf-8'))
P = json.load(open(os.path.join(ANA, 'PRISMA_链路_v2.json'), encoding='utf-8'))
G = pd.read_csv(os.path.join('03_数据', '09_软件表', '软件类别与来源表.csv'), low_memory=False)
G.columns = ['original_name', 'canonical_name', 'category', 'development_domain',
             'developer', 'source_url', 'url_status', 'n_studies']
d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v6.csv'), low_memory=False)

FILES = ['Revised_manuscript_R2.md', 'Response_to_reviewers_R2.md', 'Declarations_R2.md',
         'Highlights_R2.md', 'Supplementary_File_1_R2.md', 'Title_Page_R2.md']


def norm(s):
    return re.sub(r'\s+', ' ', s)


DOCS = {}
for f in FILES:
    p = os.path.join(D, f)
    DOCS[f] = norm(open(p, encoding='utf-8').read()) if os.path.exists(p) else ''

N = S['N']
M, RSP, DEC, HL, SUP, TP = FILES
fail, checks = [], 0


def has(doc, text, label):
    global checks
    checks += 1
    if text not in DOCS[doc]:
        fail.append('MISSING  %-28s %s' % (doc, label))


def absent(doc, text, label):
    global checks
    checks += 1
    if text in DOCS[doc]:
        fail.append('STALE    %-28s %s' % (doc, label))


# ------------------------------------------------ core counts
has(M, '%d studies were included' % N, 'abstract N')
has(M, 'in %d journals' % S['n_journals'], 'journal count')
has(M, '%d countries' % S['n_countries'], 'country count')
has(M, 'A total of %d nondental packages' % S['n_software_packages'], 'packages (abstract)')
has(M, 'One hundred nondental packages were recorded across %s software assignments'
    % format(S['software_assignments'], ','), 'packages + assignments')
has(M, '%d studies (%.1f%%) combined more than one' % (S['n_studies_multi_software'],
                                                       S['pct_multi_software']), 'multi (abstract)')
has(M, '%d studies (%.1f%%) reported more than one package' % (S['n_studies_multi_software'],
                                                               S['pct_multi_software']),
    'multi (§3.3)')
has(M, 'and %d (%.1f%%) reported a single package' % (
    S['n_studies_single_software'], round(S['n_studies_single_software'] / N * 100, 1)), 'single')
has(M, '%s study–speciality assignments' % format(S['speciality_assignments'], ','), 'spec assign')
has(M, '%s scenario assignments' % format(S['scenario_assignments'], ','), 'scen assign')
has(M, '%s software assignments' % format(S['software_assignments'], ','), 'soft assign')
has(M, 'sum to %s assignments across %d studies'
    % (format(S['speciality_assignments'], ','), N), 'assign summed')
has(M, 'The included studies appeared in %d journals' % S['n_journals'], 'journals (§3.2)')
has(M, 'the ten most frequent journals accounted for 331 studies (38.8%)', 'top10 journals')
has(M, 'China (184 studies), Turkey (80) and the United States (67)', 'top regions')
has(M, 'rose from 28 studies in 2020-H2 to 96 in 2025-H2', 'trend endpoints')
has(M, '5.95 additional studies per half-year', 'trend slope')
has(M, '4.93 excluding', 'trend slope excl')
has(M, '810 records with a month-level date', 'trend base')
has(M, 'the remaining %d records carry only a year' % S['n_year_only'], 'year-only')

# ------------------------------------------------ design / disciplines / scenarios
has(M, '%d studies (%.1f%%) were computational' % (S['study_type']['computational'],
                                                   S['study_type_pct']['computational']),
    'design computational')
has(M, '%d (%.1f%%) were in vitro' % (S['study_type']['in_vitro'],
                                      S['study_type_pct']['in_vitro']), 'design in vitro')
has(M, '%d (%.1f%%) were clinical' % (S['study_type']['clinical'],
                                      S['study_type_pct']['clinical']), 'design clinical')
for name, key in [('Prosthodontics', 'Prosthodontics'),
                  ('oral and maxillofacial surgery', 'Oral and Maxillofacial Surgery'),
                  ('oral implantology', 'Oral Implantology'),
                  ('orthodontics', 'Orthodontics'),
                  ('oral and maxillofacial radiology', 'Oral and Maxillofacial Radiology')]:
    has(M, '%s (%d' % (name, S['speciality'][key]), 'discipline %s' % key)
SCEN = {'3D Data Analysis and Accuracy Assessment': '3D data analysis and accuracy assessment',
        'Image Segmentation and 3D Reconstruction': 'image segmentation and 3D reconstruction',
        'Biomechanical Analysis and Simulation': 'biomechanical analysis and simulation',
        'Digital Design and Manufacturing': 'digital design and manufacturing',
        'Surgical Planning and Precise Implementation': 'surgical planning and implementation',
        'Morphological and Phenotypic Analysis': 'morphological and phenotypic analysis'}
for k, lab in SCEN.items():
    has(M, '%s (%d' % (lab, S['scenario'][k]), 'scenario %s' % lab)
has(M, 'The remaining seven disciplines', 'discipline remainder')

# ------------------------------------------------ archetypes
for i in range(1, 5):
    n = S['archetype_n'][str(i)]
    has(M, '%d studies, %.1f%%' % (n, round(n / N * 100, 1)), 'archetype %d' % i)
    if i < 4:
        has(M, '(n = %d' % n, 'archetype legend %d' % i)
has(RSP, 'image segmentation and 3D reconstruction (%d; %.1f%%)'
    % (S['archetype_n']['1'], round(S['archetype_n']['1'] / N * 100, 1)), 'response archetype 1')
for k in '234':
    has(RSP, '(%d; %.1f%%)' % (S['archetype_n'][k], round(S['archetype_n'][k] / N * 100, 1)),
        'response archetype %s' % k)

# ------------------------------------------------ contingency
cf, cm = E['contingency_full'], E['contingency_merged_small_specialities']
for doc in (M, RSP):
    has(doc, 'χ² = %.1f, df = %d, p = %.2f × 10⁻⁴⁶' % (cf['chi2'], cf['dof'], cf['p'] * 1e46),
        'chi2 full')
    has(doc, "Cramér's V = %.3f" % cf['cramers_v'], 'V')
    has(doc, 'χ² = %.1f, df = %d' % (cm['chi2'], cm['dof']), 'chi2 merged')

# ------------------------------------------------ RQ3
adv = {x['code']: x for x in R['advantages']}
cha = {x['code']: x for x in R['challenges']}
gap = {x['code']: x for x in R['gaps']}
with_adv, with_cha, with_gap = N - adv['A9']['n'], N - cha['C9']['n'], N - gap['G9']['n']
has(M, '%d of the %d studies (%.1f%%)' % (with_adv, N, round(with_adv / N * 100, 1)), 'adv stated')
has(M, 'measurement precision (%d studies, %.1f%%)' % (adv['A6']['n'], adv['A6']['pct']),
    'advantage A6')
for code in ('A5', 'A3', 'A1', 'A2'):
    has(M, '%d, %.1f%%)' % (adv[code]['n'], adv[code]['pct']), 'advantage %s' % code)
has(M, '%d studies (%.1f%%) stated at least one, and the remaining %d (%.1f%%)'
    % (with_cha, round(with_cha / N * 100, 1), cha['C9']['n'], cha['C9']['pct']), 'challenges')
has(M, 'limited validation evidence dominated (%d studies, %.1f%%)'
    % (cha['C4']['n'], cha['C4']['pct']), 'challenge C4')
has(M, 'A stated gap was present in %d studies (%.1f%%)' % (with_gap, round(with_gap / N * 100, 1)),
    'gaps stated')
has(M, 'was by far the most frequent (%d studies, %.1f%%)' % (gap['G1']['n'], gap['G1']['pct']),
    'gap G1')
has(M, 'multi-centre samples (%d, %.1f%%)' % (gap['G4']['n'], gap['G4']['pct']), 'gap G4')
has(RSP, 'stated explicitly in %d studies (%.1f%%)' % (with_adv, round(with_adv / N * 100, 1)),
    'response adv stated')

# ------------------------------------------------ figure legends
has(M, 'Landscape of the included literature (n = %d)' % N, 'Fig2 n')
has(M, 'Software landscape across %d studies' % N, 'Fig3 n')
has(M, 'percentages are of all %d included studies' % N, 'Fig2 denominator')
has(M, 'the denominator is all %d included studies' % N, 'Fig6 denominator')
has(M, 'no advantage was stated by %d studies (%.1f%%), no challenge by %d (%.1f%%) and no gap by %d (%.1f%%)'
    % (adv['A9']['n'], adv['A9']['pct'], cha['C9']['n'], cha['C9']['pct'],
       gap['G9']['n'], gap['G9']['pct']), 'Fig6 non-reporting')
has(M, 'All %d included records have a recorded source' % N, 'SuppFigS1')
has(M, 'the full included set (n = %d)' % N, 'SuppFigS1 denominator')

# ------------------------------------------------ PRISMA
has(M, '%s records' % format(P['identified_total'], ','), 'PRISMA identified')
has(M, '%s were duplicates' % format(P['duplicates_removed'], ','), 'PRISMA duplicates')
has(M, 'leaving %s for screening' % format(P['screened_title_abstract'], ','), 'screened')
EB = P['exclusion_breakdown']
has(M, 'Title and abstract screening excluded 1,943 records', 'screening exclusions')
has(M, 'and %d were excluded' % P['excluded_after_fulltext_assessment'], 'PRISMA excluded')
has(M, 'four were removed from the previous set', 'PRISMA prev-set removals')
has(M, 'eight because the only named tool', 'PRISMA scope removals')
# PRISMA arithmetic must reconcile
checks += 1
brk = sum(EB.values())
if brk != P['excluded_after_fulltext_assessment']:
    fail.append('ARITH    prisma_flow                     breakdown %d != excluded %d'
                % (brk, P['excluded_after_fulltext_assessment']))
checks += 1
if P['assessed_for_eligibility_full_text'] - P['excluded_after_fulltext_assessment'] != N:
    fail.append('ARITH    prisma_flow                     assessed - excluded != N')
checks += 1
if P['screened_title_abstract'] != 1943 + 613:
    fail.append('ARITH    prisma_flow                     screened != 1943 + 613')
checks += 1
if P['identified_total'] - P['duplicates_removed'] != P['screened_title_abstract']:
    fail.append('ARITH    prisma_flow                     identified - duplicates != screened')
has(M, 'and %d were excluded' % P['excluded_after_fulltext_assessment'], 'PRISMA excluded')
has(M, 'comprises %d studies' % P['included'], 'PRISMA included')
has(RSP, 'changed from 566 to **%d studies**' % N, 'response previous set')

# ------------------------------------------------ other documents
has(DEC, 'locked dataset (n = %d)' % N, 'decl dataset size')
has(DEC, 'glossary of %d software packages' % S['n_software_packages'], 'decl glossary')
has(HL, '%d studies across 12 dental disciplines' % N, 'highlight 1')
has(HL, '%d packages were recorded; %.1f%% of studies (%d/%d)'
    % (S['n_software_packages'], S['pct_multi_software'], S['n_studies_multi_software'], N),
    'highlight 3')
has(RSP, 'a single locked analysis file (n = %d)' % N, 'response n')
has(RSP, 'to **%d studies**' % N, 'response included set')
has(RSP, 'is the included set (n = %d)' % N, 'response denominator')
has(RSP, '%s study–speciality assignments across %d studies'
    % (format(S['speciality_assignments'], ','), N), 'response assignments')
has(RSP, '%s scenario assignments' % format(S['scenario_assignments'], ','), 'response scenarios')
has(RSP, '%s software assignments' % format(S['software_assignments'], ','), 'response software')
has(RSP, 'for each of the %d software' % S['n_software_packages'], 'response SF3 packages')
has(RSP, 'Each of the %d included studies was coded' % N, 'response RQ3 n')

# ------------------------------------------------ family counts in §3.3
cat_map = dict(zip(G['canonical_name'], G['category']))


def parse(v):
    try:
        return list(eval(v)) if isinstance(v, str) else list(v or [])
    except Exception:
        return []


fam = Counter()
for v in d['_soft2']:
    for x in set(cat_map.get(y, '?') for y in set(parse(v))):
        fam[x] += 1
has(M, 'Medical image processing (%d studies)' % fam['MIP'], 'family MIP')
has(M, '3D reconstruction (%d)' % fam['RE'], 'family RE')
has(M, '3D modelling (%d)' % fam['GEN3D'], 'family GEN3D')
has(M, 'engineering simulation (%d)' % fam['SIM'], 'family SIM')
has(M, 'computer-aided design (%d)' % fam['CAD'], 'family CAD')

# ------------------------------------------------ journal-format compliance
ME = DOCS[M]
checks += 6
if '## Declaration of generative AI and AI-assisted technologies' not in ME:
    fail.append('FORMAT   manuscript                      generative-AI declaration missing')
if 'DeepSeek-V4.1-Flash' not in ME or 'deepseek-chat' not in ME:
    fail.append('FORMAT   manuscript                      model name/version not stated in Methods')
if '## References' not in ME:
    fail.append('FORMAT   manuscript                      reference list not merged')
ref_entries = re.findall(r'^\[(\d+)\]',
                         open(os.path.join(D, M), encoding='utf-8').read(), re.M)
if [int(x) for x in ref_entries] != list(range(1, len(ref_entries) + 1)):
    fail.append('FORMAT   manuscript                      reference numbering not contiguous')
if len(ref_entries) != 59:
    fail.append('FORMAT   manuscript                      expected 59 references, found %d'
                % len(ref_entries))
if '**' in ME:
    fail.append('FORMAT   manuscript                      bold markers present')
if re.search(r'[\u4e00-\u9fff]', ME):
    fail.append('FORMAT   manuscript                      Chinese characters present')
print('reference entries in manuscript:', len(ref_entries))
print()

# ------------------------------------------------ stale values
STALE = ['861', '1,075', '1,046', '1,377', '297.3', '300.8', 'One hundred and ten',
         '38.9%', '335 studies', '98 in 2025-H2', '6.02 additional', '4.99 excluding',
         '817', 'the remaining 44 records', '332 studies (38.6%)', '(439 studies)',
         'reconstruction (309)', 'modelling (226)', 'simulation (168)', 'design (133)',
         'Computational (349)', 'in vitro (239)', 'clinical studies (181)',
         '349 studies', '240 were in vitro', '514 studies', '295 studies',
         '(272 studies,', '(272; ', '(556 studies,', '(556; ', '(307; ', '(307, 35.7%)',
         '601 studies', '566 (65.7%)', '(298, 34.6%)', '(298; ', '(409 studies, 47.5%)',
         '(409; ', '(87, 10.1%)', '(87; ', '347 studies', 'gap by 260',
         '20.7%', '12.4%', '40.5%', '27.8%', '21.0%', '69.8%', '65.7%', '34.3%',
         '31.6%', '47.5%', '34.6%', '13.1%', '10.1%', '35.6%', '64.4%', '38.4%',
         '(331 studies', '(245 studies', '(n = 331', '(n = 245', '(331; ', '(245; ',
         '(178; 20.7%)', '(107; 12.4%)', '110 software']
for doc in (M, RSP, DEC, HL, SUP, TP):
    for s in STALE:
        absent(doc, s, s)

print('checks run : %d' % checks)
print('failures   : %d' % len(fail))
for f in fail:
    print('   ', f)
