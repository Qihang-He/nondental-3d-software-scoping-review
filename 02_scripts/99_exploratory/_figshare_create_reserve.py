# -*- coding: utf-8 -*-
"""
_figshare_create_reserve.py —— 创建新的 figshare 条目并预留 DOI（不发布）。

用于「先预留 DOI -> 写入 README/CITATION -> 重打包 -> 上传发布」的无环形流程。
输出：02_图表附件/figshare_v2.0/pending_article.json（含 article_id 与预留 DOI）
"""
import os
import json
import time

import requests

BASE = 'https://api.figshare.com/v2'
ROOT = os.environ.get('SCOPING_ROOT') or r'd:\Desktop\v8 for JD'
OUT = os.path.join(ROOT, '02_图表附件', 'figshare_v2.0', 'pending_article.json')

TITLE = ('Application of Nondental 3D Software in Dentistry: A Scoping Review '
         '- reproducibility materials')

DESCRIPTION = """Complete reproducibility materials for a scoping review of nondental three-dimensional (3D) software use across dental disciplines, comprising 853 included studies.

CONTENTS
- Complete search strategies for PubMed, Web of Science and IEEE Xplore
- Screening and coding prompts, and the model metadata for every API call
- All analysis scripts, organised by stage: screening, full-text re-assessment, selection, charting, statistics, figures, documents, verification
- Raw model responses of all three screening runs and the run-to-run agreement analysis
- The two-stage full-text re-assessment pass covering every excluded record with a retrievable full text, together with its reconciliation and adjudication steps
- The locked analysis dataset (n = 853)
- Every derived statistic: the PRISMA chain, the discipline-by-software-family contingency analysis, the data-driven workflow archetypes, and the reported advantages, challenges and gaps
- Supplementary Files 2, 3 and 4, and the dataset provenance table
- The author verification workbook with its sampling design
- PIPELINE.md (execution order), 02_scripts/MANIFEST.csv (script index with checksums) and run_pipeline.py (executable pipeline driver)

METHODOLOGICAL NOTE
The review applies its decisive eligibility criterion - the explicit use of a named third-party nondental 3D software package - in full text rather than at abstract level, because the software is normally named only in the methods section of a paper. Re-assessing every excluded record with a retrievable full text added 304 studies to the review. A reverse check removed four studies whose full text names no such package, and three further records were removed because their publication date fell outside the prespecified window. Two additional records were removed during the current audit: one narrative/technical review and one record whose recorded software was not supported by the full text.

SOFTWARE-SCOPE AUDIT
Every package recorded in the review was finally re-verified against the review's definition of nondental 3D software. Ten entries were removed: MATLAB, Python, GNU Octave, TensorFlow and Keras, which are general-purpose programming, numerical-computing or machine-learning platforms rather than 3D software packages; Open3D, Trimesh and Iso2mesh, which are programming libraries rather than software packages; and R2 Gate and Viewbox, which were developed specifically for dentistry and therefore fail the origin criterion. CreatWare, Midas FX+ and Scalismo Lab were provisionally flagged but retained, because their full texts confirmed a nondental origin. Eight included studies named no other eligible package and were removed, so the included set comprises 853 studies and the software list comprises 100 packages. The per-record revision log is deposited as 05_results/software_scope_revision.csv.

No API key is included in this deposit. The analysis steps run without one, because the model logs are already included; only re-running the model-assisted steps requires a key."""

KEYWORDS = ['scoping review', 'dentistry', 'three-dimensional imaging', 'dental software',
            'digital workflow', 'open science', 'reproducibility']
AUTHORS = ['Qihang He', 'Yuchen Liu', 'Ruifeng Zhao', 'Zhiwen Li',
           'Miao Liu', 'Shiwei Song', 'Chen Liu', 'Shizhu Bai']
RELATED = 'https://github.com/Qihang-He/nondental-3d-software-scoping-review/releases/tag/v2.0'

TOKEN = os.environ.get('FIGSHARE_TOKEN', '').strip()
if not TOKEN:
    raise SystemExit('未设置环境变量 FIGSHARE_TOKEN')
H = {'Authorization': 'token ' + TOKEN}


def req(method, path, data=None, retries=5):
    url = path if path.startswith('http') else BASE + path
    for attempt in range(retries):
        hh = dict(H)
        body = None
        if data is not None:
            hh['Content-Type'] = 'application/json'
            body = json.dumps(data)
        r = requests.request(method, url, headers=hh, data=body, timeout=120)
        if r.status_code in (200, 201, 202):
            return r.json()
        if r.status_code in (429, 500, 502, 503) and attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
            continue
        raise SystemExit('HTTP %s on %s %s\n%s' % (r.status_code, method, url, r.text[:500]))
    raise SystemExit('请求重试耗尽')


who = req('GET', '/account')
print('已登录：%s  <%s>' % (who.get('full_name'), who.get('email')))

cats = req('GET', '/categories')
lics = req('GET', '/account/licenses')


def pick(items, name, key, idkey):
    for it in items:
        if str(it.get(key, '')).strip().lower() == name.lower():
            return it.get(idkey)
    return None


cat_ids = [cid for cid in (
    pick(cats, 'Dentistry not elsewhere classified', 'title', 'id'),
    pick(cats, 'Software and application security', 'title', 'id')) if cid]
l_id = pick(lics, 'MIT', 'name', 'value')

payload = {
    'title': TITLE,
    'description': DESCRIPTION,
    'defined_type': 'software',
    'keywords': KEYWORDS,
    'categories': cat_ids,
    'authors': [{'name': n} for n in AUTHORS],
    'license': l_id,
    'references': [RELATED],
}
art = req('POST', '/account/articles', payload)
aid = art['location'].rstrip('/').split('/')[-1]
print('已建条目 id=%s' % aid)

doi = req('POST', '/account/articles/%s/reserve_doi' % aid)
print('预留 DOI：%s' % doi.get('doi'))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({'article_id': aid, 'doi': doi.get('doi')},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('已保存：%s' % OUT)
