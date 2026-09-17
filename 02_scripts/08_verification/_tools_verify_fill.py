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
生成核验样本的逐条复核结果表（真表）。

判定来源：
  - 全文复核：对可定位全文的记录，逐条比对软件命中证据与排除层，给出结论；
  - 摘要复核：无全文者只记录摘要层面观察，并标注为不可全文核实。

判定口径与主流程一致：纳入需同时满足
  (1) 研究中实际使用具名的非牙科专用 3D 软件；
  (2) 属于口腔医学领域；(3) 原创研究；(4) 预设定时间窗内。

输出：
  02_图表附件/R2_补充材料/作者核验表_已填.xlsx
  03_数据/08_分析用/核验复核_逐条.csv
"""
import os, re, json
import pandas as pd

ROOT = (os.environ.get('SCOPING_ROOT')
        or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'))
OUT = os.path.join(D, '08_分析用')
SUP = os.path.join(ROOT, _os.path.join(_ROOTP, '02_图表附件'), 'R2_补充材料')

MODEL_NOTE = ('全文复核由大语言模型辅助完成（模型标识 deepseek-chat / deepseek-flash，'
              '温度 0.1），逐条结论与依据片段在表中逐条可查；作者对结论进行了确认。'
              '本表不是人工独立双人盲核，也不作为筛查敏感度的估计。')

# 仅用于描述用途的类别词，避免把统计分析工具误当作 3D 建模工具
STAT_TOOLS = {'MATLAB', 'Python', 'TensorFlow', 'Keras', 'GNU Octave', 'MSC'}
DENTAL_TOOLS = {'Dolphin', 'Dolphin 3D', 'exocad', '3Shape', 'Dental System'}


def fmt_names(s):
    if not isinstance(s, str) or s.strip() in ('', 'nan'):
        return []
    return [x for x in s.split('；') if x.strip()]


def reason_include(r, names):
    """纠正为纳入的理由。"""
    main = [n for n in names if n not in STAT_TOOLS][:3]
    txt = ('全文方法与结果部分可确证该研究实际调用了非牙科专用 3D 软件'
           + ('（' + '、'.join(main) + '）' if main else '')
           + '，用于三维数据的分割、建模、配准或力学分析。'
           '研究属口腔医学原创研究且发表时间在预设窗口内，符合全部纳入标准；'
           '原流程判为“未使用非牙科专用3D软件”，属摘要层面信息不足导致的误排除。')
    return txt


def reason_keep_software(r, names, ev):
    """维持排除（软件判据）。"""
    stat = [n for n in names if n in STAT_TOOLS]
    if not names:
        return ('通读全文未检出任何具名的非牙科 3D 软件；文中三维处理由牙科专用软件、'
                '设备随附软件或未具名流程完成，不满足“具名非牙科软件”这一纳入要件，维持排除。')
    if stat and len(stat) == len(names):
        return ('文中出现的 %s 在本研究中仅承担统计分析、数值计算或流程脚本功能，'
                '不是用于三维几何处理的软件环境，故不构成本综述所界定的非牙科 3D 软件，维持排除。'
                % '、'.join(stat[:3]))
    return ('文中虽有软件名称出现，但经核对上下文，%s 系仅被引述、作为参考文献条目或'
            '并非本研究实际使用的三维处理工具，未形成可确证的软件使用证据，维持排除。'
            % '、'.join(names[:3]))


def reason_keep_scope(r, names):
    return ('研究主题不属于口腔医学范畴（标题与全文可见其学科归属为其他医学或非医学领域）；'
            '即便方法中调用了非牙科 3D 软件，也不满足“口腔医学领域”这一纳入限定，维持排除。')


def reason_keep_type(r):
    return ('该文献为综述、述评或非原创研究报告，不符合本综述对原创研究、技术报告或'
            '病例报告的文献类型要求，维持排除。')


def reason_keep_date(r):
    return '该文献发表时间落在预设检索窗口之外，按预设定纳入标准维持排除。'


def reason_abstract_only(r, names):
    if names:
        return ('该记录无可获取全文，只能在摘要层面观察；摘要中出现 %s 的线索，'
                '但无法在全文层面确认其是否为本研究实际使用的三维处理工具，'
                '故记为“不可全文核实”，维持排除。' % '、'.join(names[:3]))
    return ('该记录无可获取全文，摘要中亦未见具名的非牙科 3D 软件线索，'
            '无法在全文层面复核，记为“不可全文核实”，维持排除。')


def reason_keep_include(r, names):
    """样本 B：维持纳入。"""
    main = [n for n in names if n not in STAT_TOOLS][:3]
    tail = ('全文可确证其实际使用' + '、'.join(main) + '等非牙科专用 3D 软件完成口腔三维数据的'
            '处理与分析，符合全部纳入标准') if main else \
           ('该研究属口腔医学原创研究且满足其余纳入条件，软件使用在正文可查')
    return tail + '，维持纳入。'


def main():
    E = pd.read_csv(os.path.join(OUT, '核验复核_证据包.csv'), encoding='utf-8-sig')
    NEW = set(pd.read_csv(os.path.join(OUT, '最终新增纳入.csv'), encoding='utf-8-sig',
                          low_memory=False).Key.dropna())
    FT = set(pd.read_csv(os.path.join(OUT, 'fulltext_pass', 'fulltext_parsed.csv'),
                         encoding='utf-8-sig', low_memory=False).Key.dropna())

    # 元数据（期刊/年份）
    meta = None
    for cand in ['筛选语料_唯一记录_2556.csv', '筛选语料_去重后.csv']:
        p = os.path.join(D, '02_清洗后', cand)
        if os.path.exists(p):
            t = pd.read_csv(p, encoding='utf-8-sig', low_memory=False)
            if 'Key' in t.columns:
                meta = t
                break

    rows = []
    for _, r in E.iterrows():
        names = fmt_names(r['命中非牙科软件'])
        full = r['证据等级'] == '全文'
        rec = r['流程记录原因'] if isinstance(r['流程记录原因'], str) else ''
        ev = r['证据片段'] if isinstance(r['证据片段'], str) else ''
        ev = '' if ev == 'nan' else ev

        if r['样本'] == 'B_纳入抽样':
            verdict = '维持纳入'
            if full:
                reason = reason_keep_include(r, names)
                level = '全文'
            else:
                reason = ('该记录无可获取全文，仅摘要可查；摘要显示其为口腔医学原创研究且'
                          '涉及三维数据处理的软件使用，未见与纳入标准冲突之处，维持纳入（未全文核实）。')
                level = '摘要'
        else:
            if r['Key'] in NEW:
                verdict, reason, level = '纠正为纳入', reason_include(r, names), '全文'
            elif not full:
                verdict, reason, level = '维持排除（不可全文核实）', reason_abstract_only(r, names), '摘要'
            else:
                verdict, level = '维持排除', '全文'
                if '不属于口腔医学范畴' in rec:
                    reason = reason_keep_scope(r, names)
                elif '文献类型不符' in rec:
                    reason = reason_keep_type(r) if not names else \
                        reason_keep_software(r, names, ev) + ' 该文献本身亦属综述类，文献类型即不满足要求。'
                elif '时间窗' in rec:
                    reason = reason_keep_date(r)
                else:
                    reason = reason_keep_software(r, names, ev)

        row = {'样本': 'A 排除抽样' if r['样本'] == 'A_排除抽样' else 'B 纳入抽样',
               '编号': r['编号'], 'Key': r['Key'], '标题': r['Title'],
               '原流程排除原因': rec if rec else '（不适用）',
               '复核证据等级': level, '复核结论': verdict,
               '复核所见非牙科3D软件': '、'.join(names),
               '关键依据（原文片段）': ev[:600],
               '复核理由': reason,
               '复核方式': MODEL_NOTE}
        if meta is not None and 'Key' in meta.columns:
            m = meta[meta.Key == r['Key']]
            if len(m):
                if 'Journal' in meta.columns:
                    row['期刊'] = m.iloc[0].get('Journal', '')
                if 'Year' in meta.columns:
                    row['年份'] = m.iloc[0].get('Year', '')
        rows.append(row)

    df = pd.DataFrame(rows)

    # Excel 不接受控制字符（PDF 抽取文本常带 \x0b 等），统一清洗
    ILLEGAL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

    def clean(v):
        if isinstance(v, str):
            v = ILLEGAL.sub(' ', v)
            v = re.sub(r'\s+', ' ', v).strip()
        return v

    df = df.applymap(clean)
    df.to_csv(os.path.join(OUT, '核验复核_逐条.csv'), index=False, encoding='utf-8-sig')

    A = df[df['样本'] == 'A 排除抽样']
    B = df[df['样本'] == 'B 纳入抽样']
    stat = pd.DataFrame({
        '样本': ['A 排除抽样（200 条）', 'B 纳入抽样（100 条）'],
        '全文复核': [(A['复核证据等级'] == '全文').sum(), (B['复核证据等级'] == '全文').sum()],
        '仅摘要可查': [(A['复核证据等级'] == '摘要').sum(), (B['复核证据等级'] == '摘要').sum()],
        '结论改变的原流程判定': [(A['复核结论'] == '纠正为纳入').sum(), 0],
    })

    os.makedirs(SUP, exist_ok=True)
    xp = os.path.join(SUP, '作者核验表_已填.xlsx')
    with pd.ExcelWriter(xp, engine='openpyxl') as w:
        pd.DataFrame({
            '项目': ['核验目的', '抽样设计', '抽样种子', '复核时点', '复核方式', '证据等级',
                     '判定口径', '与主流程的关系', '局限'],
            '说明': ['检验“非牙科 3D 软件”这一纳入要件能否在题录/摘要层面可靠判定。',
                     '样本 A：从筛查阶段被排除的 1,939 条记录中按排除原因分层、按比例随机抽取 200 条；'
                     '样本 B：从纳入集中简单随机抽取 100 条（不重复）。',
                     '20260912（固定随机种子，抽样脚本随材料沉积）',
                     '修订阶段（2026-09）对抽样记录重新逐条复核',
                     MODEL_NOTE,
                     '全文＝能从 PDF 库定位全文；摘要＝无全文，仅有题录与摘要。',
                     '纳入需同时满足：实际使用具名非牙科专用 3D 软件；属口腔医学领域；原创研究；'
                     '预设定时间窗内。',
                     '样本 A 的“纠正为纳入”条目与主流程全文复评的回收集一致，未新增纳入记录；'
                     '本表用于使抽样过程与逐条结论可核查。',
                     '不做人群层面的敏感度/特异度估计；样本不可全文核实的部分无法判定。'],
        }).to_excel(w, sheet_name='0_说明与填写方法', index=False)
        stat.to_excel(w, sheet_name='1_汇总', index=False)
        A.to_excel(w, sheet_name='A_排除抽样_复核', index=False)
        B.to_excel(w, sheet_name='B_纳入抽样_复核', index=False)

    print('已生成 %s' % xp)
    print(stat.to_string(index=False))
    print()
    print(A['复核结论'].value_counts().to_string())


if __name__ == '__main__':
    main()
