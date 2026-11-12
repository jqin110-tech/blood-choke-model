"""Stage 3: check the model and compare predictions with published times.

Writes results/stage3_check.txt and figures/stage3_time_vs_occlusion.png.
Run from the repo root:  python scripts/stage3_check.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from choke_model.analysis import (
    central_threshold, choke_for_flow, critical_flow_fraction,
    rossen_threshold_corners, time_to_loc,
)
from choke_model.model import NO_CHOKE, Choke, simulate
from choke_model.params import (
    FIXATION_BEFORE_LOC_S, MITCHELL_FIXATION_MEAN_S, MITCHELL_FIXATION_SD_S,
    MITCHELL_RESIDUAL_VELOCITY, ROSSEN_LOC_S, Params,
)

ROOT = Path(__file__).resolve().parents[1]

# Claassen 2021 (S4): "loss of function is observed below ~22 ml/100g/min",
# against a normal ~50 ml/100g/min (same source, same units).
CLAASSEN_FLOW_FRACTION = 22.0 / 50.0


def main() -> None:
    p = Params()
    theta = central_threshold(p)
    corners = rossen_threshold_corners(p)
    lo_theta, hi_theta = min(corners.values()), max(corners.values())
    out: list[str] = ["Stage 3 checks (nominal parameters)", ""]

    # 1. Steady state.
    r = simulate(p, NO_CHOKE, theta, t_end=300.0)
    out.append(f"[steady state] no choke, 300 s: max |C/C0 - 1| = {abs(r.o2_fraction - 1).max():.1e}")

    # 2. Monotonic: time to LOC vs carotid occlusion (vertebrals open).
    cuts = np.linspace(0.0, 1.0, 101)
    times = np.array([time_to_loc(p, Choke(c), theta) for c in cuts])
    finite = times[~np.isnan(times)]
    mono = bool(np.all(np.diff(finite) <= 1e-9))
    first = cuts[~np.isnan(times)][0] if finite.size else np.nan
    out.append(f"[monotonic] time to LOC never rises as carotid occlusion increases: {mono}")
    out.append(f"[monotonic] with vertebrals open, LOC needs carotid cut >= {first:.2f} "
               f"(central threshold {theta:.3f})")
    out.append("")

    # 3a. Rossen: in-sample, because the threshold was fitted to it.
    out.append(f"[Rossen 1943, IN-SAMPLE] observed LOC {ROSSEN_LOC_S[0]:.0f}-{ROSSEN_LOC_S[1]:.0f} s; "
               "matches by construction (threshold was fitted to it).")

    # 3b. Mitchell: held out.
    fix_lo = MITCHELL_FIXATION_MEAN_S - MITCHELL_FIXATION_SD_S
    fix_hi = MITCHELL_FIXATION_MEAN_S + MITCHELL_FIXATION_SD_S
    out.append(f"[Mitchell 2012, HELD OUT] observed ocular fixation {MITCHELL_FIXATION_MEAN_S} "
               f"+/- {MITCHELL_FIXATION_SD_S:.1f} s (mean +/- SD, derived); "
               f"model fixation = model LOC - {FIXATION_BEFORE_LOC_S[0]}-{FIXATION_BEFORE_LOC_S[1]} s")
    scenarios = {
        "A: total flow = MCA velocity ratio, R": MITCHELL_RESIDUAL_VELOCITY[0],
        "A: total flow = MCA velocity ratio, L": MITCHELL_RESIDUAL_VELOCITY[1],
        "B: carotids fully cut, vertebrals open": p.vertebral_share,
    }
    out.append("  scenario                                  | flow left | fixation, central thr | fixation over thr range | gap to 9.5 s (central)")
    for name, q in scenarios.items():
        choke = choke_for_flow(p, q)
        t_c = time_to_loc(p, choke, theta)
        fix_c = (t_c - FIXATION_BEFORE_LOC_S[1], t_c - FIXATION_BEFORE_LOC_S[0])
        earliest = time_to_loc(p, choke, hi_theta) - FIXATION_BEFORE_LOC_S[1]
        latest = time_to_loc(p, choke, lo_theta) - FIXATION_BEFORE_LOC_S[0]
        rng = f"{earliest:.1f} s to " + ("never" if np.isnan(latest) else f"{latest:.1f} s")
        gap = (sum(fix_c) / 2) - MITCHELL_FIXATION_MEAN_S
        out.append(f"  {name:41s} | {q:9.3f} | {fix_c[0]:5.1f} to {fix_c[1]:4.1f} s       | {rng:23s} | {gap:+.1f} s")
    out.append(f"  observed band (mean +/- SD): {fix_lo:.1f} to {fix_hi:.1f} s")
    out.append("")

    # 3c. Flow threshold check against Claassen 2021.
    q_crit = critical_flow_fraction(p, theta)
    q_lo, q_hi = sorted(critical_flow_fraction(p, th) for th in (lo_theta, hi_theta))
    out.append(f"[Claassen 2021, independent] function lost below ~22/50 = {CLAASSEN_FLOW_FRACTION:.2f} of normal flow")
    out.append(f"  model: lowest sustained flow that never causes LOC = {q_crit:.2f} (central), "
               f"{q_lo:.2f} to {q_hi:.2f} over the fitted threshold range")

    text = "\n".join(out) + "\n"
    (ROOT / "results" / "stage3_check.txt").write_text(text)
    print(text)

    # Figure: time to LOC vs occlusion, central threshold and fitted range.
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for th, style, lab in ((theta, "-", f"central threshold ({theta:.2f})"),
                           (hi_theta, "--", f"highest fitted threshold ({hi_theta:.2f})")):
        ts = [time_to_loc(p, Choke(c), th) for c in cuts]
        ax.plot(cuts * 100, ts, style, color="C0", label=lab)
    ax.axhspan(*ROSSEN_LOC_S, color="C1", alpha=0.15, label="Rossen 1943 LOC, 4-10 s (fitted to)")
    ax.axhspan(fix_lo + FIXATION_BEFORE_LOC_S[0], fix_hi + FIXATION_BEFORE_LOC_S[1], color="C2", alpha=0.15,
               label="Mitchell 2012 inferred LOC (held out)")
    ax.set_xlabel("carotid flow removed (%), vertebral arteries open")
    ax.set_ylabel("predicted time to LOC (s)")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    ax.set_title("Stronger occlusion, faster predicted loss of consciousness")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "stage3_time_vs_occlusion.png", dpi=150)


if __name__ == "__main__":
    main()
