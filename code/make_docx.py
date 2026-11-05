"""main.tex -> main.docx, converting from the SOURCE rather than the PDF.

Going via the PDF (pdf2docx) preserves the two-column layout as a raft of
text boxes and turns every equation into a picture. Going from the LaTeX
gives real headings, real paragraphs, and equations Word can edit, which is
the only reason to want a .docx.

Four things have to be prepared first.

  figures      Word will not embed a PDF image, so each is rendered to PNG.

  equations    pandoc cannot parse \\label inside a math environment. Each
               label becomes \\tag{N} carrying the number the built paper
               gave it, read from main.aux, so the numbering in the .docx
               matches the PDF and \\eqref keeps pointing at the right one.

  citations    pandoc's --citeproc defaults to author-date, which is wrong
               for an IEEE paper. Instead the already-built main.bbl is
               inlined: pandoc reads \\bibitem against \\cite and renders
               exactly the numbered references the PDF has.

  IEEEtran     the class, \\IEEEauthorblockN and \\IEEEkeywords are not
               LaTeX pandoc understands.
"""
import io
import pathlib
import re
import shutil
import subprocess

PAPER = pathlib.Path(r'D:/dev_notes/projects/k8s-aiops-research/paper')
WORK = PAPER / 'build' / 'docx'   # scratch: prepared source, PNGs, output
WORK.mkdir(parents=True, exist_ok=True)
(WORK / 'figures').mkdir(exist_ok=True)
B = chr(92)

# ---- figures to PNG ------------------------------------------------------
for pdf in sorted((PAPER / 'figures').glob('*.pdf')):
    subprocess.run(['pdftoppm', '-r', '300', '-png', '-singlefile', str(pdf),
                    str(WORK / 'figures' / pdf.stem)],
                   check=True, capture_output=True)
print('  figures -> PNG :', len(list((WORK / 'figures').glob('*.png'))))

# ---- the equation numbers the built paper actually assigned --------------
aux = io.open(PAPER / 'build' / 'main.aux', encoding='utf-8',
              errors='replace').read()
eqnum = dict(re.findall(r'newlabel\{(eq:[^}]+)\}\{\{([^}]+)\}', aux))
print('  equation numbers:', ', '.join('%s=%s' % kv for kv in eqnum.items()))

s = io.open(PAPER / 'main.tex', encoding='utf-8').read()

# ---- IEEEtran out, article in -------------------------------------------
s = s.replace(B + 'documentclass[conference]{IEEEtran}',
              B + 'documentclass[11pt]{article}')
s = s.replace(B + 'IEEEoverridecommandlockouts', '')
s = re.sub(re.escape(B) + r'author\{.*?\}\}\}', B + 'author{}', s, flags=re.S)
s = re.sub(re.escape(B) + r'begin\{IEEEkeywords\}(.*?)' + re.escape(B)
           + r'end\{IEEEkeywords\}',
           lambda m: B + r'bigskip' + chr(10) + chr(10)
           + B + r'noindent' + B + r'textbf{Index Terms---}' + m.group(1),
           s, flags=re.S)

# ---- labels inside math become tags carrying the real number -------------
def tag(m):
    key = m.group(1)
    # \tag parses inconsistently in pandoc's math reader; plain math always works
    return (B + 'qquad (' + eqnum[key] + ')') if key in eqnum else ''


s = re.sub(re.escape(B) + r'label\{(eq:[^}]+)\}', tag, s)
# and the references to them become that number in plain text
for key, n in eqnum.items():
    s = s.replace(B + 'eqref{' + key + '}', '(%s)' % n)
print('  eqref -> literal numbers')

# ---- citations: the numbers the built paper assigned ---------------------
# pandoc drops \cite without citeproc, and citeproc formats author-date.
# Both wrong, so substitute the literal numbers bibtex already chose.
cite_n = dict(re.findall(re.escape(B) + r'bibcite\{([^}]+)\}\{([^}]+)\}', aux))


def cites(m):
    keys = [k.strip() for k in m.group(1).split(',')]
    return ', '.join('[%s]' % cite_n.get(k, '?') for k in keys)


n_cite = len(re.findall(re.escape(B) + r'cite[tp]?\{', s))
s = re.sub(re.escape(B) + r'cite[tp]?\{([^}]+)\}', cites, s)
print('  cite -> [n]    : %d sites, %d distinct refs' % (n_cite, len(cite_n)))

# ---- the bibliography, as a numbered list under a heading ----------------
bbl = io.open(PAPER / 'build' / 'main.bbl', encoding='utf-8',
              errors='replace').read()
entries = re.split(re.escape(B) + r'bibitem\{([^}]+)\}', bbl)[1:]
items = []
for key, body in zip(entries[0::2], entries[1::2]):
    body = body.split(B + 'end{thebibliography}')[0]
    body = re.sub(r'(?m)^%.*$', '', body)
    body = re.sub(re.escape(B) + r'(?:newblock|BIBentry\w+|bibinfo|providecommand)'
                  r'(?:\[\d\])?', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    items.append(r'\item[{[%s]}] %s' % (cite_n.get(key, '?'), body))

biblio = (B + 'section*{References}' + chr(10)
          + B + 'begin{description}' + chr(10)
          + chr(10).join(items) + chr(10)
          + B + 'end{description}' + chr(10))

s = re.sub(re.escape(B) + r'bibliographystyle\{[^}]*\}\s*'
           + re.escape(B) + r'bibliography\{[^}]*\}', lambda m: biblio, s)
print('  bibliography   : %d numbered entries' % len(items))

# ---- figures point at the PNGs, and the author block is still a stub -----
s = s.replace('.pdf}', '.png}')
s = s.replace(B + 'TODO{', B + 'textbf{TO DO: ')

io.open(WORK / 'main.tex', 'w', encoding='utf-8').write(s)
shutil.copy(PAPER / 'refs.bib', WORK / 'refs.bib')

# ---- convert -------------------------------------------------------------
import pypandoc

out = WORK / 'main.docx'
pypandoc.convert_file(
    str(WORK / 'main.tex'), 'docx', outputfile=str(out),
    extra_args=['--resource-path=' + str(WORK), '--number-sections'])
shutil.copy(out, PAPER / 'main.docx')
print('  wrote %s (%.0f KB)' % (PAPER / 'main.docx', out.stat().st_size / 1024))
