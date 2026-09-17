# -*- coding: utf-8 -*-
"""
_figshare_finish.py —— 收尾既有 figshare 条目：修正分类 -> 预留 DOI -> （可选）发布

用于已建好、文件已上传的条目。令牌从环境变量 FIGSHARE_TOKEN 读取。

用法：
    python _figshare_finish.py 33684943            # 修正元数据 + 预留 DOI
    python _figshare_finish.py 33684943 --publish  # 发布（不可撤回）
"""
import os
import sys
import json
import time
import argparse

import requests

BASE = 'https://api.figshare.com/v2'
TOKEN = os.environ.get('FIGSHARE_TOKEN', '').strip()
H = {'Authorization': 'token ' + TOKEN, 'Content-Type': 'application/json'}

# 叶子分类（figshare 不允许设置父节点）
CAT_DENTISTRY = 24601          # Dentistry not elsewhere classified
CAT_SOFTWARE = 28918           # Software and application security
RELATED = 'https://github.com/Qihang-He/nondental-3d-software-scoping-review/releases/tag/v1.0'
AUTHORS = ['Qihang He', 'Yuchen Liu', 'Ruifeng Zhao', 'Zhiwen Li',
           'Miao Liu', 'Shiwei Song', 'Chen Liu', 'Shizhu Bai']


def call(method, path, data=None):
    url = path if path.startswith('http') else BASE + path
    r = requests.request(method, url, headers=H,
                         data=json.dumps(data) if data is not None else None, timeout=300)
    if r.status_code not in (200, 201, 202, 204, 205):
        raise SystemExit('HTTP %s on %s %s\n%s' % (r.status_code, method, url, r.text[:600]))
    if r.status_code == 204 or not r.content:
        return None
    try:
        return r.json()
    except ValueError:
        return r.text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('article_id', type=int)
    ap.add_argument('--publish', action='store_true')
    a = ap.parse_args()

    if not TOKEN:
        raise SystemExit('未设置 FIGSHARE_TOKEN')

    aid = a.article_id
    acc = call('GET', '/account')
    print('已登录：%s' % acc.get('email'))

    # ---- 1. 修正分类与关联链接 ----
    call('PUT', '/account/articles/%d' % aid, {
        'categories': [CAT_DENTISTRY, CAT_SOFTWARE],
        'references': [RELATED],
    })
    # figshare 会自动把编辑账户列为作者，会导致首位作者重复 -> 整表替换
    call('PUT', '/account/articles/%d/authors' % aid,
         {'authors': [{'name': n} for n in AUTHORS]})
    art = call('GET', '/account/articles/%d' % aid)
    print('标题      : %s' % art.get('title'))
    print('类型      : %s' % art.get('defined_type'))
    print('分类      : %s' % [c.get('title') for c in art.get('categories', [])])
    print('关键词    : %s' % ', '.join(art.get('keywords', []) or []))
    print('作者      : %s' % '; '.join((x.get('full_name') or x.get('name', ''))
                                       for x in art.get('authors', [])))
    print('许可      : %s' % (art.get('license') or {}).get('name'))

    files = call('GET', '/account/articles/%d/files' % aid)
    for f in files:
        print('文件      : %s  %.1f MB  status=%s'
              % (f.get('name'), f.get('size', 0) / 1024 / 1024, f.get('status')))

    # ---- 2. 预留 DOI ----
    try:
        doi = call('POST', '/account/articles/%d/reserve_doi' % aid)
        print('\n预留 DOI  : %s' % (doi or {}).get('doi'))
    except SystemExit as e:
        print('\n预留 DOI 失败：%s' % str(e)[:200])

    # ---- 3. 私密链接 ----
    shared = ''
    try:
        pl = call('POST', '/account/articles/%d/private_links' % aid, {'read_only': True})
        shared = (pl or {}).get('private_link') or ''
        print('私密链接  : %s' % shared)
    except SystemExit as e:
        print('私密链接创建失败：%s' % str(e)[:200])

    if not a.publish:
        print('\n--- 已停在发布前 ---')
        print('确认无误后运行：python _figshare_finish.py %d --publish' % aid)
        return

    # ---- 4. 发布 ----
    call('POST', '/account/articles/%d/publish' % aid)
    time.sleep(4)
    pub = call('GET', '/articles/%d' % aid)
    out = {
        'article_id': aid,
        'doi': pub.get('doi'),
        'url': pub.get('url_public_html'),
        'published_date': pub.get('published_date'),
        'title': pub.get('title'),
        'license': (pub.get('license') or {}).get('name'),
        'categories': [c.get('title') for c in pub.get('categories', [])],
    }
    dest = os.path.join(os.environ.get('SCOPING_ROOT') or r'd:\Desktop\v8 for JD',
                        '02_图表附件', 'figshare_v1.0', 'deposit_result.json')
    json.dump(out, open(dest, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('\n=== 已发布 ===')
    for k, v in out.items():
        print('%-14s %s' % (k + ':', v))
    print('\n结果已保存到 %s' % dest)


if __name__ == '__main__':
    main()
