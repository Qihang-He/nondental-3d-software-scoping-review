# -*- coding: utf-8 -*-
# --- path bootstrap added by the repository build -------------------------
# Resolves the project root from the SCOPING_ROOT environment variable, or from
# this file's location when the script sits three levels below the project root.
import os as _os
_ROOTP = (_os.environ.get('SCOPING_ROOT')
          or _os.path.dirname(_os.path.dirname(_os.path.dirname(
              _os.path.abspath(__file__)))))
# -------------------------------------------------------------------------
"""
_tools_build_repo_v5.py —— 组装可公开上传的仓库（科学、分层、可审计）

改进（相对 v4 构建脚本）：
  1. 脚本按分析阶段分目录（00_lib / 01_screening / 02_fulltext_reassessment / ...）
  2. ROOT 路径改为「环境变量 SCOPING_ROOT 优先，否则由文件位置推导」，
     克隆仓库后设置 SCOPING_ROOT 指向项目副本即可复跑（构建时逐个语法校验）
  3. 构建过程强制密钥扫描，发现 sk- 型密钥立即中止
  4. 生成 MANIFEST.csv（阶段 / 文件名 / SHA-256 / 行数）与 PIPELINE.md（执行顺序）
  5. 过时的一次性探查脚本归入 99_exploratory，保留审计痕迹但不干扰主线

运行：python _tools_build_repo_v5.py
"""
import os
import re
import csv
import glob
import json
import shutil
import hashlib
import py_compile
import subprocess

ROOT = _ROOTP
REPO = os.path.join(ROOT, _os.path.join(_ROOTP, '06_公共仓库'))
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
S2 = os.path.join(ROOT, _os.path.join(_ROOTP, '02_图表附件'), 'R2_补充材料')
SRC_A, SRC_F, SRC_D = ('04_代码/05_分析', '04_代码/06_新图', '04_代码/07_文档')
SKIP = {'_recover_from_transcript.py', '_clean_supp3.py', '_replay_edits.py'}

# ---------------------------------------------------------------- 阶段清单
STAGES = {
    '00_lib': [
        ('_tools_parallel_pass.py', SRC_A,
         'Shared DeepSeek API client, screening/coding prompts and response parsers'),
    ],
    '01_screening': [
        ('_tools_prisma_corpus.py', SRC_A, 'Define the locked screening corpus (unique records after de-duplication)'),
        ('_tools_prisma_reason_pass.py', SRC_A, 'Assign a single primary exclusion reason to every record excluded at title/abstract level'),
        ('_tools_consistency_v2.py', SRC_A, 'Run-to-run agreement of the three screening passes (Fleiss kappa)'),
        ('_check_search_counts.py', SRC_A, 'Recount records identified per database from the deposited exports'),
        ('_check_search_unique.py', SRC_A, 'Verify the number of unique records after de-duplication'),
    ],
    '02_fulltext_reassessment': [
        ('_excluded_fulltext_screen.py', SRC_A, 'Extract keyword windows around software terms from the full texts of excluded records'),
        ('_rescreen_fulltext.py', SRC_A, 'Pass A: match excluded records against tabulated full-text software names'),
        ('_rescreen_all_pdf.py', SRC_A, 'Same re-assessment applied in reverse to the previously included set'),
        ('_expand_candidates.py', SRC_A, 'Expand the candidate set to all excluded records with a high-quality excerpt'),
        ('_reconcile_passes.py', SRC_A, 'Reconcile the two re-assessment routes and list disagreements'),
        ('_final_adjudicate.py', SRC_A, 'Model-assisted adjudication of records on which the two routes disagreed'),
        ('_final_adjudicate2.py', SRC_A, 'Second adjudication round with software-name-priority excerpt extraction'),
        ('_newly_eligible_triage.py', SRC_A, 'Triage of newly identified eligible records'),
        ('_check_135_by_fulltext.py', SRC_A, 'Deterministic full-PDF check of records flagged as naming no software'),
        ('_check_7_normalized.py', SRC_A, 'Normalised (space/hyphen/case-insensitive) matching of residual software names'),
        ('_validate_E1.py', SRC_A, 'Validation of the E1 set of candidate missed inclusions'),
    ],
    '03_selection': [
        ('_tools_build_v4_dataset.py', SRC_A, 'Build the locked v4 analysis dataset (N = 863)'),
        ('_build_v4.py', SRC_A, 'Assemble v4: merge retained records with newly eligible records, resolve countries'),
        ('_tools_finalize_set.py', SRC_A, 'Finalise the included set after reconciliation'),
        ('_tools_cutlist47.py', SRC_A, 'Build the 47-record eligibility audit cut list'),
        ('_fix_window_v4.py', SRC_A, 'Remove records published outside the prespecified date window'),
        ('_tools_prisma_v2.py', SRC_A, 'Generate the two-stage PRISMA chain'),
        ('_update_prisma_v4.py', SRC_A, 'Synchronise the PRISMA chain to the final included count'),
        ('_rebuild_v4.py', SRC_D, 'Orchestrator: run the whole v4 rebuild in order'),
    ],
    '04_charting': [
        ('_tools_canon_software.py', SRC_A, 'Canonicalise software names (stage 1: versions and vendor prefixes)'),
        ('_tools_canon_software2.py', SRC_A, 'Canonicalise software names (stage 2: containment matching)'),
        ('_tools_canon_software3.py', SRC_A, 'Canonicalise software names (stage 3: explicit alias map)'),
        ('_tools_software_table.py', SRC_A, 'Build the software glossary with category and development-domain provenance'),
        ('_tools_sw_unknown.py', SRC_A, 'Resolve residual unmapped software names'),
        ('_tools_fix_dates_journals.py', SRC_A, 'Parse publication dates into half-year periods and normalise journal names'),
        ('_tools_fix_journal_and_window.py', SRC_A, 'Earlier journal/window correction pass'),
        ('_tools_fill_doi.py', SRC_A, 'Complete missing DOIs from CrossRef'),
        ('_resolve_country.py', SRC_A, 'Resolve country of the corresponding author (CrossRef, full-text affiliation, model)'),
        ('_tools_study_type.py', SRC_A, 'Code study design against the six prespecified definitions'),
        ('_tools_recode.py', SRC_A, 'Re-code charted multi-label fields'),
        ('_tools_pdf_verify.py', SRC_A, 'Verify annotated software names against the archived full texts'),
        ('_tools_pdf_risk_geomagic.py', SRC_A, 'Detect systematic mislabelling within the Geomagic product family'),
    ],
    '05_analysis': [
        ('_tools_stats_core.py', SRC_A, 'SINGLE SOURCE OF TRUTH: every headline statistic -> 统计核心.json'),
        ('_tools_extra_stats_v3.py', SRC_A, 'Trend regression, discipline x software-family contingency, software co-occurrence'),
        ('_tools_archetype.py', SRC_A, 'Data-driven workflow archetypes (Jaccard distance, average linkage, silhouette)'),
        ('_tools_extra_evidence.py', SRC_A, 'Assemble supplementary evidence tables for the manuscript'),
        ('_tools_rq3_extract.py', SRC_A, 'RQ3 coding pass: reported advantages, challenges and gaps'),
        ('_tools_rq3_extend.py', SRC_A, 'Extend the RQ3 coding to newly eligible records with the identical codebook'),
        ('_tools_rq3_fill3.py', SRC_A, 'Fill residual gaps in the RQ3 coding'),
        ('_rq3_summarize_v4.py', SRC_A, 'Summarise RQ3 frequencies over the final included set'),
        ('_verify_stats.py', SRC_A, 'Cross-check every reported statistic against the locked dataset'),
    ],
    '06_figures': [
        ('make_figures_v3.py', SRC_F, 'Figures 1-5 (PRISMA, landscape, software, archetypes, contingency)'),
        ('_run_figs.py', SRC_F, 'Driver that renders the figure set'),
        ('make_supp_fig.py', SRC_F, 'Supplementary Figure S1: journal and proceedings distribution'),
    ],
    '07_documents': [
        ('_tools_supp2_v2.py', SRC_D, 'Supplementary File 2: screening logs, exclusion reasons, outcome coding, codebook, model metadata'),
        ('_tools_supp3_v2.py', SRC_D, 'Supplementary File 3: included studies, software glossary, eligibility audit, definitions'),
        ('_tools_provenance_v4.py', SRC_D, 'Dataset provenance table: which dataset version generated which output'),
        ('_tools_md2docx.py', SRC_D, 'Convert the Markdown manuscript files to Word'),
        ('_tools_check_ms.py', SRC_D, 'Check the manuscript for recurrent formatting faults'),
        ('_tools_renumber_refs.py', SRC_D, 'Renumber in-text citations after reference-list edits'),
        ('_check_abstract.py', SRC_D, 'Verify the abstract word limit and the internal consistency of headline numbers'),
        ('_tools_final_audit.py', SRC_D, 'Final numerical audit of the submission package'),
        ('_tools_build_repo_v5.py', SRC_D, 'This script: assemble the public repository'),
    ],
    '08_verification': [
        ('_tools_verify_evidence.py', SRC_D, 'Build the evidence pack for the 300 sampled records'),
        ('_tools_verify_fill.py', SRC_D, 'Record the per-record verdict, evidence level and reason'),
        ('_fill_verification.py', SRC_A, 'Assemble the verification workbook from the sampled records'),
        ('_verify_A_deep.py', SRC_A, 'Deep check of the flagged records in sample A'),
        ('_verify_A_pdf_sw.py', SRC_A, 'Objective full-text software check for sample A'),
        ('_verify_A_review.py', SRC_A, 'Review pass for sample A'),
        ('_tools_verify_workbook.py', SRC_A, 'Build the A/B verification workbook'),
        ('_check_included_review.py', SRC_A, 'Review of records already included at the time of sampling'),
    ],
}

# 已知导入关系修正：(文件, 旧串, 新串)
IMPORT_FIXES = {
    '_tools_rq3_extend.py': (
        'sys.path.insert(0, HERE)',
        "sys.path.insert(0, HERE)\n"
        "sys.path.insert(0, os.path.join(os.path.dirname(HERE), '00_lib'))"),
    '_tools_rq3_fill3.py': (
        'sys.path.insert(0, HERE)',
        "sys.path.insert(0, HERE)\n"
        "sys.path.insert(0, os.path.join(os.path.dirname(HERE), '00_lib'))"),
}

# ---------------- 英文规范化重命名映射（去掉中文名与版本号） ----------------
# 主线脚本：去掉 _v2/_v3/_v4/_v5 版本后缀
SCRIPT_RENAME = {
    '_tools_consistency_v2.py': '_tools_consistency.py',
    '_build_v4.py': '_build_dataset.py',
    '_fix_window_v4.py': '_fix_window.py',
    '_rebuild_v4.py': '_rebuild_dataset.py',
    '_tools_build_v4_dataset.py': '_tools_build_dataset.py',
    '_tools_prisma_v2.py': '_tools_prisma.py',
    '_update_prisma_v4.py': '_update_prisma.py',
    '_rq3_summarize_v4.py': '_rq3_summarize.py',
    '_tools_extra_stats_v3.py': '_tools_extra_stats.py',
    'make_figures_v3.py': 'make_figures.py',
    '_tools_build_repo_v5.py': '_tools_build_repo.py',
    '_tools_provenance_v4.py': '_tools_provenance.py',
    '_tools_supp2_v2.py': '_tools_supp2.py',
    '_tools_supp3_v2.py': '_tools_supp3.py',
    '_tools_archetype_derive_v5.py': '_tools_archetype_derive.py',
    '_tools_apply_fulltext_decisions_20260916.py': '_tools_apply_fulltext_decisions.py',
    '_tools_build_repo_v2.py': '_tools_build_repo_legacy.py',
    '_tools_build_repo_v4.py': '_tools_build_repo_previous.py',
    '_tools_summarize_author_reviews_v2.py': '_tools_summarize_author_reviews.py',
    'make_figures_v2.py': 'make_figures_legacy.py',
}

# 05_results 结果文件：中文名 + 版本号 -> 英文名
RESULTS_RENAME = {
    '统计核心_v5.json': 'statistics_core.json',
    'PRISMA_链路_v2.json': 'prisma_flow.json',
    '补充统计_v3.json': 'supplementary_statistics.json',
    'RQ3_频次汇总.json': 'rq3_frequencies.json',
    'RQ3_编码明细_v5.csv': 'rq3_coding.csv',
    '软件规范名清单_v5.csv': 'software_names.csv',
    '工作流分型_描述.csv': 'workflow_archetypes.csv',
    '工作流分型_逐篇标签.csv': 'workflow_archetypes_labels.csv',
    '工作流分型_方法参数.json': 'workflow_archetypes_methods.json',
    '刊名补全_证据表.csv': 'journal_name_completion.csv',
    'DOI补全_证据表.csv': 'doi_completion.csv',
    '纳入集复核_确定性核查.csv': 'inclusion_set_review.csv',
    '7篇归一化核查.csv': 'software_name_normalization.csv',
    '软件标注修正_3条.csv': 'software_annotation_corrections.csv',
    '变更日志_v3_to_v4.csv': 'dataset_changelog.csv',
    '最终纳入集修订记录.csv': 'inclusion_set_revisions.csv',
    '时间窗外补充剔除_v4.csv': 'outside_window_exclusions.csv',
    '窗口外剔除_3条.csv': 'outside_date_window_exclusions.csv',
    '新增纳入_逐条溯源.csv': 'newly_included_traceability.csv',
    '最终新增纳入.csv': 'newly_included_records.csv',
    '漏排候选_E1.csv': 'missed_inclusion_candidates.csv',
}

# 06_data 锁定数据集列名：中文列名 -> 英文列名
DATASET_COLUMN_RENAME = {
    '序号': 'record_id',
    '原始AI分类': 'ai_original_label',
    '裁定': 'decision',
    '裁定理由': 'decision_reason',
    '裁定2': 'decision_2',
    '裁定2理由': 'decision_2_reason',
    'AI多数': 'ai_majority_label',
    '裁定3': 'decision_3',
    '裁定3理由': 'decision_3_reason',
    '_来源': '_source',
}

# 派生结果文件列名英文化（软件词典 / 软件清单 / 工作流原型 / RQ3 编码）
GLOSSARY_COLUMN_RENAME = {
    '原始名称': 'original_name',
    '规范名称': 'canonical_name',
    '类别': 'category',
    '原始开发领域': 'development_domain',
    '开发商': 'developer',
    '来源URL': 'source_url',
    'URL状态': 'url_status',
    '研究数': 'n_studies',
}
SOFTWARE_NAMES_COLUMN_RENAME = {'软件': 'software', '研究数': 'n_studies'}
ARCHETYPES_COLUMN_RENAME = {
    'Archetype': 'archetype',
    'n': 'n',
    '占比%': 'pct',
    '场景1': 'scenario_1',
    '场景1%': 'scenario_1_pct',
    '场景2': 'scenario_2',
    '场景2%': 'scenario_2_pct',
    '软件族1': 'software_family_1',
    '软件族2': 'software_family_2',
    '研究类型': 'study_types',
}
ARCHETYPES_LABELS_COLUMN_RENAME = {'序号': 'record_id'}
RQ3_CODING_COLUMN_RENAME = {
    '序号': 'record_id',
    '优势': 'advantages',
    '挑战': 'challenges',
    '缺口': 'gaps',
    '原始返回': 'raw_response',
}

# 04_logs 日志文件：中文名 + 版本号 -> 英文名
LOGS_RENAME = {
    'consistency_report_v2.json': 'consistency_report.json',
    '三轮逐条结果与多数标签_v2.csv': 'run_agreement.csv',
}

# 03_search_strategies 检索式：中文名 -> 英文名
SEARCH_RENAME = {
    'Pubme检索式.txt': 'pubmed_search.txt',
    'ieee检索式.txt': 'ieee_search.txt',
    'wos检索式.txt': 'wos_search.txt',
}

# 07_supplementary 补充材料：去掉 R2 后缀
SUPP_RENAME = {
    'Supplementary_File_2_R2.xlsx': 'Supplementary_File_2.xlsx',
    'Supplementary_File_3.xlsx': 'Supplementary_File_3.xlsx',
}

# figshare 存档 DOI（写入 README 与 CITATION.cff）
FIGSHARE_DOI = '10.6084/m9.figshare.33886810'

ROOT_NEW = ("_ROOTP")
HEADER = (
    "# --- path bootstrap added by the repository build -------------------------\n"
    "# Resolves the project root from the SCOPING_ROOT environment variable, or from\n"
    "# this file's location when the script sits three levels below the project root.\n"
    "import os as _os\n"
    "_ROOTP = (_os.environ.get('SCOPING_ROOT')\n"
    "          or _os.path.dirname(_os.path.dirname(_os.path.dirname(\n"
    "              _os.path.abspath(__file__)))))\n"
    "# -------------------------------------------------------------------------\n"
)

# 绝对路径字面量：_ROOTP 及其任意子路径
ABS_RE = re.compile(r"r?(['\"])d:\\+Desktop\\+v8 for JD((?:\\+[^'\"]*)?)\1")
# 相对项目根的路径字面量：_os.path.join(_ROOTP, '03_数据', '08_分析用') 等
_PROJ_TOPS = (_os.path.join(_ROOTP, '02_图表附件'), _os.path.join(_ROOTP, '03_数据'), _os.path.join(_ROOTP, '04_代码'), _os.path.join(_ROOTP, '05_图表'), _os.path.join(_ROOTP, '06_公共仓库'),
              _os.path.join(_ROOTP, '07_AI重跑原始记录'), _os.path.join(_ROOTP, '10_全文PDF库'), _os.path.join(_ROOTP, '11_检索策略'))
REL_RE = re.compile(r"r?(['\"])((?:%s)(?:\\+[^'\"]*)?)\1" % '|'.join(_PROJ_TOPS))


def _join(rel):
    segs = [s for s in rel.replace('/', '\\').split('\\') if s]
    return "_os.path.join(_ROOTP, %s)" % ", ".join(repr(s) for s in segs)


def _bootstrap(txt, base):
    """把项目根路径字面量改写为可移植表达式，并在文件头插入引导代码。"""
    hits = len(ABS_RE.findall(txt)) + len(REL_RE.findall(txt))
    if hits == 0:
        return txt, 'verbatim'

    txt = ABS_RE.sub(lambda m: '_ROOTP' if not m.group(2) else _join(m.group(2)), txt)
    txt = REL_RE.sub(lambda m: _join(m.group(2)), txt)

    lines = txt.split('\n')
    pos = 1 if lines and lines[0].lstrip().startswith('#') and 'coding' in lines[0] else 0
    txt = '\n'.join(lines[:pos] + HEADER.rstrip('\n').split('\n') + lines[pos:])
    return txt, 'rewritten'


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def prepare_py(src, dst):
    """复制脚本并改写路径与导入，改写后做语法校验；失败则回退原文件并告警。"""
    txt = open(src, encoding='utf-8').read()
    orig = txt
    base = os.path.basename(src)

    txt, mode = _bootstrap(txt, base)

    if base in IMPORT_FIXES:
        a, b = IMPORT_FIXES[base]
        if a in txt:
            txt = txt.replace(a, b, 1)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w', encoding='utf-8').write(txt)
    try:
        compile(txt, dst, 'exec')          # 内存语法校验（Windows 上 cfile=nul 会失败）
    except SyntaxError as e:
        open(dst, 'w', encoding='utf-8').write(orig)
        print('  [reverted: %s] %s' % (e.msg, base))
        return 'reverted'
    return mode


def copy(src, dst, note=''):
    if not os.path.exists(src):
        print('  [missing]', os.path.relpath(src, ROOT))
        return 0
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return os.path.getsize(dst)


def copy_csv_renamed(src, dst, colmap):
    """复制 CSV 并英文化列名。"""
    if not os.path.exists(src):
        print('  [missing]', os.path.relpath(src, ROOT))
        return 0
    import pandas as _pd
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    df = _pd.read_csv(src, low_memory=False)
    df = df.rename(columns=colmap)
    df.to_csv(dst, index=False, encoding='utf-8-sig')
    return os.path.getsize(dst)


def copy_glob(pattern, dst_dir, skip=()):
    n = 0
    for p in sorted(glob.glob(pattern)):
        if os.path.basename(p) in skip:
            continue
        copy(p, os.path.join(dst_dir, os.path.basename(p)))
        n += 1
    return n


def _force_rm(path):
    """Windows 下 git 对象是只读的，删除前需清除只读属性。"""
    import stat as _stat

    def _onerr(func, p, exc):
        try:
            os.chmod(p, _stat.S_IWRITE)
            func(p)
        except Exception:
            pass

    for d, dirs, fs in os.walk(path):
        for name in dirs + fs:
            try:
                os.chmod(os.path.join(d, name), _stat.S_IWRITE)
            except Exception:
                pass
    shutil.rmtree(path, onerror=_onerr)


def build():
    if os.path.exists(REPO):
        _force_rm(REPO)
    os.makedirs(REPO)

    manifest = []

    # ---------------- 02 scripts（按阶段） ----------------
    print('[02_scripts]')
    for stage, items in STAGES.items():
        for fn, srcdir, purpose in items:
            src = os.path.join(ROOT, srcdir.replace('/', os.sep), fn)
            if not os.path.exists(src):
                print('  [missing]', fn)
                continue
            out_fn = SCRIPT_RENAME.get(fn, fn)
            dst = os.path.join(REPO, '02_scripts', stage, out_fn)
            mode = prepare_py(src, dst)
            manifest.append({'stage': stage, 'script': out_fn, 'purpose': purpose,
                             'path': '02_scripts/%s/%s' % (stage, out_fn),
                             'lines': sum(1 for _ in open(src, encoding='utf-8')),
                             'sha256': sha256(src)[:16], 'root_rewrite': mode})
    # 过时的一次性脚本
    listed = {fn for items in STAGES.values() for fn, _, _ in items}
    n_exp = 0
    for sub in ('05_分析', '06_新图', '07_文档'):
        for p in sorted(glob.glob(os.path.join(ROOT, _os.path.join(_ROOTP, '04_代码'), sub, '*.py'))):
            fn = os.path.basename(p)
            if fn in listed or fn in SKIP:
                continue
            out_fn = SCRIPT_RENAME.get(fn, fn)
            copy(p, os.path.join(REPO, '02_scripts', '99_exploratory', out_fn))
            n_exp += 1
    print('  主线脚本 %d 个，探查脚本 %d 个' % (len(manifest), n_exp))

    # ---------------- 01 protocol ----------------
    print('[01_protocol]')
    copy(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'system_prompt.txt'),
         os.path.join(REPO, '01_protocol', 'screening_prompt.txt'))
    copy(os.path.join(ANA, '核验抽样_设计.json'),
         os.path.join(REPO, '01_protocol', 'verification_sampling_design.json'))
    copy(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'config.example.json'),
         os.path.join(REPO, '01_protocol', 'config.example.json'))

    # ---------------- 03 search strategies ----------------
    print('[03_search_strategies]')
    for p in sorted(glob.glob(os.path.join(ROOT, _os.path.join(_ROOTP, '11_检索策略'), '*'))):
        fn = os.path.basename(p)
        out_fn = SEARCH_RENAME.get(fn, fn)
        copy(p, os.path.join(REPO, '03_search_strategies', out_fn))

    # ---------------- 04 logs ----------------
    print('[04_logs]')
    for i in (1, 2, 3):
        for f in ('raw_responses.jsonl', 'classification_parsed.csv', 'run_meta.json'):
            copy(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), 'run%d' % i, f),
                 os.path.join(REPO, '04_logs', 'screening_run%d' % i, f))
    for f in ('consistency_report_v2.json', '三轮逐条结果与多数标签_v2.csv'):
        copy(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), '一致性分析', f),
             os.path.join(REPO, '04_logs', LOGS_RENAME.get(f, f)))
    for f, n in (('prisma_pass/reason_parsed.csv', 'title_abstract_exclusion_reasons.csv'),
                 ('prisma_pass/reason_raw.jsonl', 'title_abstract_exclusion_reasons_raw.jsonl'),
                 ('prisma_pass/run_extra_parsed.csv', 'screening_run_extra_parsed.csv'),
                 ('fulltext_pass/fulltext_parsed.csv', 'fulltext_reassessment_parsed.csv'),
                 ('fulltext_pass/fulltext_raw.jsonl', 'fulltext_reassessment_raw.jsonl'),
                 ('fulltext_pass/fulltext_included_parsed.csv',
                  'fulltext_reassessment_reverse_check_parsed.csv'),
                 ('fulltext_pass/fulltext_included_raw.jsonl',
                  'fulltext_reassessment_reverse_check_raw.jsonl'),
                 ('final_pass/final_parsed.csv', 'fulltext_reassessment_adjudicated.csv'),
                 ('final_pass/final_raw.jsonl', 'fulltext_reassessment_adjudicated_raw.jsonl'),
                 ('final_pass/final_raw2.jsonl', 'fulltext_reassessment_adjudicated_raw2.jsonl'),
                 ('rescreen_pass/rescreen_parsed.csv', 'reverse_check_parsed.csv'),
                 ('rescreen_pass/rescreen_raw.jsonl', 'reverse_check_raw.jsonl'),
                 ('rq3_pass/rq3_parsed.csv', 'outcome_coding.csv'),
                 ('rq3_pass/rq3_raw.jsonl', 'outcome_coding_raw.jsonl')):
        copy(os.path.join(ANA, f.replace('/', os.sep)), os.path.join(REPO, '04_logs', n))

    # ---------------- 05 results ----------------
    print('[05_results]')
    _csv_colmap = {
        'software_names.csv': SOFTWARE_NAMES_COLUMN_RENAME,
        'workflow_archetypes.csv': ARCHETYPES_COLUMN_RENAME,
        'workflow_archetypes_labels.csv': ARCHETYPES_LABELS_COLUMN_RENAME,
        'rq3_coding.csv': RQ3_CODING_COLUMN_RENAME,
    }
    for src_f, out_f in RESULTS_RENAME.items():
        dst = os.path.join(REPO, '05_results', out_f)
        if out_f in _csv_colmap:
            copy_csv_renamed(os.path.join(ANA, src_f), dst, _csv_colmap[out_f])
        else:
            copy(os.path.join(ANA, src_f), dst)
    copy(os.path.join(ROOT, _os.path.join(_ROOTP, '05_图表'), 'fig5_stats.json'),
         os.path.join(REPO, '05_results', 'contingency_statistics.json'))

    # ---------------- 06 data ----------------
    print('[06_data]')
    # 锁定数据集：列名英文化，去掉版本号
    import pandas as _pd
    os.makedirs(os.path.join(REPO, '06_data'), exist_ok=True)
    _df = _pd.read_csv(os.path.join(ANA, '分析数据集_final_v5.csv'), low_memory=False)
    _df = _df.rename(columns=DATASET_COLUMN_RENAME)
    _df.to_csv(os.path.join(REPO, '06_data', 'locked_analysis_dataset.csv'),
               index=False, encoding='utf-8-sig')
    print('  locked_analysis_dataset.csv (%d records)' % len(_df))
    copy(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '06_锁定数据集', '剔除清单_共44条.csv'),
         os.path.join(REPO, '06_data', 'eligibility_audit_records.csv'))
    copy_csv_renamed(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '09_软件表', '软件类别与来源表.csv'),
                     os.path.join(REPO, '06_data', 'software_glossary.csv'),
                     GLOSSARY_COLUMN_RENAME)
    copy(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '07_PDF与语料对照', 'pdf_match.csv'),
         os.path.join(REPO, '06_data', 'pdf_to_record_match.csv'))
    copy(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后', '筛选语料_唯一记录_2556.csv'),
         os.path.join(REPO, '06_data', 'screening_corpus_unique_records.csv'))

    # ---------------- 07 supplementary ----------------
    print('[07_supplementary]')
    for f in ('Supplementary_File_2_R2.xlsx', 'Supplementary_File_3.xlsx',
              'Dataset_provenance_table.csv'):
        copy(os.path.join(S2, f), os.path.join(REPO, '07_supplementary', SUPP_RENAME.get(f, f)))

    # ---------------- 08 verification ----------------
    print('[08_verification]')
    for f, n in (('核验抽样_样本A明细.csv', 'verification_sample_A_excluded.csv'),
                 ('核验抽样_样本B明细.csv', 'verification_sample_B_included.csv')):
        copy(os.path.join(ANA, f), os.path.join(REPO, '08_verification', n))
    # 逐条复核结论（2026-09 修订阶段补做；取代早期的空白登记表）
    copy(os.path.join(ANA, '核验复核_逐条.csv'),
         os.path.join(REPO, '08_verification', 'verification_sample_outcomes.csv'))
    copy(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用', '核验复核_证据包.csv'),
         os.path.join(REPO, '08_verification', 'verification_evidence_pack.csv'))

    # ---------------- MANIFEST ----------------
    with open(os.path.join(REPO, '02_scripts', 'MANIFEST.csv'), 'w',
              newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=['stage', 'script', 'purpose', 'path', 'lines',
                                           'sha256', 'root_rewrite'])
        w.writeheader()
        w.writerows(manifest)
    print('  + 02_scripts/MANIFEST.csv')

    write_pipeline_py()
    write_pipeline_md()
    write_readme()
    write_citation()
    write_gitignore()
    write_license()

    # ---------------- 密钥扫描（强制） ----------------
    print('\n[安全扫描]')
    bad = []
    for d, _, fs in os.walk(REPO):
        for f in fs:
            p = os.path.join(d, f)
            if os.path.getsize(p) > 40 * 1024 * 1024:
                continue
            try:
                txt = open(p, encoding='utf-8', errors='ignore').read()
            except Exception:
                continue
            for m in re.finditer(r'sk-[A-Za-z0-9]{20,}', txt):
                bad.append((os.path.relpath(p, REPO), m.group(0)[:12] + '...'))
    if bad:
        print('!!! 发现疑似密钥，构建中止 !!!')
        for b in bad:
            print('   ', b)
        raise SystemExit(1)
    print('  OK：未发现密钥；未包含 config.local.json / .pkl')

    n_files = sum(len(f) for _, _, f in os.walk(REPO))
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(REPO) for f in fs)
    print('\n完成：%d 个文件，%.1f MB' % (n_files, size / 1024 / 1024))


def write_pipeline_py():
    """run_pipeline.py：可执行的流程驱动，替代散落的手工命令。"""
    src = '''# -*- coding: utf-8 -*-
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
    ('05_analysis', '_tools_extra_stats.py',
     'trend regression, contingency analysis, software co-occurrence'),
    ('03_selection', '_update_prisma.py', 'the two-stage PRISMA chain'),
    ('05_analysis', '_rq3_summarize.py', 'RQ3 frequencies'),
    ('06_figures', '_run_figs.py', 'Figures 1-5'),
    ('06_figures', 'make_supp_fig.py', 'Supplementary Figure S1'),
    ('07_documents', '_tools_supp2.py', 'Supplementary File 2'),
    ('07_documents', '_tools_supp3.py', 'Supplementary File 3 and the provenance table'),
]

# 模型辅助步骤：复跑需要 API 密钥，默认跳过（其输出已在 04_logs/）
MODEL_STEPS = [
    ('01_screening', '_tools_prisma_reason_pass.py', 'exclusion reasons'),
    ('01_screening', '_tools_consistency.py', 'three-run agreement'),
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
        print('\\nModel-assisted steps (run with --with-model):')
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
    print('\\nDone. See 05_results/ for the regenerated statistics.')


if __name__ == '__main__':
    main()
'''
    open(os.path.join(REPO, 'run_pipeline.py'), 'w', encoding='utf-8').write(src)
    print('  + run_pipeline.py')


def write_pipeline_md():
    md = '''# Pipeline

The review is reproduced in the stages listed below. Each folder under
`02_scripts/` corresponds to one stage; `02_scripts/MANIFEST.csv` lists every
script with a one-line purpose, line count and checksum.

```
01_protocol/           prompts, codebook, sampling design, config template
02_scripts/00_lib/     shared API client, prompts and response parsers
02_scripts/01_screening/                title/abstract screening and exclusion reasons
02_scripts/02_fulltext_reassessment/    the stage-2 full-text pass of excluded records
02_scripts/03_selection/                building the locked included set and the PRISMA chain
02_scripts/04_charting/                 software canonicalisation, dates, journals, country, design
02_scripts/05_analysis/                 statistics, contingency analysis, clustering, RQ3
02_scripts/06_figures/                  Figures 1-6 and Supplementary Figure S1
02_scripts/07_documents/                supplementary files, provenance table, manuscript checks
02_scripts/08_verification/             sample re-examination: evidence pack and per-record verdicts
02_scripts/99_exploratory/              superseded one-off QC scripts (kept for the audit trail)
```

## Execution order

Model-assisted steps produce the logs in `04_logs/`; the analysis steps turn those
logs into the reported numbers. Only the analysis steps are needed to regenerate
every statistic, table and figure, because the model logs are already deposited.

**Analysis steps (no API key required)**

| # | Script | Produces |
|---|---|---|
| 1 | `04_charting/_tools_fix_dates_journals.py` | half-year periods, normalised journal names |
| 2 | `05_analysis/_tools_archetype.py` | workflow archetypes |
| 3 | `05_analysis/_tools_stats_core.py` | **`05_results/statistics_core.json` — the single source of truth** |
| 4 | `05_analysis/_tools_extra_stats.py` | trend regression, contingency analysis, co-occurrence |
| 5 | `03_selection/_update_prisma.py` | two-stage PRISMA chain |
| 6 | `05_analysis/_rq3_summarize.py` | RQ3 frequencies |
| 7 | `06_figures/_run_figs.py`, `make_supp_fig.py` | Figures 1-5, Supplementary Figure S1 |
| 8 | `07_documents/_tools_supp2.py`, `_tools_supp3.py` | Supplementary Files 2 and 3, provenance table |

`python run_pipeline.py` runs this list; `--with-model` additionally re-runs the
model-assisted steps (requires an API key).

## Path configuration

All scripts resolve the project root as

```python
ROOT = os.environ.get('SCOPING_ROOT') or <derived from the file location>
```

so they run unchanged from either the original project layout or a clone of this
repository once `SCOPING_ROOT` points at the working copy that contains the data
folders. Scripts in `99_exploratory/` were **not** normalised and keep the original
absolute paths.
'''
    open(os.path.join(REPO, 'PIPELINE.md'), 'w', encoding='utf-8').write(md)
    print('  + PIPELINE.md')


def write_readme():
    S = json.load(open(os.path.join(ANA, '统计核心_v5.json'), encoding='utf-8'))
    P = json.load(open(os.path.join(ANA, 'PRISMA_链路_v2.json'), encoding='utf-8'))
    N = S['N']
    readme = f'''# Application of Nondental 3D Software in Dentistry: A Scoping Review
## Reproducibility repository

**Repository:** https://github.com/Qihang-He/nondental-3d-software-scoping-review

Everything needed to reproduce the review is here: the search strategies, the screening and coding
prompts, every script, the raw model responses, the locked dataset, all derived statistics, the
figures' inputs, and the per-record sample re-examination verdicts.

**Locked dataset:** `06_data/locked_analysis_dataset.csv` (n = {N} included studies).
Every quantitative value in the manuscript is generated from this file by
`02_scripts/05_analysis/_tools_stats_core.py`.
See `PIPELINE.md` for the execution order and `02_scripts/MANIFEST.csv` for the full script index.

---

## 1. What changed in this version of the analysis

The decisive eligibility criterion of this review is the **explicit use of a named third-party
nondental 3D software package**. That information is normally reported in the *methods section of
the full text*, not in the abstract. In the first version of this analysis the criterion was
nevertheless applied at title/abstract level, which excluded a large number of eligible studies.

This revision therefore applies the criterion in two stages:

| Stage | Scope | Outcome |
|---|---|---|
| 1. Title/abstract screening | {P['screened_title_abstract']:,} unique records | {P['excluded_at_title_abstract']:,} excluded |
| 2. Full-text re-assessment of excluded records | every excluded record with a retrievable full text: {P['fulltext_recheck']['excluded_records_with_full_text_available']:,} records | **{P['fulltext_recheck']['records_reclassified_as_eligible']} studies met the criteria and were added** |
| Reverse check of the previously included set | same standard applied in reverse | 4 records removed (no named package in the full text); 3 software annotations corrected |
| Date-window check | publication after 30 June 2026 | 3 records removed |

The included set consequently changed from 566 to **{N} studies**.
{P['fulltext_recheck']['excluded_records_without_full_text']} excluded records had no retrievable
full text and could not be re-assessed; this residual uncertainty is stated in the manuscript.

### PRISMA chain (from `05_results/prisma_flow.json`)

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
| `01_protocol/` | Screening prompt, config template, sampling design |
| `02_scripts/` | Every script, organised by analysis stage (see `MANIFEST.csv`) |
| `03_search_strategies/` | Complete search strings and database exports for PubMed, Web of Science and IEEE Xplore |
| `04_logs/` | Raw JSON responses of all screening runs, agreement analysis, exclusion reasons, the full-text re-assessment pass, outcome coding |
| `05_results/` | Statistics core, PRISMA chain, contingency statistics, clustering parameters and labels, per-record traceability of every dataset change |
| `06_data/` | Locked analysis dataset, eligibility audit, software glossary, screening corpus, PDF-to-record matching |
| `07_supplementary/` | Supplementary Files 2 and 3, dataset provenance table |
| `08_verification/` | Sampling outputs, the evidence pack for the sampled records, and the per-record verdicts with evidence level and supporting passage |

---

## 3. Model and API details

Screening and coding used the DeepSeek chat-completions API with the identifier `deepseek-chat`,
decoding parameters `temperature = 0.1`, `max_tokens = 300-500`, `stream = false`. The identifier is
a rolling alias and is not pinned to a version; the `model` field returned by the API resolved to
`deepseek-flash` (DeepSeek-V4.1-Flash) at the time of the calls. Every entry in `04_logs/` records
the request timestamp, returned model identifier, provider response id, returned content and latency.

**No API key is stored in this repository.** `01_protocol/config.example.json` shows the expected
shape. The scripts read the key from a local `config.local.json` placed in the project's
`07_AI重跑原始记录/` folder; that file is git-ignored and is **not** part of this repository. To
re-run the model-assisted steps you must supply your own key there.

Note that the analysis steps (§PIPELINE.md) do **not** require a key at all: they consume the
model logs already deposited in `04_logs/`.

The raw model responses in `04_logs/` are retained **verbatim** in the language of the screening
pass (Chinese); the derived results, datasets and statistics under `05_results/` and `06_data/`
use English field names and labels.

## 4. What these materials do and do not establish

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

## 5. Licensing and citation

Code and data are released for reuse with attribution; see `LICENSE`. If you use these materials,
please cite the published article and this repository:
https://github.com/Qihang-He/nondental-3d-software-scoping-review

The archived dataset is available from figshare:
https://doi.org/{FIGSHARE_DOI}
'''
    open(os.path.join(REPO, 'README.md'), 'w', encoding='utf-8').write(readme)
    print('  + README.md')


def write_citation():
    cit = f'''cff-version: 1.2.0
message: "If you use these reproducibility materials, please cite both the published article and this repository."
title: "Application of Nondental 3D Software in Dentistry: A Scoping Review - reproducibility materials"
authors:
  - family-names: He
    given-names: Qihang
  - family-names: Liu
    given-names: Yuchen
  - family-names: Zhao
    given-names: Ruifeng
  - family-names: Li
    given-names: Zhiwen
  - family-names: Liu
    given-names: Miao
  - family-names: Song
    given-names: Shiwei
  - family-names: Liu
    given-names: Chen
  - family-names: Bai
    given-names: Shizhu
identifiers:
  - type: doi
    value: {FIGSHARE_DOI}
    description: figshare archive (locked dataset, n = 861)
repository-code: "https://github.com/Qihang-He/nondental-3d-software-scoping-review"
license: MIT
'''
    open(os.path.join(REPO, 'CITATION.cff'), 'w', encoding='utf-8').write(cit)
    print('  + CITATION.cff')


def write_gitignore():
    open(os.path.join(REPO, '.gitignore'), 'w', encoding='utf-8').write(
        '# Credentials - never commit\n'
        'config.local.json\n*.local.json\n.env\n*.key\n*.pem\n\n'
        '# OS / editor\n.DS_Store\nThumbs.db\ndesktop.ini\n.vscode/\n.idea/\n\n'
        '# Python\n__pycache__/\n*.pyc\n*.pyo\n\n'
        '# Large binary intermediates not required for reproduction\n*.pkl\n*.h5\n*.pt\n')
    print('  + .gitignore')


def write_license():
    open(os.path.join(REPO, 'LICENSE'), 'w', encoding='utf-8').write(
        'MIT License\n\n'
        'Copyright (c) 2026 The authors of "Application of Nondental 3D Software in Dentistry: '
        'A Scoping Review"\n\n'
        'Permission is hereby granted, free of charge, to any person obtaining a copy of this '
        'software and associated documentation files (the "Software"), to deal in the Software '
        'without restriction, including without limitation the rights to use, copy, modify, merge, '
        'publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons '
        'to whom the Software is furnished to do so, subject to the following conditions:\n\n'
        'The above copyright notice and this permission notice shall be included in all copies or '
        'substantial portions of the Software.\n\n'
        'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, '
        'INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR '
        'PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE '
        'FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR '
        'OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER '
        'DEALINGS IN THE SOFTWARE.\n')
    print('  + LICENSE')


if __name__ == '__main__':
    build()
