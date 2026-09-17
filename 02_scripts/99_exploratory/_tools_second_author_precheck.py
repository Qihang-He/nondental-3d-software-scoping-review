# -*- coding: utf-8 -*-
"""为第二作者审核包生成独立的模型预审意见；不填写第二作者答案。"""
import os, re
import pandas as pd

ROOT = (os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PKG = os.path.join(ROOT, '第二作者独立审核包')

# 仅表示预审意见，不能替代第二作者的独立判断。
INC_WEAK = {4, 10, 11, 18, 21, 24, 26, 30}
INC_RECHECK = {4, 10, 11, 18, 21, 24, 26, 30}
EXC_RECHECK = {4, 6, 7, 9, 11, 12, 17, 28, 29, 31, 32, 33, 34, 36, 38}
EXC_POSSIBLE = {4, 6, 7, 9, 11, 12, 17, 28, 29, 31, 32, 33, 34, 36, 38}


def main():
    book = os.path.join(PKG, '独立审核表.xlsx')
    x = pd.ExcelFile(book)
    inc = x.parse('1_纳入独立审核30条')
    exc = x.parse('2_排除独立审核20条')

    inc['模型预审意见（不作为第二作者答案）'] = ''
    inc['模型预审依据'] = ''
    for idx, r in inc.iterrows():
        n = int(r['独立审核编号'])
        software = str(r.get('数据集标注的软件', ''))
        specialty = str(r.get('数据集标注的学科', ''))
        ev = str(r.get('原文证据片段（供快速定位）', ''))
        if n in INC_RECHECK or not ev.strip() or ev == 'nan':
            opinion = '建议第二作者重点复核：软件名、实际使用角色和学科归属'
            basis = '证据片段为空/较弱，或数据集软件标注与片段中的首个软件名可能不完全一致。应以全文方法部分为准。'
        else:
            opinion = '初步支持纳入记录'
            basis = '标题、数据集标注和证据片段总体支持研究使用了具名非牙科3D软件；仍需第二作者独立查看全文。'
        inc.at[idx, '模型预审意见（不作为第二作者答案）'] = opinion
        inc.at[idx, '模型预审依据'] = basis

    exc['模型预审意见（不作为第二作者答案）'] = ''
    exc['模型预审依据'] = ''
    for idx, r in exc.iterrows():
        n = int(r['独立审核编号'])
        reason = str(r.get('全文复评时的判定理由', ''))
        ev = str(r.get('原文证据片段（供快速定位）', ''))
        if n in EXC_RECHECK:
            opinion = '建议第二作者重点复核：可能存在漏纳风险'
            basis = '排除理由涉及具名软件、3D处理、主题范围或软件角色边界；需阅读方法与纳入标准后独立判断。'
        else:
            opinion = '初步支持排除记录'
            basis = '当前排除理由与记录摘要/证据片段总体一致；仍需第二作者独立查看全文。'
        exc.at[idx, '模型预审意见（不作为第二作者答案）'] = opinion
        exc.at[idx, '模型预审依据'] = basis

    note = pd.DataFrame({
        '项目': ['用途', '独立性', '重要限制', '建议顺序'],
        '说明': [
            '这是对第二作者审核材料的模型辅助预审意见，用于帮助定位重点记录。',
            '该文件不包含第一作者的已完成答案，也不应作为第二作者的答案。第二作者应先完成独立审核。',
            '模型预审不是人工审核、不是最终结论、不是一致率计算，也不能替代全文阅读。',
            '第二作者先填写“第二作者填写”列；保存原始答案后，再查看本文件进行比较和讨论。',
        ],
    })
    out = os.path.join(PKG, '模型预审意见_供第二作者参考.xlsx')
    with pd.ExcelWriter(out, engine='openpyxl') as w:
        note.to_excel(w, sheet_name='0_说明', index=False)
        inc.to_excel(w, sheet_name='1_纳入预审意见30条', index=False)
        exc.to_excel(w, sheet_name='2_排除预审意见20条', index=False)
    inc.to_csv(os.path.join(PKG, 'included_model_precheck_30.csv'), index=False, encoding='utf-8-sig')
    exc.to_csv(os.path.join(PKG, 'excluded_model_precheck_20.csv'), index=False, encoding='utf-8-sig')
    print('已生成:', out)
    print('纳入重点复核:', sum(inc['模型预审意见（不作为第二作者答案）'].str.startswith('建议')))
    print('排除重点复核:', sum(exc['模型预审意见（不作为第二作者答案）'].str.startswith('建议')))

if __name__ == '__main__':
    main()
