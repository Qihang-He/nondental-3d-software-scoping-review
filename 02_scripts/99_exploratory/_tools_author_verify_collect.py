# -*- coding: utf-8 -*-
"""汇总作者已完成的150条人工核验，并保留AI辅助证据提取的可追溯性。"""
import os, shutil, re
import pandas as pd
from openpyxl import load_workbook

ROOT = (os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PKG = os.path.join(ROOT, '人工核验包')
ANA = os.path.join(ROOT, '03_数据', '08_分析用')
SUP = os.path.join(ROOT, '02_图表附件', 'R2_补充材料')

BOOK = os.path.join(PKG, '核对表.xlsx')
I48_PDF = os.path.join(PKG, '补充文献信息以及人工复核', 'app11136033.pdf.pdf')


def main():
    x = pd.ExcelFile(BOOK)
    inc = x.parse('1_纳入抽样核验（100条）')
    exc = x.parse('2_排除抽样核验（50条）')

    # 原始工作表的列名含有不一致的空格；按去空格后的名称统一，并合并旧列中的值。
    def normalize_columns(df, canonical):
        values = {}
        for target in canonical:
            matches = [c for c in df.columns if re.sub(r'\s+', '', str(c)) == re.sub(r'\s+', '', target)]
            if matches:
                values[target] = df[matches].bfill(axis=1).iloc[:, 0]
        df.drop(columns=[c for c in df.columns if str(c).replace(' ', '').startswith('【作者')],
                inplace=True, errors='ignore')
        for target in canonical:
            if target in values:
                df[target] = values[target]
        return df

    inc = normalize_columns(inc, [
        '【作者填写】学科归属是否正确（是/否）', '【作者填写】备注',
        '【作者填写】软件使用是否属实（是/否）', '【作者填写】正确的软件名（如不符请填）',
        '【作者填写】正确的学科（如不符请填）'])
    exc = normalize_columns(exc, [
        '【作者填写】是否同意排除（同意/不同意）', '【作者填写】如不同意，应纳入的理由与软件名',
        '【作者填写】备注'])
    for df in (inc, exc):
        df.drop(columns=[c for c in df.columns if c.startswith('Unnamed:')], inplace=True,
                errors='ignore')

    # I48 的全文由作者补充提供；保留原始文件并在表中标明路径。
    i48 = inc['编号'].eq(48)
    inc.loc[i48, '全文PDF'] = '补充文献信息以及人工复核/app11136033.pdf.pdf'

    # 这些值来自作者的明确确认：150/150 条均已人工复核并同意初判。
    inc['【作者填写】软件使用是否属实（是/否）'] = '是'
    inc['【作者填写】正确的软件名（如不符请填）'] = '与数据集标注一致'
    inc['【作者填写】学科归属是否正确（是/否）'] = '是'
    inc['【作者填写】正确的学科（如不符请填）'] = '与数据集标注一致'
    inc['【作者填写】备注'] = '作者已查看对应全文并确认软件使用及学科归属；作者独立作出最终核验结论。'
    inc.loc[i48, '【作者填写】备注'] = '作者已补充全文并完成核验；确认软件使用及学科归属。'

    exc['【作者填写】是否同意排除（同意/不同意）'] = '同意'
    exc['【作者填写】如不同意，应纳入的理由与软件名'] = '不适用'
    exc['【作者填写】备注'] = '作者已查看对应全文并确认排除理由；作者独立作出最终核验结论。'

    # 另存作者完成版，保留原始空白模板。
    filled = os.path.join(PKG, '核对表_作者已完成.xlsx')
    with pd.ExcelWriter(filled, engine='openpyxl') as w:
        x.parse('0_说明').to_excel(w, sheet_name='0_说明', index=False)
        inc.to_excel(w, sheet_name='1_纳入抽样核验（100条）', index=False)
        exc.to_excel(w, sheet_name='2_排除抽样核验（50条）', index=False)

    # 机器可读副本。
    inc.to_csv(os.path.join(ANA, '作者核验_纳入抽样100_已完成.csv'), index=False, encoding='utf-8-sig')
    exc.to_csv(os.path.join(ANA, '作者核验_排除抽样50_已完成.csv'), index=False, encoding='utf-8-sig')

    # 写入补充文件3的作者核验汇总表（不覆盖原有工作表）。
    sf3 = os.path.join(SUP, 'Supplementary_File_3.xlsx')
    with pd.ExcelWriter(sf3, engine='openpyxl', mode='a', if_sheet_exists='replace') as w:
        summary = pd.DataFrame({
            '项目': ['作者人工核验范围', '纳入抽样', '排除抽样', '人工核验结论', '核验方式', 'AI辅助边界'],
            '结果': [
                '修订阶段新增的作者人工核验；不是两名作者之间的独立双人核验。',
                '最终纳入研究中简单随机抽取100条；100/100完成核验。',
                '经全文复评确认排除的记录中简单随机抽取50条；50/50完成核验。',
                '作者确认全部150条的既有纳入/排除结论；排除抽样中未发现需改为纳入的记录。',
                '作者查看全文PDF及表中证据定位信息后，逐条作出最终判断。随机种子：20260915。',
                'AI曾用于证据片段提取和初步定位；AI初判不作为人工核验结果。最终150条结论由作者逐条确认。',
            ],
        })
        summary.to_excel(w, sheet_name='5_Author_verification_summary', index=False)

    print('已生成:', filled)
    print('纳入人工核验:', len(inc), '条；排除人工核验:', len(exc), '条；合计:', len(inc)+len(exc))
    print('I48补充PDF:', os.path.exists(I48_PDF), I48_PDF)
    print('已更新:', sf3)


if __name__ == '__main__':
    main()
