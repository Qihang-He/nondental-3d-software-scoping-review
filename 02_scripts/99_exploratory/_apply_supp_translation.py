# -*- coding: utf-8 -*-
"""Apply the English translations to the supplementary workbooks.

Each column that contains Chinese becomes:  <English column> | <English header> (original Chinese).
The original workbooks are backed up to _backup_pre_en/ first.
"""
import json, os, re, shutil, sys

import openpyxl
from openpyxl.styles import Font

sys.stdout.reconfigure(encoding='utf-8')

D = r'd:\Desktop\v8 for JD\02_图表附件\R2_补充材料'
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_F = os.path.join(HERE, '_supp_translation_cache.json')
BACKUP = os.path.join(D, '_backup_pre_en')
CJK = re.compile(r'[\u4e00-\u9fff]')
FILES = ['Supplementary_File_2_R2.xlsx', 'Supplementary_File_3.xlsx',
         'Supplementary_File_4_Author_verification.xlsx']

cache = json.load(open(CACHE_F, encoding='utf-8'))
os.makedirs(BACKUP, exist_ok=True)


def en(v):
    if isinstance(v, str) and CJK.search(v):
        s = v.strip()
        if s in cache:
            lead = v[:len(v) - len(v.lstrip())]
            return lead + cache[s]
        return v
    return v


for fn in FILES:
    src = os.path.join(D, fn)
    bak = os.path.join(BACKUP, fn)
    if os.path.exists(bak):                # rebuild from the untouched original
        shutil.copy2(bak, src)
    else:
        shutil.copy2(src, bak)
    wb = openpyxl.load_workbook(src)
    for ws in wb.worksheets:
        cjk_cols = []
        twin_cols = set()
        for col in range(1, ws.max_column + 1):
            body_cjk = False
            head_cjk = False
            for row in range(1, ws.max_row + 1):
                v = ws.cell(row=row, column=col).value
                if isinstance(v, str) and CJK.search(v):
                    if row == 1:
                        head_cjk = True
                    else:
                        body_cjk = True
            if head_cjk or body_cjk:
                cjk_cols.append(col)
            if body_cjk:
                twin_cols.add(col)
        for col in sorted(cjk_cols, reverse=True):
            # snapshot the original column
            orig = [(r, ws.cell(row=r, column=col).value) for r in range(1, ws.max_row + 1)]
            head = orig[0][1]
            # rewrite the column in English
            for r, v in orig[1:]:
                ws.cell(row=r, column=col).value = en(v)
            new_head = en(head) if isinstance(head, str) else 'Column %d' % col
            ws.cell(row=1, column=col).value = new_head
            ws.cell(row=1, column=col).font = Font(bold=True)
            ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 42
            if col not in twin_cols:
                continue
            # insert the Chinese reference column right after it
            ws.insert_cols(col + 1)
            ws.cell(row=1, column=col + 1).value = '%s (original Chinese)' % new_head
            ws.cell(row=1, column=col + 1).font = Font(bold=True)
            for r, v in orig[1:]:
                ws.cell(row=r, column=col + 1).value = v
            ws.column_dimensions[openpyxl.utils.get_column_letter(col + 1)].width = 42
    wb.save(src)
    wb.close()
    print('rewritten:', fn)
print('done')
