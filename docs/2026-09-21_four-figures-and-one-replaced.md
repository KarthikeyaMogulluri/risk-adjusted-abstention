# Four figures, three defects, and one replaced entirely

*Research journal entry — 2026-09-21. Part of the [risk-adjusted abstention](../README.md) study.*

---

> **Summary:** The paper's four figures were drawn, then looked at — and looking found three real defects that the code had not complained about. One figure was scrapped completely, because it mixed two different units on one axis and so displayed a seventeen-fold change as nothing at all. Its slot went to the one claim in the paper that had evidence but no picture.

---

> [!NOTE]
> **What this code/concept does**
> A figure in a paper has one job: make a claim visible faster than a sentence can make it understood. This session produced the four figures for the paper, sized for a narrow two-column page, and then checked each rendered figure by eye against the claim it was supposed to support.
>
> Three of them had problems that no error message would ever report: a text label sitting on top of a data line, a set of vertical jumps that came from how the curve was drawn rather than from the data, and mangled mathematical symbols that had rendered as nonsense letters. The fourth was worse — it was the wrong figure, and it was replaced.

> [!NOTE]
> **Why we are doing it this way**
> **Because plotting code cannot fail loudly.** Code that computes a wrong number can be caught by a test. Code that draws a misleading picture produces a valid image file and exits successfully. The only detector is a person looking at the output and asking whether it says what it is supposed to say.
>
> **Because the figures must survive being printed in black and white.** A reader may print the paper, photocopy it, or be unable to distinguish certain colours. If two lines are told apart only by being red and green, that figure is unreadable for some fraction of its audience. So every series is distinguished by its marker shape *and* its line style, with colour as a bonus rather than the carrier of the information.
>
> **Because vector output does not blur.** Saving the figures as scalable drawings rather than grids of pixels means the text in them stays crisp at any zoom and matches the paper's own type size.
>
> **Because a figure slot is scarce.** Four figures is what the page budget allows. A slot spent on a picture that duplicates a table is a slot not spent on a claim with no evidence attached.

> [!NOTE]
> **How it works step by step**
> **1. Re-plan the set before drawing.** One originally planned figure was meant to show two populations straddling a boundary. By this point in the work it was known that nothing straddles that boundary — everything sits on one side of it. A figure of an empty region is not a modest figure; it is a misleading one. It was cut before it was drawn.
>
> **2. Draw all four, sized for the real page.** Not sized for a screen and shrunk afterwards, which makes labels unreadably small. Sized for the column they will occupy, so the type in the figure matches the type around it.
>
> **3. Look at each rendered figure.** This is the step that found everything. Three defects:
> - *A label collided with a data line* in the second figure, so the line disappeared behind the text at the point where it mattered.
> - *The third figure had vertical discontinuities* — sudden jumps that looked like real behaviour in the data. They were not. They came from one of the three plotted bands collapsing to nothing as the threshold crossed its own median value. The fix was to switch to the conventional two-way sweep instead, which is also the more honest picture: the third option is never chosen anyway.
> - *Mathematical symbols had rendered as stray letters* — a Greek character was appearing as an ordinary two-letter fragment, which looks like a typo to a reader and like carelessness to a reviewer.
>
> **4. Replace the fourth figure entirely.** The planned before-and-after bar chart had two faults at once. Its axis mixed two quantities measured in different units, so a seventeen-fold change in one of them rendered as a bar that looked flat. And the comparison it made was already in a table two pages earlier. Both faults point the same way: the slot was being wasted.
>
> The replacement shows, incident by incident, that the middle option is never the cheapest one. That fact directly contradicts one of the paper's own stated contributions, it had been measured, and it had no picture. A figure that argues against your own earlier framing is worth more than a figure that repeats a table.
>
> **5. Wire them in with captions and references.** Each figure is referred to from the text that discusses it, so a reader never meets a picture without knowing why it is there.

> [!NOTE]
> **Key terms defined**
> - **Vector figure** — a drawing stored as shapes and coordinates rather than pixels, so it stays sharp at any size.
> - **Two-column format** — the narrow page layout of most conference papers; figures must be legible at about half a page width.
> - **Greyscale-legible** — readable when printed without colour.
> - **Marker and linestyle** — the shape of the points and the dash pattern of the line; the two ways to tell series apart without colour.
> - **Plotting artefact** — a feature of the picture caused by how it was drawn, not by the data it represents.
> - **Overfull box** — a typesetting warning that something is wider than the space it was given.
> - **Dominated option** — a choice that is never the best one under any circumstances in the measured range.

> [!WARNING]
> **Common mistakes to avoid**
> - **Generating figures and not looking at them.** The code succeeding tells you nothing about whether the picture is right.
> - **Distinguishing series by colour alone.** It fails in print, in photocopies, and for colour-blind readers — a large fraction of any audience.
> - **Mixing units on one axis.** Whichever quantity has the smaller numbers becomes invisible, and the figure lies by omission.
> - **Keeping a planned figure after its subject disappears.** A picture of an empty region implies the region was worth examining and found empty, which is a different claim from "nothing was ever there".
> - **Spending a figure slot on something already in a table.** Duplication costs a claim that had no evidence shown.
> - **Sizing for the screen.** Shrinking a screen-sized figure to column width makes its labels too small to read.
> - **Assuming a mathematical symbol rendered correctly.** They frequently do not, and the result looks like a spelling error.

> [!TIP]
> **How this connects to the bigger picture**
> By this point the paper's central result was a negative one, which places an unusual burden on its figures: a reader who wants to disbelieve a negative result will look hardest at the pictures. Three sloppy figures would have made a careful result look careless.
>
> The fourth figure's replacement also did real argumentative work. It shows the middle action is always dominated — the fact that [2026-09-21_owning-the-three-action-contradiction](2026-09-21_owning-the-three-action-contradiction.md) later turned from an embarrassment into the paper's scoped claim. The picture was ready before the argument that needed it.

> [!IMPORTANT]
> **Portfolio note**
> Demonstrates treating figures as claims to be checked rather than output to be generated — including scrapping a planned figure whose subject had ceased to exist, and giving its slot to the evidence that contradicted the author's own earlier framing.

---

## The four figures as shipped

| # | Shows | Note |
|---|---|---|
| 1 | Stake distribution across both corpora | — |
| 2 | Threshold against stake | label collision fixed |
| 3 | Two-way action sweep | switched from three-way; removed false discontinuities |
| 4 | Middle option dominated, incident by incident | replaced the planned before/after bars |

---
