# -*- coding: utf-8 -*-
"""Markdown → Word（基础格式：标题/粗体/表格/列表），用于投稿回复信"""
import os, re, sys
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_runs(par, text):
    # 处理 **粗体**
    for i, seg in enumerate(re.split(r"(\*\*[^*]+\*\*)", text)):
        if not seg: continue
        if seg.startswith("**") and seg.endswith("**"):
            r = par.add_run(seg[2:-2]); r.bold = True
        else:
            par.add_run(seg)

def md_to_docx(md_path, docx_path):
    lines = open(md_path, encoding="utf-8").read().split("\n")
    doc = Document()
    st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11)
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        # 表格
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1].strip()):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                if not re.match(r"^\|[\s:\-|]+\|$", lines[i].strip()):
                    rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            if rows:
                t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Light Grid Accent 1"
                for r, row in enumerate(rows):
                    for c, val in enumerate(row[:len(rows[0])]):
                        cell = t.cell(r, c); cell.text = ""
                        add_runs(cell.paragraphs[0], val)
                        for run in cell.paragraphs[0].runs:
                            run.font.size = Pt(9.5)
                            if r == 0: run.bold = True
            doc.add_paragraph()
            continue
        if ln.startswith("# "):
            h = doc.add_heading(ln[2:], level=1)
        elif ln.startswith("## "):
            doc.add_heading(ln[3:], level=2)
        elif ln.startswith("### "):
            doc.add_heading(ln[4:], level=3)
        elif ln.startswith("- ") or ln.startswith("* "):
            add_runs(doc.add_paragraph(style="List Bullet"), ln[2:])
        elif re.match(r"^\d+\.\s", ln):
            add_runs(doc.add_paragraph(style="List Number"), re.sub(r"^\d+\.\s", "", ln))
        elif ln.startswith("---"):
            doc.add_paragraph("―" * 30).alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif ln.strip() == "":
            pass
        else:
            add_runs(doc.add_paragraph(), ln)
        i += 1
    doc.save(docx_path)
    print("saved", docx_path)

if __name__ == "__main__":
    md_to_docx(sys.argv[1], sys.argv[2])
