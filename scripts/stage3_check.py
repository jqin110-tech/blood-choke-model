"""Stage 3: check the model and compare predictions with published data.

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
    FIXATION_BEFORE_LOC_S, MITCHELL_FIXATION_MEAN_S, MITCHELL_FIXATION_RANGE_S,
    MITCHELL_FIXATION_SD_S, MITCHELL_NO_LOC_HOLD_S, MITCHELL_TIME_TO_MIN_VELOCITY_S,
    MITCHELL_VELOCITY_LEFT_LOC, MITCHELL_VELOCITY_LEFT_NO_LOC,
    NJEMANZE_VELOCITY_THRESHOLD, ROSSEN_LOC_S, Params,
)

ROOT = Path(__file__).resolve().parents[1]

# Claassen 2021 (S4): "loss of function is observed below ~22 ml/100g/min",
# against a normal ~50 ml/100g/min (same source, same units).
CLAASSEN_FLOW_FRACTION = 22.0 / 50.0


def fmt(t: float) -> str:
    """A time in seconds, or 'never' when the model predicts no LOC."""
    return "never" if np.isnan(t) else f"{t:.1f} s"


def mitchell_scenarios(p: Params, velocity_left: tuple[float, float]) -> dict[str, float]:
    """Three readings of whole-brain flow left during neck restraint (A11).

    The paper measured velocity in the middle cerebral arteries only, so the
    whole-brain flow is not known. These readings bracket it.
    """
    v = p.vertebral_share
    mca = sum(velocity_left) / 2
    return {
        "A  whole brain falls like the MCA velocity": mca,
        "B  carotids shut, vertebrals normal": v,
        "C  carotids pass the MCA fraction, vertebrals normal": (1 - v) * mca + v,
    }


def main() -> None:
    p = Params()
    theta = central_threshold(p)
    corners = rossen_threshold_corners(p)
    lo_theta, hi_theta = min(corners.values()), max(corners.values())
    ramp = MITCHELL_TIME_TO_MIN_VELOCITY_S
    mid_lag = sum(FIXATION_BEFORE_LOC_S) / 2
    out: list[str] = ["Stage 3 checks (nominal parameters)", ""]

    # 1. Steady state.
    r = simulate(p, NO_CHOKE, theta, t_end=300.0)
    out.append(f"[steady state] no choke, 300 s: max |C/C0 - 1| = {abs(r.o2_fraction - 1).max():.1e}")

    # 2. Monotonic: time to LOC vs carotid occlusion (vertebrals open).
    cuts = np.linspace(0.0, 1.0, 101)
    times = np.array([time_to_loc(p, Choke(c), theta) for c in cuts])
    finite = times[~np.isnan(times)]
    mono = bool(np.all(np.diff(finite) <= 1e-9))
    out.append(f"[monotonic] time to LOC never rises as carotid occlusion increases: {mono}")
    out.append(f"[monotonic] with vertebrals open, LOC needs carotid cut >= {cuts[~np.isnan(times)][0]:.2f} "
               f"(central threshold {theta:.3f})")
    out.append("")

    # 3a. Rossen: in-sample, because the threshold was fitted to it.
    out.append(f"[Rossen 1943, IN-SAMPLE] observed LOC {ROSSEN_LOC_S[0]:.0f}-{ROSSEN_LOC_S[1]:.0f} s; "
               "matches by construction (threshold was fitted to it).")
    out.append("")

    # 3b. Mitchell, group that lost consciousness (held out).
    fix_lo = MITCHELL_FIXATION_MEAN_S - MITCHELL_FIXATION_SD_S
    fix_hi = MITCHELL_FIXATION_MEAN_S + MITCHELL_FIXATION_SD_S
    out.append("[Mitchell 2012, HELD OUT, test 1] 16 subjects who lost consciousness")
    out.append(f"  observed ocular fixation: {MITCHELL_FIXATION_MEAN_S} +/- {MITCHELL_FIXATION_SD_S:.1f} s "
               f"(mean +/- SD, derived); individual range {MITCHELL_FIXATION_RANGE_S[0]}-"
               f"{MITCHELL_FIXATION_RANGE_S[1]} s (read from Figure 6)")
    out.append(f"  model fixation = model LOC - {mid_lag} s (S1: fixation 0.5-1 s before LOC)")
    out.append(f"  'ramp' = flow falls over {ramp} s (measured time to minimum velocity), not instantly")
    out.append("  reading of flow left                                  | flow | instant | gap    | ramp    | gap    | ramp, over threshold range")
    for name, q in mitchell_scenarios(p, MITCHELL_VELOCITY_LEFT_LOC).items():
        t_inst = time_to_loc(p, choke_for_flow(p, q), theta) - mid_lag
        t_ramp = time_to_loc(p, choke_for_flow(p, q, ramp), theta) - mid_lag
        early = time_to_loc(p, choke_for_flow(p, q, ramp), hi_theta) - mid_lag
        late = time_to_loc(p, choke_for_flow(p, q, ramp), lo_theta) - mid_lag
        gaps = ["  n/a " if np.isnan(t) else f"{t - MITCHELL_FIXATION_MEAN_S:+.1f} s" for t in (t_inst, t_ramp)]
        out.append(f"  {name:53s} | {q:.2f} | {fmt(t_inst):7s} | {gaps[0]} | {fmt(t_ramp):7s} | {gaps[1]} | "
                   f"{fmt(early)} to {fmt(late)}")
    out.append(f"  observed band (mean +/- SD): {fix_lo:.1f} to {fix_hi:.1f} s")
    out.append("")

    # 3c. Mitchell, group that did not lose consciousness (held out).
    out.append(f"[Mitchell 2012, HELD OUT, test 2] 4 subjects with no fixation after {MITCHELL_NO_LOC_HOLD_S} s")
    out.append("  reading of flow left                                  | flow | model LOC (central) | agrees with 'no LOC'?")
    for name, q in mitchell_scenarios(p, MITCHELL_VELOCITY_LEFT_NO_LOC).items():
        if name.startswith("B"):
            continue  # B assumes shut carotids, which the velocities rule out for this group
        t = time_to_loc(p, choke_for_flow(p, q, ramp), theta)
        ok = np.isnan(t) or t > MITCHELL_NO_LOC_HOLD_S
        out.append(f"  {name:53s} | {q:.2f} | {fmt(t):19s} | {ok}")
    out.append("")

    # 3d. Flow thresholds from the literature.
    q_crit = critical_flow_fraction(p, theta)
    q_lo, q_hi = sorted(critical_flow_fraction(p, th) for th in (lo_theta, hi_theta))
    out.append("[flow threshold, independent of the fit]")
    out.append(f"  model: lowest sustained flow that never causes LOC = {q_crit:.2f} of normal (central), "
               f"{q_lo:.2f} to {q_hi:.2f} over the fitted threshold range")
    out.append(f"  Claassen 2021 (S4): function lost below ~22/50 = {CLAASSEN_FLOW_FRACTION:.2f} of normal flow")
    out.append(f"  Njemanze 1992 (secondary, via S3): LOC if velocity falls below {NJEMANZE_VELOCITY_THRESHOLD:.2f} of baseline")

    text = "\n".join(out) + "\n"
    (ROOT / "results" / "stage3_check.txt").write_text(text)
    print(text)

    # Figure: time to LOC vs occlusion, central threshold and fitted range.
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for th, style, lab in ((theta, "-", f"central threshold ({theta:.2f})"),
                           (hi_theta, "--", f"highest fitted threshold ({hi_theta:.2f})")):
        ax.plot(cuts * 100, [time_to_loc(p, Choke(c), th) for c in cuts], style, color="C0", label=lab)
    ax.axhspan(*ROSSEN_LOC_S, color="C1", alpha=0.15, label="Rossen 1943 LOC, 4-10 s (fitted to)")
    ax.axhspan(fix_lo + mid_lag, fix_hi + mid_lag, color="C2", alpha=0.15,
               label="Mitchell 2012 inferred LOC, mean +/- SD (held out)")
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
