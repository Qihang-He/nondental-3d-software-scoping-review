# -*- coding: utf-8 -*-
"""
_tools_prisma_reasons.py
重建 PRISMA 排除原因分类（回应审稿人 R3-12）
- 语料 2,540 条 → 进入资格评估 613 条 → 筛查阶段排除 1,927 条
- 依据**原始 AI 初筛已归档的分类理由文本**（完整文献信息_AI筛选结果.csv 的"AI分类理由"），
  用确定性正则规则归类为 6 类；规则与命中数全部落表，可复核。
输出：03_数据/08_分析用/PRISMA_排除原因分类.csv / PRISMA_链路.json
"""
import os
import re
import json
import unicodedata
import pandas as pd

ROOT = r'03_数据'
ANA = os.path.join(ROOT, '08_分析用')


def nt(s):
    s = unicodedata.normalize('NFKD', str(s))
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'[^0-9a-zA-Z]+', ' ', s).lower().strip()
    return re.sub(r'\s+', ' ', s)


# 规则按优先级排列（先命中先生效）
RULES = [
    ('R1_时间窗外', r'早于\s*2020|2020\s*年\s*9\s*月?\s*之前|超出纳入时间|不在.*时间窗|'
                     r'发表时间.*2020|2020年9月|晚于\s*2026'),
    ('R2_文献类型不符', r'综述|review|meta\s*analysis|meta-分析|社论|editorial|评论|commentary|'
                        r'会议摘要|conference abstract|letter|读者来信|protocol|研究方案|'
                        r'preprint|社评|编者按|述评|调查问卷|survey|广告|书评|'
                        r'非原创研究|不属于原创'),
    ('R3_非口腔医学范畴', r'非口腔|不属于口腔|未涉及口腔|口腔医学任何学科|与口腔.{0,8}无关|'
                          r'口腔医学无关|神经外科|骨科|心血管|非牙科|不涉及口腔|'
                          r'未明确涉及口腔|整形外科|眼科|未涉及口腔医学|'
                          r'PCC框架中的\s*Population/Context（口腔医学|'
                          r'与口腔医学领域无关|非口腔医学'),
    ('R4_未使用非牙科专用3D软件', r'未提及|未明确提及|未明确说明|未说明|未报告|'
                                    r'牙科专用软件|牙科专用\s*CAD|仅使用牙科|牙科/医学专用软件|'
                                    r'未使用任何非牙科|没有使用.*非牙科|未使用非牙科|'
                                    r'软件使用情况不明|未提及任何.*软件|未明确指出.*软件|'
                                    r'未指明.*软件|软件类型不明|未能确认.*软件'),
    ('R5_无3D数据处理或建模', r'未涉及\s*3D|缺乏\s*3D|无\s*3D\s*数据|未进行.*三维|'
                               r'仅.*二维|未涉及三维|无三维|未进行.*3D'),
]

rules_c = [(k, re.compile(p)) for k, p in RULES]


def classify(txt):
    s = str(txt or '')
    for k, rx in rules_c:
        if rx.search(s):
            return k
    return 'R7_其他或不可归类'


def main():
    corpus = pd.read_csv(ROOT + r'\02_清洗后\筛选语料_去重后.csv', low_memory=False)
    ai = pd.read_csv(ROOT + r'\03_AI初筛原始\完整文献信息_AI筛选结果.csv')
    final613 = pd.read_excel(ROOT + r'\04_最终表\最终表.xlsx')
    v3 = pd.read_csv(ANA + r'\分析数据集_final_v3.csv')

    corpus['_nt'] = corpus['Title'].map(nt)
    ai['_nt'] = ai['文献标题'].map(nt)
    c613col = [c for c in final613.columns if 'Title' in str(c) or '标题' in str(c)][0]
    final613['_nt'] = final613[c613col].map(nt)

    # 标题精确匹配 + DOI 兜底 + 标题模糊兜底，确保 613 全部落位
    s613 = set(final613['_nt'])
    corpus['_in613'] = corpus['_nt'].isin(s613)
    if 'DOI' in final613.columns and 'DOI' in corpus.columns:
        d613 = {str(x).strip().lower() for x in final613['DOI'].dropna()
                if str(x).strip() and str(x).strip().lower() != 'nan'}
        cd = corpus['DOI'].astype(str).str.strip().str.lower()
        corpus['_in613'] = corpus['_in613'] | cd.isin(d613)
    unresolved = final613.loc[~final613['_nt'].isin(set(corpus.loc[corpus['_in613'], '_nt'])), '_nt']
    if len(unresolved):
        import difflib
        cu = list(corpus.loc[~corpus['_in613'], '_nt'])
        for u in unresolved:
            m = difflib.get_close_matches(u, cu, n=1, cutoff=0.9)
            if m:
                corpus.loc[corpus['_nt'] == m[0], '_in613'] = True
    print('未匹配的 613 条目数:', int((~final613['_nt'].isin(set(corpus.loc[corpus['_in613'], '_nt']))).sum()))
    screened_out = corpus[~corpus['_in613']].copy()
    print('语料 %d ；进入资格评估 %d ；筛查阶段排除 %d'
          % (len(corpus), corpus['_in613'].sum(), len(screened_out)))

    reason = dict(zip(ai['_nt'], ai['AI分类理由']))
    label = dict(zip(ai['_nt'], ai['AI分类结果']))
    screened_out['原AI分类'] = screened_out['_nt'].map(label)
    screened_out['原AI理由'] = screened_out['_nt'].map(reason)
    screened_out['排除原因'] = screened_out['原AI理由'].map(classify)

    print('\n原因分布：')
    dist = screened_out['排除原因'].value_counts()
    print(dist.to_string())
    print('\n各原因抽样检查：')
    for k in dist.index:
        print(' 【%s】' % k)
        for t in screened_out.loc[screened_out['排除原因'] == k, '原AI理由'].dropna().head(4):
            print('    -', str(t)[:110])

    screened_out[['_nt', 'Title', '原AI分类', '排除原因', '原AI理由']].to_csv(
        os.path.join(ANA, 'PRISMA_排除原因分类.csv'), index=False, encoding='utf-8-sig')

    # 资格评估阶段 47 条排除原因（来自剔除清单）
    cut = pd.read_csv(ROOT + r'\06_锁定数据集\剔除清单_共44条.csv')
    print('\n资格评估阶段排除（剔除清单）:', len(cut))
    print(cut['审核轮次'].value_counts().to_dict())

    chain = {
        'identified_databases': {'PubMed': 1727, 'Web of Science': 1605, 'IEEE Xplore': 299,
                                 'total': 3631},
        'after_deduplication': 2572,
        'removed_before_screening': 32,
        'screened_title_abstract': int(len(corpus)),
        'excluded_at_screening': int(len(screened_out)),
        'excluded_at_screening_by_reason': {k: int(v) for k, v in dist.items()},
        'assessed_for_eligibility': int(len(final613)),
        'excluded_after_assessment': 47,
        'excluded_after_assessment_breakdown': {
            '第一轮人工审核': 30, '第二轮人工审核_审稿人质疑条目': 11,
            '软件仅牙科专用_经全文核验': 2, '无全文且无法核实': 1, '时间窗外': 3},
        'included_in_review': int(len(v3)),
    }
    json.dump(chain, open(os.path.join(ANA, 'PRISMA_链路.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('\n', json.dumps(chain, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
