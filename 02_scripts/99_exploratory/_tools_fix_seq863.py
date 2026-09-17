# -*- coding: utf-8 -*-
"""
_tools_fix_seq863.py —— 补标序号 863 的软件（编码遗漏）

背景：该纳入研究（Denadai et al. 2021, J Plast Reconstr Aesthet Surg）在阶段二全文重评时
      被纳入，但软件字段漏填，导致"单软件 525 vs 统计核心 526"的内部不一致。
证据：全文明确写有 "Geomagic 3D software, 3D Systems, Rock Hill, SC, USA"，用于配准精度
      的距离色图核验（reverse-engineering / metrology 用途，属非牙科软件）。
      全文另提及 Dolphin 3D（牙科专用，不在本综述范围）、ProPlan（Materialise）与
      3dMD Vultus；本次按作者确认，仅补标注已在规范名清单中的 Geomagic。

输出：写回 分析数据集_final_v4.csv，并追加一条变更记录。
"""
import os
import pandas as pd

ROOT = r'd:\Desktop\v8 for JD'
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
FP = os.path.join(ANA, '分析数据集_final_v4.csv')
SOFT = 'Geomagic (unspecified)'

d = pd.read_csv(FP, low_memory=False)
m = d['序号'] == 863
assert m.sum() == 1, '未定位到唯一目标记录'
_cur = str(d.loc[m, 'Software Used (fixed)'].iloc[0]).strip()
assert _cur in ('nan', '', 'None'), '该记录已有软件标注（%s），请复核后再执行' % _cur

d.loc[m, 'Software Used (fixed)'] = SOFT
d.loc[m, '_soft2'] = str([SOFT])
d.loc[m, '裁定3'] = '补标软件'
d.loc[m, '裁定3理由'] = ('编码遗漏修正：全文第 3 页写明 "Geomagic 3D software, 3D Systems, '
                         'Rock Hill, SC, USA"，用于术前术后三维配准精度核验；'
                         '该软件属逆向工程/计量范畴，符合非牙科软件纳入标准。')

d.to_csv(FP, index=False, encoding='utf-8-sig')
print('已写回', FP)

chg = pd.DataFrame([{
    '序号': 863, 'Key': '3LP7326M',
    'Title': 'Type of maxillary segment mobilization affects three-dimensional nasal morphology',
    '字段': 'Software Used (fixed) / _soft2',
    '原值': '(空)',
    '新值': SOFT,
    '证据': '全文: "Geomagic 3D software, 3D Systems, Rock Hill, SC, USA"，用于配准精度距离色图核验',
}])
out = os.path.join(ANA, '软件补标_863.csv')
chg.to_csv(out, index=False, encoding='utf-8-sig')
print('变更记录:', out)
print(d[m][['序号', 'Software Used (fixed)', '_soft2']].to_string(index=False))
