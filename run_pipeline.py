# -*- coding: utf-8 -*-
"""
run_pipeline.py -- reproduce every quantitative value in the manuscript.

Prerequisites
-------------
1. Set SCOPING_ROOT to a working copy of the project (the folder that contains
   03_数据/, 04_代码/, 05_图表/). If it is not set, the repository layout is assumed.
2. Python 3.12 with pandas, numpy, scipy, scikit-learn, matplotlib, geopandas,
   PyMuPDF, openpyxl, python-docx, requests.
3. To re-run the model-assisted steps, copy 01_protocol/config.example.json to
   <SCOPING_ROOT>/07_AI重跑原始记录/config.local.json and insert your own API key.
   The model-assisted steps are NOT required for reproducing the reported numbers:
   their outputs are already in 04_logs/, and only the analysis steps below are
   needed to regenerate the statistics, tables and figures.
Usage
-----
    python run_pipeline.py --from 04        # run from stage 04 onwards
    python run_pipeline.py --list           # show the order and skip
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, '02_scripts')

# (stage folder, script, what it produces)
PIPELINE = [
    ('04_charting', '_tools_fix_dates_journals.py',
     'publication half-year periods and normalised journal names'),
    ('04_charting', '_tools_canon_software3.py',
     'final canonical software names'),
    ('05_analysis', '_tools_archetype.py',
     'workflow archetypes (k by silhouette, bootstrap ARI)'),
    ('05_analysis', '_tools_stats_core.py',
     'THE single source of truth: every headline statistic'),
    ('05_analysis', '_tools_extra_stats_v3.py',
     'trend regression, contingency analysis, software co-occurrence'),
    ('03_selection', '_update_prisma_v4.py', 'the two-stage PRISMA chain'),
    ('05_analysis', '_rq3_summarize_v4.py', 'RQ3 frequencies'),
    ('06_figures', '_run_figs.py', 'Figures 1-5'),
    ('06_figures', 'make_supp_fig.py', 'Supplementary Figure S1'),
    ('07_documents', '_tools_supp2_v2.py', 'Supplementary File 2'),
    ('07_documents', '_tools_supp3_v2.py', 'Supplementary File 3 and the provenance table'),
]

# 模型辅助步骤：复跑需要 API 密钥，默认跳过（其输出已在 04_logs/）
MODEL_STEPS = [
    ('01_screening', '_tools_prisma_reason_pass.py', 'exclusion reasons'),
    ('01_screening', '_tools_consistency_v2.py', 'three-run agreement'),
    ('02_fulltext_reassessment', '_rescreen_fulltext.py', 'pass A of the full-text re-assessment'),
    ('02_fulltext_reassessment', '_rescreen_all_pdf.py', 'reverse check of the included set'),
    ('02_fulltext_reassessment', '_reconcile_passes.py', 'reconciliation of the two routes'),
    ('02_fulltext_reassessment', '_final_adjudicate2.py', 'adjudication of disagreements'),
    ('05_analysis', '_tools_rq3_extract.py', 'RQ3 coding'),
]


def run(stage, script):
    p = os.path.join(SCRIPTS, stage, script)
    if not os.path.exists(p):
        print('  [skip]  %s/%s (not present)' % (stage, script))
        return False
    print('  [run ]  %s' % script, flush=True)
    r = subprocess.run([sys.executable, p])
    if r.returncode != 0:
        print('  [FAIL]  %s exited with %d' % (script, r.returncode))
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='start', default='04',
                    help='start at this stage prefix, e.g. 04')
    ap.add_argument('--with-model', action='store_true',
                    help='also run the model-assisted steps (requires an API key)')
    ap.add_argument('--list', action='store_true', help='list the pipeline and exit')
    a = ap.parse_args()

    if a.list:
        for i, (s, f, w) in enumerate(PIPELINE, 1):
            print('%2d. %-28s %-34s %s' % (i, s, f, w))
        print('\nModel-assisted steps (run with --with-model):')
        for s, f, w in MODEL_STEPS:
            print('    %-28s %-34s %s' % (s, f, w))
        return

    if a.with_model:
        for s, f, w in MODEL_STEPS:
            if not run(s, f):
                print('Pipeline stopped at %s' % f)
                return

    for s, f, w in PIPELINE:
        if not s.startswith(a.start):
            continue
        if not run(s, f):
            print('Pipeline stopped at %s' % f)
            return
    print('\nDone. See 05_results/ for the regenerated statistics.')


if __name__ == '__main__':
    main()
