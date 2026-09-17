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
_rebuild_v4.py —— 一键重建：从全文再筛查结果到全部统计、PRISMA、图表、补充材料
按顺序执行，任一步失败即停止并报错。
"""
import os
import subprocess
import sys

ROOT = _ROOTP
PY = sys.executable

STEPS = [
    ('构建 v4 纳入集（补全元数据与国家）', _os.path.join(_ROOTP, '04_代码', '05_分析', '_build_v4.py')),
    ('新增记录 RQ3 编码', _os.path.join(_ROOTP, '04_代码', '05_分析', '_tools_rq3_extend.py')),
    ('合并生成分析数据集 v4', _os.path.join(_ROOTP, '04_代码', '05_分析', '_tools_build_v4_dataset.py')),
    ('重算工作流分型', _os.path.join(_ROOTP, '04_代码', '05_分析', '_tools_archetype.py')),
    ('重算统计核心', _os.path.join(_ROOTP, '04_代码', '05_分析', '_tools_stats_core.py')),
    ('重算补充统计（趋势/列联/共现）', _os.path.join(_ROOTP, '04_代码', '05_分析', '_tools_extra_stats_v3.py')),
    ('重建 PRISMA 链路', _os.path.join(_ROOTP, '04_代码', '05_分析', '_tools_prisma_v2.py')),
    ('重画全部图件', _os.path.join(_ROOTP, '04_代码', '06_新图', 'make_figures_v3.py')),
    ('重画补充图 S1', _os.path.join(_ROOTP, '04_代码', '06_新图', 'make_supp_fig.py')),
    ('重建补充材料 2', _os.path.join(_ROOTP, '04_代码', '07_文档', '_tools_supp2_v2.py')),
    ('重建补充材料 3 与溯源表', _os.path.join(_ROOTP, '04_代码', '07_文档', '_tools_supp3_v2.py')),
]

env = dict(os.environ, PYTHONIOENCODING='utf-8')
for name, script in STEPS:
    p = os.path.join(ROOT, script)
    if not os.path.exists(p):
        print('!! 缺少脚本:', script)
        sys.exit(1)
    print('\n' + '=' * 80)
    print('>>>', name)
    r = subprocess.run([PY, p], cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    print(out.strip()[-2500:])
    if r.returncode != 0:
        print('!! 步骤失败，已停止:', name)
        sys.exit(1)
print('\n全部完成。')
