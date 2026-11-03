"""
The measured figures. Vector PDF, sized for a two-column IEEE page.

The figure set was re-planned after RQ1 was refuted. The originally planned
figure 1 -- "the joint distribution straddling the sign-flip boundary" -- has
no subject, because nothing straddles it. These show what was actually
measured:

  fig1  the premise fails: threshold dispersion collapses on both datasets
  fig2  where the answer comes from: non-overlapping win windows   <- the claim
  fig4  assist is dominated: the three-action space collapses to two

  fig3  risk-coverage stratified by stake quartile -- the refutation seen
        from a third angle: if stake governed the operating point the
        quartiles would separate, and they do not.

SIZING RULE. Everything the paper includes at \\columnwidth is authored at
3.45 in, the IEEE column width. Authoring at page width and letting LaTeX
scale to a column halves every font with it -- 8 pt labels land at 4 pt, which
is how a careful plot ends up looking machine-generated. Author at final size.

GREYSCALE RULE: every series is distinguished by marker and linestyle as well
as colour, and no statement in a caption depends on colour. Printed in mono,
all of them still read.

    python figures.py
"""

from __future__ import annotations

import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from stakes import StakeParams
from policy import CostParams, tau_act, tau_assist, ACT, ASSIST, ESCALATE
from evaluate import (all_baselines, simulate_confidence, fixed_policy,
                      regret, coverage, stake_decile_masks)
from rebalance import calibrate
import rcaeval_loader
import rca100_loader

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "paper" / "figures"        # every figure the manuscript includes
P = CostParams()
SP = StakeParams()

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "lines.linewidth": 1.3, "pdf.fonttype": 42,
})

# dataset styling: distinct colour AND marker AND linestyle
STYLE = {
    "RCAEval RE1": dict(color="#1a1a1a", marker="o", ls="-", ms=3.4),
    "RCA100":      dict(color="#b2560d", marker="s", ls="--", ms=3.2),
}
COL_WIDTH, PAGE_WIDTH = 3.45, 7.16
INK, FLIP, MUTE = "#1a1a1a", "#b2560d", "#555555"


def load():
    _, _, _, a = rcaeval_loader.build_dataset("RE1", ("ob", "ss"), verbose=False)
    _, _, _, b = rca100_loader.build_dataset(verbose=False)
    out = {}
    for name, df in (("RCAEval RE1", a), ("RCA100", b)):
        le, ls, _ = calibrate(df)
        out[name] = (df, le, ls)
    return out


def compose(df, le, ls, boost=1.0):
    rho = (df["rho_infra"].to_numpy() + le * df["r_fail"].to_numpy()
           + ls * boost * df["burn"].to_numpy())
    D = SP.kappa * df["blast"].to_numpy() * float(np.mean(rho))
    return rho, D, df["T_faulty"].to_numpy()


# --------------------------------------------------------------------------
def fig1(data):
    """The premise fails: threshold dispersion collapses under balance.

    Panels are stacked, not side by side, because at column width two panels
    leave each one 1.7 in -- too narrow for a labelled histogram.
    """
    fig, axes = plt.subplots(2, 1, figsize=(COL_WIDTH, 2.58))
    fig.subplots_adjust(hspace=0.72)

    ax = axes[0]
    for name, (df, le, ls) in data.items():
        rho, _, _ = compose(df, le, ls)
        ax.hist(np.log10(rho), bins=28, histtype="step", density=True,
                color=STYLE[name]["color"], ls=STYLE[name]["ls"],
                lw=1.2, label=name)
    ax.set_xlabel(r"$\log_{10}$ stake $\rho$  (USD/s)", labelpad=1.5)
    ax.set_ylabel("density", labelpad=2)
    ax.set_title("(a) stake, balanced composition", loc="left", pad=3)
    ax.legend(frameon=False, loc="upper right", handlelength=1.6)

    ax = axes[1]
    hi = 0.0
    for name, (df, le, ls) in data.items():
        rho, D, _ = compose(df, le, ls)
        ta = tau_act(rho, D, P)
        hi = max(hi, float(np.max(ta)))
        iqr = float(np.subtract(*np.percentile(ta, [75, 25])))
        ax.hist(ta, bins=28, histtype="step", density=True,
                color=STYLE[name]["color"], ls=STYLE[name]["ls"], lw=1.2,
                label=f"{name}   IQR = {iqr:.3f}")

    const = 0.845
    ax.axvline(const, color=MUTE, lw=0.9, ls=":")
    top = ax.get_ylim()[1]
    ax.text(const + 0.02, top * 0.97, "tuned constant", fontsize=6.4,
            color=MUTE, va="top", ha="left", rotation=90)

    # the empty space between the two IS the finding, so measure it rather
    # than leaving three quarters of the axis looking like dead margin
    y = top * 0.42
    ax.annotate("", xy=(const, y), xytext=(hi, y),
                arrowprops=dict(arrowstyle="<|-|>", color=FLIP, lw=0.9,
                                mutation_scale=7))
    ax.text((hi + const) / 2, y + top * 0.06,
            f"gap {const - hi:.2f}", fontsize=6.6, color=FLIP,
            ha="center", va="bottom")

    ax.set_xlabel(r"derived threshold $\tau^{\mathrm{act}}$", labelpad=1.5)
    ax.set_ylabel("density", labelpad=2)
    ax.set_xlim(0, 1)
    ax.set_title("(b) threshold dispersion", loc="left", pad=3)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.46, 1.02),
              handlelength=1.6)

    fig.savefig(OUT / "fig1_premise.pdf")
    plt.close(fig)
    print("  fig1_premise.pdf")


# --------------------------------------------------------------------------
def fig2(data):
    """THE figure: the win windows do not coincide."""
    boosts = np.array([1, 3, 10, 30, 100, 300, 1000, 3000, 10000], dtype=float)
    fig, ax = plt.subplots(figsize=(COL_WIDTH, 2.18))

    curves = {}
    for name, (df, le, ls) in data.items():
        ds = []
        for b in boosts:
            rho, D, T_e = compose(df, le, ls, b)
            rng = np.random.default_rng(0)
            q, Y = simulate_confidence(len(rho), rng, 0.62, 0.08)
            r = all_baselines(q, Y, rho, D, T_e, P)
            ds.append((r["derived"] - r["fixed_hindsight"])
                      / r["fixed_hindsight"] * 100)
        curves[name] = np.array(ds)

    # shade each dataset's win region, and SAY which band is whose -- an
    # unexplained shaded region is a reader asking the caption a question
    spans = {}
    for name, hatch in zip(curves, ("////", "\\\\\\\\")):
        d = curves[name]
        win = d < 0
        lo = hi = None
        for i in range(len(boosts) - 1):
            if win[i] and win[i + 1]:
                ax.axvspan(boosts[i], boosts[i + 1], alpha=0.10, lw=0,
                           hatch=hatch, facecolor=STYLE[name]["color"],
                           edgecolor=STYLE[name]["color"], zorder=0)
                lo = boosts[i] if lo is None else lo
                hi = boosts[i + 1]
        if lo is not None:
            spans[name] = (lo, hi)

    for name, d in curves.items():
        ax.plot(boosts, d, label=name, zorder=3, **STYLE[name])

    ax.axhline(0, color="#333", lw=1.0, zorder=2)
    ax.set_xscale("log")
    ax.set_xlabel(r"error-budget dominance  "
                  r"($\lambda_{\mathrm{slo}} b$ / $\rho^{\mathrm{infra}}$)",
                  labelpad=1.5)
    ax.set_ylabel("regret vs tuned constant (%)", labelpad=2)
    ax.text(0.985, 0.05, "derived wins", transform=ax.transAxes, fontsize=6.5,
            color="#333", ha="right")
    ax.text(0.985, 0.95, "derived loses", transform=ax.transAxes, fontsize=6.5,
            color="#333", ha="right", va="top")

    # reserve a clear strip below the data, then name each band inside it --
    # otherwise the label lands on whichever curve dips into that band
    lo_y, hi_y = ax.get_ylim()
    ax.set_ylim(lo_y - 0.30 * (hi_y - lo_y), hi_y)
    for name, (lo, hi) in spans.items():
        ax.text(np.sqrt(lo * hi), lo_y - 0.27 * (hi_y - lo_y),
                f"{name}\nwins here", fontsize=6.0, ha="center", va="bottom",
                color=STYLE[name]["color"], linespacing=0.95)

    # bottom-left: the only corner neither curve nor band label reaches
    ax.legend(frameon=False, loc="lower left", handlelength=2.0,
              bbox_to_anchor=(0.0, 0.0), borderaxespad=0.3)
    fig.savefig(OUT / "fig2_windows.pdf")
    plt.close(fig)
    print("  fig2_windows.pdf")
    return curves


# --------------------------------------------------------------------------
def fig3(data):
    """Risk-coverage, stratified by stake quartile."""
    fig, axes = plt.subplots(1, 2, figsize=(COL_WIDTH, 2.10), sharey=True)

    for ax, (name, (df, le, ls)) in zip(axes, data.items()):
        rho, D, T_e = compose(df, le, ls)
        rng = np.random.default_rng(0)
        q, Y = simulate_confidence(len(rho), rng, 0.62, 0.08)
        masks = stake_decile_masks(rho, 4)
        shades = ["#d9d9d9", "#a8a8a8", "#6e6e6e", "#1a1a1a"]
        lss = [":", "-.", "--", "-"]
        for k, (m, c, l) in enumerate(zip(masks, shades, lss)):
            if m.sum() < 8:
                continue
            # TWO-action sweep (act vs escalate). The three-action policy is
            # degenerate here -- assist is dominated on 100% of incidents at
            # the balanced composition -- and sweeping it introduces a
            # discontinuity where tau crosses the median tau_assist that is an
            # artefact of the band construction, not of the data.
            taus = np.linspace(1.0, 0.0, 40)
            cov, rsk = [], []
            for t in taus:
                a = np.where(q[m] >= t, ACT, ESCALATE)
                cov.append(coverage(a))
                rsk.append(regret(a, Y[m], rho[m], D[m], T_e[m], P))
            ax.plot(cov, rsk, color=c, lw=1.2, ls=l,
                    label=f"Q{k+1} (n={int(m.sum())})"
                          + ("  low stake" if k == 0 else
                             "  high stake" if k == 3 else ""))
        ax.set_xlabel("coverage")
        ax.set_title(name, loc="left")
    axes[0].set_ylabel("cost-weighted regret")
    axes[0].legend(frameon=False, loc="upper left", ncol=1)
    fig.savefig(OUT / "fig3_risk_coverage.pdf")
    plt.close(fig)
    print("  fig3_risk_coverage.pdf")


# --------------------------------------------------------------------------
def fig4(data):
    """Assist is a dominated action throughout the measured regime.

    One panel, both corpora. Two panels wasted half the slot showing the same
    thing twice, and each was 70% empty: every point sits in a narrow band far
    from the diagonal, so the full unit square was mostly margin. Zoomed to the
    region the data occupies, with the diagonal still in frame -- which is the
    whole claim.

    The plot is square (equal aspect, as any y-vs-x-with-a-diagonal must be),
    so the key sits beside it rather than inside. That fills the column width
    at scale 1.0; a bare square crops to 2.2 in and LaTeX would then upscale it
    by 1.56x, printing this figure's labels half again as large as every other
    figure's.
    """
    fig, ax = plt.subplots(figsize=(COL_WIDTH, 1.86))
    fig.subplots_adjust(left=0.13, right=0.57, bottom=0.17, top=0.97)

    counts = {}
    for name, (df, le, ls) in data.items():
        rho, D, _ = compose(df, le, ls)
        ta = tau_act(rho, D, P)
        ts = tau_assist(rho, P)
        dominated = ts > ta
        counts[name] = (int(dominated.sum()), len(ta), float(dominated.mean()))
        ax.scatter(ta, ts, s=11, marker=STYLE[name]["marker"],
                   facecolors="none", edgecolors=STYLE[name]["color"],
                   linewidths=0.7, zorder=3,
                   label=f"{name}  ({counts[name][0]}/{counts[name][1]})")

    lim = 0.52
    ax.plot([0, lim], [0, lim], color=MUTE, lw=0.9, ls="--", zorder=2)
    ax.fill_between([0, lim], [0, lim], lim, color="#f0f0f0", lw=0, zorder=0)
    ax.text(0.30, 0.345, r"$\tau^{\mathrm{assist}}=\tau^{\mathrm{act}}$",
            fontsize=6.4, color=MUTE, rotation=45, rotation_mode="anchor")

    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax.set_xlabel(r"$\tau^{\mathrm{act}}$", labelpad=1.5)
    ax.set_ylabel(r"$\tau^{\mathrm{assist}}$", labelpad=2)

    leg = ax.legend(frameon=False, fontsize=6.6, handletextpad=0.3,
                    loc="upper left", bbox_to_anchor=(1.06, 1.0),
                    title="cases dominated", alignment="left")
    leg.get_title().set_fontsize(6.8)
    ax.text(1.06, 0.50, "Every incident in both\ncorpora lies above the\n"
                        "diagonal, so assist is\nnever the cheapest\naction.",
            transform=ax.transAxes, fontsize=6.6, color=INK,
            va="top", ha="left", linespacing=1.3)
    fig.savefig(OUT / "fig4_dominated_assist.pdf")
    plt.close(fig)
    print("  fig4_dominated_assist.pdf")
    for n, (d, tot, frac) in counts.items():
        print(f"      {n:<14} {d}/{tot} dominated ({frac:.1%})")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("loading both datasets ...")
    data = load()
    print(f"writing paper figures to {OUT}")
    fig1(data)
    curves = fig2(data)
    fig3(data)
    fig4(data)
    print("\nwin windows (negative = derived wins):")
    for n, d in curves.items():
        print(f"  {n:<14} {np.array2string(d, precision=1, floatmode='fixed')}")


if __name__ == "__main__":
    main()
