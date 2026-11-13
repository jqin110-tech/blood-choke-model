"""Stage 2: fit the LOC threshold to Rossen (1943) and plot example trajectories.

Writes results/stage2_threshold.txt and figures/stage2_trajectories.png.
Run from the repo root:  python -m scripts.stage2_model
"""

from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from choke_model.model import NO_CHOKE, Choke, fit_threshold, simulate
from choke_model.params import ROSSEN_LOC_S, Params

ROOT = Path(__file__).resolve().parents[1]


def rossen_cuff(vertebral_open: float) -> Choke:
    """The Rossen cuff: carotids fully occluded, vertebrals partly (A7)."""
    return Choke(carotid_occlusion=1.0, vertebral_open=vertebral_open)


def threshold_fits(p: Params) -> dict[tuple[float, float], float]:
    """Fitted threshold for each corner of (observed LOC time, vertebral flow left)."""
    return {
        (t_obs, v_open): fit_threshold(p, rossen_cuff(v_open), t_obs)
        for t_obs, v_open in itertools.product(ROSSEN_LOC_S, (0.0, 1.0))
    }


def main() -> None:
    p = Params()
    lines = [
        "Stage 2: threshold fitted to Rossen et al. 1943 (S1/S2), nominal parameters",
        f"Arterial O2 content Ca (derived)  = {p.arterial_o2:.4f} ml O2/ml blood",
        f"Baseline brain O2 C0              = {p.baseline_o2:.4f} ml O2/100 ml tissue",
        f"Store / consumption, C0 / CMRO2    = {p.baseline_o2 / p.cmro2:.2f} s",
        f"Consumption half-saturation kappa  = {p.kappa:g} of baseline O2 (A5, NO SOURCE)",
        "",
        "observed LOC (s) | vertebral flow left | fitted threshold C/C0",
    ]
    fits = threshold_fits(p)
    for (t_obs, v_open), theta in fits.items():
        lines.append(f"{t_obs:16.1f} | {v_open:19.1f} | {theta:.4f}")
    central = fit_threshold(p, rossen_cuff(0.5), sum(ROSSEN_LOC_S) / 2)
    lines += [
        "",
        f"Fitted threshold range: {min(fits.values()):.4f} to {max(fits.values()):.4f}",
        f"Central fit (7 s, half vertebral flow left): {central:.4f}",
    ]

    steady = simulate(p, NO_CHOKE, central, t_end=60.0)
    drift = abs(steady.o2_fraction - 1.0).max()
    lines.append(f"No-choke drift over 60 s (max |C/C0 - 1|): {drift:.2e}")

    out = ROOT / "results" / "stage2_threshold.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))

    fig, ax = plt.subplots(figsize=(7, 4.2))
    for occ in (0.5, 0.8, 1.0):
        r = simulate(p, Choke(carotid_occlusion=occ, t_on=5.0, t_off=25.0), central, t_end=45.0)
        ax.plot(r.t, r.o2_fraction, label=f"carotid flow cut {occ:.0%}")
    ax.plot(steady.t[steady.t <= 45], steady.o2_fraction[steady.t <= 45], "k--", lw=1, label="no choke")
    ax.axhline(central, color="grey", lw=1)
    ax.text(45, central, "fitted threshold ", ha="right", va="bottom", color="grey", fontsize=9)
    ax.axvspan(5, 25, color="grey", alpha=0.08)
    ax.set_xlabel("time (s); occlusion on from 5 to 25 s")
    ax.set_ylabel("brain O2, fraction of baseline")
    ax.set_ylim(0, 1.05)
    ax.set_title("Brain oxygen during and after an occlusion (nominal parameters)")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig_path = ROOT / "figures" / "stage2_trajectories.png"
    fig_path.parent.mkdir(exist_ok=True)
    fig.savefig(fig_path, dpi=150)


if __name__ == "__main__":
    main()
