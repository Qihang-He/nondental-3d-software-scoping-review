# -*- coding: utf-8 -*-
"""
_tools_pack_verify.py —— 打包人工核验材料：
  - 核对表（含"模型辅助初判"列，供作者确认/更正）
  - 对应 PDF（按编号重命名，可直接点开）
  - 工作说明

输出目录：<ROOT>/人工核验包/
"""
import os, re, shutil
import pandas as pd

ROOT = (os.environ.get('SCOPING_ROOT')
        or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
PDFDIR = os.path.join(ROOT, '10_全文PDF库')
PKG = os.path.join(ROOT, '人工核验包')

# ---------- 模型辅助初判（2026-09-16，供作者确认） ----------
INC_DEFAULT = ('确认：软件使用属实', '证据片段显示该研究实际使用了具名的非牙科 3D 软件。')
INC_OVR = {
    2:  ('确认，软件名建议复核', '首段证据显示 ImageJ，标注为 Mimics；可能为多软件或标注名不一致，请核对全文。'),
    5:  ('确认，软件名建议复核', '首段证据显示 Meshmixer，标注为 Mimics。'),
    11: ('确认，证据较弱', '证据片段未命中 nTop，请打开全文确认。'),
    19: ('确认，软件名建议复核', '证据显示 Brainlab iPlan，标注为 Meshmixer。'),
    23: ('确认，证据较弱', '证据未命中 Fusion 360。'),
    27: ('确认，软件名建议复核', '证据显示 Abaqus，标注为 Mimics。'),
    29: ('确认，证据较弱', '证据未命中软件名，请打开全文确认。'),
    36: ('确认，证据较弱', '证据未命中 InVesalius。'),
    39: ('确认，软件名建议复核', '证据显示 Abaqus，标注为 Siemens NX/Mimics/Magics。'),
    41: ('确认，软件名建议复核', '证据显示 HyperMesh，标注为 Mimics/ABAQUS/Geomagic Wrap。'),
    44: ('确认，软件名建议复核', '证据显示 TensorFlow，标注为 3D Slicer。'),
    48: ('无全文，需另行核对', '未定位到全文 PDF；标题似为综述性质，请一并确认文献类型。'),
    57: ('确认，证据较弱', '证据未命中 SolidWorks/ABAQUS。'),
    65: ('确认，证据较弱', '证据未命中软件名，请打开全文确认。'),
    67: ('确认，证据较弱', '证据未命中 Mimics/3-Matic。'),
    77: ('确认，软件名建议复核', '证据显示 VRMesh，标注为 Simpleware/Rhinoceros。'),
    89: ('确认，软件名建议复核', '证据显示 ImageJ，标注为 Creo。'),
    90: ('确认，软件名建议复核', '证据显示 Geomagic Studio，标注为 Mimics。'),
    97: ('确认，证据较弱', '证据未命中软件名，请打开全文确认。'),
    98: ('确认，软件名建议复核', '证据显示 Geomagic Verify，标注为 Magics。'),
}
EXC_DEFAULT = ('同意排除', '证据与排除理由一致。')
EXC_OVR = {
    2:  ('同意排除（边缘）', 'MATLAB 仅用于标注，未用于 3D 处理。'),
    14: ('同意排除（边缘）', 'MATLAB 用于 OCT 二维图像处理，不属于 3D 软件使用。'),
    33: ('建议复核（可能漏纳）', '该研究用 MATLAB 实现 Dijkstra 算法对牙列 3D 模型分割；若视 MATLAB 为具名非牙科软件且用于 3D 处理，可能应纳入。'),
    43: ('建议复核（主题归属）', '判定理由显示其使用了 3D Slicer 设计支架；需确认主题是否属口腔范畴。'),
    44: ('建议复核（可能漏纳）', '使用 Open3D/VTK/PyTorch 做下颌骨重建自动规划；Open3D/VTK 为具名非牙科 3D 处理库，可能应纳入。'),
}

ILLEGAL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def clean(v):
    if isinstance(v, str):
        v = ILLEGAL.sub(' ', v)
        return re.sub(r'\s+', ' ', v).strip()
    return v


def idx_pdfs():
    """文件名 -> 全路径。"""
    d = {}
    for tdir, _, fs in os.walk(PDFDIR):
        for f in fs:
            if f.lower().endswith('.pdf'):
                d.setdefault(f, os.path.join(tdir, f))
    return d


def main():
    v1 = pd.read_csv(os.path.join(ANA, '作者核验_纳入抽样100.csv'), encoding='utf-8-sig', low_memory=False)
    v2 = pd.read_csv(os.path.join(ANA, '作者核验_排除抽样50.csv'), encoding='utf-8-sig', low_memory=False)
    idx = idx_pdfs()

    if os.path.exists(PKG):
        shutil.rmtree(PKG)
    os.makedirs(os.path.join(PKG, 'PDF'))

    # ---- 工作表1 ----
    for _, r in v1.iterrows():
        i = int(r['编号'])
        concl, why = INC_OVR.get(i, INC_DEFAULT)
        v1.loc[v1['编号'] == i, '模型辅助初判'] = concl
        v1.loc[v1['编号'] == i, '初判依据'] = why

    # ---- 工作表2 ----
    for _, r in v2.iterrows():
        i = int(r['编号'])
        concl, why = EXC_OVR.get(i, EXC_DEFAULT)
        v2.loc[v2['编号'] == i, '模型辅助初判'] = concl
        v2.loc[v2['编号'] == i, '初判依据'] = why

    # ---- 复制 PDF ----
    copied = 0
    missing = []
    for prefix, df in (('I', v1), ('E', v2)):
        for _, r in df.iterrows():
            fn = r.get('全文PDF', '')
            if not isinstance(fn, str) or fn in ('', '（未定位到全文）', 'nan'):
                continue
            src = idx.get(fn)
            if not src:
                missing.append('%s%02d %s' % (prefix, int(r['编号']), fn))
                continue
            dst = os.path.join(PKG, 'PDF', '%s%02d_%s.pdf' % (prefix, int(r['编号']), r['Key']))
            shutil.copy2(src, dst)
            copied += 1

    # ---- 写入核对表 ----
    for df in (v1, v2):
        df = df.map(clean)
    xp = os.path.join(PKG, '核对表.xlsx')
    with pd.ExcelWriter(xp, engine='openpyxl') as w:
        pd.DataFrame({
            '项目': ['核对内容', '来源', '初判列说明', '填写要求', 'PDF 文件夹', '完成后'],
            '说明': [
                '逐条核对两条最关键的数据：(1) 研究是否确实使用了具名的非牙科专用 3D 软件；(2) 学科归属是否正确。排除抽样另需判断是否存在本应纳入而漏纳的情况。',
                '纳入 100 条来自最终纳入集（n=863）简单随机抽样；排除 50 条来自全文复评确认不符合的记录（n=864）简单随机抽样；种子 20260915，可由脚本复现。',
                '模型辅助初判是助手模型的第二遍独立复核结论，仅供作者快速定位，不构成人工核验；作者必须逐条确认或更正。',
                '在作者填写列填 是/同意 或 否/不同意；不同意请写明正确内容。留空视为未核验。',
                'PDF 文件夹内文件按 I01_Key / E01_Key 命名，与核对表编号一一对应；无对应 PDF 的记录已单独标出。',
                '填完后告知助手，由脚本汇总为可写入论文的核验结果句段。',
            ],
        }).to_excel(w, sheet_name='0_说明', index=False)
        v1.to_excel(w, sheet_name='1_纳入抽样核验（100条）', index=False)
        v2.to_excel(w, sheet_name='2_排除抽样核验（50条）', index=False)

    # ---- 工作说明 ----
    guide = """# 人工核验工作说明

## 你要做什么
逐条核对两件事，并在【作者填写】列填结果：
1. **纳入抽样（100 条）**：这篇研究是不是真的用了"具名的非牙科专用 3D 软件"？学科标得对不对？
2. **排除抽样（50 条）**：这篇被我们排除的记录，排除得对不对？有没有"本应纳入却漏了"的？

## 文件怎么对应
- `核对表.xlsx` —— 三个工作表：0_说明 / 1_纳入抽样核验 / 2_排除抽样核验
- `PDF\\` 文件夹 —— 每条记录对应的全文，按 `I01_Key.pdf`、`E01_Key.pdf` 命名，
  编号与核对表一一对应，直接双击打开

## 表里的"模型辅助初判"是什么
这是助手模型的第二遍独立复核结论，**只是给你定位用的，不是你的人工核验**。
你需要在【作者填写】列逐条确认或更正。留空 = 未核验，会在统计时单独列出。

## 重点看这几条
纳入抽样里标"软件名建议复核/证据较弱/无全文"的约 20 条，请打开 PDF 确认软件名。
排除抽样里标"建议复核"的 3 条（E33、E43、E44）最值得看：
- E33：用 MATLAB 做牙列 3D 模型分割，可能算漏纳
- E43：用了 3D Slicer 设计支架，需确认主题是否属口腔
- E44：用 Open3D/VTK 做下颌骨重建，可能算漏纳

## 大约要花多久
每条 1–3 分钟；优先看"建议复核"和"软件名建议复核"的条目，其余可快速过。

## 完成后
告诉助手"核验表已填好"，助手会运行汇总脚本，生成核验一致率与可写入论文的句段。
"""
    with open(os.path.join(PKG, '工作说明.md'), 'w', encoding='utf-8') as f:
        f.write(guide)

    print('已生成 %s' % PKG)
    print('  核对表.xlsx（3 个工作表）')
    print('  PDF 文件夹：%d 个文件' % copied)
    if missing:
        print('  未能定位的 PDF（%d）：' % len(missing))
        for m in missing:
            print('    ', m)
    print('  工作说明.md')
    print()
    print('纳入初判分布：')
    print(v1['模型辅助初判'].value_counts().to_string())
    print()
    print('排除初判分布：')
    print(v2['模型辅助初判'].value_counts().to_string())


if __name__ == '__main__':
    main()
