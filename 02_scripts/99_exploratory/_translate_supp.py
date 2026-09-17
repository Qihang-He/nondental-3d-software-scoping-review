# -*- coding: utf-8 -*-
"""Translate the Chinese content of the supplementary workbooks into English.

For every column that contains Chinese text, the English column replaces it and the
original Chinese column is re-inserted immediately afterwards, named
"<header> (original Chinese)", so the two can be compared side by side.

Originals are backed up to _backup_pre_en/ before the files are rewritten.
"""
import json, os, re, shutil, sys, time, urllib.request

import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

D = r'd:\Desktop\v8 for JD\02_图表附件\R2_补充材料'
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_F = os.path.join(HERE, '_supp_translation_cache.json')
BACKUP = os.path.join(D, '_backup_pre_en')
CJK = re.compile(r'[\u4e00-\u9fff]')

FILES = ['Supplementary_File_2_R2.xlsx', 'Supplementary_File_3.xlsx',
         'Supplementary_File_4_Author_verification.xlsx']

API = 'https://api.deepseek.com/chat/completions'
KEY = os.environ.get('DEEPSEEK_API_KEY', '')
BATCH = 12


def load_cache():
    if os.path.exists(CACHE_F):
        with open(CACHE_F, encoding='utf-8') as f:
            return json.load(f)
    return {}


def call_api(items):
    payload = {
        'model': 'deepseek-chat',
        'temperature': 0.0,
        'messages': [
            {'role': 'system', 'content':
             'You translate Chinese text into concise, professional English for the supplementary '
             'tables of a scientific review article. Keep terminology consistent (software names, '
             'dental disciplines, verdicts). Do not add commentary, do not shorten the meaning. '
             'Return ONLY a JSON object mapping the given key to the English translation.'},
            {'role': 'user', 'content': json.dumps(items, ensure_ascii=False)},
        ],
    }
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + KEY})
    with urllib.request.urlopen(req, timeout=300) as r:
        out = json.load(r)['choices'][0]['message']['content']
    out = re.sub(r'^```(json)?|```$', '', out.strip(), flags=re.M).strip()
    return json.loads(out)


def main():
    cache = load_cache()
    todo = []
    for fn in FILES:
        wb = openpyxl.load_workbook(os.path.join(D, fn))
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    v = c.value
                    if isinstance(v, str) and CJK.search(v):
                        s = v.strip()
                        if s and s not in cache and s not in todo:
                            todo.append(s)
        wb.close()
    print('unique untranslated strings:', len(todo), '| cached:', len(cache))

    done = 0
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        items = {str(j): s for j, s in enumerate(chunk)}
        for attempt in range(3):
            try:
                res = call_api(items)
                break
            except Exception as e:
                print('  batch %d attempt %d failed: %s' % (i // BATCH + 1, attempt + 1, e))
                time.sleep(3)
        else:
            print('  batch %d GIVEN UP' % (i // BATCH + 1))
            continue
        for j, s in enumerate(chunk):
            t = res.get(str(j))
            if isinstance(t, str) and t.strip():
                cache[s] = t.strip()
        done += len(chunk)
        with open(CACHE_F, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=0)
        print('  translated %d/%d' % (done, len(todo)))

    missing = [s for s in todo if s not in cache]
    print('still missing:', len(missing))
    for s in missing[:5]:
        print('   ', s[:70])
    return 0 if not missing else 1


if __name__ == '__main__':
    sys.exit(main())
