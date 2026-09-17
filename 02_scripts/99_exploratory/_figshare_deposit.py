# -*- coding: utf-8 -*-
"""
_figshare_deposit.py —— 通过 figshare REST API 完成存档并取得 DOI

认证：从环境变量 FIGSHARE_TOKEN 读取个人令牌（**绝不写入文件**）。
      令牌在 https://figshare.com/account/applications 生成。

流程（与 figshare 官方 API 文档一致）：
  1. GET  /item_types, /categories, /licenses      —— 动态解析元数据的 id，避免硬编码猜测
  2. POST /account/articles                        —— 建条目（私有）
  3. POST /account/articles/{id}/files             —— 申请上传，返回 upload_url 与分片
  4. GET  {upload_url}                             —— 取分片清单
  5. PUT  {upload_url}/{partNo}                    —— 逐片上传二进制
  6. POST /account/articles/{id}/files/{file_id}   —— 完成上传
  7. POST /account/articles/{id}/reserve_doi       —— 预留 DOI（先看号，不公开）
  8. POST /account/articles/{id}/publish           —— 发布（需 --publish）

用法：
    $env:FIGSHARE_TOKEN='...'
    python _figshare_deposit.py                # 建私有条目并预留 DOI，打印私密链接
    python _figshare_deposit.py --publish      # 真正发布（这一步之后不可撤回）
"""
import os
import sys
import json
import time
import hashlib
import argparse

import requests

BASE = 'https://api.figshare.com/v2'
ROOT = os.environ.get('SCOPING_ROOT') or r'd:\Desktop\v8 for JD'
ZIP = os.path.join(ROOT, '02_图表附件', 'figshare_v2.0',
                   'nondental-3d-software-reproducibility-materials.zip')
CHUNK = 1024 * 1024

TITLE = ('Application of Nondental 3D Software in Dentistry: A Scoping Review '
         '- reproducibility materials')

DESCRIPTION = """Complete reproducibility materials for a scoping review of nondental three-dimensional (3D) software use across dental disciplines, comprising 861 included studies.

CONTENTS
- Complete search strategies for PubMed, Web of Science and IEEE Xplore
- Screening and coding prompts, and the model metadata for every API call
- All analysis scripts, organised by stage: screening, full-text re-assessment, selection, charting, statistics, figures, documents, verification
- Raw model responses of all three screening runs and the run-to-run agreement analysis
- The two-stage full-text re-assessment pass covering all 1,168 excluded records with a retrievable full text, together with its reconciliation and adjudication steps
- The locked analysis dataset (n = 861)
- Every derived statistic: the PRISMA chain, the discipline-by-software-family contingency analysis, the data-driven workflow archetypes, and the reported advantages, challenges and gaps
- Supplementary Files 2, 3 and 4, and the dataset provenance table
- The author verification workbook with its sampling design
- PIPELINE.md (execution order), 02_scripts/MANIFEST.csv (script index with checksums) and run_pipeline.py (executable pipeline driver)

METHODOLOGICAL NOTE
The review applies its decisive eligibility criterion - the explicit use of a named third-party nondental 3D software package - in full text rather than at abstract level, because the software is normally named only in the methods section of a paper. Re-assessing every excluded record with a retrievable full text added 304 studies to the review. A reverse check removed four studies whose full text names no such package, and three further records were removed because their publication date fell outside the prespecified window. The included set therefore comprises 861 studies. Two additional records were removed during the current audit: one narrative/technical review and one record whose recorded software was not supported by the full text.

No API key is included in this deposit. The analysis steps run without one, because the model logs are already included; only re-running the model-assisted steps requires a key."""

KEYWORDS = ['scoping review', 'dentistry', 'three-dimensional imaging', 'dental software',
            'digital workflow', 'open science', 'reproducibility']

AUTHORS = ['Qihang He', 'Yuchen Liu', 'Ruifeng Zhao', 'Zhiwen Li',
           'Miao Liu', 'Shiwei Song', 'Chen Liu', 'Shizhu Bai']

RELATED = 'https://github.com/Qihang-He/nondental-3d-software-scoping-review/releases/tag/v2.0'

# figshare 只允许设置**叶子**分类；"Dentistry" 是父节点，必须用其子节点
CATEGORY_NAMES = ['Dentistry not elsewhere classified', 'Software and application security']
# figshare 对 defined_type 只接受这组固定枚举值（见 API 报错与官方文档）
VALID_TYPES = ['figure', 'media', 'dataset', 'poster', 'journal contribution',
               'presentation', 'thesis', 'software', 'online resource', 'preprint',
               'book', 'conference contribution']
ITEM_TYPE = 'software'
LICENSE_NAMES = ['MIT']

TOKEN = os.environ.get('FIGSHARE_TOKEN', '').strip()
H = {'Authorization': 'token ' + TOKEN} if TOKEN else {}


def req(method, path, data=None, binary=None, retries=3, soft=False):
    url = path if path.startswith('http') else BASE + path
    for attempt in range(retries):
        if binary is not None:
            r = requests.request(method, url, headers=H, data=binary, timeout=600)
        else:
            hh = dict(H)
            body = None
            if data is not None:
                hh['Content-Type'] = 'application/json'
                body = json.dumps(data)
            r = requests.request(method, url, headers=hh, data=body, timeout=600)
        if r.status_code in (200, 201, 202) or method == 'PUT':
            if r.status_code in (200, 201, 202) and 'json' in r.headers.get('Content-Type', ''):
                try:
                    return r.json()
                except ValueError:
                    return r.text
            return r.text
        if r.status_code in (429, 500, 502, 503) and attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
            continue
        if soft:
            raise RuntimeError('HTTP %s on %s %s\n%s' % (r.status_code, method, url, r.text[:500]))
        raise SystemExit('HTTP %s on %s %s\n%s' % (r.status_code, method, url, r.text[:800]))
    raise SystemExit('请求重试耗尽: %s %s' % (method, url))


def pick(items, names, key='title', idkey='id'):
    """在 figshare 返回的列表中按名称匹配，返回 (id, 匹配到的名称)。
    注意：/licenses 用 value 作标识，/categories 与 /item_types 用 id。"""
    it = pick_item(items, names, key)
    return (it.get(idkey), it.get(key)) if it else (None, None)


def pick_item(items, names, key='title'):
    """返回第一个名称匹配的完整对象。"""
    for want in names:
        for it in items:
            if str(it.get(key, '')).strip().lower() == want.lower():
                return it
    for want in names:                       # 退化为包含匹配
        for it in items:
            if want.lower() in str(it.get(key, '')).lower():
                return it
    return None


def file_md5_size(path):
    md5 = hashlib.md5()
    size = 0
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(CHUNK), b''):
            md5.update(block)
            size += len(block)
    return md5.hexdigest(), size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--publish', action='store_true',
                    help='发布条目（不可撤回）。不加此参数则只建私有条目并预留 DOI。')
    a = ap.parse_args()

    if not TOKEN:
        raise SystemExit('未设置环境变量 FIGSHARE_TOKEN。\n'
                         '请到 https://figshare.com/account/applications 生成个人令牌后：\n'
                         "  $env:FIGSHARE_TOKEN='你的令牌'")

    who = req('GET', '/account')
    print('已登录：%s  <%s>' % (who.get('full_name'), who.get('email')))

    if not os.path.exists(ZIP):
        raise SystemExit('找不到压缩包：%s' % ZIP)
    md5, size = file_md5_size(ZIP)
    print('待上传：%s（%.1f MB, md5=%s）' % (os.path.basename(ZIP), size / 1024 / 1024, md5[:12]))

    # ---- 解析元数据 id，不做硬编码猜测 ----
    types = req('GET', '/item_types')
    strings = {it.get('string_id') for it in types}
    t_string = ITEM_TYPE if ITEM_TYPE in VALID_TYPES else 'dataset'
    cats = req('GET', '/categories')
    lics = req('GET', '/account/licenses')
    l_id, l_name = pick(lics, LICENSE_NAMES, 'name', 'value')
    print('条目类型：%s | 许可：%s (value=%s) | 账户可选类型：%s'
          % (t_string, l_name, l_id, sorted(x for x in strings if x)))
    cat_ids = []
    _cat_map = []
    for cn in CATEGORY_NAMES:
        cid, cname = pick(cats, [cn], 'title', 'id')
        if cid:
            _cat_map.append((cid, cname))
            if cid not in cat_ids:
                cat_ids.append(cid)
                print('  分类：%s (id=%s)' % (cname, cid))
    assert t_string, '未找到合适的条目类型'
    assert l_id, '未找到合适的许可协议'

    # ---- 1. 建条目 ----
    art = None
    for _attempt in range(len(cat_ids) + 2):
        payload = {
            'title': TITLE,
            'description': DESCRIPTION,
            'defined_type': t_string,
            'keywords': KEYWORDS,
            'categories': cat_ids,
            'authors': [{'name': n} for n in AUTHORS],
            'license': l_id,
            'references': [RELATED],
        }
        try:
            art = req('POST', '/account/articles', payload, soft=True)
            break
        except RuntimeError as e:
            msg = str(e)
            # 某些父级分类不允许直接设置 -> 从列表中剔除该名称后重试
            dropped = None
            for cn in list(CATEGORY_NAMES):
                if cn in msg and cn.lower() in [m.lower() for m in [cn]]:
                    for cid, cname in _cat_map:
                        if cname == cn and cid in cat_ids:
                            cat_ids.remove(cid)
                            dropped = cn
                            break
            if dropped:
                print('  分类“%s”不被允许，已剔除后重试' % dropped)
                continue
            raise SystemExit(msg)
    if art is None:
        raise SystemExit('创建条目失败')
    aid = art['location'].rstrip('/').split('/')[-1]
    print('已建条目 id=%s' % aid)

    # ---- 2-6. 上传 ----
    init = req('POST', '/account/articles/%s/files' % aid,
               {'md5': md5, 'size': size, 'name': os.path.basename(ZIP)})
    finfo = req('GET', init['location'])
    fid, upload_url = finfo['id'], finfo['upload_url']

    parts = req('GET', upload_url)['parts']
    print('分片数：%d' % len(parts))
    with open(ZIP, 'rb') as f:
        for p in parts:
            f.seek(p['startOffset'])
            blob = f.read(p['endOffset'] - p['startOffset'] + 1)
            req('PUT', '%s/%s' % (upload_url, p['partNo']), binary=blob)
            print('  分片 %s 已上传 (%.1f MB)' % (p['partNo'], len(blob) / 1024 / 1024))
    req('POST', '/account/articles/%s/files/%s' % (aid, fid))
    print('上传完成')

    # ---- 7. 预留 DOI ----
    try:
        doi = req('POST', '/account/articles/%s/reserve_doi' % aid)
        print('预留 DOI：%s' % doi.get('doi'))
    except SystemExit as e:
        print('预留 DOI 失败（不影响发布）：%s' % str(e)[:120])

    detail = req('GET', '/account/articles/%s' % aid)
    print('\n私密链接（仅你可见，可先给审稿人看）：\n  %s' % detail.get('private_url', ''))

    if not a.publish:
        print('\n已停在发布前。确认无误后加 --publish 再跑一次即可（会新条目，'
              '若要发布同一条目请在网页上点 Publish）。')
        return

    # ---- 8. 发布 ----
    req('POST', '/account/articles/%s/publish' % aid)
    time.sleep(3)
    pub = req('GET', '/articles/%s' % aid)
    print('\n=== 已发布 ===')
    print('URL        : %s' % pub.get('url_public_html'))
    print('DOI        : %s' % pub.get('doi'))
    print('版本 DOI   : %s' % pub.get('doi', '').rstrip() )
    json.dump({'article_id': aid, 'doi': pub.get('doi'), 'url': pub.get('url_public_html')},
              open(os.path.join(ROOT, '02_图表附件', 'figshare_v2.0', 'deposit_result.json'),
                   'w', encoding='utf-8'), ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
