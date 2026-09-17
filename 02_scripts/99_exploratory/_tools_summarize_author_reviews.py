# -*- coding: utf-8 -*-
"""在重跑前汇总两位作者的审核意见；只生成留痕，不修改数据集。"""
import os
import pandas as pd
ROOT = (os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUTD = os.path.join(ROOT, '08_留痕文档')

reviews = pd.DataFrame([
    [1, 'I48 / 6UCDT3F9', '第一作者', '全文补充后判断为叙述性/技术综述', '排除', '从最终纳入候选集删除'],
    [1, '6KRL8HF5', '第一作者', 'Fusion 360 在方法部分用于三维模型构建和处理', '支持纳入', '保留 Fusion 360'],
    [1, '8RD3AVC7', '第一作者', 'SolidWorks 用于模型构建，ANSYS 用于有限元分析', '支持纳入', '保留两者'],
    [1, 'SILBC2M4', '第一作者', '全文为 Vesalius 3D；官方名称映射为 InVesalius', '支持纳入', '规范名称为 InVesalius'],
    [1, 'Z5PYCCYC', '第一作者', '全文未找到当前 Geomagic 标注的支持', '排除', '从候选集删除'],
    [1, '88HUKGCR', '第一作者', 'Simpleware、Rhinoceros、VRMesh Studio、Algor均有方法学证据', '支持纳入/补录', '补录 VRMesh Studio 和 Algor'],
    [1, 'TLW8WS3P', '第一作者', 'Cero 8.0 用于3D CAD模型设计，按规则规范为 Creo', '支持纳入', '软件字段使用 Creo，不写版本'],
    [1, 'Y2LB4NXX', '第一作者', 'InVesalius 3 用于 DICOM 转 STL', '支持纳入', '软件字段使用 InVesalius'],
    [2, 'GMQCCFR9', '第二作者', '3D Slicer 使用属实，学科正确', '支持纳入', '无变更'],
    [2, 'CES5463F', '第二作者', '软件使用属实；属于人类学交叉应用', '支持纳入/学科备注', '不扩展 taxonomy，保留最接近类别并加备注'],
    [2, '5SW9J4UC', '第二作者', 'SolidWorks、ANSYS 使用属实，学科正确', '支持纳入', '无变更'],
    [2, 'GNNPTY9X', '第二作者', '软件使用属实；属于法医人类学交叉应用', '支持纳入/学科备注', '保留预设最接近类别并加备注'],
    [2, 'DQD774W7', '第二作者', '软件和学科属实；建议补充 ABAQUS', '支持纳入/补录', '补充软件字段'],
    [2, 'CI6MMSH5', '第二作者', 'Mimics使用属实；软件标注不完整', '支持纳入/补录', '补充全文实际使用的软件'],
    [2, '7W7AW9ET', '第二作者', 'VGSTUDIO MAX使用属实，学科基本正确', '支持纳入/备注', '补充应用场景/学科备注'],
    [2, '排除抽样50条', '第二作者', '50/50同意排除；未发现应改为纳入的记录', '维持排除', '无记录改为纳入'],
], columns=['作者序号', 'Key/范围', '审核者', '全文审核意见', '结论', '建议处理'])

sample = pd.DataFrame([
    ['第一作者', '纳入随机样本', 100, '100/100确认软件使用和学科字段', '单作者全文质量核验'],
    ['第一作者', '排除随机样本', 50, '50/50同意排除', '单作者全文质量核验'],
    ['第二作者', '独立纳入样本', 30, '意见文件明确覆盖7条；其余记录需以独立审核表原始填写为准', '第二作者独立审核包'],
    ['第二作者', '独立排除样本', 20, '意见文件未逐条覆盖；不得将模型预审意见当作第二作者答案', '第二作者独立审核包'],
], columns=['审核者', '样本范围', '样本量', '当前记录状态', '备注'])

path = os.path.join(OUTD, '18_两位作者审核意见汇总_20260916.xlsx')
with pd.ExcelWriter(path, engine='openpyxl') as writer:
    pd.DataFrame({
        '项目': ['第一作者审核', '第二作者审核', 'AI边界', '数据变更规则'],
        '说明': [
            '第一作者已完成100条纳入和50条排除的全文核验。',
            '第二作者独立审核包抽取30条纳入和20条排除；意见文件明确覆盖7条纳入意见，其余以第二作者原始审核表为准。',
            'AI只能提供证据提取、候选定位和预审意见；不能替代作者最终判断。',
            '本汇总不修改候选数据；数据只有在作者意见明确且全文证据支持后才进入最终v5。',
        ],
    }).to_excel(writer, sheet_name='0_说明', index=False)
    reviews.to_excel(writer, sheet_name='1_逐条重要意见', index=False)
    sample.to_excel(writer, sheet_name='2_审核覆盖与证据边界', index=False)

md = os.path.join(OUTD, '18_两位作者审核意见汇总_20260916.md')
with open(md, 'w', encoding='utf-8') as f:
    f.write('# 两位作者审核意见汇总（2026-09-16）\n\n')
    f.write('本文件在重跑数据链前建立；仅汇总审核意见，不修改数据。\n\n')
    f.write('## 第一作者\n- 纳入100条、排除50条均已全文核验。\n- I48确定排除；Z5PYCCYC无全文支持的软件标注确定删除；88HUKGCR补录VRMesh Studio和Algor。\n')
    f.write('## 第二作者\n- 意见文件明确覆盖7条纳入预审记录；结论均支持纳入，但部分学科/软件字段需备注或补录。\n- 排除抽样50条：第二作者核验表需作为正式原始记录；未以模型预审意见替代。\n')
    f.write('## 当前边界\n- 本汇总不计算作者间一致率。\n- 不恢复历史κ值。\n- 不把模型预审意见写作第二作者结论。\n- 待两位作者的原始审核表、全文证据和变更表一致后，才正式锁定v5。\n')
print('written', path, md)
