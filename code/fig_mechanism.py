"""
Figure 1 -- the mechanism, drawn.

Every other figure in the paper reports a measurement. None shows what the
paper proposes, so a reader currently meets the three-action space and the
sign flip only as equations. This is the comprehension figure.

  (a)  the confidence axis, three actions, and the fact that both thresholds
       MOVE between a cheap incident and an expensive one
  (b)  a regime map for Proposition 2: which way they move, and where our
       parameter anchors sit on it

SIZING. Authored at 3.45 in -- the IEEE \\columnwidth -- because the paper
includes it at \\columnwidth. The earlier version was authored at 7.0 in and
scaled down by half on the page, which halved every font with it: 8 pt labels
rendered at 4 pt. Author at final size or the type is wrong.

LABELLING. The bands are named once, in a key, not inside the bands. Labelling
in-band forces a choice between an unreadable label over hatching and no label
at all on whichever band is narrow, and the narrow band is a different one on
each row -- which reads as carelessness.

WHY PANEL (b) IS A MAP AND NOT TWO CURVES. The obvious drawing -- tau against
stake, one rising curve and one falling -- does not work. Both branches share
the asymptote tau -> Delta^-/(Delta^+ + Delta^-), and they approach it on
different decades of rho: the rise is visible around 1e-3..1e0, the fall only
above 1e0. On a single axis either the fall looks flat or the rise does. The
regime map avoids the scale problem and states the proposition exactly: the
sign of the derivative depends on two ratios and nothing else.

    python fig_mechanism.py
"""

from __future__ import annotations

import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch, Rectangle

from policy import CostParams, dtau_dstake_sign

# The paper reads paper/figures/. Write there directly -- a repo-root copy
# that has to be moved by hand is a copy that goes stale.
OUT = pathlib.Path(__file__).resolve().parent.parent / "paper" / "figures"
P = CostParams()

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 1.1, "pdf.fonttype": 42,
})

INK = "#1a1a1a"
FLIP = "#b2560d"

# greyscale-safe: fill AND hatch differ, so the three read in mono
ESC = dict(facecolor="#8c8c8c", edgecolor=INK, hatch=None)
ASSIST = dict(facecolor="#e2e2e2", edgecolor=INK, hatch="////")
ACT = dict(facecolor="#ffffff", edgecolor=INK, hatch=None)

ROWS = (  # y, tau_assist, tau_act, row label
    (1.0, 0.14, 0.33, "cheap\nincident"),
    (0.0, 0.46, 0.88, "costly\nincident"),
)


def panel_a(ax):
    """Three actions, and both thresholds move with what the incident is worth."""
    h = 0.30
    for y, ts, ta, tag in ROWS:
        for x0, x1, style in ((0.0, ts, ESC), (ts, ta, ASSIST), (ta, 1.0, ACT)):
            ax.add_patch(Rectangle((x0, y - h / 2), x1 - x0, h, lw=0.8, **style))
        ax.text(-0.03, y, tag, ha="right", va="center", fontsize=7, color=INK)

    # the shift itself: quiet dotted connectors, so the eye follows each
    # threshold from one row to the other without an arrow thicket
    # horizontal, in the clear gap between the rows: two short arrows, each
    # carrying one threshold from its cheap position to its costly one
    (y0, ts0, ta0, _), (y1, ts1, ta1, _) = ROWS
    for x0, x1 in ((ts0, ts1), (ta0, ta1)):
        ax.annotate("", xy=(x1, 0.5), xytext=(x0, 0.5),
                    arrowprops=dict(arrowstyle="-|>", color=FLIP, lw=0.9,
                                    mutation_scale=6))

    # aligned with the row labels, so it cannot collide with the arrows
    ax.text(-0.03, 0.5, "thresholds\nshift", color=FLIP, fontsize=6.4,
            ha="right", va="center")

    # name the two thresholds once, over the top row
    for x, lab in ((ts0, r"$\tau^{\mathrm{assist}}$"), (ta0, r"$\tau^{\mathrm{act}}$")):
        ax.plot([x, x], [y0 + h / 2, y0 + h / 2 + 0.12], lw=0.8, color=INK)
        ax.text(x, y0 + h / 2 + 0.17, lab, ha="center", va="bottom", fontsize=7)

    ax.set_xlim(-0.30, 1.005)
    ax.set_ylim(-0.32, 1.62)
    ax.set_yticks([])
    ax.set_xticks([0, 0.5, 1.0])
    ax.set_xlabel(r"agent confidence $q$", labelpad=1.5)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_bounds(0.0, 1.0)   # no axis stub under the row labels
    ax.set_title("(a) three actions, two moving thresholds", loc="left", pad=12)

    ax.legend(handles=[Patch(lw=0.8, label="escalate", **ESC),
                       Patch(lw=0.8, label="assist", **ASSIST),
                       Patch(lw=0.8, label="act", **ACT)],
              loc="upper center", bbox_to_anchor=(0.42, -0.34), ncol=3,
              frameon=False, handlelength=1.5, handleheight=0.9,
              columnspacing=1.2, handletextpad=0.5)


def panel_b(ax):
    """Regime map for Proposition 2."""
    x = np.logspace(-3, 3, 200)
    ax.fill_between(x, x, 1e3, color="#e8e8e8", lw=0)
    ax.fill_between(x, 1e-3, x, color=FLIP, alpha=0.16, lw=0)
    ax.loglog(x, x, color=FLIP, lw=1.5, zorder=3)

    ax.text(1.3e-2, 2.6e2, "$\\tau$ rises\nbe more careful",
            fontsize=6.8, ha="center", va="center", color=INK)
    ax.text(60, 1.4e-2, "$\\tau$ falls\nact sooner",
            fontsize=6.8, ha="center", va="center", color=FLIP)

    # the boundary, named along the line it describes rather than floated
    # below the axes where it reads as an afterthought
    ax.text(1.4e-3, 2.1e-3, r"$D/(wH_e)=\Delta^{-}/\Delta^{+}$",
            fontsize=6.6, color=FLIP, rotation=45,
            rotation_mode="anchor", ha="left", va="bottom")

    ratio = P.delta_minus_act / P.delta_plus_act
    ax.plot([1], [ratio], marker="o", ms=4, color=INK, zorder=5)
    # above the dot: the left margin is taken by the boundary label and the
    # upper left by "be more careful", so this is the one clear approach
    ax.annotate("our anchors", xy=(1, ratio), xytext=(0.5, 45),
                fontsize=6.6, color=INK, ha="center", va="center",
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.7,
                                shrinkA=2, shrinkB=3))

    ax.set_xlim(1e-3, 1e3)
    ax.set_ylim(1e-3, 1e3)
    ax.set_xticks([1e-3, 1e-1, 1e1, 1e3])
    ax.set_yticks([1e-3, 1e-1, 1e1, 1e3])
    ax.tick_params(which="minor", length=0)
    ax.set_xlabel(r"$D/(wH_e)$" "\n" "damage vs. cost of paging",
                  fontsize=7.2, labelpad=1.5)
    ax.set_ylabel(r"$\Delta^{-}/\Delta^{+}$" "\n" "automation asymmetry",
                  fontsize=7.2, labelpad=1.5)
    ax.set_title("(b) which way they move", loc="left", pad=4)
    for s in ("top", "right"):
        ax.spines[s].set_visible(True)
        ax.spines[s].set_linewidth(0.6)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(3.45, 2.88))
    gs = GridSpec(2, 1, figure=fig, height_ratios=[1.0, 1.42], hspace=0.88)
    panel_a(fig.add_subplot(gs[0]))
    panel_b(fig.add_subplot(gs[1]))
    fig.savefig(OUT / "fig0_mechanism.pdf")
    fig.savefig(OUT / "fig0_mechanism.png", dpi=220)
    plt.close(fig)
    print(f"  fig0_mechanism.pdf -> {OUT}")

    # the drawn boundary must be the one Proposition 2 states
    b = P.delta_minus_act / P.delta_plus_act
    below = dtau_dstake_sign(np.array([0.5 * b * P.wHe]), P)[0]
    above = dtau_dstake_sign(np.array([2.0 * b * P.wHe]), P)[0]
    print(f"  boundary at D = {b * P.wHe:.0f} USD")
    print(f"  below -> {below:+.0f} (expect +1, rises)")
    print(f"  above -> {above:+.0f} (expect -1, falls)")
    assert below > 0 > above, "the map does not match Proposition 2"
    print("  map is faithful to Prop 2")


if __name__ == "__main__":
    main()
