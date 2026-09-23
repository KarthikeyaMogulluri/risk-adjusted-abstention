# The first compile, and the shell corruption it exposed

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** The paper was compiled for the first time. Compiling immediately exposed damage that had been sitting in the source for hours: an earlier edit written as an unquoted shell block had let the shell eat every dollar sign and the numbers attached to them, silently deleting values out of a table, three passages of prose and an entire paragraph. The tell was the string `/usr/bin/bash` appearing where a price should have been.

---

> [!CAUTION]
> **The corruption**
> ```
> ...threshold of /usr/bin/bash.8, rising to ...
> ```
> `$0.8` had become `/usr/bin/bash` — the shell substituting the name of the running program for `$0`. Similar damage at `$1`, `$3`, `$5` and `$8`, plus stripped row terminators in a table.

---

> [!NOTE]
> **What this code/concept does**
> The paper is written in a typesetting language: a plain text file with markup, which a compiler turns into a finished PDF. Up to this point the text had been written and edited but never compiled, so nobody had ever seen the output.
>
> This session compiled it for the first time. Two things came out of that: a working nine-page document, and the discovery that the source file had been quietly corrupted by an editing method used hours earlier.

> [!NOTE]
> **Why we are doing it this way**
> **Because compiling is a correctness check, not a final step.** It is easy to treat "make the PDF" as the thing you do once at the end. But the compiler is the first reader that checks the document is well-formed. Everything before it is unverified text.
>
> **Because nothing else would have found this.** The corrupted file was still valid text. It opened, it looked plausible, it contained sentences. A number had simply vanished from the middle of a sentence and been replaced with a file path. No editor, no spell check and no reading-for-sense would reliably catch that across an eleven-page document — but a compiler that tries to typeset a broken table row stops dead.
>
> **Because the toolchain should not require installing anything.** There was no typesetting software on the machine. Rather than installing a multi-gigabyte system-wide package, a single self-contained binary was fetched into a scratch directory. If it turns out to be the wrong choice, deleting one file undoes it.
>
> **Because the repair had to not repeat the cause.** The corruption came from writing an edit as an inline shell block. The repair was written to a file and run as a script — which has no such expansion behaviour.

> [!NOTE]
> **How it works step by step**
> **1. Get a compiler without installing one.** A single 22 MB self-contained binary was downloaded into the scratch directory. It fetches what it needs on demand rather than shipping a full distribution.
>
> **2. Work around a broken download.** Its default source serves the large package archive but returns "not found" for the checksum file that sits beside it, so the binary refuses to proceed. Pointing it at a specific older package collection directly avoided the missing file. Worth noting because the error message blames the checksum, not the host.
>
> **3. Compile — and read the errors.** The compiler stopped on a malformed table. Investigating that one error led to the real problem.
>
> **4. Understand the cause.** Hours earlier, an edit had been applied by writing the replacement text inline in a shell command using an *unquoted* delimiter. In that form the shell expands anything beginning with a dollar sign before the text is ever written to disk. In a document full of prices, that is catastrophic:
> - `$0` expands to the name of the running shell — hence `/usr/bin/bash` mid-sentence
> - `$1`, `$3`, `$5`, `$8` are positional arguments, and since none were supplied, each expanded to **nothing at all**
>
> So `$5.20` became `.20`, and `$3` simply disappeared. The same expansion also consumed the backslashes that terminate table rows, which is why the compiler complained about the table rather than the prices.
>
> **5. Find every site.** The damage was in five places: a comparison table, three passages of prose, and the whole of one sensitivity paragraph. Each was located by searching for the symptoms — the shell path, and orphaned decimal points with no leading digit.
>
> **6. Repair with a method that cannot cause the same fault.** The fixes were written into a script file and executed, rather than typed inline.
>
> **7. Recompile.** Nine pages, zero errors, three warnings about lines slightly too wide.

> [!IMPORTANT]
> **The fix**
> Quote the delimiter. An unquoted here-document expands variables; a quoted one is literal:
> ```bash
> cat > file.tex <<EOF     # WRONG — $0, $1, $3 all expand
> Threshold of $0.8 per hour
> EOF
>
> cat > file.tex <<'EOF'   # RIGHT — quoted delimiter, nothing expands
> Threshold of $0.8 per hour
> EOF
> ```
> Better still for anything long: write the content to a file with a real editor or a script, not inline in a shell command.

> [!NOTE]
> **Key terms defined**
> - **Typesetting compiler** — a program that turns a marked-up text file into a finished document.
> - **Here-document** — a way of feeding a block of text into a command inline in a shell script.
> - **Variable expansion** — the shell replacing `$name` with a value before the command runs.
> - **Positional parameter** — `$1`, `$2` and so on: the arguments a script was called with. Unset ones expand to nothing.
> - **`$0`** — the name of the running program. Expands to the shell's own path.
> - **Quoted delimiter** — writing `<<'EOF'` instead of `<<EOF`, which turns off all expansion inside the block.
> - **Silent corruption** — damage that leaves a file valid and readable, so no tool reports it.
> - **Overfull box** — a typesetting warning that a line is wider than the column.

> [!WARNING]
> **Common mistakes to avoid**
> - **Leaving the first compile until the end.** Every hour of editing before the first compile is an hour of unverified changes.
> - **Using an unquoted here-document for content containing `$`.** Prices, currency, mathematical symbols and shell-like text are all destroyed silently.
> - **Assuming a file edit landed because the command exited zero.** The shell succeeded. It wrote exactly what it was told. What it was told had already been mangled.
> - **Fixing the error the compiler reported and stopping.** The table was the *symptom*. Four more damaged sites had no symptom the compiler could see.
> - **Repairing with the same tool that caused the damage.** A second inline block would have reintroduced it.
> - **Trusting a fetch error's blame.** The message named the checksum; the real problem was the host serving an incomplete set.
> - **Installing a large system-wide toolchain for one document.** A single binary in a scratch directory is trivially reversible.

> [!TIP]
> **How this connects to the bigger picture**
> The whole paper argues that measurement beats assumption. This is the same lesson applied to its own source: the text was assumed intact for hours, and it was not. Compiling is to a document what running the tests is to code.
>
> It is also the reason the later sessions audit rather than assume. The incomplete correction found in [2026-09-21_correcting-the-overclaim-properly](2026-09-21_correcting-the-overclaim-properly.md) — one site fixed out of four — is the same failure mode as this one: an edit applied, and its result not checked.

> [!IMPORTANT]
> **Portfolio note**
> Shows diagnosing silent data corruption from a single odd string in rendered output, tracing it to shell expansion in an editing method, finding the four additional damaged sites that produced no error, and repairing with a method that could not reintroduce the fault.

---

## Result

```
9 pages · 0 LaTeX errors · 3 overfull boxes
Damage repaired at 5 sites: 1 comparison table, 3 prose passages, 1 full paragraph
```

---
