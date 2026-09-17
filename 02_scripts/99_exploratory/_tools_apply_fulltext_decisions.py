# -*- coding: utf-8 -*-
"""Apply author-confirmed full-text decisions; preserve v4 and write an audit log."""
import os, ast
import pandas as pd
ROOT=(os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ANA=os.path.join(ROOT,'03_数据','08_分析用')
SRC=os.path.join(ANA,'分析数据集_final_v4.csv')
OUT=os.path.join(ANA,'分析数据集_final_v5_candidate.csv')
LOG=os.path.join(ANA,'全文核验变更_v4_to_v5_candidate.csv')

def lst(v):
 try:return list(ast.literal_eval(v)) if isinstance(v,str) and v.startswith('[') else []
 except:return []
def dump(x):return repr(x)

def main():
 d=pd.read_csv(SRC,encoding='utf-8-sig',low_memory=False)
 changes=[]
 # I48: author-confirmed narrative/technical review; exclude from evidence set.
 r=d[d.Key=='6UCDT3F9']
 if len(r):
  changes.append({'Key':'6UCDT3F9','action':'exclude','reason':'Author confirmed narrative/technical review; excluded by eligibility criteria','old_software':r.iloc[0]['Software Used (fixed)'],'new_software':''})
  d=d[d.Key!='6UCDT3F9'].copy()
 # Z5: full text does not support the recorded Geomagic software; no qualifying software remains.
 r=d[d.Key=='Z5PYCCYC']
 if len(r):
  changes.append({'Key':'Z5PYCCYC','action':'exclude','reason':'Full text checked; recorded Geomagic software not supported and no qualifying alternative confirmed','old_software':r.iloc[0]['Software Used (fixed)'],'new_software':''})
  d=d[d.Key!='Z5PYCCYC'].copy()
 # 88HUKGCR: add two software packages explicitly used in the full-text method.
 r=d[d.Key=='88HUKGCR']
 if len(r):
  i=r.index[0]
  old=lst(d.at[i,'_soft2']); new=[]
  for x in old+['VRMesh Studio','Algor']:
   if x not in new:new.append(x)
  d.at[i,'_soft2']=dump(new)
  d.at[i,'Software Used (fixed)']=';'.join(new)
  changes.append({'Key':'88HUKGCR','action':'update_software','reason':'Full text supports VRMesh Studio and Algor as mesh/FEA tools','old_software':';'.join(old),'new_software':';'.join(new)})
 # Make the audit candidate explicit and do not overwrite v4.
 d.to_csv(OUT,index=False,encoding='utf-8-sig')
 pd.DataFrame(changes).to_csv(LOG,index=False,encoding='utf-8-sig')
 print('wrote',OUT,'N=',len(d)); print(pd.DataFrame(changes).to_string(index=False))
if __name__=='__main__':main()
