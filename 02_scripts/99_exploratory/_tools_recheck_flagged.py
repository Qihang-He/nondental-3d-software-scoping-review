# -*- coding: utf-8 -*-
"""对第一作者人工核验中标记为"软件名建议复核/证据较弱"的20条做第二次证据复核。
只生成意见报告，不修改锁定数据集。
"""
import os,re,glob
import pandas as pd
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf
ROOT=(os.environ.get('SCOPING_ROOT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ANA=os.path.join(ROOT,'03_数据','08_分析用')
PDFDIR=os.path.join(ROOT,'10_全文PDF库')
OUT=os.path.join(ROOT,'人工核验包','二次复核意见_重点20条.md')

def build_idx():
 d={}
 for root,_,fs in os.walk(PDFDIR):
  for f in fs:
   if f.lower().endswith('.pdf'): d.setdefault(f,os.path.join(root,f))
 return d

def text(p):
 try:
  doc=pymupdf.open(p); t='\n'.join(pg.get_text() for pg in doc); doc.close(); return re.sub(r'\s+',' ',t)
 except Exception:return ''
def contexts(t,names):
 out=[]
 for nm in names:
  if not nm or nm.lower()=='nan':continue
  for m in re.finditer(re.escape(nm),t,re.I):
   s=max(0,m.start()-250);e=min(len(t),m.end()+450);w=t[s:e]
   if re.search(r'software|program|package|tool|using|model|mesh|segment|finite element|analysis|reconstruct',w,re.I):
    out.append((nm,w));break
 return out

def main():
 d=pd.read_csv(os.path.join(ANA,'作者核验_纳入抽样100_已完成.csv'),encoding='utf-8-sig',low_memory=False)
 ids=[2,5,11,19,23,27,29,36,39,41,44,48,57,65,67,77,89,90,97,98]
 d=d[d['编号'].isin(ids)].sort_values('编号')
 idx=build_idx(); lines=['# 第一作者重点记录二次证据复核\n','**用途：**本报告是第二次证据检查，不修改锁定数据集；最终是否修改由作者确认。\n']
 for _,r in d.iterrows():
  fn=str(r['全文PDF']); p=None
  if fn not in ('nan','（未定位到全文）'): p=idx.get(fn)
  # I48 supplemental PDF
  if int(r['编号'])==48:
   q=os.path.join(ROOT,'人工核验包','补充文献信息以及人工复核','app11136033.pdf.pdf')
   if os.path.exists(q):p=q
  t=text(p) if p else ''
  names=[x.strip() for x in re.split(r'[;；]',str(r['数据集标注的软件']))]
  cs=contexts(t,names)
  # also search common packages reported in first-author evidence
  evidence=str(r['原文证据片段（供快速定位）'])
  lines += [f"## I{int(r['编号']):02d} — {r['Key']}",f"**题目：** {r['标题']}",f"**数据集软件/学科：** {r['数据集标注的软件']} / {r['数据集标注的学科']}",f"**PDF：** {'已定位' if p else '未定位'}"]
  if cs:
   for nm,w in cs[:4]: lines.append(f"- **{nm}：** {w[:700]}")
  else: lines.append('- 未从PDF中检索到足够的“软件名+实际使用”上下文；不能仅据此否定记录。')
  if int(r['编号']) in [11,23,29,36,57,65,67,89,97]:
   opinion='**暂不建议改动纳入结论；但该条证据不足，需作者再看全文方法段并确认。**'
  else: opinion='**纳入结论有支持；主要问题是软件清单可能不完整，应由作者决定是否补录软件。**'
  if int(r['编号'])==48: opinion='**I48已由作者补充PDF并核验；建议保留纳入，但应确认原文属于原创研究/技术说明而非一般软件介绍或综述。**'
  lines += [f"**二次复核意见：** {opinion}","**需作者确认：** 软件是否为该研究实际使用；软件承担的3D角色；学科是否符合既定12类 taxonomy。\n"]
 open(OUT,'w',encoding='utf-8').write('\n'.join(lines))
 print('written',OUT)
if __name__=='__main__':main()
