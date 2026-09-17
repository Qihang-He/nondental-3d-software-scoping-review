# -*- coding: utf-8 -*-
"""生成全文优先审计工作表；不修改锁定数据集。"""
import os,re
import pandas as pd
ROOT=(os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ANA=os.path.join(ROOT,'03_数据','08_分析用'); PKG=os.path.join(ROOT,'人工核验包')
def main():
 d=pd.read_csv(os.path.join(ANA,'分析数据集_final_v4.csv'),encoding='utf-8-sig',low_memory=False)
 pm=pd.read_csv(os.path.join(ROOT,'03_数据','07_PDF与语料对照','pdf_match.csv'),encoding='utf-8-sig',low_memory=False)
 keys=set(pm.Key.dropna()); d['全文映射']='有' ; d.loc[~d.Key.isin(keys),'全文映射']='无'
 q=d[['序号','Key','Title','DOI','Journal','Year','Dental Specialty','Software Used (fixed)','Application Scenario','_来源']].copy()
 q['全文状态']=d['全文映射'].values
 q['作者审核要求']='优先核对全文 Methods/Materials 中的软件实际使用、软件官方名称、角色和学科归属；若全文无支持，删除该软件标注或将记录列入待排除。'
 q['当前结论']='待全文审计；不自动修改锁定数据'
 out=os.path.join(PKG,'全文优先审计总表_863条.xlsx')
 with pd.ExcelWriter(out,engine='openpyxl') as w:
  pd.DataFrame({'项目':['审计原则','软件字段规则','版本号规则','学科字段规则','无法找到全文','当前状态'],'说明':['全文方法证据优先；摘要、参考文献和模型推断不能单独支持软件使用。','只记录研究实际使用且承担3D处理、建模、配准、测量或有限元角色的软件。','最终软件名称不写版本号，例如 Creo 8.0 记录为 Creo。','优先使用现有预设专业分类；新增或改名必须记录依据并重跑学科分析。','无法找到全文的记录不自动删除，列入待作者确认清单。','该表是审计工作表，不是已完成审核结果。']}).to_excel(w,sheet_name='0_规则',index=False)
  q[q['全文状态']=='有'].to_excel(w,sheet_name='1_有全文808条',index=False)
  q[q['全文状态']=='无'].to_excel(w,sheet_name='2_无全文55条',index=False)
 q.to_csv(os.path.join(PKG,'全文优先审计总表_863条.csv'),index=False,encoding='utf-8-sig')
 print(out,'rows',len(q),'with pdf',sum(q.全文状态=='有'),'without',sum(q.全文状态=='无'))
if __name__=='__main__':main()
