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
_tools_verify_workbook.py —— 生成"作者核验工作簿"（方案 A）
设计（诊断准确性评估）：
  样本 A（筛查阶段被排除的记录，共 1,943 条）
      分层随机抽样（按排除原因分层、按比例分配），n = 200
      目的：估计"被错误排除的合格研究"比例；若 0 例，报告精确单侧 95% 上界（Clopper–Pearson）
  样本 B（最终纳入的记录，共 566 条）
      简单随机抽样，n = 100
      目的：核验纳入判定；报告不一致比例与 95% CI
抽样用固定随机种子（20260912）——完全可复现。
作者只需在 Excel 中逐行选择"同意 / 不同意"；随后自动汇总。
输出：02_图表附件/R2_补充材料/作者核验工作簿.xlsx
      03_数据/08_分析用/核验抽样_设计.json
"""
import os
import json
import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
OUTDIR = os.path.join(ROOT, _os.path.join(_ROOTP, '02_图表附件'), 'R2_补充材料')
os.makedirs(OUTDIR, exist_ok=True)
SEED = 20260912
N_A, N_B = 200, 100

REASON_LABEL = {
    1: '不属于口腔医学范畴',
    2: '文献类型不符（综述/社论/会议摘要等）',
    3: '未使用非牙科专用3D软件',
    4: '不在预设时间窗内',
    5: '其他',
}


def upper_bound(k, n, alpha=0.05):
    """观测到 k 例阳性中的单侧 95% 上界（Clopper–Pearson）"""
    if k >= n:
        return 1.0
    return float(beta.ppf(1 - alpha, k + 1, n - k))


d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v4.csv'), low_memory=False)
universe = pd.read_csv(os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '02_清洗后',
                                    '筛选语料_唯一记录_2556.csv'), low_memory=False)


def nt(s):
    import re
    s = re.sub(r'<[^>]+>', ' ', str(s))
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


universe['_nt'] = universe['Title'].map(nt)
d['_nt'] = d['Title'].map(nt)
in_set = set(d['_nt'])

# ---- 样本 A：筛查阶段被排除 ----
rp = os.path.join(ANA, 'prisma_pass', 'reason_parsed.csv')
if os.path.exists(rp):
    rz = pd.read_csv(rp, low_memory=False)
    rz = rz.drop_duplicates('_nt')
    rz['排除原因'] = rz['原因代码'].map(REASON_LABEL).fillna('未归类')
    popA = rz[['_nt', 'Title', '原因代码', '排除原因']].copy()
else:
    popA = pd.DataFrame({'原因代码': [], '排除原因': []})
    print('!! 尚未生成 reason_parsed.csv，样本 A 将退化为简单随机抽样')

# 补齐摘要
_ac = 'Abstract' if 'Abstract' in universe.columns else 'Abstract Note'
abst = universe.set_index('_nt')[_ac].to_dict()
keymap = universe.set_index('_nt')['Key'].to_dict()
popA['Abstract'] = popA['_nt'].map(abst)
popA['Key'] = popA['_nt'].map(keymap)
popA = popA[popA['Abstract'].notna()]

rng = np.random.default_rng(SEED)
if popA['排除原因'].nunique() > 1:
    # 按原因分层、比例分配
    strata = popA.groupby('排除原因')
    n_total = len(popA)
    picks = []
    alloc = {}
    for name, g in strata:
        k = max(1, int(round(N_A * len(g) / n_total)))
        k = min(k, len(g))
        alloc[name] = k
        picks.append(g.sample(n=k, random_state=SEED))
    sampleA = pd.concat(picks, ignore_index=True)
    # 若四舍五入导致总数偏离，随机增删到 N_A
    if len(sampleA) > N_A:
        sampleA = sampleA.sample(n=N_A, random_state=SEED)
    elif len(sampleA) < N_A:
        rest = popA[~popA['_nt'].isin(sampleA['_nt'])]
        add = rest.sample(n=min(N_A - len(sampleA), len(rest)), random_state=SEED)
        sampleA = pd.concat([sampleA, add], ignore_index=True)
    sampleA = sampleA.sample(frac=1, random_state=SEED).reset_index(drop=True)
else:
    alloc = {}
    sampleA = popA.sample(n=min(N_A, len(popA)), random_state=SEED).reset_index(drop=True)

# ---- 样本 B：最终纳入 ----
popB = d[['序号', 'Key', 'Title', 'DOI', 'Journal', '_nt', 'Dental Specialty',
          'Software Used (fixed)']].copy()
popB['Abstract'] = popB['_nt'].map(abst)
popB = popB.rename(columns={'Dental Specialty': '专业',
                            'Software Used (fixed)': '软件'})
sampleB = popB.sample(n=min(N_B, len(popB)), random_state=SEED).reset_index(drop=True)


def shrink(s):
    return (s.astype(str).str.slice(0, 900))


sheetA = pd.DataFrame({
    '编号': range(1, len(sampleA) + 1),
    '标题': sampleA['Title'].values,
    '摘要（截断至900字符）': shrink(sampleA['Abstract']).values,
    'AI/流程判定': '排除（筛查阶段）',
    '流程记录的原因': sampleA['排除原因'].values,
    '【作者请填写】是否同意排除': '',
    '【作者请填写】如不同意，理由/应归原因': '',
})
sheetB = pd.DataFrame({
    '编号': range(1, len(sampleB) + 1),
    '标题': sampleB['Title'].values,
    '摘要（截断至900字符）': shrink(sampleB['Abstract']).values,
    'AI 标注的专科': sampleB['专业'].values,
    'AI 标注的软件': sampleB['软件'].values,
    '【作者请填写】是否符合纳入标准（是/否）': '',
    '【作者请填写】如不符合，理由': '',
})

info = pd.DataFrame({
    '项目': ['核验目的', '样本 A', '样本 B', '抽样方法', '随机种子', '为何样本量是 200 而非 384',
             '统计解释', '预估用时', '填写方式', '责任说明', '生成日期'],
    '说明': [
        '核验 LLM 辅助筛选的判定质量，以便在论文中报告可核验的人工核验结果。',
        '从"筛查阶段被排除"的 %d 条记录中分层随机抽取 %d 条（按排除原因分层、按比例分配）。'
        % (len(popA), len(sampleA)),
        '从"最终纳入"的 %d 条记录中简单随机抽取 %d 条。' % (len(popB), len(sampleB)),
        '按排除原因分层、比例分配的随机抽样；全部抽样过程由脚本完成并记录随机种子。',
        str(SEED),
        '若样本中"被错误排除"的例数为 0，则用 Clopper–Pearson 精确法给出单侧 95% 上界 = 3/n。'
        'n=200 时上界为 1.5%，即"错误排除率不超过约 1.5%"，这比把样本量加到 384 更有信息量也更省时。',
        '样本 A：报告错误排除例数与其精确 95% 上界；样本 B：报告不符合纳入标准的例数与其 95% CI。',
        '样本 A 约 200 条、样本 B 约 100 条，按每条 20–30 秒计，合计约 1.5–2 小时。',
        '只需在带【作者请填写】的两列中填写。选择项已设为下拉菜单。',
        '核验结果由作者本人填写并署名，作为"作者确认"的证据；未填写前不得在稿件中声明已完成人工核验。',
        '2026-09-12',
    ],
})

xls = os.path.join(OUTDIR, '作者核验工作簿.xlsx')
with pd.ExcelWriter(xls, engine='openpyxl') as w:
    info.to_excel(w, sheet_name='0_说明与填写方法', index=False)
    sheetA.to_excel(w, sheet_name='A_排除抽样（200条）', index=False)
    sheetB.to_excel(w, sheet_name='B_纳入抽样（100条）', index=False)

    from openpyxl.worksheet.datavalidation import DataValidation
    wsA = w.sheets['A_排除抽样（200条）']
    dv = DataValidation(type='list', formula1='"同意排除,应纳入,不确定"', allow_blank=True)
    wsA.add_data_validation(dv)
    col = sheetA.columns.get_loc('【作者请填写】是否同意排除') + 1
    L = chr(64 + col)
    dv.add('%s2:%s%d' % (L, L, len(sheetA) + 1))
    wsB = w.sheets['B_纳入抽样（100条）']
    dv2 = DataValidation(type='list', formula1='"是,否"', allow_blank=True)
    wsB.add_data_validation(dv2)
    col2 = sheetB.columns.get_loc('【作者请填写】是否符合纳入标准（是/否）') + 1
    L2 = chr(64 + col2)
    dv2.add(dv2.sqref if False else '%s2:%s%d' % (L2, L2, len(sheetB) + 1))
    for ws in (wsA, wsB):
        ws.column_dimensions['A'].width = 6
        for c in range(2, 8):
            ws.column_dimensions[chr(64 + c)].width = 34 if c < 5 else 26
        ws.freeze_panes = 'B2'

design = {
    'seed': SEED,
    'population_A_screening_excluded': int(len(popA)),
    'sample_A_n': int(len(sampleA)),
    'allocation_A': {str(k): int(v) for k, v in alloc.items()},
    'population_B_included': int(len(popB)),
    'sample_B_n': int(len(sampleB)),
    'decision_rule': '若样本 A 中错误排除例数为 0，报告 Clopper-Pearson 单侧 95% 上界 3/n',
    'upper_bound_if_zero_A': round(upper_bound(0, len(sampleA)), 4),
}
json.dump(design, open(os.path.join(ANA, '核验抽样_设计.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
sampleA[['_nt', 'Key', 'Title', '排除原因']].to_csv(
    os.path.join(ANA, '核验抽样_样本A明细.csv'), index=False, encoding='utf-8-sig')
sampleB[['_nt', 'Key', 'Title']].to_csv(
    os.path.join(ANA, '核验抽样_样本B明细.csv'), index=False, encoding='utf-8-sig')

print(json.dumps(design, ensure_ascii=False, indent=2))
print('[saved]', xls)
