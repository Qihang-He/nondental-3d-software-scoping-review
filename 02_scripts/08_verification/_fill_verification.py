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
_fill_verification.py —— 依据作者的复核意见填回核验工作簿，并附客观复核证据

作者结论（用户 2026-09-12 复核）：
  · 未提及的 A 表条目视为"同意排除"；B 表未发现应剔除条目
  · 点出 9 条存疑（104/153/157/23/33/117/137/55/119）及 3 条需复核（107/160/152）
本项目对上述条目做了独立复核（含 PDF 全文核验），逐条给出裁定与证据。
"""
import os
import re
import pandas as pd
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.styles import Font, Alignment, PatternFill

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '08_分析用')
XL = os.path.join(ROOT, _os.path.join(_ROOTP, '02_图表附件'), 'R2_补充材料', '作者核验工作簿.xlsx')

# 作者裁定 + 客观复核（编号 -> (是否同意排除, 应归原因, 复核证据)）
VERDICT = {
    104: ('同意排除', '未使用非牙科专用3D软件',
          '主题确属口腔医学（牙体牙髓再生），原原因标签有误；该文为 PCL/HA 支架的3D打印材料学研究，'
          '未使用任何命名的非牙科3D软件，排除决定成立。'),
    153: ('同意排除', '未使用非牙科专用3D软件',
          '主题确属口腔医学（口腔癌），原原因标签有误；但所用为自建 U-Net 变体分割 H&E 二维组织'
          '病理图像，非3D软件，排除决定成立。'),
    157: ('同意排除', '未使用非牙科专用3D软件',
          '主题确属口腔颌面外科，原原因标签有误；所用 nnU-Net 为自研深度学习分割框架。'
          '纳入集85种软件中不含任何深度学习框架，按同一口径（需为具名的第三方软件包）排除决定成立；'
          '该口径已在 Methods 中明确。'),
    23: ('同意排除', '未使用非牙科专用3D软件',
          'PDF 首页明确标注 ORIGINAL ARTICLE，原"文献类型不符"标签有误；但全文核验显示其使用的 '
          'Relu Creator 为**牙科专用**AI 分割平台，不属非牙科软件，排除决定成立。'),
    33: ('应纳入', '—',
          '★确认漏排。PDF 首页明确标注 ORIGINAL ARTICLE；全文明确写有"3D analysis software '
          '(Geomagic Studio, Raindrop, USA)"用于比较植入与计划种植体位置。Geomagic Studio 已在'
          '纳入集软件表中（24 篇研究使用），故该文满足全部纳入标准，应补入。'),
    117: ('同意排除', '未使用非牙科专用3D软件',
          'Sc Rep 原创研究，原"文献类型不符"标签有误；但为自建多模态深度集成框架，输入为口内二维'
          '图像，未使用非牙科3D软件，排除决定成立。'),
    137: ('同意排除', '文献类型不符',
          'Odontology PDF 首页明确标注 REVIEW ARTICLE（integrative review），排除决定成立；'
          '原标签"未使用非牙科专用3D软件"有误，应改为"文献类型不符"。'),
    55: ('不确定', '—',
          'J Prosthet Dent 2026（无全文可取）。摘要显示使用"AI-driven platform"完成 CBCT/IOS 分割'
          '与配准并生成3D咬合模型，主题与3D处理均符合，但平台是否属非牙科软件无法从摘要判定，'
          '建议获取全文后再定。不计入已确认漏排。'),
    119: ('同意排除', '不属于口腔医学范畴',
          'Phys Med Biol 通用 CBCT 高锥角伪影研究，摘要与期刊均无牙科背景，原原因标签可保留，'
          '排除决定成立。'),
    107: ('同意排除', '未使用非牙科专用3D软件',
          '眶爆裂骨折经口内镜钛网修复术式报告，仅提及"术后 CT 3D 重建"，未使用任何具名的非牙科'
          '3D 软件，排除决定成立。'),
    160: ('同意排除', '未使用非牙科专用3D软件',
          '自研 CoTracker 跟踪 + 模糊控制器，离体猪舌实验，未使用第三方3D软件，排除决定成立。'),
    152: ('同意排除', '未使用非牙科专用3D软件',
          '会议论文；自研 graph-cut 分割、marching cubes 重建与 ICP 配准，无第三方3D软件，'
          '排除决定成立。'),
}

sa = pd.read_csv(os.path.join(ANA, '核验抽样_样本A明细.csv'), low_memory=False).reset_index(drop=True)
sa['编号'] = sa.index + 1
sb = pd.read_csv(os.path.join(ANA, '核验抽样_样本B明细.csv'), low_memory=False).reset_index(drop=True)
sb['编号'] = sb.index + 1

# 纳入集软件全文核验结果（用于 B 表补充客观证据）
vfp = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), '05_审计与核验', 'PDF核验', 'PDF软件核验_逐篇.csv')
vfy = {}
if os.path.exists(vfp):
    v = pd.read_csv(vfp, low_memory=False)
    tc = [c for c in v.columns if 'Title' in str(c) or '标题' in str(c)][0]
    sc = [c for c in v.columns if '软件' in str(c) and '是否' in str(c)]
    vfy = {'_cols': list(v.columns), 'n': len(v), 'title_col': tc, 'status_cols': sc}
    print('PDF 核验表列:', list(v.columns))
    print(v.head(2).to_string()[:500])

wb = load_workbook(XL)
wsA = wb['A_排除抽样（200条）']
# 定位列
hdr = [c.value for c in wsA[1]]
iA = hdr.index('【作者请填写】是否同意排除') + 1
iR = hdr.index('【作者请填写】如不同意，理由/应归原因') + 1
# 新增两列：应归原因 / 复核证据
c1 = len(hdr) + 1
c2 = c1 + 1
wsA.cell(row=1, column=c1, value='建议应归原因')
wsA.cell(row=1, column=c2, value='复核证据（含PDF全文核验）')
for c in (c1, c2):
    wsA.cell(row=1, column=c).font = Font(bold=True, color='FFFFFF')
    wsA.cell(row=1, column=c).fill = PatternFill('solid', fgColor='1F4E78')
    wsA.cell(row=1, column=c).alignment = Alignment(vertical='center', wrap_text=True)

for r in range(2, len(sa) + 2):
    n = int(wsA.cell(row=r, column=1).value)
    if n in VERDICT:
        v, reason, ev = VERDICT[n]
        wsA.cell(row=r, column=iA, value=v)
        wsA.cell(row=r, column=iR, value=('原因标签有误' if v == '同意排除' and reason else
                                          ('确认漏排，需补入' if v == '应纳入' else '待全文核验')))
        wsA.cell(row=r, column=c1, value=reason)
        wsA.cell(row=r, column=c2, value=ev)
    else:
        wsA.cell(row=r, column=iA, value='同意排除')
wsA.column_dimensions[chr(64 + c1)].width = 26
wsA.column_dimensions[chr(64 + c2)].width = 70
dv = DataValidation(type='list', formula1='"同意排除,应纳入,不确定"', allow_blank=True)
wsA.add_data_validation(dv)
dv.add('%s2:%s%d' % (chr(64 + iA), chr(64 + iA), len(sa) + 1))

wsB = wb['B_纳入抽样（100条）']
hdrB = [c.value for c in wsB[1]]
iB = hdrB.index('【作者请填写】是否符合纳入标准（是/否）') + 1
iBR = hdrB.index('【作者请填写】如不符合，理由') + 1

# 用全文文本匹配结果给出客观证据列
vmap = {}
if os.path.exists(vfp):
    v = pd.read_csv(vfp, low_memory=False)
    vmap = {str(r['ID']).strip(): (str(r['核验']), str(r['命中']), str(r['未命中']))
            for _, r in v.iterrows()}
cB1 = len(hdrB) + 1
wsB.cell(row=1, column=cB1, value='全文本核对软件标注的核验结果（客观证据）')
wsB.cell(row=1, column=cB1).font = Font(bold=True, color='FFFFFF')
wsB.cell(row=1, column=cB1).fill = PatternFill('solid', fgColor='1F4E78')
wsB.cell(row=1, column=cB1).alignment = Alignment(vertical='center', wrap_text=True)
doi_of = {}
_d = pd.read_csv(os.path.join(ANA, '分析数据集_final_v3.csv'), low_memory=False)
_nt2doi = dict(zip(_d['Title'].map(lambda s: re.sub(
    r'[^0-9a-zA-Z]+', ' ', str(s)).lower().strip()), _d['DOI']))
_dk = dict(zip(_d['Key'].astype(str), _d['DOI']))
for r in range(2, len(sb) + 2):
    n = int(wsB.cell(row=r, column=1).value)
    row = sb.iloc[n - 1] if n - 1 < len(sb) else None
    d = ''
    if row is not None:
        d = str(_dk.get(str(row['Key']), '') or '').strip()
    st = vmap.get(d)
    wsB.cell(row=r, column=cB1, value=(
        ('核验=%s；命中 %s；未命中 %s' % st) if st else '无全文或未纳入文本核验'))
wsB.column_dimensions[chr(64 + cB1)].width = 60

for r in range(2, len(sb) + 2):
    wsB.cell(row=r, column=iB, value='是')
    wsB.cell(row=r, column=iBR,
             value='作者未见不符合纳入标准者；软件标注无法仅凭摘要核验，'
                   '已另用全文文本匹配单独核验（见 Supplementary File 3 与仓库）')
dv2 = DataValidation(type='list', formula1='"是,否"', allow_blank=True)
wsB.add_data_validation(dv2)
dv2.add('%s2:%s%d' % (chr(64 + iB), chr(64 + iB), len(sb) + 1))

wb.save(XL)
print('已填回:', XL)
print('A 表：同意排除 %d，应纳入 %d，不确定 %d'
      % (len(sa) - len([k for k, v in VERDICT.items() if v[0] != '同意排除']),
         len([k for k, v in VERDICT.items() if v[0] == '应纳入']),
         len([k for k, v in VERDICT.items() if v[0] == '不确定'])))
print('B 表：全部填"是"（%d 条）' % len(sb))
