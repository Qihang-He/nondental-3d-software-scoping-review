# -*- coding: utf-8 -*-
"""对无全文映射记录做摘要级证据审计；不修改数据。"""
import os,re
import pandas as pd
ROOT=(os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ANA=os.path.join(ROOT,'03_数据','08_分析用'); PKG=os.path.join(ROOT,'人工核验包')

def main():
 d=pd.read_csv(os.path.join(ANA,'分析数据集_final_v4.csv'),encoding='utf-8-sig',low_memory=False)
 c=pd.read_csv(os.path.join(ROOT,'03_数据','02_清洗后','筛选语料_唯一记录_2556.csv'),encoding='utf-8-sig',low_memory=False)[['Key','Abstract']]
 pm=pd.read_csv(os.path.join(ROOT,'03_数据','07_PDF与语料对照','pdf_match.csv'),encoding='utf-8-sig',low_memory=False)
 q=d[~d.Key.isin(set(pm.Key.dropna()))].merge(c,on='Key',how='left')
 names=['3D Slicer','Mimics','InVesalius','Geomagic','Meshmixer','MeshLab','CloudCompare','ANSYS','Abaqus','SolidWorks','Rhinoceros','Blender','MATLAB','Simpleware','Magics','3-Matic','GOM Inspect','Open3D','VTK','Creo','Fusion 360','Avizo','Amira','ITK-SNAP','Brainlab','nTop','VRMesh','Algor']
 def find_context(x):
  text=str(x); hits=[]
  for name in names:
   pat=re.compile(r'(?<![A-Za-z0-9])'+re.escape(name)+r'(?![A-Za-z0-9])',re.I)
   for m in pat.finditer(text):
    win=text[max(0,m.start()-180):min(len(text),m.end()+280)]
    if re.search(r'used|using|software|program|package|tool|platform|model|segment|reconstruct|mesh|analysis|measure|design|finite element|simulation',win,re.I):
     hits.append(name); break
  return '; '.join(dict.fromkeys(hits))
 q['摘要软件命中']=q.Abstract.fillna('').map(find_context)
 q['摘要状态']=q.apply(lambda r:'摘要明确提及软件及其研究用途；可保留但标记“无全文”' if r['摘要软件命中'] else ('无摘要软件证据；无法全文核验' if len(str(r.Abstract))>10 else '无可用摘要；无法全文核验'),axis=1)
 q['处理原则']='摘要明确且软件承担角色可从摘要判断：可保留；否则不据摘要推断全文结论。'
 out=os.path.join(PKG,'无全文记录_摘要证据审计.xlsx')
 with pd.ExcelWriter(out,engine='openpyxl') as w:
  pd.DataFrame({'项目':['范围','摘要明确软件','摘要没有软件证据','重要边界'],'说明':['最终纳入集中无全文映射记录；该表不修改锁定数据。','若摘要明确写出软件，保留但标记无全文，不能称为全文核验。','列为无法全文核验，不自动排除，因为缺全文不等于不符合。','综述中报告全文不可得记录属于正常限制；应报告检索、全文获取和可审计的数量，不应伪称完成全文核验。']}).to_excel(w,sheet_name='0_规则',index=False)
  q.to_excel(w,sheet_name='1_无全文55条',index=False)
 q.to_csv(os.path.join(PKG,'无全文记录_摘要证据审计.csv'),index=False,encoding='utf-8-sig')
 print('rows',len(q)); print(q['摘要状态'].value_counts().to_string())
 print(q[['Key','摘要软件命中','摘要状态']].to_string(index=False))
if __name__=='__main__':main()
