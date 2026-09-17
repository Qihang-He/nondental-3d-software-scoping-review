# -*- coding: utf-8 -*-
"""Strip editorial annotations left in the reference list and update the check scripts."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
D = os.path.join('01_投稿文件', 'R2_草稿')

# ---- 1) remove trailing editorial notes from every reference entry
P = os.path.join(D, 'References_R2.md')
s = open(P, encoding='utf-8').read()
before = s
s = re.sub(r'\s*(?:←|<-|â†)\s*\*{0,2}(?:added|replaced|new|revised|updated|removed)\*{0,2}\s*$',
           '', s, flags=re.M | re.I)
s = re.sub(r'\s+$', '', s, flags=re.M)
# any other annotation after a left arrow is an internal note, not part of the citation
s = re.sub(r'\s*(?:←|<-)\s*[^\n]*$', '', s, flags=re.M)
open(P, 'w', encoding='utf-8').write(s)
print('reference annotations removed:', len(re.findall(r'(?:←|<-)', before)))
print('bold markers left in references:', len(re.findall(r'\*\*', s)))

# ---- 2) abstract checker must work without bold labels
Q = os.path.join('04_代码', '07_文档', '_check_abstract_words.py')
t = open(Q, encoding='utf-8').read()
t = t.replace("ab_no_kw.index('**Objective.**')", "ab_no_kw.index('Objective.')")
t = t.replace("body[body.index('**Clinical significance.**'):]",
              "body[body.index('Clinical significance.'):]")
t = t.replace("body[:body.index('**Clinical significance.**')]",
              "body[:body.index('Clinical significance.')]")
open(Q, 'w', encoding='utf-8').write(t)
print('abstract checker updated')

# ---- 3) verify the trend-base wording in the consistency checker
R = os.path.join('04_代码', '07_文档', '_verify_submission_numbers.py')
t = open(R, encoding='utf-8').read()
t = t.replace("has(M, 'the 810 studies whose records carry a month-level publication date', 'trend base')",
              "has(M, '810 records with a month-level date', 'trend base')")
open(R, 'w', encoding='utf-8').write(t)
print('consistency checker updated')

# ---- 4) final scan of every submission document for leftover editing marks
print()
print('=== leftover editorial marks in submission documents ===')
pats = [r'←', r'<-', r'\bTODO\b', r'\bTBD\b', r'\bXXX\b', r'\[insert', r'«', r'»',
        r'\(\*\)', r'\bADDED\b', r'\bREPLACED\b', r'\bNEW\b', r'\bREMOVED\b']
for f in sorted(os.listdir(D)):
    if not f.endswith('.md'):
        continue
    txt = open(os.path.join(D, f), encoding='utf-8').read()
    for p in pats:
        for m in re.finditer(p, txt):
            line = txt[:m.start()].count('\n') + 1
            print('   %-34s line %-4d %s' % (f, line, txt.splitlines()[line - 1][:90]))
