# -*- coding: utf-8 -*-
"""Translate the manuscript into Chinese (internal Chinese version).

Block-by-block translation with a cache; the reference list is copied verbatim and the
prompt pins software names, statistics, identifiers, citation markers and links.

Usage:  python _translate_manuscript.py
"""
import io, json, os, re, sys, time, urllib.request

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'd:\Desktop\v8 for JD'
SRC = os.path.join(ROOT, '01_投稿文件', 'R2_草稿', 'Revised_manuscript_R2.md')
OUTDIR = os.path.join(ROOT, '01_投稿文件', '中文版')
OUT = os.path.join(OUTDIR, 'Revised_manuscript_R2_中文.md')
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '_manuscript_zh_cache.json')

API = 'https://api.deepseek.com/chat/completions'
KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not KEY:
    raise SystemExit('DEEPSEEK_API_KEY not set')
BATCH = 5

SYSTEM = (
    'You translate a scientific manuscript (a scoping review in dentistry) from English into '
    'Simplified Chinese for an internal Chinese version. Rules: (1) academic, precise, natural '
    'Chinese, not machine-like; (2) keep EXACTLY unchanged: software and product names, journal '
    'names, statistical symbols and values (e.g. kappa, chi-squared, Cramers V, n = 853, 38.5%), '
    'all numbers, DOIs and URLs, citation markers such as [12,13] or [28-33], and cross-references '
    'such as Figure 2a, Table 1, Supplementary File 3; (3) if a block starts with one or more "#", '
    'keep the same number of "#" characters followed by a space, and translate only the heading '
    'text after them; (4) do not add, drop or summarise content. '
    'Return ONLY a JSON object mapping each input key to its Chinese translation.'
)


def api(items):
    payload = {'model': 'deepseek-chat', 'temperature': 0.0,
               'messages': [{'role': 'system', 'content': SYSTEM},
                            {'role': 'user', 'content': json.dumps(items, ensure_ascii=False)}]}
    req = urllib.request.Request(API, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json',
                                          'Authorization': 'Bearer ' + KEY})
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.load(r)['choices'][0]['message']['content']
    out = re.sub(r'^```(json)?|```$', '', out.strip(), flags=re.M).strip()
    return json.loads(out)


text = io.open(SRC, encoding='utf-8').read()
blocks = text.split('\n\n')
ref_start = next(i for i, b in enumerate(blocks) if b.strip().startswith('## References'))
cache = json.load(io.open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}

todo = [(i, b) for i, b in enumerate(blocks[:ref_start])
        if b.strip() and b.strip() not in cache]
print('blocks total %d | to translate %d | cached %d' % (len(blocks), len(todo), len(cache)))

for n in range(0, len(todo), BATCH):
    chunk = todo[n:n + BATCH]
    items = {str(i): b for i, b in chunk}
    for attempt in range(3):
        try:
            res = api(items)
            break
        except Exception as e:
            print('  batch %d attempt %d failed: %s' % (n // BATCH + 1, attempt + 1, e))
            time.sleep(4)
    else:
        raise SystemExit('batch %d failed' % (n // BATCH + 1))
    for i, b in chunk:
        t = res.get(str(i))
        if isinstance(t, str) and t.strip():
            cache[b.strip()] = t.strip()
    json.dump(cache, io.open(CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('  translated %d/%d' % (min(n + BATCH, len(todo)), len(todo)))

missing = [b for i, b in todo if b.strip() not in cache]
print('missing:', len(missing))
if missing:
    for b in missing[:3]:
        print('   ', b[:70])
    raise SystemExit(1)

def clean_zh(s):
    """Remove line-wrap artefacts: internal newlines and spaces between Chinese characters."""
    parts = [p.strip() for p in s.split('\n')]
    heads = ''
    if parts and parts[0].startswith('#'):
        heads = parts[0]
        parts = parts[1:]
    body = ''.join(parts)
    body = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', body)
    body = re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[，。；：、）】」])', '', body)
    body = re.sub(r'(?<=[（【「])\s+', '', body)
    body = re.sub(r'\s{2,}', ' ', body)
    return (heads + body).strip() if heads else body


out_blocks = []
for i, b in enumerate(blocks):
    if i >= ref_start:
        if i == ref_start:
            out_blocks.append('## 参考文献')
        elif b.strip():
            out_blocks.append(b)          # reference entries stay in English
        continue
    if b.strip():
        out_blocks.append(clean_zh(cache.get(b.strip(), b)))
    else:
        out_blocks.append(b)

os.makedirs(OUTDIR, exist_ok=True)
io.open(OUT, 'w', encoding='utf-8').write('\n\n'.join(out_blocks))
print('written:', OUT)
