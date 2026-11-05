"""
Checks on the manuscript that LaTeX will not do for you.

A clean compile proves only that TeX could parse the file. It does not prove
the document is correct. Three defects in this paper compiled with zero
errors and printed visible garbage into the PDF, because a command that loses
its backslash is not a broken command -- it is ordinary words, and TeX sets
them. So every check here runs against the BUILT PDF as well as the source.

    python audit_paper.py                  # all groups
    python audit_paper.py --group hygiene  # one group
    python audit_paper.py --quiet          # exit code only, for CI

Exit code 0 if every check passes, 1 otherwise. TODO placeholders are
reported but do not fail the run: they are expected until submission.

GROUPS
    hygiene   control characters in the source; label keys leaked into the
              rendered text. These catch the escape-conversion bug class.
    ieee      template, abstract length, float captions and placement,
              figure and table cross-references, Fig. vs Figure.
    eqnums    equation numbers cited in code docstrings against the built
              paper, which renumbers whenever it is restructured.
    refs      citations resolve both ways against refs.bib.
    figures   each figure's scale factor on the page.
    docx      the Word version against the PDF: IEEE layout, and that nothing
              was lost converting.
    voice     punctuation density and sentence shape, against ranges that
              published prose actually occupies.
"""

from __future__ import annotations

import argparse
import io
import pathlib
import re
import statistics
import subprocess
import sys

B = chr(92)
HERE = pathlib.Path(__file__).resolve().parent
PAPER = HERE.parent / "paper"
TEX = PAPER / "main.tex"
PDF = PAPER / "build" / "main.pdf"
BIB = PAPER / "refs.bib"

_fail = 0
_warn = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    """Record one check. Anything false sets the exit code."""
    global _fail
    mark = "ok  " if ok else "FAIL"
    if not ok:
        _fail += 1
    print("  [%s] %-44s %s" % (mark, label, detail))


def note(label: str, detail: str = "") -> None:
    global _warn
    _warn += 1
    print("  [note] %-44s %s" % (label, detail))


def head(title: str) -> None:
    print()
    print("=" * 72)
    print("  " + title)
    print("=" * 72)


# --------------------------------------------------------------------------
def load():
    """Source, comment-stripped source, and the PDF's extracted text.

    The comment-stripped copy matters: an earlier version of this audit
    reported the wrong document class because its pattern matched a
    commented-out line offering an alternative template.
    """
    src_raw = io.open(TEX, encoding="utf-8").read()
    src = re.sub(r"(?m)^%.*$", "", src_raw)
    txt = ""
    if PDF.exists():
        out = PAPER / "build" / "plain.txt"
        try:
            subprocess.run(["pdftotext", str(PDF), str(out)],
                           check=True, capture_output=True)
            txt = io.open(out, encoding="utf-8", errors="replace").read()
        except (OSError, subprocess.CalledProcessError):
            note("pdftotext unavailable", "PDF-side checks skipped")
    else:
        note("no build/main.pdf", "build the paper first for PDF-side checks")
    return src_raw, src, txt


def prose_of(src: str) -> str:
    """Body prose only: no math, floats, citations, label keys or macros.

    Label keys have to go via their arguments, not just the command name --
    stripping \\ref but leaving {sec:stake} counts a colon that is not
    punctuation, which inflated the colon measurement by a factor of two the
    first time this was run.
    """
    s = re.sub(r"\\(?:ref|eqref|label|cite[tp]?)\{[^}]*\}", " ", src)
    s = re.sub(r"\$[^$]*\$", " X ", s)
    s = re.sub(r"\\begin\{(table|figure|align|equation|tabular)\*?\}.*?"
               r"\\end\{\1\*?\}", " ", s, flags=re.S)
    s = re.sub(r"\\(?:emph|textbf|texttt|textit)\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    return re.sub(r"[{}~]", " ", s)


# --------------------------------------------------------------------------
def g_hygiene(src_raw: str, src: str, txt: str) -> None:
    head("HYGIENE -- the bug class LaTeX will not report")

    # \f \t \r \n in generated text become the characters they stand for,
    # and the command loses its first letter with the backslash.
    raw = io.open(TEX, "rb").read()
    bad = []
    for i, b in enumerate(raw):
        if (b < 32 and b not in (10, 13)) or b == 127:
            bad.append((i, b))
        elif b == 13 and (i + 1 >= len(raw) or raw[i + 1] != 10):
            bad.append((i, b))
    check(not bad, "no control characters in source",
          "" if not bad else "%d found: %s" % (len(bad), bad[:4]))

    # \ref{sec:x} prints a number. The key itself can never appear.
    if txt:
        leaked = sorted(set(re.findall(
            r"\b(?:sec|eq|fig|tab|prop|ass):[a-z]+", txt)))
        check(not leaked, "no label keys in rendered text",
              "" if not leaked else ", ".join(leaked[:6]))

        # the signature of a decapitated command, in the output
        frags = sorted(set(re.findall(
            r"\b(?:ootnotesize|abcolsep|ewcommand|onumber|oprule|ottomrule"
            r"|idrule|oindent|extbf|extit|exttt|rac\{)", txt)))
        check(not frags, "no decapitated commands in rendered text",
              "" if not frags else ", ".join(frags))

    todo = re.findall(r"\\TODO\{([^}]*)", src)
    if todo:
        note("TODO placeholders still live", "%d" % len(todo))
        for x in todo:
            print("         - %s" % x[:60])


def g_ieee(src: str, txt: str) -> None:
    head("IEEE -- template and house style")

    m = re.search(r"\\documentclass\[([^]]*)\]\{([^}]*)\}", src)
    check(bool(m) and m.group(2) == "IEEEtran" and "conference" in m.group(1),
          "documentclass", m.group(0) if m else "not found")

    m = re.search(r"\\bibliographystyle\{([^}]*)\}", src)
    check(bool(m) and m.group(1) == "IEEEtran", "bibliographystyle",
          m.group(1) if m else "not found")

    check("\\begin{IEEEkeywords}" in src, "IEEEkeywords block present")

    wrong = len(re.findall(r"\bFigure~\\ref", src))
    check(wrong == 0, "Fig.~ not Figure~ in cross-references",
          "%d wrong, %d right" % (wrong, len(re.findall(r"\bFig\.~\\ref", src))))

    eqr = len(re.findall(r"Eq\.~\\ref", src))
    check(eqr == 0, "\\eqref not Eq.~\\ref",
          "%d \\eqref, %d Eq.~\\ref" % (len(re.findall(r"\\eqref", src)), eqr))

    a = src.split(r"\begin{abstract}")[1].split(r"\end{abstract}")[0]
    a = re.sub(r"\\emph\{([^}]*)\}", r"\1", a)
    a = re.sub(r"\\[a-zA-Z]+", "", a).replace("---", " ").replace("$", "")
    aw = len([w for w in a.split() if re.search(r"[a-zA-Z0-9]", w)])
    check(150 <= aw <= 250, "abstract within IEEE's 150-250 words",
          "%d words" % aw)

    figs = re.findall(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", src, re.S)
    tabs = re.findall(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", src, re.S)
    check(all(r"\caption" in f for f in figs), "every figure captioned",
          "%d figures" % len(figs))
    check(all(r"\caption" in t for t in tabs), "every table captioned",
          "%d tables" % len(tabs))
    check(all(f.index(r"\caption") > f.index(r"\includegraphics")
              for f in figs if r"\includegraphics" in f),
          "figure captions below the image")
    check(all(t.index(r"\caption") < t.index(r"\begin{tabular}")
              for t in tabs if r"\begin{tabular}" in t),
          "table captions above the tabular")

    # a \noindent after a float is unsafe: the float can land anywhere, and
    # when it does not land adjacent the paragraph reads as a line break
    unsafe = len(re.findall(r"\\end\{(?:figure|table)\*?\}\s*\n\s*\n\\noindent",
                            src))
    check(unsafe == 0, "no \\noindent following a float", "%d found" % unsafe)

    lab = set(re.findall(r"\\label\{([^}]+)\}", src))
    ref = set(re.findall(r"\\ref\{([^}]+)\}", src))
    check(not (ref - lab), "no dangling \\ref", ", ".join(sorted(ref - lab)))
    orphan = sorted(l for l in lab - ref if l.split(":")[0] in ("fig", "tab"))
    check(not orphan, "every float cited in the text", ", ".join(orphan))


def g_eqnums() -> None:
    """Equation numbers cited in code docstrings against the built paper.

    Equations renumber whenever the paper is restructured, and nothing used to
    connect the two. policy.py spent a while pointing at Eq. (7) for a formula
    that had become Eq. (5), sending anyone reading code beside paper to the
    wrong equation every time.
    """
    head("EQUATION NUMBERS -- code docstrings against the built paper")
    aux = PAPER / "build" / "main.aux"
    if not aux.exists():
        note("no build/main.aux", "build the paper to check equation numbers")
        return
    num = dict(re.findall(r"newlabel\{(eq:[^}]+)\}\{\{([^}]+)\}",
                          io.open(aux, encoding="utf-8", errors="replace").read()))
    # which label each module's cited equation should correspond to
    expect = {
        "policy.py": {"5": "eq:tauact", "6": "eq:tauass", "8": "eq:signflip"},
        "stakes.py": {"10": "eq:stake", "11": "eq:damage"},
        "topology.py": {"11": "eq:damage"},
    }
    for mod, mapping in expect.items():
        p = HERE / mod
        if not p.exists():
            continue
        cited = set(re.findall(r"Eq\. \((\d+)\)",
                               io.open(p, encoding="utf-8").read()))
        stale = sorted(c for c in cited
                       if c in mapping and num.get(mapping[c]) != c)
        unknown = sorted(c for c in cited if c not in mapping)
        check(not stale, "%s equation numbers current" % mod,
              "" if not stale else "cites Eq. %s, paper says otherwise"
              % ", ".join(stale))
        if unknown:
            print("         (also cites Eq. %s, not cross-checked)"
                  % ", ".join(unknown))


def g_refs(src: str) -> None:
    head("REFERENCES -- both directions")
    cited = set()
    for m in re.findall(r"\\cite[tp]?\{([^}]+)\}", src):
        cited |= {k.strip() for k in m.split(",")}
    bib = set(re.findall(r"@\w+\{([^,]+),", io.open(BIB, encoding="utf-8").read()))
    check(not (cited - bib), "every \\cite resolves in refs.bib",
          ", ".join(sorted(cited - bib)))
    check(not (bib - cited), "no unused entry in refs.bib",
          ", ".join(sorted(bib - cited)))
    print("  [info] %d cited, %d in refs.bib" % (len(cited), len(bib)))


def g_figures(src: str) -> None:
    head("FIGURES -- scale on the page")
    print("  A figure authored wider than the column is scaled down by LaTeX,")
    print("  and its labels shrink with it. Author at final size.")
    print()
    col_in = 3.45
    for inc in re.findall(r"\\includegraphics\[width=\\columnwidth\]\{([^}]+)\}",
                          src):
        p = PAPER / inc
        if not p.exists():
            check(False, pathlib.Path(inc).name, "missing")
            continue
        d = io.open(p, "rb").read()
        m = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+"
                      rb"([-\d.]+)\s+([-\d.]+)", d)
        w = (float(m.group(3)) - float(m.group(1))) / 72.0
        sc = col_in / w
        check(0.85 <= sc <= 1.20, pathlib.Path(inc).name,
              "%.2f in -> scale %.2fx" % (w, sc))


def g_docx() -> None:
    """The Word version against the PDF it was made from.

    Converting loses things quietly. Rebuilding the abstract paragraph once
    dropped both percentages out of it, because OMML maths is an <m:oMath>
    element and not a <w:r>, so python-docx's paragraph.runs never saw them.
    The document still looked right.
    """
    head("WORD VERSION -- against the PDF it was made from")
    path = PAPER / "main.docx"
    if not path.exists():
        note("no main.docx", "run make_docx.py and ieee_docx.py to build it")
        return
    try:
        import docx as _docx
        from docx.oxml.ns import qn
    except ImportError:
        note("python-docx not installed", "Word checks skipped")
        return

    import zipfile
    d = _docx.Document(str(path))
    xml = zipfile.ZipFile(str(path)).read("word/document.xml").decode(
        "utf8", "replace")
    text = re.sub(r"\s+", " ", " ".join(p.text for p in d.paragraphs))

    # --- IEEE layout ------------------------------------------------------
    cols = []
    for s in d.sections:
        c = s._sectPr.find(qn("w:cols"))
        cols.append(int(c.get(qn("w:num")) or 1) if c is not None else 1)
    check(cols == [1, 2], "title block full width, body two columns",
          "columns per section: %s" % cols)
    if d.sections:
        s0 = d.sections[0]
        check(abs(s0.page_width.inches - 8.5) < 0.01
              and abs(s0.left_margin.inches - 0.625) < 0.01,
              "Letter page, IEEE margins",
              "%.2f in wide, %.3f in sides"
              % (s0.page_width.inches, s0.left_margin.inches))

    # --- IEEE house style -------------------------------------------------
    check(not any(p.style.name == "Abstract Title" for p in d.paragraphs),
          "no standalone Abstract heading (IEEE runs it in)")
    check(text.lstrip().find("Abstract—") >= 0
          or "Abstract—" in text[:400],
          "abstract opens with an em-dash run-in")

    # --- nothing lost in conversion ---------------------------------------
    abstract = next((p for p in d.paragraphs if p.style.name == "Abstract"),
                    None)
    if abstract is not None:
        n = sum(1 for c in abstract._p if c.tag == qn2("m:oMath"))
        check(n > 0, "abstract kept its inline maths",
              "%d oMath elements (the two percentages)" % n)

    pdf_txt = ""
    if (PAPER / "build" / "plain.txt").exists():
        pdf_txt = io.open(PAPER / "build" / "plain.txt", encoding="utf-8",
                          errors="replace").read()
    n_doc = len(set(re.findall(r"\[(\d+)\]", text)))
    n_pdf = len(set(re.findall(r"\[(\d+)\]", pdf_txt))) if pdf_txt else n_doc
    check(n_doc == n_pdf, "same distinct citation numbers as the PDF",
          "Word %d, PDF %d" % (n_doc, n_pdf))

    n_img = len([r for r in d.part.rels.values() if "image" in r.reltype])
    n_fig = len(re.findall(r"\\includegraphics", io.open(
        PAPER / "main.tex", encoding="utf-8").read()))
    check(n_img == n_fig, "every figure embedded",
          "Word %d, paper %d" % (n_img, n_fig))
    print("  [info] %d display equations, %d inline maths, %d words"
          % (xml.count("<m:oMathPara"), xml.count("<m:oMath>"),
             sum(len(p.text.split()) for p in d.paragraphs)))


def qn2(tag):
    """qn() for the math namespace, which docx.oxml.ns does not carry."""
    pfx, local = tag.split(":")
    return "{http://schemas.openxmlformats.org/officeDocument/2006/math}" + local


def g_voice(src: str) -> None:
    head("VOICE -- punctuation density and sentence shape")
    print("  Ranges are what published prose occupies, not hard limits. A")
    print("  number outside one is a habit worth looking at, not an error.")
    print()
    s = prose_of(src)
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", s)
    n = len(words)
    sents = [re.sub(r"\s+", " ", x).strip()
             for x in re.split(r"(?<=[.!?])\s+", s) if len(x.split()) > 3]
    k = lambda c: c / n * 1000

    for name, pat, lo, hi in (("em dash", r"---", 0, 4),
                              ("colon", r":", 0, 8),
                              ("semicolon", r";", 0, 8),
                              ("parentheses", r"\(", 0, 9)):
        c = len(re.findall(pat, s))
        check(k(c) <= hi, "%s density" % name,
              "%d = %.1f per 1000 (typical under %d)" % (c, k(c), hi))

    pas = re.findall(r"\b(?:is|are|was|were|be|been|being)\s+\w+(?:ed|en)\b",
                     s, flags=re.I)
    print("  [info] passive voice %.1f per 1000 (technical prose runs 15-25)"
          % k(len(pas)))

    L = sorted(len(x.split()) for x in sents)
    sd = statistics.pstdev(L)
    check(sd >= 8, "sentence-length variance",
          "stdev %.1f, median %d, max %d (uniform length reads as generated)"
          % (sd, L[len(L) // 2], L[-1]))

    runs, cur = [], 1
    for a, b in zip(sents, sents[1:]):
        cur = cur + 1 if a.split()[0].lower() == b.split()[0].lower() else 1
        if cur >= 3:
            runs.append(b.split()[0])
    check(not runs, "no run of 3+ sentences sharing an opener",
          ", ".join(sorted(set(runs))))

    SLOP = ("delve", "crucial", "pivotal", "landscape", "realm", "tapestry",
            "underscore", "showcase", "leverage", "comprehensive", "nuanced",
            "intricate", "myriad", "testament", "seamless", "paramount",
            "meticulous", "furthermore", "moreover", "additionally",
            "it is worth noting", "it is important to note")
    low = s.lower()
    hits = {w: low.count(w) for w in SLOP if low.count(w)}
    check(sum(hits.values()) <= 3, "stock vocabulary",
          ", ".join("%s x%d" % kv for kv in hits.items()) or "none")


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--group", choices=("hygiene", "ieee", "eqnums", "refs",
                                        "figures", "docx", "voice"),
                    help="run one group instead of all")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress output; exit code only")
    a = ap.parse_args()

    if a.quiet:
        sys.stdout = io.StringIO()

    src_raw, src, txt = load()
    groups = {
        "hygiene": lambda: g_hygiene(src_raw, src, txt),
        "ieee": lambda: g_ieee(src, txt),
        "eqnums": lambda: g_eqnums(),
        "refs": lambda: g_refs(src),
        "figures": lambda: g_figures(src),
        "docx": lambda: g_docx(),
        "voice": lambda: g_voice(src),
    }
    for name, fn in groups.items():
        if a.group in (None, name):
            fn()

    head("RESULT")
    print("  checks failed : %d" % _fail)
    print("  notes         : %d  (TODO placeholders are expected pre-submission)"
          % _warn)
    print()
    print("  " + ("ALL CHECKS PASS" if _fail == 0 else "SOME CHECKS FAILED"))

    if a.quiet:
        sys.stdout = sys.__stdout__
    return 1 if _fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
