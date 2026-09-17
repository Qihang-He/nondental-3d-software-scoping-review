# -*- coding: utf-8 -*-
"""Finalise the submission documents for the Journal of Dentistry.

A. manuscript: name the model in the Methods, append the mandatory generative-AI declaration and
   merge the reference list into the manuscript file
B. declarations and Supplementary File 1: remove revision markers
C. response letter: correct the trend slope, the regulatory reference numbers and the awkward
   section references produced by the earlier mechanical substitution, and record the renumbering
D. references: fix punctuation and HTML entities
E. create the cover letter
"""
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')
MS = os.path.join(D, 'Revised_manuscript_R2.md')
REF = os.path.join(D, 'References_R2.md')
DEC = os.path.join(D, 'Declarations_R2.md')
SUP = os.path.join(D, 'Supplementary_File_1_R2.md')
RSP = os.path.join(D, 'Response_to_reviewers_R2.md')

report = []


def sub(path, pairs, label):
    s = open(path, encoding='utf-8').read()
    missed = []
    for old, new in pairs:
        pat = re.compile(r'\s+'.join(re.escape(w) for w in old.split()))
        if pat.search(s):
            s = pat.sub(lambda _m: new, s, count=1)
        else:
            missed.append(old[:70])
    open(path, 'w', encoding='utf-8').write(s)
    report.append('%-28s applied %d/%d' % (label, len(pairs) - len(missed), len(pairs)))
    for m in missed:
        report.append('      NOT FOUND: ' + m)


# =============================================================== A. manuscript
ms = open(MS, encoding='utf-8').read()

# A1. name the model, its version and its manufacturer in the Methods
old_sent = ("Records were screened at title and abstract level with large-language-model assistance. "
            "The model, the prompt and the decoding parameters are recorded with each call, and "
            "screening was re-executed three times on the locked corpus (n = 2,556) with identical "
            "settings in order to document run-to-run reproducibility; agreement across the three "
            "runs was 94.3% (Fleiss' κ = 0.936; pairwise agreement 95.1–98.2%).")
new_sent = ("Records were screened at title and abstract level with large-language-model assistance. "
            "The model was DeepSeek (Hangzhou, China), accessed through its deepseek-chat endpoint "
            "at a temperature of 0.1 and resolving to DeepSeek-V4.1-Flash (deepseek-flash); the "
            "prompt, the decoding parameters and the returned model identifier are recorded with "
            "each call. Screening was re-executed three times on the locked corpus (n = 2,556) with "
            "identical settings in order to document run-to-run reproducibility; agreement across "
            "the three runs was 94.3% (Fleiss' κ = 0.936; pairwise agreement 95.1–98.2%).")
pat = re.compile(r'\s+'.join(re.escape(w) for w in old_sent.split()))
assert pat.search(ms), 'model sentence not found'
ms = pat.sub(lambda _m: new_sent, ms, count=1)

# A2. offset the added words with two trims elsewhere
TRIMS = [
    ("The searches returned 3,726 records (PubMed 1,727; Web of Science 1,695; IEEE Xplore 304), of which 1,170 were duplicates, leaving 2,556 records for screening.",
     "The searches returned 3,726 records (PubMed 1,727; Web of Science 1,695; IEEE Xplore 304); 1,170 were duplicates, leaving 2,556 for screening."),
    ("For the 54 included records without a retrievable full text, a record was retained only when its abstract explicitly named a potentially eligible software package and described its use; 12 records met this criterion, and the remaining 42 are flagged as not verifiable at full-text level and were not treated as negative findings.",
     "Of the 54 included records without a retrievable full text, 12 were retained because their abstract explicitly named a potentially eligible package and described its use; the remaining 42 are flagged as not verifiable at full-text level and were not treated as negative findings."),
    ("Educational and case-report work illustrates how the same tools are repurposed for teaching and for individualised planning [19,48,49].",
     "Educational and case-report work illustrates how the same tools are repurposed for teaching and planning [19,48,49]."),
]
for old, new in TRIMS:
    pat = re.compile(r'\s+'.join(re.escape(w) for w in old.split()))
    if pat.search(ms):
        ms = pat.sub(lambda _m: new, ms, count=1)
    else:
        report.append('   trim not found: ' + old[:60])

# A3. clean the reference list first, then append it to the manuscript
refs = open(REF, encoding='utf-8').read()
refs = refs.replace('&amp;', '&')
refs = re.sub(r'(\S)\s{2,}([A-Z])', r'\1 \2', refs)
refs = re.sub(r'(https?://\S+?)\s*$', r'\1', refs, flags=re.M)
_lines = []
for _ln in refs.splitlines():
    if re.match(r'^\[\d+\]', _ln) and not _ln.rstrip().endswith('.'):
        _ln = _ln.rstrip() + '.'
    _lines.append(_ln)
refs = '\n'.join(_lines) + '\n'
open(REF, 'w', encoding='utf-8').write(refs)
report.append('%-28s punctuation and entities cleaned' % 'references')

ref_body = refs[refs.index('[1]'):].rstrip()

AI_DECL = """## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work the authors used DeepSeek in order to improve the language and
readability of the manuscript. After using this tool, the authors reviewed and edited the content as
needed and take full responsibility for the content of the publication.

Large-language-model assistance was also used within the research method, and its extent is stated
here explicitly rather than in general terms. The model performed the title and abstract triage of the
2,556 de-duplicated records, assigned a single exclusion reason to each of the 1,943 records excluded
at that stage, carried out the two full-text re-assessment routes applied to the 1,168 excluded records
with a retrievable full text together with the adjudication of the records on which those routes
disagreed, ran the two repeated coding passes for study design, and coded the reported advantages,
challenges and gaps. The model did not determine the final included set on its own authority. The
prompts, decoding parameters, complete per-record raw responses, returned model identifiers and the
dates of all API calls are deposited in the public repository. The authors, and not the model, designed
and executed the searches, retrieved and managed the full texts, defined the eligibility criteria,
verified the software glossary, set the analysis plan, interpreted the findings and wrote the
manuscript.

## References

"""

ms = ms.rstrip() + '\n\n' + AI_DECL + ref_body + '\n'
open(MS, 'w', encoding='utf-8').write(ms)
report.append('%-28s merged; manuscript now %d lines'
              % ('manuscript', ms.count('\n') + 1))

# archive the standalone reference files
arc = os.path.join('09_归档', 'R2_参考文献_已并入稿件')
os.makedirs(arc, exist_ok=True)
for f in ('References_R2.md', 'References_R2.docx'):
    p = os.path.join(D, f)
    if os.path.exists(p):
        shutil.move(p, os.path.join(arc, f))
report.append('%-28s archived standalone References files' % 'references')

# =============================================================== B. small fixes
sub(DEC, [('Data availability (updated):', 'Data availability:')], 'declarations')
sub(SUP, [('NOTE (added in revision).', 'Note.')], 'supplementary file 1')

# =============================================================== C. response
sub(RSP, [
    ('(5.96 additional studies per\nhalf-year)',
     '(5.95 additional studies per half-year)'),
    ('refs 59–60 added', 'refs 56–57 added'),
    ('**Changes:** Methods, Information sources and search strategy–2.4; Results, Study selection.',
     '**Changes:** the Information sources and search strategy and Study selection sections of the '
     'Methods; the Study selection section of the Results.'),
    ('**Changes:** new Figure 5; new Results, Discipline and software family; Discussion; Abstract; new contingency-statistics file in the\nrepository.',
     '**Changes:** new Figure 5; the new Discipline and software family section of the Results; '
     'Discussion; Abstract; new contingency-statistics file in the repository.'),
    ('**Changes:** Methods, Data charting and synthesis; Figures 2d, 3a, 5; Results, Characteristics of the included studies and Software; Supplementary File 3.',
     '**Changes:** the Data charting and synthesis section of the Methods; Figures 2d, 3a and 5; the '
     'Characteristics of the included studies and Software sections of the Results; Supplementary File 3.'),
    ('**Changes:** Methods, Data charting and synthesis (new paragraph); new Figure 4; new Results, Workflow patterns; new archetype',
     '**Changes:** the Data charting and synthesis section of the Methods (new paragraph); new '
     'Figure 4; the new Workflow patterns section of the Results; new archetype'),
    ('**Changes:** Methods, Study selection; Results, Study selection; Limitations; new Figure 1; repository.',
     '**Changes:** the Study selection sections of the Methods and the Results; Limitations; new '
     'Figure 1; repository.'),
    ('**Changes:** Methods, Data charting and synthesis; new Results, Advantages, challenges and gaps; new Figure 6; Discussion; Conclusions; repository.',
     '**Changes:** the Data charting and synthesis section of the Methods; the new Advantages, '
     'challenges and gaps section of the Results; new Figure 6; Discussion; Conclusions; repository.'),
    ('**Changes:** Results, Characteristics of the included studies; new Figure 2c; Abstract; Discussion; Conclusions.',
     '**Changes:** the Characteristics of the included studies section of the Results; new Figure 2c; '
     'Abstract; Discussion; Conclusions.'),
    ('Results, Study selection and Characteristics of the included studies; Supplementary File 3; new provenance table.',
     'the Study selection and Characteristics of the included studies sections of the Results; '
     'Supplementary File 3; new provenance table.'),
    ('Both values are now stated in Results, Characteristics of the included studies and in the legend to Figure 2.',
     'Both values are now stated in the Results, under "Characteristics of the included studies", and '
     'in the legend to Figure 2.'),
    ('**Changes:** Figure 2a (caveat removed); Results, Characteristics of the included studies (sensitivity analysis stated); legend to\nFigure 2.',
     '**Changes:** Figure 2a (caveat removed); the Characteristics of the included studies section of '
     'the Results (sensitivity analysis stated); legend to Figure 2.'),
    ('**Changes:** Supplementary File 3, sheets 1 and 2; Methods, Data charting and synthesis; Results, Software; all figures.',
     '**Changes:** Supplementary File 3, sheets 1 and 2; the Data charting and synthesis section of the '
     'Methods; the Software section of the Results; all figures.'),
    # reference numbers now that the list runs in citation order
    ('Ref 49 has been replaced with Monaghesh et al. (BMC Oral Health 2026), a',
     'Ref 49 has been replaced with Monaghesh et al. (BMC Oral Health 2026; reference [51] in the '
     'revised list), a'),
    ('Ref 52 has been replaced with\nRombaut et al.',
     'Ref 52 has been replaced with Rombaut et al. (reference [53] in the revised list),'),
    ('It has been deleted and all subsequent references and in-text citations have been\nrenumbered; every entry in the reference list is now cited in the text.',
     'It has been deleted and all subsequent references and in-text citations have been renumbered. '
     'As the journal requires, the revised list has also been renumbered so that references follow '
     'the order of first citation in the text; reference numbers quoted in this letter are those of '
     'the previous version, and the number in the revised list is given in square brackets where the '
     'two differ. Every entry in the list is now cited in the text.'),
], 'response letter')

print('\n'.join(report))
