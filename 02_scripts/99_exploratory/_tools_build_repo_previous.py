# -*- coding: utf-8 -*-
"""
_tools_build_repo_v4.py —— 组装可公开上传的仓库目录（06_公共仓库），v4 / N=863 口径

结构：
  README.md
  LICENSE
  01_protocol/           筛选提示词、编码提示词、抽样设计、纳排标准
  02_scripts/            全部可复现脚本（分析 / 制图 / 文档）
  03_search_strategies/  三个数据库的完整检索式与导出文件
  04_logs/               三轮筛查原始返回、一致性、排除原因、全文重评、结局编码
  05_results/            统计核心、PRISMA 链路、补充统计、分型参数与标签
  06_data/               锁定分析集、剔除清单、软件表、语料与 PDF 对照
  07_supplementary/      补充材料 2/3、溯源表
  08_verification/       抽样明细与作者核验工作簿

运行：python _tools_build_repo_v4.py
"""
import os
import glob
import json
import shutil

ROOT = r'd:\Desktop\v8 for JD'
REPO = os.path.join(ROOT, '06_公共仓库')
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
S2 = os.path.join(ROOT, '02_图表附件', 'R2_补充材料')

SKIP_SCRIPTS = {'_recover_from_transcript.py', '_clean_supp3.py', '_replay_edits.py'}


def copy(src, dst):
    if not os.path.exists(src):
        print('  [skip]', os.path.relpath(src, ROOT))
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print('  +', os.path.relpath(dst, REPO))
    return True


def copy_glob(pattern, dst_dir, skip=()):
    for p in sorted(glob.glob(pattern)):
        if os.path.basename(p) in skip:
            continue
        copy(p, os.path.join(dst_dir, os.path.basename(p)))


def build():
    if os.path.exists(REPO):
        shutil.rmtree(REPO)
    os.makedirs(REPO)

    # ---------------- 01 protocol ----------------
    print('[01_protocol]')
    copy(os.path.join(ROOT, '07_AI重跑原始记录', 'system_prompt.txt'),
         os.path.join(REPO, '01_protocol', 'screening_prompt.txt'))
    copy(os.path.join(ANA, '核验抽样_设计.json'),
         os.path.join(REPO, '01_protocol', 'verification_sampling_design.json'))
    copy(os.path.join(ROOT, '04_代码', '05_分析', '_tools_parallel_pass.py'),
         os.path.join(REPO, '01_protocol', 'coding_prompts.py'))
    copy(os.path.join(ROOT, '07_AI重跑原始记录', 'config.example.json'),
         os.path.join(REPO, '01_protocol', 'config.example.json'))

    # ---------------- 02 scripts ----------------
    print('[02_scripts]')
    for sub in ('05_分析', '06_新图', '07_文档'):
        copy_glob(os.path.join(ROOT, '04_代码', sub, '*.py'),
                  os.path.join(REPO, '02_scripts'),
                  skip=SKIP_SCRIPTS)

    # ---------------- 03 search strategies ----------------
    print('[03_search_strategies]')
    copy_glob(os.path.join(ROOT, '11_检索策略', '*'),
              os.path.join(REPO, '03_search_strategies'))

    # ---------------- 04 logs ----------------
    print('[04_logs]')
    for i in (1, 2, 3):
        for f in ('raw_responses.jsonl', 'classification_parsed.csv', 'run_meta.json'):
            copy(os.path.join(ROOT, '07_AI重跑原始记录', 'run%d' % i, f),
                 os.path.join(REPO, '04_logs', 'screening_run%d' % i, f))
    for f in ('consistency_report_v2.json', '三轮逐条结果与多数标签_v2.csv'):
        copy(os.path.join(ROOT, '07_AI重跑原始记录', '一致性分析', f),
             os.path.join(REPO, '04_logs', f))
    # 筛查阶段排除原因
    for f, n in (('prisma_pass/reason_parsed.csv', 'title_abstract_exclusion_reasons.csv'),
                 ('prisma_pass/reason_raw.jsonl', 'title_abstract_exclusion_reasons_raw.jsonl'),
                 ('prisma_pass/run_extra_parsed.csv', 'screening_run_extra_parsed.csv')):
        copy(os.path.join(ANA, f.replace('/', os.sep)), os.path.join(REPO, '04_logs', n))
    # 全文重评（阶段二）—— 本次修订的核心材料
    for f, n in (('fulltext_pass/fulltext_parsed.csv', 'fulltext_reassessment_parsed.csv'),
                 ('fulltext_pass/fulltext_raw.jsonl', 'fulltext_reassessment_raw.jsonl'),
                 ('fulltext_pass/fulltext_included_parsed.csv',
                  'fulltext_reassessment_reverse_check_parsed.csv'),
                 ('fulltext_pass/fulltext_included_raw.jsonl',
                  'fulltext_reassessment_reverse_check_raw.jsonl'),
                 ('final_pass/final_parsed.csv', 'fulltext_reassessment_adjudicated.csv'),
                 ('final_pass/final_raw.jsonl', 'fulltext_reassessment_adjudicated_raw.jsonl'),
                 ('final_pass/final_raw2.jsonl', 'fulltext_reassessment_adjudicated_raw2.jsonl'),
                 ('rescreen_pass/rescreen_parsed.csv', 'reverse_check_parsed.csv'),
                 ('rescreen_pass/rescreen_raw.jsonl', 'reverse_check_raw.jsonl')):
        copy(os.path.join(ANA, f.replace('/', os.sep)), os.path.join(REPO, '04_logs', n))
    # 结局编码
    for f, n in (('rq3_pass/rq3_parsed.csv', 'outcome_coding.csv'),
                 ('rq3_pass/rq3_raw.jsonl', 'outcome_coding_raw.jsonl')):
        copy(os.path.join(ANA, f.replace('/', os.sep)), os.path.join(REPO, '04_logs', n))

    # ---------------- 05 results ----------------
    print('[05_results]')
    for f in ('统计核心.json', 'PRISMA_链路_v2.json', '补充统计_v3.json', 'RQ3_频次汇总.json',
              '工作流分型_描述.csv', '工作流分型_逐篇标签.csv', '工作流分型_方法参数.json',
              'RQ3_编码明细_863.csv', '软件规范名清单_v4.csv',
              '刊名补全_证据表.csv', 'DOI补全_证据表.csv',
              '纳入集复核_确定性核查.csv', '7篇归一化核查.csv', '软件标注修正_3条.csv',
              '变更日志_v3_to_v4.csv', '最终纳入集修订记录.csv',
              '时间窗外补充剔除_v4.csv', '窗口外剔除_3条.csv',
              '新增纳入_逐条溯源.csv', '最终新增纳入.csv', '漏排候选_E1.csv'):
        copy(os.path.join(ANA, f), os.path.join(REPO, '05_results', f))
    copy(os.path.join(ROOT, '05_图表', 'fig5_stats.json'),
         os.path.join(REPO, '05_results', 'figure5_contingency_stats.json'))

    # ---------------- 06 data ----------------
    print('[06_data]')
    copy(os.path.join(ANA, '分析数据集_final_v4.csv'),
         os.path.join(REPO, '06_data', 'locked_analysis_dataset_v4.csv'))
    copy(os.path.join(ROOT, '03_数据', '06_锁定数据集', '剔除清单_共44条.csv'),
         os.path.join(REPO, '06_data', 'eligibility_audit_records.csv'))
    copy(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'),
         os.path.join(REPO, '06_data', 'software_glossary.csv'))
    copy(os.path.join(ROOT, '03_数据', '07_PDF与语料对照', 'pdf_match.csv'),
         os.path.join(REPO, '06_data', 'pdf_to_record_match.csv'))
    copy(os.path.join(ROOT, '03_数据', '02_清洗后', '筛选语料_唯一记录_2556.csv'),
         os.path.join(REPO, '06_data', 'screening_corpus_unique_records.csv'))

    # ---------------- 07 supplementary ----------------
    print('[07_supplementary]')
    for f in ('Supplementary_File_2_R2.xlsx', 'Supplementary_File_3.xlsx',
              'Dataset_provenance_table.csv'):
        copy(os.path.join(S2, f), os.path.join(REPO, '07_supplementary', f))

    # ---------------- 08 verification ----------------
    print('[08_verification]')
    for f, n in (('核验抽样_样本A明细.csv', 'verification_sample_A_excluded.csv'),
                 ('核验抽样_样本B明细.csv', 'verification_sample_B_included.csv')):
        copy(os.path.join(ANA, f), os.path.join(REPO, '08_verification', n))
    copy(os.path.join(S2, '作者核验工作簿.xlsx'),
         os.path.join(REPO, '08_verification', 'author_verification_sheet.xlsx'))

    # ---------------- README ----------------
    S = json.load(open(os.path.join(ANA, '统计核心.json'), encoding='utf-8'))
    P = json.load(open(os.path.join(ANA, 'PRISMA_链路_v2.json'), encoding='utf-8'))
    N = S['N']
    readme = f"""# Application of Nondental 3D Software in Dentistry: A Scoping Review
## Reproducibility repository

Everything needed to reproduce the review is here: the search strategies, the screening and coding
prompts, every script, the raw model responses, the locked dataset, all derived statistics, the
figures' inputs, and the author-verification materials.

**Locked dataset:** `06_data/locked_analysis_dataset_v4.csv` (n = {N} included studies).
Every quantitative value in the manuscript is generated from this file by
`02_scripts/_tools_stats_core.py`.

---

## 1. What is new in this version of the analysis

The decisive eligibility criterion of this review is the **explicit use of a named third-party
nondental 3D software package**. That information is normally reported in the *methods section of
the full text*, not in the abstract. In the first version of this analysis the criterion was
nevertheless applied at title/abstract level, which excluded a large number of eligible studies.

This revision therefore applies the criterion in two stages:

| Stage | Scope | Outcome |
|---|---|---|
| 1. Title/abstract screening | {P['screened_title_abstract']:,} unique records | {P['excluded_at_title_abstract']:,} excluded |
| 2. Full-text re-assessment of excluded records | every excluded record with a retrievable full text: {P['fulltext_recheck']['excluded_records_with_full_text_available']:,} records | **{P['fulltext_recheck']['records_reclassified_as_eligible']} studies met the criteria and were added** |
| Reverse check of the previously included set | same standard applied in reverse | 4 records removed (no named package in full text); 3 software annotations corrected |
| Date-window check | publication after 30 June 2026 | 3 records removed |

The included set consequently changed from 566 to **{N} studies**.
`{P['fulltext_recheck']['excluded_records_without_full_text']} excluded records had no retrievable
full text` and could not be re-assessed; this residual uncertainty is stated in the manuscript.

### PRISMA chain (from `05_results/PRISMA_链路_v2.json`)

```
identified            PubMed {P['identified']['PubMed']:,} | Web of Science {P['identified']['Web of Science']:,} | IEEE Xplore {P['identified']['IEEE Xplore']:,}   = {P['identified_total']:,}
duplicates removed    {P['duplicates_removed']:,}
screened (title/abs)  {P['screened_title_abstract']:,}
excluded at stage 1   {P['excluded_at_title_abstract']:,}   (of which {P['fulltext_recheck']['excluded_records_with_full_text_available']:,} re-assessed in full text, {P['fulltext_recheck']['excluded_records_without_full_text']:,} without full text)
assessed at full text {P['assessed_for_eligibility_full_text']:,}
excluded at full text {P['excluded_after_fulltext_assessment']:,}
INCLUDED              {P['included']}
```

---

## 2. Repository map

| Folder | Contents |
|---|---|
| `01_protocol/` | Screening prompt, coding prompts, sampling design, config template |
| `02_scripts/` | Every analysis, plotting and document script (see §3) |
| `03_search_strategies/` | Complete search strings and database exports for PubMed, Web of Science and IEEE Xplore |
| `04_logs/` | Raw JSON responses of all screening runs, agreement analysis, exclusion reasons, **full-text re-assessment pass**, outcome coding |
| `05_results/` | Statistics core, PRISMA chain, contingency statistics, workflow-clustering parameters and labels, per-record traceability of every dataset change |
| `06_data/` | Locked analysis dataset (v4), eligibility audit, software glossary, screening corpus, PDF-to-record matching |
| `07_supplementary/` | Supplementary Files 2 and 3 and the dataset provenance table |
| `08_verification/` | Sampling design outputs and the author verification workbook |

---

## 3. Reproducing the analysis

Python 3.12 with `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `geopandas`,
`PyMuPDF`, `openpyxl`, `python-docx`, `requests`.

Run in this order after any change to the data:

```
02_scripts/_tools_fix_dates_journals.py     # date parsing and journal-name normalisation
02_scripts/_tools_archetype.py              # workflow clustering
02_scripts/_tools_stats_core.py             # THE single source of truth -> 统计核心.json
02_scripts/_tools_extra_stats_v3.py         # trend regression, contingency, co-occurrence
02_scripts/_update_prisma_v4.py             # PRISMA chain
02_scripts/_rq3_summarize_v4.py             # RQ3 frequencies
02_scripts/_run_figs.py                     # Figures 1-5
02_scripts/make_supp_fig.py                 # Supplementary Figure S1
02_scripts/_tools_supp2_v2.py               # Supplementary File 2
02_scripts/_tools_supp3_v2.py               # Supplementary File 3 (+ provenance table)
02_scripts/_tools_md2docx.py <in.md> <out.docx>
```

---

## 4. Model and API details

Screening and coding used the DeepSeek chat-completions API with the identifier `deepseek-chat`,
decoding parameters `temperature = 0.1`, `max_tokens = 300-500`, `stream = false`. The identifier is
a rolling alias and is not pinned to a version; the `model` field returned by the API resolved to
`deepseek-flash` (DeepSeek-V4.1-Flash) at the time of the calls. Every entry in `04_logs/` records
the request timestamp, returned model identifier, provider response id, returned content and
latency. **No API key is stored in this repository**; `01_protocol/config.example.json` shows the
expected shape and the key must be supplied by the user.

## 5. What these materials do and do not establish

- Agreement across the three screening runs (94.3%; Fleiss' kappa = 0.936) measures the
  **reproducibility** of the procedure, not its accuracy.
- No population-level sensitivity, specificity or confusion matrix is reported, because no complete
  human reference standard exists for the whole corpus.
- Study-design agreement (97.6%; Cohen's kappa = 0.966) is **coding stability** across two
  model-assisted passes, not agreement between two human raters.
- The workflow archetypes are **algorithmically derived** groupings, reproducible from this dataset;
  they are not manually coded categories, and no inter-rater reliability is claimed for them.
- Reported advantages, challenges and gaps were coded from **titles and abstracts** of the included
  studies, so the frequencies reflect what authors state prominently rather than every qualification
  in the full text.

## 6. Licensing and citation

Code and data are released for reuse with attribution; see `LICENSE`. If you use these materials,
please cite the published article and this repository (DOI to be added on archiving).
"""
    open(os.path.join(REPO, 'README.md'), 'w', encoding='utf-8').write(readme)
    print('  + README.md')

    lic = """MIT License

Copyright (c) 2026 The authors of "Application of Nondental 3D Software in Dentistry:
A Scoping Review"

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES
OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
    open(os.path.join(REPO, 'LICENSE'), 'w', encoding='utf-8').write(lic)
    print('  + LICENSE')


if __name__ == '__main__':
    build()
    n_files = sum(len(f) for _, _, f in os.walk(REPO))
    size = sum(os.path.getsize(os.path.join(d, f))
               for d, _, fs in os.walk(REPO) for f in fs)
    print('\n完成：%d 个文件，%.1f MB' % (n_files, size / 1024 / 1024))
