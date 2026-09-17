# -*- coding: utf-8 -*-
"""
_figshare_upload_publish.py —— 向已创建的 figshare 条目上传压缩包并发布。

读取 02_图表附件/figshare_v2.0/pending_article.json 中的 article_id，
上传 02_图表附件/figshare_v2.0/nondental-3d-software-reproducibility-materials.zip，然后发布。
"""
import os
import json
import time
import hashlib

import requests

BASE = 'https://api.figshare.com/v2'
ROOT = os.environ.get('SCOPING_ROOT') or r'd:\Desktop\v8 for JD'
ZIP = os.path.join(ROOT, '02_图表附件', 'figshare_v2.0',
                   'nondental-3d-software-reproducibility-materials.zip')
PEND = os.path.join(ROOT, '02_图表附件', 'figshare_v2.0', 'pending_article.json')
OUT = os.path.join(ROOT, '02_图表附件', 'figshare_v2.0', 'deposit_result.json')
CHUNK = 1024 * 1024

TOKEN = os.environ.get('FIGSHARE_TOKEN', '').strip()
if not TOKEN:
    raise SystemExit('未设置环境变量 FIGSHARE_TOKEN')
H = {'Authorization': 'token ' + TOKEN}
AID = json.load(open(PEND, encoding='utf-8'))['article_id']


def req(method, path, data=None, binary=None, retries=5):
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
        if r.status_code in (200, 201, 202):
            if 'json' in r.headers.get('Content-Type', ''):
                try:
                    return r.json()
                except ValueError:
                    return r.text
            return r.text
        if r.status_code in (429, 500, 502, 503) and attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
            continue
        raise SystemExit('HTTP %s on %s %s\n%s' % (r.status_code, method, url, r.text[:600]))
    raise SystemExit('请求重试耗尽')


def md5_size(path):
    m = hashlib.md5()
    size = 0
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(CHUNK), b''):
            m.update(b)
            size += len(b)
    return m.hexdigest(), size


md5, size = md5_size(ZIP)
print('条目 id=%s | 上传 %s (%.1f MB)' % (AID, os.path.basename(ZIP), size / 1024 / 1024))
init = req('POST', '/account/articles/%s/files' % AID,
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
req('POST', '/account/articles/%s/files/%s' % (AID, fid))
print('上传完成')

req('POST', '/account/articles/%s/publish' % AID)
time.sleep(5)
pub = req('GET', '/articles/%s' % AID)
doi = pub.get('doi')
url = pub.get('url_public_html') or pub.get('url_public_api')
print('\n=== 已发布 ===')
print('URL : %s' % url)
print('DOI : %s' % doi)

json.dump({'article_id': AID, 'doi': doi, 'url': url},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('结果已保存：%s' % OUT)
