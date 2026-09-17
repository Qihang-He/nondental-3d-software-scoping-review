# -*- coding: utf-8 -*-
import os
import pandas as pd
ROOT=(os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PKG=os.path.join(ROOT,'人工核验包')
rows=[
[23,'6KRL8HF5','保留 Fusion 360','全文明确写明 Autodesk Fusion360 用于模型构建和处理；支持纳入。','作者已确认；可保留 Fusion 360。Simulation Mechanical 作为求解器是否补录可不影响纳入。','不改变纳入结论'],
[29,'8RD3AVC7','保留 ANSYS、SolidWorks','全文方法分别说明 SolidWorks 用于模型部件构建，ANSYS 18.1 用于有限元分析；支持纳入。','作者已确认；软件标注完整。','不改变纳入结论'],
[36,'SILBC2M4','核对软件规范名','全文明确为 Vesalius 3D，用于分割和体积测定；与 InVesalius 不同名。','请确认词典是否将 Vesalius 3D 与 InVesalius 视为同一软件。若不能证明映射，应修正为 Vesalius 3D 或删除该软件标注。','暂不改数据'],
[48,'6UCDT3F9','排除','已确定为叙述性/技术综述，不符合原创研究/技术说明纳入类型。','从最终纳入集排除；N 将由863变为862。','待正式重跑'],
[65,'Z5PYCCYC','核对软件证据','当前PDF文本提取未检出 Geomagic、Geomagic Studio、Geomagic Wrap 或 Geomagic Design X；现有软件标注暂不能由提取文本确认。','请查看PDF方法部分，确认是否实际使用三维软件及准确名称。','暂不改数据'],
[77,'88HUKGCR','补充软件记录','全文明确支持 Simpleware、Rhinoceros、VRMesh Studio 和 Algor，均承担三维建模、网格或有限元角色。','建议补充 VRMesh Studio、Algor；保留 Simpleware、Rhinoceros。','待作者确认后改字段'],
[89,'TLW8WS3P','保留 Creo（需确认拼写）','全文原文写 Cero 8.0，用于设计3D CAD模型；很可能是 Creo 的OCR/拼写错误。ImageJ仅用于SEM孔径分析。','请确认PDF原版软件名；确认后保留 Creo，ImageJ不纳入。','暂不改数据'],
[97,'Y2LB4NXX','保留 InVesalius 3','全文明确写明 InVesalius 3 用于DICOM转换为STL；支持纳入。','建议规范为 InVesalius 3。','不改变纳入结论'],
]
df=pd.DataFrame(rows,columns=['编号','Key','二次全文核对意见','全文依据','请作者确认','当前处理'])
summary=pd.DataFrame({'项目':['I48','建议暂不改纳入结论','软件名称/字段待确认','需要最终重跑'], '内容':['排除：叙述性/技术综述','23、29、97可保留；36、65、77、89需确认软件名或补录字段','36 Vesalius 3D；65 Geomagic实际软件名；77补充VRMesh/Algor；89 Cero/Creo','I48排除后统一重跑统计、PRISMA、图表、补充材料和Word']})
out=os.path.join(PKG,'复核意见_全文核对结果.xlsx')
with pd.ExcelWriter(out,engine='openpyxl') as w:
 summary.to_excel(w,sheet_name='0_汇总',index=False); df.to_excel(w,sheet_name='1_逐条结果',index=False)
df.to_csv(os.path.join(PKG,'复核意见_全文核对结果.csv'),index=False,encoding='utf-8-sig')
print('written',out)
