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
研究设计分层编码（回应审稿人 R3-7）
输入：锁定数据集 572 篇（标题+摘要）
输出：03_数据/10_研究设计/study_type.csv（含两次运行的一致性与理由）
标签：clinical | in_vitro | computational | case_report | technical_note | educational | other
"""
import os, re, json, time, html
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd, requests

ROOT = _ROOTP
ANA = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "08_分析用")
CORPUS = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "02_清洗后", "筛选语料_去重后.csv")
OUTD = os.path.join(ROOT, _os.path.join(_ROOTP, '03_数据'), "10_研究设计")
os.makedirs(OUTD, exist_ok=True)
MODEL, TEMP, MAXTOK = "deepseek-chat", 0.1, 300
API_URL = "https://api.deepseek.com/v1/chat/completions"
RUNS, WORKERS = 2, 8

SYS = """你是医学文献方法学分类助手。请仅根据给定的标题与摘要，判断该研究的**研究设计类型**，并从下列标签中选择**唯一一个最贴切**的：

- clinical：以患者/受试者为对象的研究（队列、横断面、RCT、诊断准确性临床研究、临床评估、临床病例系列等）
- in_vitro：体外/实验室研究（模型、离体牙/样本、材料测试、体外表征、动物实验等）
- computational：计算/仿真研究（有限元分析、数值模拟、算法与深度学习模型开发、软件/工具开发与验证、形状建模等）
- case_report：病例报告或临床技术报告（个例/少数病例的描述性报告）
- technical_note：技术说明（dental technique / technical note，介绍操作流程或技术创新，常无系统结果）
- educational：教育/培训研究（教学干预、学生技能评估、课程开发）
- other：无法归入以上任何一类

输出格式（只输出三行）：
【类型】: <标签>
【理由】: <1-2句，说明判断依据>
【依据】: <标题/摘要中的关键线索>"""

def clean(s):
    if pd.isna(s): return ""
    s = re.sub(r"<[^>]+>", " ", str(s)); s = html.unescape(s)
    return re.sub(r"\s+", " ", s.replace("\u00a0", " ")).strip()
def nt(s): return re.sub(r"[^a-z0-9]+", "", str(s).lower())

d = pd.read_csv(os.path.join(ANA, "分析数据集_572_定稿.csv"), encoding="utf-8-sig")
corpus = pd.read_csv(CORPUS); corpus["_n"] = corpus["Title_clean"].map(nt)
c2a = dict(zip(corpus["_n"], corpus["Abstract_clean"].map(clean)))
c2t = dict(zip(corpus["_n"], corpus["Title_clean"].map(clean)))
d["_n"] = d["Title"].map(nt)
d["_t"] = d["_n"].map(lambda k: c2t.get(k, clean(d.loc[d["_n"] == k, "Title"].iloc[0])))
d["_a"] = d["_n"].map(lambda k: c2a.get(k, ""))

key = json.load(open(os.path.join(ROOT, _os.path.join(_ROOTP, '07_AI重跑原始记录'), "config.local.json"), encoding="utf-8"))["deepseek_api_key"]
HEAD = {"Content-Type": "application/json", "Authorization": "Bearer " + key}

def parse(c):
    def g(t):
        m = re.search(r"【%s】\s*[:：]\s*(.*)" % t, c); return m.group(1).strip() if m else ""
    return {"类型": g("类型"), "理由": g("理由"), "依据": g("依据")}

def run_one(run_id):
    path = os.path.join(OUTD, f"run{run_id}.csv")
    if os.path.exists(path):
        done = set(pd.read_csv(path, encoding="utf-8-sig")["ID"])
    else:
        done = set()
    lock = __import__("threading").Lock()
    def work(row):
        if row["ID"] in done: return
        payload = {"model": MODEL, "temperature": TEMP, "max_tokens": MAXTOK, "stream": False,
                   "messages": [{"role": "system", "content": SYS},
                                {"role": "user", "content": f"【标题】\n{row['_t']}\n\n【摘要】\n{row['_a']}\n\n请判断研究设计类型。"}]}
        for att in range(1, 4):
            try:
                r = requests.post(API_URL, headers=HEAD, json=payload, timeout=120)
                body = r.json(); c = body["choices"][0]["message"]["content"]
                p = parse(c)
                p.update({"ID": row["ID"], "Title": row["_t"], "model": body.get("model", ""),
                          "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                with lock:
                    pd.DataFrame([p]).to_csv(path, mode="a", header=not os.path.exists(path),
                                             index=False, encoding="utf-8-sig")
                return
            except Exception:
                if att < 3: time.sleep(2)
                else:
                    with lock:
                        pd.DataFrame([{"ID": row["ID"], "Title": row["_t"], "类型": "api_error",
                                       "理由": "", "依据": "", "model": "", "ts": ""}]).to_csv(
                            path, mode="a", header=not os.path.exists(path), index=False, encoding="utf-8-sig")
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(as_completed([ex.submit(work, r) for _, r in d.iterrows()]))
    t = pd.read_csv(path, encoding="utf-8-sig")
    print(f"run{run_id}: {len(t)} 条 |", t["类型"].value_counts().to_dict())

for i in (1, 2):
    run_one(i)

r1 = pd.read_csv(os.path.join(OUTD, "run1.csv"), encoding="utf-8-sig")[["ID", "类型", "理由"]].rename(columns={"类型": "类型_1", "理由": "理由_1"})
r2 = pd.read_csv(os.path.join(OUTD, "run2.csv"), encoding="utf-8-sig")[["ID", "类型", "理由"]].rename(columns={"类型": "类型_2", "理由": "理由_2"})
m = r1.merge(r2, on="ID", how="outer")
m["类型_最终"] = m.apply(lambda r: r["类型_1"] if r["类型_1"] == r["类型_2"] else (r["类型_1"] if r["类型_1"] != "api_error" else r["类型_2"]), axis=1)
m["两次一致"] = m["类型_1"] == m["类型_2"]
m.to_csv(os.path.join(OUTD, "study_type.csv"), index=False, encoding="utf-8-sig")
agree = m["两次一致"].mean()
from collections import Counter
cats = sorted(set(m["类型_1"]) | set(m["类型_2"]))
# Cohen kappa
ct = pd.crosstab(m["类型_1"], m["类型_2"])
po = sum(ct.iloc[i, i] for i in range(min(ct.shape))) / ct.values.sum() if ct.shape[0] == ct.shape[1] else float("nan")
pe = (ct.sum(axis=1) * ct.sum(axis=0)).sum() / ct.values.sum() ** 2
print(f"\n两次一致率: {agree:.3f} | Cohen's kappa: {(po-pe)/(1-pe):.3f}")
print("最终分布:", m["类型_最终"].value_counts().to_dict())
