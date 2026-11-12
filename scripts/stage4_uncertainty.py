"""Stage 4: Monte Carlo uncertainty and sensitivity analysis.

Writes results/stage4_uncertainty.txt, figures/stage4_spread.png and
figures/stage4_sensitivity.png.
Run from the repo root:  python -m scripts.stage4_uncertainty   (about 3 minutes)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from choke_model.analysis import central_threshold, loc_time
from choke_model.model import Choke
from choke_model.params import (
    MITCHELL_FIXATION_MEAN_S, MITCHELL_FIXATION_RANGE_S, MITCHELL_FIXATION_SD_S,
    MITCHELL_NO_LOC_HOLD_S, NJEMANZE_VELOCITY_THRESHOLD, SECONDS_PER_MINUTE, Params,
)
from choke_model.uncertainty import INPUTS, READINGS, Normal, rank_correlation, run_monte_carlo

ROOT = Path(__file__).resolve().parents[1]
N_DRAWS = 20_000
SEED = 2026
CLAASSEN_FLOW_FRACTION = 22.0 / 50.0  # S4

# Plot colours: one hue for model output, neutral greys for observations.
BLUE, INK, MUTED, GRID, SURFACE = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

LABELS = {
    "cbf": "blood flow (CBF)",
    "cmro2": "oxygen use (CMRO2)",
    "oef": "oxygen extraction (OEF)",
    "cbv": "blood volume in brain (CBV)",
    "vertebral_share": "vertebral share of flow",
    "kappa": "kappa (no source)",
    "rossen_loc_s": "Rossen LOC time fitted to (4-10 s)",
    "rossen_vertebral_open": "vertebral flow left by Rossen's cuff",
    "threshold": "LOC threshold",
}
READING_NAMES = {
    "A": "A  whole brain falls like the MCA velocity",
    "B": "B  carotids shut, vertebrals normal",
    "C": "C  carotids pass the MCA fraction, vertebrals normal",
}
OBS_BAND = (MITCHELL_FIXATION_MEAN_S - MITCHELL_FIXATION_SD_S, MITCHELL_FIXATION_MEAN_S + MITCHELL_FIXATION_SD_S)


def pct(mask: np.ndarray) -> str:
    return f"{100 * np.mean(mask):5.1f} %"


def spread(t: np.ndarray) -> str:
    """Median and 5-95 % range of the draws in which LOC happens."""
    lo, mid, hi = np.percentile(t[~np.isnan(t)], [5, 50, 95])
    return f"median {mid:5.1f} s, 5-95 % range {lo:4.1f} to {hi:5.1f} s"


def inside(t: np.ndarray, band: tuple[float, float]) -> np.ndarray:
    return (t >= band[0]) & (t <= band[1])  # nan compares False


def one_at_a_time(theta_range: tuple[float, float]) -> list[tuple[str, float, float]]:
    """Predicted LOC time (full carotid choke) with one input at each end of its range.

    Everything else stays at its central value and the threshold is held at
    the central fit, as if it were known.
    """
    base = Params()
    theta = central_threshold(base)
    rows = []
    for name in ("cbf", "cmro2", "oef", "cbv", "vertebral_share", "kappa"):
        dist = INPUTS[name]
        ends = (dist.mean - 2 * dist.sd, dist.mean + 2 * dist.sd) if isinstance(dist, Normal) else (dist.low, dist.high)
        scale = 1 / SECONDS_PER_MINUTE if name in ("cbf", "cmro2") else 1.0
        rows.append((name, *(loc_time(base.with_(**{name: e * scale}), Choke(1.0), theta) for e in ends)))
    rows.append(("threshold", *(loc_time(base, Choke(1.0), th) for th in theta_range)))
    return rows


def main() -> None:
    inputs, out = run_monte_carlo(N_DRAWS, SEED)
    theta = out["threshold"]
    full = out["loc_full_carotid_s"]
    lines = [f"Stage 4: Monte Carlo, {N_DRAWS} draws, seed {SEED}", ""]

    lines.append("[inputs sampled]")
    for name, dist in INPUTS.items():
        shape = (f"normal {dist.mean:g} +/- {dist.sd:g}, cut at +/- 2 SD" if isinstance(dist, Normal)
                 else f"{'log-' if dist.log else ''}uniform {dist.low:g} to {dist.high:g}")
        lines.append(f"  {name:22s} {shape:38s} {dist.source}")
    lines.append("")

    t5, t50, t95 = np.percentile(theta, [5, 50, 95])
    lines.append(f"[fitted threshold C/C0] median {t50:.2f}, 5-95 % range {t5:.3f} to {t95:.2f}")
    lines.append("")

    lines.append("[plain blood choke: carotids shut at once, vertebrals open]")
    lines.append(f"  LOC never happens in {pct(np.isnan(full))} of draws")
    lines.append(f"  when it does: {spread(full)}")
    lines.append("")

    lines.append("[Mitchell 2012, HELD OUT] predicted time to ocular fixation, 16 subjects who lost consciousness")
    lines.append(f"  observed: {MITCHELL_FIXATION_MEAN_S} +/- {MITCHELL_FIXATION_SD_S:.1f} s (mean +/- SD), "
                 f"individual range {MITCHELL_FIXATION_RANGE_S[0]}-{MITCHELL_FIXATION_RANGE_S[1]} s")
    for r in READINGS:
        t = out[f"fixation_{r}_s"]
        lines.append(f"  {READING_NAMES[r]}")
        lines.append(f"      never: {pct(np.isnan(t))} | when it does: {spread(t)}")
        lines.append(f"      inside observed range: {pct(inside(t, MITCHELL_FIXATION_RANGE_S))} of all draws | "
                     f"inside mean +/- SD: {pct(inside(t, OBS_BAND))}")
    lines.append("")

    lines.append(f"[Mitchell 2012, HELD OUT] 4 subjects with no fixation after {MITCHELL_NO_LOC_HOLD_S} s")
    for r in ("A", "C"):
        ok_no = out[f"no_loc_{r}"] == 1.0
        both = ok_no & inside(out[f"fixation_{r}_s"], MITCHELL_FIXATION_RANGE_S)
        lines.append(f"  reading {r}: model agrees (no LOC) in {pct(ok_no)} of draws | "
                     f"gets BOTH groups right in {pct(both)}")
    lines.append("")

    crit = out["critical_flow"]
    c5, c50, c95 = np.percentile(crit, [5, 50, 95])
    lines.append("[lowest sustained flow that never causes LOC, as a fraction of normal]")
    lines.append(f"  model: median {c50:.2f}, 5-95 % range {c5:.2f} to {c95:.2f}")
    lines.append(f"  Claassen 2021 (S4): {CLAASSEN_FLOW_FRACTION:.2f} | "
                 f"Njemanze 1992 (secondary, velocity): {NJEMANZE_VELOCITY_THRESHOLD:.2f}")
    lines.append("")

    # Global sensitivity: rank correlation with the plain-choke LOC time.
    names = ["cbf", "cmro2", "oef", "cbv", "vertebral_share", "kappa", "rossen_loc_s", "rossen_vertebral_open"]
    rho = {n: rank_correlation(inputs[n], full) for n in names}
    order = sorted(names, key=lambda n: -abs(rho[n]))
    lines.append("[sensitivity 1: rank correlation of each sampled input with plain-choke LOC time]")
    lines.append("  ('never' counts as the longest time; +1 = input up, time up)")
    for n in order:
        lines.append(f"  {LABELS[n]:38s} {rho[n]:+.2f}")
    lines.append(f"  for reference, the fitted threshold itself: {rank_correlation(theta, full):+.2f}")
    lines.append("")

    # One-at-a-time sensitivity with the threshold treated as known.
    oat = one_at_a_time((t5, t95))
    base_t = loc_time(Params(), Choke(1.0), central_threshold(Params()))
    lines.append("[sensitivity 2: one input at a time, others central, threshold held at the central fit]")
    lines.append(f"  central prediction {base_t:.1f} s; each row: LOC time at the low and high end of the input")
    for n, lo, hi in oat:
        ends = " -> ".join("never" if np.isnan(v) else f"{v:.1f} s" for v in (lo, hi))
        lines.append(f"  {LABELS[n]:38s} {ends}")
    lines.append("")

    # What the held-out data would say about the threshold. Not a prediction.
    for r in ("A", "C"):
        both = (out[f"no_loc_{r}"] == 1.0) & inside(out[f"fixation_{r}_s"], MITCHELL_FIXATION_RANGE_S)
        if both.sum() >= 100:
            a, b = np.percentile(theta[both], [5, 95])
            lines.append(f"[NOT a prediction] thresholds in draws that get both Mitchell groups right, reading {r}: "
                         f"{a:.2f} to {b:.2f} (5-95 %)")
    b_ok = inside(out["fixation_B_s"], MITCHELL_FIXATION_RANGE_S)
    a, b = np.percentile(theta[b_ok], [5, 95])
    lines.append(f"[NOT a prediction] thresholds in draws inside the observed range, reading B: {a:.2f} to {b:.2f} (5-95 %)")
    lines.append("")

    half = N_DRAWS // 2
    m1, m2 = np.nanmedian(full[:half]), np.nanmedian(full[half:])
    n1, n2 = np.isnan(full[:half]).mean(), np.isnan(full[half:]).mean()
    lines.append(f"[convergence] plain-choke median, first vs second half of draws: {m1:.2f} vs {m2:.2f} s; "
                 f"'never' share {100 * n1:.1f} vs {100 * n2:.1f} %")

    text = "\n".join(lines) + "\n"
    (ROOT / "results" / "stage4_uncertainty.txt").write_text(text)
    print(text)

    plot_spread(out)
    plot_sensitivity(order, rho, oat, base_t)


def style(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)


def plot_spread(out: dict[str, np.ndarray]) -> None:
    """Predicted fixation time under each reading, next to the observed range."""
    t_max = 30.0
    bins = np.arange(0, t_max + 0.5, 0.5)
    fig, axes = plt.subplots(3, 1, figsize=(7.5, 7.2), sharex=True, sharey=True, facecolor=SURFACE)
    for ax, r in zip(axes, READINGS):
        t = out[f"fixation_{r}_s"]
        style(ax)
        ax.axvspan(*MITCHELL_FIXATION_RANGE_S, color="#d9d8d3", lw=0, zorder=0)
        ax.axvspan(*OBS_BAND, color="#b9b8b1", lw=0, zorder=0)
        weights = np.full(t.shape, 100.0 / t.size)
        ax.hist(t, bins=bins, weights=weights, color=BLUE, edgecolor=SURFACE, linewidth=0.6, zorder=2)
        never, late = np.isnan(t).mean(), (t > t_max).mean()
        hit = np.mean(inside(t, MITCHELL_FIXATION_RANGE_S))
        ax.set_title(READING_NAMES[r], loc="left", fontsize=10, color=INK)
        ax.text(0.995, 0.92, f"inside observed range: {100 * hit:.0f} % of draws\n"
                             f"no LOC predicted: {100 * never:.0f} %\nlater than {t_max:.0f} s: {100 * late:.0f} %",
                transform=ax.transAxes, ha="right", va="top", fontsize=9, color=MUTED)
        ax.set_ylabel("% of draws", color=MUTED, fontsize=9)
        ax.grid(axis="y", color=GRID, lw=0.6, zorder=1)
    axes[0].text(MITCHELL_FIXATION_MEAN_S, axes[0].get_ylim()[1] * 0.97, "observed\n(Mitchell 2012)",
                 ha="center", va="top", fontsize=8, color=INK)
    axes[-1].set_xlabel("predicted time to ocular fixation (s)", color=MUTED, fontsize=9)
    axes[-1].set_xlim(0, t_max)
    fig.suptitle("Predicted time to eye fixation in the held-out neck-restraint study\n"
                 "dark grey: observed mean +/- SD; light grey: observed individual range",
                 x=0.07, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.99))
    fig.savefig(ROOT / "figures" / "stage4_spread.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


def plot_sensitivity(order: list[str], rho: dict[str, float],
                     oat: list[tuple[str, float, float]], base_t: float) -> None:
    """Rank correlations (left) and one-at-a-time ranges (right)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), facecolor=SURFACE)
    style(ax1)
    y = np.arange(len(order))[::-1]
    ax1.barh(y, [rho[n] for n in order], color=BLUE, height=0.6, zorder=2)
    ax1.axvline(0, color=MUTED, lw=0.8)
    ax1.set_yticks(y, [LABELS[n] for n in order])
    ax1.set_xlim(-1, 1)
    ax1.set_xlabel("rank correlation with predicted LOC time", color=MUTED, fontsize=9)
    ax1.set_title("All inputs varied together\n(threshold re-fitted to Rossen in every draw)",
                  loc="left", fontsize=10, color=INK)
    ax1.grid(axis="x", color=GRID, lw=0.6, zorder=1)

    style(ax2)
    cap = 30.0
    oat = sorted(oat, key=lambda row: -(np.nan_to_num(max(row[1], row[2]), nan=cap)
                                        - np.nan_to_num(min(row[1], row[2]), nan=cap)
                                        + (cap if np.isnan(row[1]) or np.isnan(row[2]) else 0)))
    y = np.arange(len(oat))[::-1]
    for yi, (_, lo, hi) in zip(y, oat):
        ends = [cap if np.isnan(v) else min(v, cap) for v in (lo, hi)]
        ax2.barh(yi, max(ends) - min(ends), left=min(ends), color=BLUE, height=0.6, zorder=2)
        if np.isnan(lo) or np.isnan(hi) or max(lo, hi) > cap:
            label = "never" if np.isnan(lo) or np.isnan(hi) else f"{max(lo, hi):.0f} s"
            ax2.text(cap - 0.3, yi, label + " ", ha="right", va="center", fontsize=8, color=SURFACE)
    ax2.axvline(base_t, color=INK, lw=1)
    ax2.text(base_t, 0, f" central prediction {base_t:.1f} s", fontsize=8, color=INK, va="center")
    ax2.set_yticks(y, [LABELS[n] for n, _, _ in oat])
    ax2.set_xlim(0, cap)
    ax2.set_xlabel("predicted LOC time (s), plain blood choke", color=MUTED, fontsize=9)
    ax2.set_title("One input at a time, across its range\n(threshold held at the central fit)",
                  loc="left", fontsize=10, color=INK)
    ax2.grid(axis="x", color=GRID, lw=0.6, zorder=1)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "stage4_sensitivity.png", dpi=150, facecolor=SURFACE)
    plt.close(fig)


if __name__ == "__main__":
    main()
