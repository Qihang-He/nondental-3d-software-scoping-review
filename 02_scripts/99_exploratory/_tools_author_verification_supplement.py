# -*- coding: utf-8 -*-
"""生成可作为补充材料的作者审核包；不把模型预审意见写成作者结论。"""
import os
import pandas as pd
ROOT=(os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PKG=os.path.join(ROOT,'人工核验包'); OUTD=os.path.join(ROOT,'02_图表附件','R2_补充材料')

def main():
 inc=pd.read_csv(os.path.join(ROOT,'03_数据','08_分析用','作者核验_纳入抽样100_已完成.csv'),encoding='utf-8-sig',low_memory=False)
 exc=pd.read_csv(os.path.join(ROOT,'03_数据','08_分析用','作者核验_排除抽样50_已完成.csv'),encoding='utf-8-sig',low_memory=False)
 # 清理列名中的排版空格，并保留作者真实结论；不引用模型预审列。
 def clean_cols(d):
  d=d.copy(); rename={}
  for c in d.columns:
   nc=str(c).replace(' ','')
   if '软件使用是否属实' in nc: rename[c]='Author-confirmed software use'
   elif '学科归属是否正确' in nc: rename[c]='Author-confirmed specialty'
   elif '正确的软件名' in nc: rename[c]='Author-corrected software name'
   elif '正确的学科' in nc: rename[c]='Author-corrected specialty'
   elif '是否同意排除' in nc: rename[c]='Author-confirmed exclusion'
   elif '如不同意' in nc: rename[c]='Author-correction if not excluded'
   elif nc.endswith('备注'): rename[c]='Author note'
  d=d.rename(columns=rename)
  # 删除所有模型预审列，防止读者误认为作者结论。
  d=d[[c for c in d.columns if '模型辅助初判' not in str(c) and '初判依据' not in str(c)]]
  return d
 inc=clean_cols(inc); exc=clean_cols(exc)
 notes=pd.DataFrame({
  'Item':['Purpose','Author 1 audit','Author 2 audit','AI boundary','Interpretation'],
  'Description':[
   'Author-led quality checks of eligibility and coding decisions; these checks are supplementary audits, not a reconstruction of the historical two-reviewer process.',
   'One author reviewed 100 included studies and 50 records that remained excluded after full-text reassessment. All 150 decisions were confirmed.',
    'A second author reviewed selected key records as documented in the author-supplied review notes. Records not explicitly discussed in those notes are not assigned an item-level second-author verdict in this supplement; no model precheck was counted as a second-author judgement.',
   'AI-assisted extraction and triage materials are archived separately. AI excerpts were used for navigation and evidence retrieval; author conclusions were recorded separately.',
   'The audits do not provide a population-level sensitivity estimate and no historical reviewer-agreement kappa is reported.',
  ]
 })
 out=os.path.join(OUTD,'Supplementary_File_4_Author_verification.xlsx')
 # 仅纳入第二作者明确提供的7条意见，来源单独标明。
 second=pd.DataFrame([
  ['GMQCCFR9','3D Slicer use and specialty confirmed','Supported inclusion'],
  ['CES5463F','Software use confirmed; specialty requires anthropological note','Supported inclusion; note taxonomy boundary'],
  ['5SW9J4UC','SolidWorks and ANSYS use and specialty confirmed','Supported inclusion'],
  ['GNNPTY9X','Software use confirmed; forensic anthropology crossover','Supported inclusion; note taxonomy boundary'],
  ['DQD774W7','Software and specialty confirmed; ABAQUS suggested for supplementation','Supported inclusion; supplement software field'],
  ['CI6MMSH5','Mimics use confirmed; software list incomplete','Supported inclusion; supplement only confirmed actual-use tools'],
  ['7W7AW9ET','VGSTUDIO MAX use confirmed; specialty broadly appropriate','Supported inclusion; add application note'],
 ],columns=['Key','Second-author supplied opinion','Action'])
 with pd.ExcelWriter(out,engine='openpyxl') as w:
  notes.to_excel(w,sheet_name='0_Notes',index=False)
  inc.to_excel(w,sheet_name='1_Author1_included100',index=False)
  exc.to_excel(w,sheet_name='2_Author1_excluded50',index=False)
  second.to_excel(w,sheet_name='3_Author2_explicit_opinions7',index=False)
 with open(os.path.join(OUTD,'Supplementary_File_4_Author_verification_notes.md'),'w',encoding='utf-8') as f:
  f.write('# Supplementary File 4: Author verification\n\n')
  f.write('This file reports author-led quality checks. It does not claim that the original screening was independently duplicated by two human reviewers.\n\n')
  f.write('- Author 1: 100 included and 50 excluded records reviewed against full text; all 150 decisions confirmed.\n')
  f.write('- Author 2: seven explicit key-record opinions supplied in the author review notes are listed separately. Routine unmentioned records are not converted into fabricated item-level conclusions.\n')
  f.write('- AI-generated excerpts are not presented as author judgements.\n')
 print('written',out)
if __name__=='__main__':main()
