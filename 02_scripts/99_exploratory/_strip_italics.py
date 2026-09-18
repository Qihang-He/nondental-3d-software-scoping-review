# -*- coding: utf-8 -*-
"""Remove unnecessary italics from the journal-facing documents.

Journal of Dentistry (Elsevier) uses roman type for software names, journal names and defined
group labels; italics are reserved for statistical symbols, which are already roman in this
manuscript. Reviewer comments in the response letter keep their italics (conventional).

Usage:  python _strip_italics.py            # dry run, lists what would change
        APPLY=1 python _strip_italics.py    # rewrite the files
"""
import io, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
D = r'd:\Desktop\v8 for JD\01_投稿文件\R2_草稿'
# the response letter keeps *italic* reviewer comments on purpose
# only the manuscript body: elsewhere '*' marks corresponding authors (Title_Page) or search
# wildcards (Supplementary_File_1), and the response letter keeps italic reviewer comments.
FILES = ['Revised_manuscript_R2.md']
SKIP_REASON = {
    'Title_Page_R2.md': "asterisks mark corresponding authors",
    'Supplementary_File_1_R2.md': "asterisks are search wildcards",
    'Response_to_reviewers_R2.md': "italic reviewer comments are intentional",
}
APPLY = os.environ.get('APPLY', '') == '1'
PAT = re.compile(r'\*([^*\n]{1,200}?)\*')

for fn in FILES:
    p = os.path.join(D, fn)
    if not os.path.exists(p):
        print('missing', fn)
        continue
    t = io.open(p, encoding='utf-8').read()
    spans = PAT.findall(t)
    if not spans:
        print('%-30s no italic spans' % fn)
        continue
    new = PAT.sub(r'\1', t)
    print('%-30s %d span(s) -> %s' % (fn, len(spans), '; '.join(s[:60] for s in spans[:8])))
    if APPLY:
        io.open(p, 'w', encoding='utf-8').write(new)
print('APPLIED' if APPLY else 'DRY RUN (set APPLY=1 to write)')
