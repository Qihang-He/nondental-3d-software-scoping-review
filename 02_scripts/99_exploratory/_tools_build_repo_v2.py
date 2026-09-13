# -*- coding: utf-8 -*-
"""
_tools_build_repo_v2.py —— 组装可公开上传的仓库目录（06_公共仓库）
结构：
  README.md
  01_protocol/           提示词、编码本、抽样设计
  02_scripts/            全部可复现脚本
  03_logs/               三轮原始返回、一致性、排除原因、结局编码
  04_results/            统计核心、PRISMA 链路、补充统计、分型参数
  05_data/               锁定分析集、剔除清单、软件表、语料清单
  06_supplementary/      补充材料 2 与 3
  07_verification/       抽样明细与作者核验工作簿
运行：python _tools_build_repo_v2.py
"""
import os
import json
import shutil

ROOT = r'd:\Desktop\v8 for JD'
REPO = os.path.join(ROOT, '06_公共仓库')
ANA = os.path.join(ROOT, '03_数据', '08_分析用')


def copy(src, dst):
    if not os.path.exists(src):
        print('  [skip]', src)
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print('  +', os.path.relpath(dst, REPO))


def build():
    if os.path.exists(REPO):
        shutil.rmtree(REPO)
    os.makedirs(REPO)

    # 01 protocol
    copy(os.path.join(ROOT, '07_AI重跑原始记录', 'system_prompt.txt'),
         os.path.join(REPO, '01_protocol', 'screening_prompt.txt'))
    copy(os.path.join(ANA, '核验抽样_设计.json'),
         os.path.join(REPO, '01_protocol', 'verification_sampling_design.json'))
    copy(os.path.join(ROOT, '04_代码', '05_分析', '_tools_parallel_pass.py'),
         os.path.join(REPO, '01_protocol', 'coding_prompts.py'))

    # 02 scripts
    SRC = [('04_代码/05_分析', [
        '_tools_stats_core.py', '_tools_extra_stats_v3.py', '_tools_archetype.py',
        '_tools_prisma_corpus.py', '_tools_prisma_complete.py', '_tools_prisma_final.py',
        '_tools_parallel_pass.py', '_tools_verify_workbook.py',
        '_tools_fix_journal_and_window.py', '_tools_fill_doi.py', '_tools_cutlist47.py',
        '_tools_consistency_v2.py']),
        ('04_代码/06_新图', ['make_figures_v3.py', 'make_supp_fig.py', '_run_figs.py']),
        ('04_代码/07_文档', ['_tools_supp2_v2.py', '_tools_supp3_v2.py',
                             '_tools_check_ms.py', '_tools_renumber_refs.py'])]
    for d, files in SRC:
        for f in files:
            copy(os.path.join(ROOT, d.replace('/', os.sep), f),
                 os.path.join(REPO, '02_scripts', f))

    # 03 logs
    for i in (1, 2, 3):
        for f in ('raw_responses.jsonl', 'classification_parsed.csv', 'run_meta.json'):
            copy(os.path.join(ROOT, '07_AI重跑原始记录', 'run%d' % i, f),
                 os.path.join(REPO, '03_logs', 'run%d' % i, f))
    for f in ('consistency_report_v2.json', '三轮逐条结果与多数标签_v2.csv'):
        copy(os.path.join(ROOT, '07_AI重跑原始记录', '一致性分析', f),
             os.path.join(REPO, '03_logs', f))
    copy(os.path.join(ANA, 'prisma_pass', 'reason_parsed.csv'),
         os.path.join(REPO, '03_logs', 'screening_exclusion_reasons.csv'))
    copy(os.path.join(ANA, 'prisma_pass', 'reason_raw.jsonl'),
         os.path.join(REPO, '03_logs', 'screening_exclusion_reasons_raw.jsonl'))
    copy(os.path.join(ANA, 'prisma_pass', 'run_extra_parsed.csv'),
         os.path.join(REPO, '03_logs', 'run_extra_parsed.csv'))
    copy(os.path.join(ANA, 'rq3_pass', 'rq3_parsed.csv'),
         os.path.join(REPO, '03_logs', 'outcome_coding.csv'))
    copy(os.path.join(ANA, 'rq3_pass', 'rq3_raw.jsonl'),
         os.path.join(REPO, '03_logs', 'outcome_coding_raw.jsonl'))

    # 04 results
    for f in ('统计核心.json', 'PRISMA_链路.json', '补充统计_v3.json', 'RQ3_频次汇总.json',
              '工作流分型_描述.csv', '工作流分型_逐篇标签.csv', '工作流分型_方法参数.json',
              '刊名补全_证据表.csv', 'DOI补全_证据表.csv', 'PRISMA_语料定义校验.json',
              '窗口外剔除_3条.csv'):
        copy(os.path.join(ANA, f), os.path.join(REPO, '04_results', f))
    copy(os.path.join(ROOT, '05_图表', 'fig5_stats.json'),
         os.path.join(REPO, '04_results', 'figure5_contingency_stats.json'))

    # 05 data
    for f in ('分析数据集_final_v3.csv',):
        copy(os.path.join(ANA, f), os.path.join(REPO, '05_data', f))
    copy(os.path.join(ROOT, '03_数据', '06_锁定数据集', '剔除清单_共44条.csv'),
         os.path.join(REPO, '05_data', 'eligibility_audit_47_records.csv'))
    copy(os.path.join(ROOT, '03_数据', '09_软件表', '软件类别与来源表.csv'),
         os.path.join(REPO, '05_data', 'software_glossary.csv'))
    copy(os.path.join(ROOT, '03_数据', '11_PDF核验', 'PDF软件核验_逐篇.csv'),
         os.path.join(REPO, '05_data', 'fulltext_software_verification.csv'))

    # 06 supplementary
    for f in ('Supplementary_File_2_R2.xlsx', 'Supplementary_File_3.xlsx',
              'Dataset_provenance_table.csv'):
        copy(os.path.join(ROOT, '02_图表附件', 'R2_补充材料', f),
             os.path.join(REPO, '06_supplementary', f))

    # 07 verification
    for f in ('核验抽样_样本A明细.csv', '核验抽样_样本B明细.csv'):
        copy(os.path.join(ANA, f), os.path.join(REPO, '07_verification', f))
    copy(os.path.join(ROOT, '02_图表附件', 'R2_补充材料', '作者核验工作簿.xlsx'),
         os.path.join(REPO, '07_verification', 'author_verification_sheet.xlsx'))

    # README
    S = json.load(open(os.path.join(ANA, '统计核心.json'), encoding='utf-8'))
    CH = json.load(open(os.path.join(ANA, 'PRISMA_链路.json'), encoding='utf-8'))
    readme = f"""# Application of Nondental 3D Software in Dentistry: A Scoping Review
## Reproducibility repository

This repository contains the complete prompt, scripts, logs, results, locked dataset and
verification materials for the scoping review. All quantitative values in the manuscript are
generated from `05_data/分析数据集_final_v3.csv` (n = {S['N']}) by `02_scripts/_tools_stats_core.py`.

### Screening chain

| Step | n |
|---|---|
| Records identified (PubMed 1,727; Web of Science 1,605; IEEE Xplore 299) | 3,631 |
| Duplicates removed | 1,075 |
| Records screened at title/abstract level | 2,556 |
| Excluded at screening | 1,943 |
| Assessed for eligibility | 613 |
| Excluded after full-text assessment | 47 |
| **Included** | **{S['N']}** |

Exclusion reasons at screening: """ + '; '.join(
        '%s = %s' % (k, format(v, ',')) for k, v in
        sorted(CH['excluded_at_screening_by_reason_en'].items(), key=lambda x: -x[1])) + f"""

### Model

- Endpoint: `https://api.deepseek.com/v1/chat/completions`
- Requested identifier: `deepseek-chat` (rolling alias); resolved to `deepseek-flash`
  (DeepSeek-V4.1-Flash), as returned in every API response
- Decoding: temperature 0.1, max_tokens 500, streaming disabled
- Screening runs: 3 independent runs, identical prompt and parameters
- Run-to-run agreement: 94.3% unanimous; Fleiss' kappa = {S['ai_consistency']['Fleiss_kappa']}
- Screening dates: 10 September 2026; coding passes: 12 September 2026

### Directory guide

| Folder | Contents |
|---|---|
| `01_protocol/` | Screening prompt, coding prompts, verification sampling design |
| `02_scripts/` | All scripts needed to reproduce every number and figure |
| `03_logs/` | Per-record raw API responses, parsed classifications, consistency analysis, exclusion-reason pass, outcome-coding pass |
| `04_results/` | Statistics core (single source of truth), PRISMA chain, contingency statistics, archetype parameters, metadata-completion evidence |
| `05_data/` | Locked analysis dataset, eligibility audit, software glossary, full-text software verification |
| `06_supplementary/` | Supplementary Files 2 and 3 and the dataset provenance table |
| `07_verification/` | Sampling design, sampled records, author verification sheet |

### Verification of the screening output

A stratified random sample of 200 records was drawn from the 1,939 excluded records with an
available abstract, allocated in proportion to the exclusion reasons, together with a simple random
sample of 100 included studies. Sampling used the fixed seed 20260912 and is reproducible from
`02_scripts/_tools_verify_workbook.py`. Where no eligible study is found among the 200 sampled
exclusions, the one-sided 95% upper bound on the proportion of eligible studies wrongly excluded is
""" + '%.1f%%' % (json.load(open(os.path.join(ANA, '核验抽样_设计.json'), encoding='utf-8'))
                  ['upper_bound_if_zero_A'] * 100) + """ (Clopper-Pearson).

### Environment

Python 3.12 with pandas, numpy, scipy, scikit-learn, matplotlib, geopandas, openpyxl, requests,
PyMuPDF.
"""
    open(os.path.join(REPO, 'README.md'), 'w', encoding='utf-8').write(readme)
    print('  + README.md')


if __name__ == '__main__':
    build()
    tot = sum(os.path.getsize(os.path.join(r, f))
              for r, _, fs in os.walk(REPO) for f in fs)
    print('\n[repo]', REPO, 'size = %.1f MB' % (tot / 1024 / 1024))
