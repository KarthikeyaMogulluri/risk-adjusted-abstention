"""
The four figures. Vector PDF, sized for a two-column IEEE page.

The figure set was re-planned after RQ1 was refuted. The originally planned
figure 1 -- "the joint distribution straddling the sign-flip boundary" -- has
no subject, because nothing straddles it. These four show what was actually
measured:

  fig1  the premise fails: threshold dispersion collapses on both datasets
  fig2  where the answer comes from: non-overlapping win windows   <- the claim
  fig3  risk-coverage stratified by stake decile
  fig4  assist is dominated: the three-action space collapses to two

GREYSCALE RULE: every series is distinguished by marker and linestyle as well
as colour, and no statement in a caption depends on colour. Printed in mono,
all four still read.

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

# Repo-root figures/. The manuscript is not published with this code, so
# figures are regenerated rather than shipped.
OUT = pathlib.Path(__file__).resolve().parent.parent / "figures"
P = CostParams()
SP = StakeParams()

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8.5,
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
COL_WIDTH, PAGE_WIDTH = 3.4, 7.0


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
    """The premise fails: threshold dispersion collapses under balance."""
    fig, axes = plt.subplots(1, 2, figsize=(PAGE_WIDTH, 2.25))

    ax = axes[0]
    for name, (df, le, ls) in data.items():
        rho, _, _ = compose(df, le, ls)
        ax.hist(np.log10(rho), bins=28, histtype="step", density=True,
                color=STYLE[name]["color"], ls=STYLE[name]["ls"],
                lw=1.3, label=name)
    ax.set_xlabel(r"$\log_{10}$ stake $\rho$  (USD/s)")
    ax.set_ylabel("density")
    ax.set_title("(a) stake, balanced composition", loc="left")
    ax.legend(frameon=False, loc="upper right")

    ax = axes[1]
    for name, (df, le, ls) in data.items():
        rho, D, _ = compose(df, le, ls)
        ta = tau_act(rho, D, P)
        ax.hist(ta, bins=28, histtype="step", density=True,
                color=STYLE[name]["color"], ls=STYLE[name]["ls"], lw=1.3,
                label=f"{name}  IQR={np.subtract(*np.percentile(ta,[75,25])):.3f}")
    ax.axvline(0.845, color="#555", lw=0.9, ls=":")
    ax.text(0.845, ax.get_ylim()[1] * 0.92, "  tuned constant",
            fontsize=6.5, color="#555", va="top")
    ax.set_xlabel(r"derived threshold $\tau^{\mathrm{act}}$")
    ax.set_xlim(0, 1)
    ax.set_title("(b) threshold dispersion", loc="left")
    ax.legend(frameon=False, loc="upper center")

    fig.savefig(OUT / "fig1_premise.pdf")
    plt.close(fig)
    print("  fig1_premise.pdf")


# --------------------------------------------------------------------------
def fig2(data):
    """THE figure: the win windows do not coincide."""
    boosts = np.array([1, 3, 10, 30, 100, 300, 1000, 3000, 10000], dtype=float)
    fig, ax = plt.subplots(figsize=(COL_WIDTH + 0.5, 2.5))

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

    # shade each dataset's win region
    for name, hatch in zip(curves, ("////", "\\\\\\\\")):
        d = curves[name]
        win = d < 0
        for i in range(len(boosts) - 1):
            if win[i] and win[i + 1]:
                ax.axvspan(boosts[i], boosts[i + 1], alpha=0.10, lw=0,
                           hatch=hatch, facecolor=STYLE[name]["color"],
                           edgecolor=STYLE[name]["color"])

    for name, d in curves.items():
        ax.plot(boosts, d, label=name, **STYLE[name])

    ax.axhline(0, color="#333", lw=1.0)
    ax.set_xscale("log")
    ax.set_xlabel(r"error-budget dominance  ($\lambda_{\mathrm{slo}} b$ / $\rho^{\mathrm{infra}}$)")
    ax.set_ylabel("regret vs tuned constant (%)")
    ax.text(0.98, 0.06, "derived wins", transform=ax.transAxes, fontsize=6.5,
            color="#333", ha="right")
    ax.text(0.98, 0.94, "derived loses", transform=ax.transAxes, fontsize=6.5,
            color="#333", ha="right", va="top")
    ax.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.10))
    fig.savefig(OUT / "fig2_windows.pdf")
    plt.close(fig)
    print("  fig2_windows.pdf")
    return curves


# --------------------------------------------------------------------------
def fig3(data):
    """Risk-coverage, stratified by stake decile."""
    fig, axes = plt.subplots(1, 2, figsize=(PAGE_WIDTH, 2.35), sharey=True)

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

    Replaces the originally planned before/after bar chart, which mixed units
    on one axis (so the 17x change in tau IQR rendered as nothing) and
    duplicated the table in Section 6.1. This finding had no figure and
    contradicts a stated contribution, so it earns the slot.
    """
    fig, axes = plt.subplots(1, 2, figsize=(PAGE_WIDTH * 0.82, 2.5),
                             sharex=True, sharey=True)

    for ax, (name, (df, le, ls)) in zip(axes, data.items()):
        rho, D, _ = compose(df, le, ls)
        ta = tau_act(rho, D, P)
        ts = tau_assist(rho, P)
        dominated = ts > ta
        ax.scatter(ta[~dominated], ts[~dominated], s=9, facecolors="none",
                   edgecolors="#1a1a1a", linewidths=0.7,
                   label=f"assist usable ({(~dominated).sum()})")
        ax.scatter(ta[dominated], ts[dominated], s=9, marker="x",
                   color="#b2560d", linewidths=0.7,
                   label=f"assist dominated ({dominated.sum()})")
        lim = [0, 1]
        ax.plot(lim, lim, color="#555", lw=0.9, ls="--")
        ax.text(0.52, 0.44, r"$\tau^{\mathrm{assist}}=\tau^{\mathrm{act}}$",
                fontsize=6.2, color="#555", rotation=38,
                transform=ax.transAxes)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel(r"$\tau^{\mathrm{act}}$")
        ax.set_title(f"{name}  ({dominated.mean():.0%} dominated)", loc="left")
        ax.legend(frameon=False, loc="lower right", fontsize=6.2)
    axes[0].set_ylabel(r"$\tau^{\mathrm{assist}}$")
    fig.savefig(OUT / "fig4_dominated_assist.pdf")
    plt.close(fig)
    print("  fig4_dominated_assist.pdf")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("loading both datasets ...")
    data = load()
    print("writing figures to paper/figures/")
    fig1(data)
    curves = fig2(data)
    fig3(data)
    fig4(data)
    print("\nwin windows (negative = derived wins):")
    for n, d in curves.items():
        print(f"  {n:<14} {np.array2string(d, precision=1, floatmode='fixed')}")


if __name__ == "__main__":
    main()
