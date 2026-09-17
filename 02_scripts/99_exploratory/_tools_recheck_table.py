# -*- coding: utf-8 -*-
"""生成作者待复核文献表，不修改锁定数据集。"""
import os
import pandas as pd
ROOT=(os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ANA=os.path.join(ROOT,'03_数据','08_分析用')
PKG=os.path.join(ROOT,'人工核验包')

def main():
 d=pd.read_csv(os.path.join(ANA,'作者核验_纳入抽样100_已完成.csv'),encoding='utf-8-sig',low_memory=False)
 ids=[23,29,36,48,65,77,89,97]
 q=d[d['编号'].isin(ids)].copy().sort_values('编号')
 action={
 23:'确认 Fusion 360 是否在方法部分实际使用，并承担三维建模/几何处理角色；若仅有标题或背景提及，不应作为纳入依据。',
 29:'确认 ANSYS 和 SolidWorks 是否均在方法部分实际使用；当前全文证据已支持 ANSYS，重点核对 SolidWorks。',
 36:'确认 InVesalius 是否用于三维重建、分割或体积分析，而非仅作为影像查看或背景软件。',
 48:'I48 已确定为叙述性/技术综述，应从最终纳入集中排除；此条不再需要作者重新判断纳入资格。',
 65:'确认 Geomagic Wrap/Geomagic Design X 是否在方法部分实际用于扫描数据配准、测量或三维处理。',
 77:'确认 Simpleware、Rhinoceros、VRMesh、Algor 的实际使用角色；仅纳入实际承担三维建模/有限元处理的软件。',
 89:'确认 Creo 是否在方法部分实际用于三维支架/模型设计；ImageJ 仅作图像分析时不作为纳入软件。',
 97:'确认 InVesalius 是否实际用于三维数据重建/处理；仅有牙科CAD/CAM或扫描设备信息不足以支持该软件标注。',
 }
 q['待复核问题']=[action[int(x)] for x in q['编号']]
 q['建议查看位置']='全文 Materials and Methods / Software / Image processing / 3D modelling 段落'
 q['当前处理']='不改变数据；作者复核后再决定是否补录软件或调整字段'
 cols=['编号','Key','标题','期刊','年份','全文PDF','数据集标注的软件','数据集标注的学科','原文证据片段（供快速定位）','待复核问题','建议查看位置','当前处理']
 q=q[[c for c in cols if c in q.columns]]
 out=os.path.join(PKG,'作者待复核文献表.xlsx')
 with pd.ExcelWriter(out,engine='openpyxl') as w:
  pd.DataFrame({'项目':['用途','范围','重要说明'],'说明':['供作者对证据强度不足或软件标注需二次确认的记录进行复核。','8条记录；I48已由作者确定为叙述性/技术综述，将排除。','复核应以全文方法部分为准；该表不替代作者判断，也不自动修改锁定数据集。']}).to_excel(w,sheet_name='0_说明',index=False)
  q.to_excel(w,sheet_name='1_待复核记录',index=False)
 q.to_csv(os.path.join(PKG,'作者待复核文献表.csv'),index=False,encoding='utf-8-sig')
 print('written',out,'rows',len(q))
 print(q[['编号','Key','待复核问题']].to_string(index=False))
if __name__=='__main__':main()
