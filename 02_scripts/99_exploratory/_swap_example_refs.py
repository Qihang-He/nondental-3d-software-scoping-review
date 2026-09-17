# -*- coding: utf-8 -*-
"""Swap the 8 mismatched illustrative citations for included studies that are
charted under the scenario each citation is used for.

Numbers stay identical (only the reference-list entry content changes), so the
first-citation numbering 1..59 is preserved.
"""
import json, re, sys, urllib.request, urllib.parse, os

sys.stdout.reconfigure(encoding='utf-8')

ROOT = r'd:\Desktop\v8 for JD'
MS = ROOT + r'\01_投稿文件\R2_草稿\Revised_manuscript_R2.md'
UA = 'nondental-review-reference-swap/1.0 (mailto:qihanghe05@foxmail.com)'
DRY = os.environ.get('APPLY', '') != '1'

# slot -> (DOI, journal abbreviation override, note)
SWAPS = {
    14: ('10.1016/j.prosdent.2026.05.013', 'J Prosthet Dent', 'scenario: 3D data analysis and accuracy assessment'),
    27: ('10.1186/s12903-026-08336-0', 'BMC Oral Health', 'scenario: image segmentation and 3D reconstruction'),
    34: ('10.3390/bioengineering12050436', 'Bioengineering (Basel)', 'scenario: digital design and manufacturing'),
    36: ('10.1016/j.prosdent.2026.02.049', 'J Prosthet Dent', 'scenario: digital design and manufacturing'),
    43: ('10.1016/j.prosdent.2025.11.030', 'J Prosthet Dent', 'scenario: surgical planning and implementation'),
    44: ('10.1186/s12903-026-07871-0', 'BMC Oral Health', 'scenario: surgical planning and implementation'),
    49: ('10.3389/froh.2026.1763657', 'Front Oral Health', 'scenario: morphological and phenotypic analysis'),
    52: ('10.1016/j.jdent.2024.105493', 'J Dent', 'educational study repurposing nondental tools'),
}


def fetch(doi):
    url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)['message']


def initials(author):
    given = (author.get('given') or '').strip()
    fam = (author.get('family') or '').strip()
    if not fam:
        return (author.get('name') or '').strip()
    out = []
    for tok in [t for t in re.split(r'\s+', given) if t]:
        if '-' in tok:
            out.append('-'.join(p[0].upper() + '.' for p in tok.split('-') if p))
        elif tok.endswith('.'):
            out.append(tok)
        elif len(tok) == 1:
            out.append(tok.upper() + '.')
        else:
            out.append(tok[0].upper() + '.')
    return (''.join(out) + ' ' + fam).strip()


def build(doi, j_override):
    m = fetch(doi)
    authors = ', '.join(initials(a) for a in m.get('author', []) if (a.get('family') or a.get('name')))
    title = re.sub(r'\s+', ' ', m.get('title', [''])[0]).strip().rstrip('.')
    if title.isupper():
        title = title.capitalize()
    year = None
    for k in ('published-print', 'published-online', 'issued', 'published'):
        if k in m and m[k].get('date-parts'):
            year = m[k]['date-parts'][0][0]
            break
    vol = m.get('volume', '')
    page = m.get('page') or m.get('article-number') or ''
    page = page.replace('-', '\u2013') if re.fullmatch(r'[0-9A-Za-z.]+-[0-9A-Za-z.]+', page or '') else page
    journal = j_override or (m.get('short-container-title') or m.get('container-title') or [''])[0]
    entry = f'{authors}, {title}, {journal} {vol} ({year}) {page}. https://doi.org/{doi}.'
    entry = re.sub(r'\s+', ' ', entry).replace(' (year) ', ' ')
    return entry, m


old_txt = open(MS, encoding='utf-8').read()
new_txt = old_txt
report = []
for slot, (doi, j_abbr, note) in sorted(SWAPS.items()):
    entry, raw = build(doi, j_abbr)
    pat = re.compile(r'^\[%d\]\s+.*$' % slot, re.M)
    old = pat.search(new_txt)
    old_line = old.group(0) if old else '(NOT FOUND)'
    report.append((slot, note, old_line, entry))
    if old:
        new_txt = new_txt[:old.start()] + f'[{slot}] {entry}' + new_txt[old.end():]

for slot, note, old_line, entry in report:
    print(f'--- [{slot}] {note}')
    print(f'  OLD: {old_line[:150]}')
    print(f'  NEW: [{slot}] {entry}')
print()

# duplicate-DOI check across the whole list
dois = re.findall(r'doi\.org/(10\.\S+?)\.?\s*$', new_txt, re.M)
seen, dupes = set(), []
for d in [x.lower().rstrip('.,;') for x in dois]:
    if d in seen:
        dupes.append(d)
    seen.add(d)
print('total DOIs:', len(dois), '| duplicates:', dupes or 'none')
print('reference count:', len(re.findall(r'^\[\d+\]\s', new_txt, re.M)))

if DRY:
    print('DRY RUN (set APPLY=1 to write)')
else:
    open(MS, 'w', encoding='utf-8').write(new_txt)
    log = ROOT + r'\08_留痕文档\R2_参考文献_示例引用替换记录.csv'
    with open(log, 'w', encoding='utf-8-sig', newline='') as f:
        import csv as _csv
        w = _csv.writer(f)
        w.writerow(['编号', '替换原因', '原条目', '新条目', '新条目DOI'])
        for slot, note, old_line, entry in report:
            w.writerow([slot, note, old_line, '[' + str(slot) + '] ' + entry, SWAPS[slot][0]])
    print('manuscript updated; log written to', log)
