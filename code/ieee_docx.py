"""
Put a pandoc-produced .docx into IEEE conference format.

pandoc gives correct content in a generic single-column document: Letter size
is not even set. An IEEE venue that accepts Word expects its own two-column
layout, and a single-column file is not submittable. This rewrites the
geometry, the type and the heading numbering to match the PDF the same source
produces.

WHAT IT SETS, and where the numbers come from (IEEE conference template,
US Letter):

    page            8.5 x 11 in
    margins         top 0.75, bottom 1.0, left/right 0.625 in
    columns         two, 3.5 in each, 0.25 in gutter -- which is exactly the
                    7.25 in of text width those margins leave
    title           24 pt, centred, spanning both columns
    authors         11 pt, centred, spanning both columns
    abstract        9 pt bold, with a bold-italic "Abstract---" lead-in
    index terms     9 pt bold italic
    body            10 pt justified, 0.2 in first-line indent
    headings        10 pt, centred, small caps, Roman numeral
    subheadings     10 pt italic, left, lettered
    references      8 pt

The title block spans the page while the body is in two columns, so the
document needs two sections: a one-column section ending after the authors,
then a continuous two-column section for everything else. python-docx can
only append a section, so the first section's properties are inserted
directly into the paragraph that ends it.

    python ieee_docx.py            # formats paper/main.docx in place
"""

from __future__ import annotations

import copy
import pathlib
import re
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

PAPER = pathlib.Path(__file__).resolve().parent.parent / "paper"
DOCX = PAPER / "main.docx"

TIMES = "Times New Roman"
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV"]


# --------------------------------------------------------------------------
def _el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn("w:" + k), str(v))
    return e


def page_setup(sectPr, columns: int, continuous: bool = False) -> None:
    """IEEE geometry on one section's properties.

    sectPr's children are a SEQUENCE in the schema, not a bag: w:type must
    precede w:pgSz, which precedes w:pgMar, which precedes w:cols. Appending
    w:type last leaves it out of order, Word ignores it, and a section meant
    to be continuous becomes a page break -- which is what put the title
    alone on page one. So the managed children are rebuilt in order, and only
    the note properties, which legitimately come first, are kept.
    """
    keep = [c for c in list(sectPr)
            if c.tag in (qn("w:footnotePr"), qn("w:endnotePr"))]
    for c in list(sectPr):
        sectPr.remove(c)
    for c in keep:
        sectPr.append(c)

    if continuous:
        sectPr.append(_el("w:type", val="continuous"))
    sectPr.append(_el("w:pgSz", w=12240, h=15840))          # 8.5 x 11 in
    sectPr.append(_el("w:pgMar", top=1080, bottom=1440,     # 0.75 / 1.0 in
                      left=900, right=900,                  # 0.625 in
                      header=720, footer=720, gutter=0))
    cols = _el("w:cols", num=columns, space=360, equalWidth=1)  # 0.25 in
    sectPr.append(cols)


def split_title_block(doc) -> int:
    """Give the title block its own one-column section.

    Returns the index of the paragraph that now carries the first section's
    properties. Everything from the abstract on stays in the document-level
    section, which becomes the two-column one.
    """
    paras = doc.paragraphs
    # the two-column region starts at the abstract
    start = next((i for i, p in enumerate(paras)
                  if p.style.name.startswith("Abstract")), None)
    if start is None or start == 0:
        return -1
    end = paras[start - 1]            # last paragraph of the title block

    body_sectPr = doc.element.body.find(qn("w:sectPr"))
    first = copy.deepcopy(body_sectPr)
    page_setup(first, columns=1, continuous=True)

    pPr = end._p.get_or_add_pPr()
    pPr.append(first)
    return start


def style_runs(p, size=None, bold=None, italic=None, caps=None) -> None:
    for r in p.runs:
        r.font.name = TIMES
        r._element.rPr.rFonts.set(qn("w:eastAsia"), TIMES)
        if size is not None:
            r.font.size = Pt(size)
        if bold is not None:
            r.font.bold = bold
        if italic is not None:
            r.font.italic = italic
        if caps is not None:
            r.font.small_caps = caps


def runin_abstract(doc) -> bool:
    """Fold the "Abstract" heading into the abstract itself.

    IEEE has no standalone Abstract heading. The abstract is one paragraph
    opening with a bold-italic "Abstract" and an em dash, then the text in
    bold: *Abstract*---Automated agents increasingly... pandoc emits the
    word as its own paragraph, which is the single most visible way a
    converted document announces it is not in the template.

    Nothing is moved between paragraphs. An earlier version rebuilt the
    paragraph by copying its runs across, which silently dropped the two
    percentages from the abstract: OMML maths is an <m:oMath> element, not a
    <w:r>, so paragraph.runs does not see it and it was left behind with the
    discarded paragraph. Insert in place instead.
    """
    paras = doc.paragraphs
    head = next((p for p in paras if p.style.name == "Abstract Title"), None)
    body = next((p for p in paras if p.style.name == "Abstract"), None)
    if head is None or body is None or not body.runs:
        return False

    from docx.text.run import Run
    first = body.runs[0]._element
    tag = copy.deepcopy(first)
    first.addprevious(tag)
    tag_run = Run(tag, body)
    tag_run.text = "Abstract—"
    tag_run.font.bold = True
    tag_run.font.italic = True
    tag_run.font.size = Pt(9)
    tag_run.font.name = TIMES

    head._p.getparent().remove(head._p)
    return True


def runin_index_terms(doc) -> bool:
    """IEEE italicises only the words "Index Terms", not the list."""
    for p in doc.paragraphs:
        if p.text.strip().startswith("Index Terms") and p.runs:
            for i, r in enumerate(p.runs):
                r.font.bold = True
                r.font.italic = (i == 0)
                r.font.size = Pt(9)
                r.font.name = TIMES
            p.paragraph_format.first_line_indent = Inches(0)
            return True
    return False


def renumber_headings(doc) -> tuple[int, int]:
    """pandoc numbers 1, 2.1, 2.2. IEEE numbers I, II and then A, B."""
    sec = 0
    sub = 0
    n1 = n2 = 0
    for p in doc.paragraphs:
        if p.style.name == "Heading 1":
            text = re.sub(r"^\s*\d+\s*", "", p.text).strip()
            # unnumbered back matter keeps its name
            if text.lower().startswith(("references", "data availability")):
                new = text
            else:
                sec += 1
                sub = 0
                new = "%s. %s" % (ROMAN[sec] if sec < len(ROMAN) else sec, text)
            n1 += 1
        elif p.style.name == "Heading 2":
            text = re.sub(r"^\s*\d+\.\d+\s*", "", p.text).strip()
            new = "%s. %s" % (chr(ord("A") + sub), text)
            sub += 1
            n2 += 1
        else:
            continue
        for r in list(p.runs)[1:]:
            r._element.getparent().remove(r._element)
        if p.runs:
            p.runs[0].text = new
        else:
            p.add_run(new)
    return n1, n2


# --------------------------------------------------------------------------
def main() -> int:
    if not DOCX.exists():
        print("  no %s -- run make_docx.py first" % DOCX)
        return 1

    doc = docx.Document(str(DOCX))

    # --- two sections: title block full width, body in two columns --------
    start = split_title_block(doc)
    # w:type describes how the section it belongs to BEGINS, so "continuous"
    # goes on the body section -- the one that has to start on the same page
    # as the title block. Putting it only on the title block's own sectPr
    # left the title alone on page one.
    body_sectPr = doc.element.body.find(qn("w:sectPr"))
    page_setup(body_sectPr, columns=2, continuous=True)
    print("  sections        : title block full width, body two columns"
          if start > 0 else "  sections        : single (no abstract found)")

    # --- the default style, so anything untouched is still Times ----------
    normal = doc.styles["Normal"]
    normal.font.name = TIMES
    normal.font.size = Pt(10)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), TIMES)

    # --- type, block by block ---------------------------------------------
    in_refs = False
    counts = {"body": 0, "ref": 0}
    for i, p in enumerate(doc.paragraphs):
        name = p.style.name

        if name == "Title":
            style_runs(p, size=24)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif name in ("Author", "Subtitle"):
            style_runs(p, size=11)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif name.startswith("Abstract"):
            style_runs(p, size=9, bold=True)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif name.startswith("Heading 1"):
            style_runs(p, size=10, bold=False, caps=True)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if p.text.strip().lower().startswith("references"):
                in_refs = True
        elif name.startswith("Heading 2"):
            style_runs(p, size=10, italic=True, bold=False)
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif name in ("Image Caption", "Table Caption", "Captioned Figure"):
            style_runs(p, size=8)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            if in_refs:
                style_runs(p, size=8)
                counts["ref"] += 1
            else:
                style_runs(p, size=10)
                if p.text.strip():
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.first_line_indent = Inches(0.2)
                    counts["body"] += 1
            p.paragraph_format.space_after = Pt(0)

    print("  abstract        : %s"
          % ("run-in, no standalone heading" if runin_abstract(doc)
             else "left as-is (no Abstract style found)"))
    print("  index terms     : %s"
          % ("italic lead-in only" if runin_index_terms(doc) else "not found"))

    n1, n2 = renumber_headings(doc)
    print("  headings        : %d numbered I, II, ... and %d lettered A, B, ..."
          % (n1, n2))
    print("  body paragraphs : %d at 10 pt justified" % counts["body"])
    print("  references      : %d at 8 pt" % counts["ref"])

    doc.save(str(DOCX))
    print("  wrote %s" % DOCX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
