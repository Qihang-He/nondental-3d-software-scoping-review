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
_tools_renumber_refs.py —— 删除重复参考文献（原 [40] 与 [5] 为同一文献）并整体重编号
处理对象：01_投稿文件/R2_草稿/Revised_manuscript_R2.md、References_R2.md
"""
import os
import re

ROOT = _os.path.join(_ROOTP, '01_投稿文件', 'R2_草稿')
DROP = 40          # 要删除的编号（与 [5] 重复）


def remap(n):
    return n - 1 if n > DROP else n


# ---------- 1. 正文引用重编号 ----------
ms_fp = os.path.join(ROOT, 'Revised_manuscript_R2.md')
txt = open(ms_fp, encoding='utf-8').read()


def fix_bracket(m):
    inner = m.group(1)
    parts = [p.strip() for p in inner.split(',')]
    out = []
    for p in parts:
        if re.fullmatch(r'\d+', p):
            n = int(p)
            if n == DROP:
                continue
            out.append(str(remap(n)))
        else:
            q = re.split(r'([\u2013\u2014-])', p)
            if len(q) == 3 and q[0].strip().isdigit() and q[2].strip().isdigit():
                a, b = int(q[0]), int(q[2])
                rng = [x for x in range(a, b + 1) if x != DROP]
                if not rng:
                    continue
                if len(rng) == 1:
                    out.append(str(remap(rng[0])))
                else:
                    out.append('%d\u2013%d' % (remap(rng[0]), remap(rng[-1])))
            else:
                out.append(p)
    return '[' + ','.join(out) + ']' if out else ''


new_txt = re.sub(r'\[([0-9,\u2013\u2014\- ]+)\]', fix_bracket, txt)
open(ms_fp, 'w', encoding='utf-8').write(new_txt)
print('正文引用已重编号')

# ---------- 2. 参考文献表重编号 ----------
rf_fp = os.path.join(ROOT, 'References_R2.md')
lines = open(rf_fp, encoding='utf-8').read().split('\n')
out_lines, header = [], []
for ln in lines:
    m = re.match(r'^\[(\d+)\]\s', ln)
    if m:
        n = int(m.group(1))
        if n == DROP:
            print('  删除重复条目:', ln[:90])
            continue
        out_lines.append(re.sub(r'^\[(\d+)\]', '[%d]' % remap(n), ln, count=1))
    else:
        header.append(ln)

note = ('> Ref 40 of the previous R2 draft was an exact duplicate of Ref 5 (Eldahmy et al., '
        'Sci Rep 2025) and has been deleted; all subsequent references and in-text citations have '
        'been renumbered accordingly.')
final = '\n'.join(header) + '\n' + note + '\n\n' + '\n'.join(out_lines) + '\n'
open(rf_fp, 'w', encoding='utf-8').write(final)
print('参考文献表已重编号')
