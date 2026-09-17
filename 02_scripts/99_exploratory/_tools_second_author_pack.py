# -*- coding: utf-8 -*-
"""生成第二位作者的独立审核包。此包不含第一位作者的结论。"""
import os, shutil, re
import pandas as pd

ROOT = (os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PKG = os.path.join(ROOT, '第二作者独立审核包')
SOURCE = os.path.join(ROOT, '人工核验包')
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
PDFDIR = os.path.join(SOURCE, 'PDF')
SEED = 20260916
N_INC, N_EXC = 30, 20


def main():
    src = pd.ExcelFile(os.path.join(SOURCE, '核对表.xlsx'))
    inc = src.parse('1_纳入抽样核验（100条）')
    exc = src.parse('2_排除抽样核验（50条）')
    # 不从第一作者完成表读取，以防意外泄露其结论；重新抽样并只保留必要事实字段。
    i = inc.sample(n=N_INC, random_state=SEED).copy()
    e = exc.sample(n=N_EXC, random_state=SEED + 1).copy()
    inc_cols = ['编号','Key','标题','期刊','年份','全文PDF','数据集标注的软件','数据集标注的学科','数据集标注的应用场景','原文证据片段（供快速定位）']
    exc_cols = ['编号','Key','标题','期刊','文献类型','全文PDF','原文证据片段（供快速定位）']
    i = i[inc_cols].rename(columns={'编号':'原始样本编号'})
    e = e[exc_cols].rename(columns={'编号':'原始样本编号'})
    i['独立审核编号'] = range(1, len(i)+1)
    e['独立审核编号'] = range(1, len(e)+1)
    i['【第二作者填写】软件使用是否属实（是/否）'] = ''
    i['【第二作者填写】学科归属是否正确（是/否）'] = ''
    i['【第二作者填写】如不正确，请填写更正'] = ''
    i['【第二作者填写】备注'] = ''
    e['【第二作者填写】是否同意排除（同意/不同意）'] = ''
    e['【第二作者填写】如不同意，请填写纳入理由和软件名'] = ''
    e['【第二作者填写】备注'] = ''

    if os.path.exists(PKG): shutil.rmtree(PKG)
    os.makedirs(os.path.join(PKG, 'PDF'))
    copied = 0
    for prefix, df in [('I', i), ('E', e)]:
        for _, r in df.iterrows():
            fn = str(r['全文PDF'])
            if fn in ('', 'nan', '（未定位到全文）'): continue
            # 原PDF在人工核验包中按 Ixx_Key / Exx_Key 命名；按原始编号匹配。
            stem = '%s%02d_%s.pdf' % (prefix, int(r['原始样本编号']), r['Key'])
            srcpdf = os.path.join(PDFDIR, stem)
            if not os.path.exists(srcpdf):
                # 兼容 I48 的补充PDF：第二作者审核包仍明确标出缺失。
                continue
            shutil.copy2(srcpdf, os.path.join(PKG, 'PDF', '%s%02d_%s.pdf' % (prefix, int(r['独立审核编号']), r['Key'])))
            copied += 1

    guide = pd.DataFrame({
        '项目':['目的','审核范围','独立性','审核标准','填写要求','PDF','完成后'],
        '说明':[
            '对第一作者完成的人工质量核验进行独立抽查；本审核不是对原始AI筛查的重新全量复核。',
            '纳入样本30条；排除样本20条；随机种子 %d。'%SEED,
            '请在查看任何第一作者结论前独立填写本表。不要打开“人工核验包/核对表_作者已完成.xlsx”。',
            '按论文纳入标准核对全文：具名非牙科3D软件实际使用、口腔医学范围、文献类型和日期条件。',
            '只填写“第二作者填写”列；如果无法判断，填“无法判断”并说明原因。',
            'PDF按 I01_Key / E01_Key 命名，与本包的独立审核编号对应；如缺失请记录。',
            '完成后保存本表，并将第一作者结果与本表逐条比较，记录一致、不一致和讨论后的最终结论；不要事后修改原始独立答案。',
        ]
    })
    with pd.ExcelWriter(os.path.join(PKG, '独立审核表.xlsx'), engine='openpyxl') as w:
        guide.to_excel(w, sheet_name='0_工作说明', index=False)
        i.to_excel(w, sheet_name='1_纳入独立审核30条', index=False)
        e.to_excel(w, sheet_name='2_排除独立审核20条', index=False)
    with open(os.path.join(PKG, '工作说明.md'), 'w', encoding='utf-8') as f:
        f.write('''# 第二作者独立审核说明\n\n'
请先独立阅读全文并填写 `独立审核表.xlsx`，不要查看第一作者的已完成表。\n\n'
- 纳入样本：30 条；核对软件使用和学科归属。\n- 排除样本：20 条；核对排除决定，特别关注是否应纳入。\n- 随机种子：20260916。\n- 所有答案必须在比较前保存。\n- 完成后再与第一作者结果比较，并单独记录分歧。\n''')
    i.to_csv(os.path.join(PKG, 'included_independent_review_30.csv'), index=False, encoding='utf-8-sig')
    e.to_csv(os.path.join(PKG, 'excluded_independent_review_20.csv'), index=False, encoding='utf-8-sig')
    print('已生成:', PKG)
    print('纳入:',len(i),'排除:',len(e),'PDF:',copied)

if __name__ == '__main__': main()
