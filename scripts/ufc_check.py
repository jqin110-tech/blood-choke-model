"""UFC check: compare the model with choke times measured in UFC fights.

The data (Stellpflug 2020, S12) were not used to fit anything, so this is a
third held-out test. Writes results/ufc_check.txt and figures/ufc_check.png.
Run from the repo root:  python -m scripts.ufc_check
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from choke_model.analysis import central_threshold, choke_for_flow, loc_time, rossen_threshold_corners
from choke_model.params import (
    MITCHELL_TIME_TO_MIN_VELOCITY_S, MITCHELL_VELOCITY_LEFT_LOC, UFC_ARM_IN_S, UFC_BY_TYPE_SECONDARY_S,
    UFC_CHOKE_FINISHES, UFC_CHOKE_LOC_SHARE, UFC_CHOKE_SHARE_OF_OUTCOMES, UFC_LOC_CI95_S, UFC_LOC_MEAN_S,
    UFC_LOC_N, UFC_NECK_ONLY_S, UFC_RNC_SHARE, Params,
)
from scripts.stage3_check import fmt, mitchell_scenarios

ROOT = Path(__file__).resolve().parents[1]


def ufc_predictions(p: Params, threshold: float, ramp_s: float = MITCHELL_TIME_TO_MIN_VELOCITY_S) -> dict[str, float]:
    """Model time to LOC for a fight choke, under each reading of flow left (A14).

    No source measures blood flow during a choke in a fight. The flow left is
    taken from the laboratory neck-restraint study (S3), read three ways (A11).
    """
    readings = mitchell_scenarios(p, MITCHELL_VELOCITY_LEFT_LOC)
    return {name: loc_time(p, choke_for_flow(p, q, ramp_s), threshold) for name, q in readings.items()}


def main() -> None:
    p = Params()
    theta = central_threshold(p)
    corners = rossen_threshold_corners(p)
    lo_theta, hi_theta = min(corners.values()), max(corners.values())
    lo, hi = UFC_LOC_CI95_S
    out = ["UFC check (nominal parameters)", ""]
    out.append(f"[UFC fights, S13, context] {UFC_CHOKE_FINISHES} fight-ending chokes = "
               f"{UFC_CHOKE_SHARE_OF_OUTCOMES:.1%} of fight outcomes; {UFC_CHOKE_LOC_SHARE:.0%} of them ended in "
               f"loss of consciousness; the rear naked choke was {UFC_RNC_SHARE:.1%} of them.")
    out.append("")
    out.append(f"[Stellpflug 2020, S12, HELD OUT, test 3] {UFC_LOC_N} chokes to LOC in UFC fights, timed from video")
    out.append(f"  observed: mean {UFC_LOC_MEAN_S} s from 'the establishment of a choke' to LOC, 95% CI {lo}-{hi} s")
    out.append(f"  by category: neck-only {UFC_NECK_ONLY_S[0]} s ({UFC_NECK_ONLY_S[1]}-{UFC_NECK_ONLY_S[2]}); "
               f"arm-in {UFC_ARM_IN_S[0]} s ({UFC_ARM_IN_S[1]}-{UFC_ARM_IN_S[2]})")
    out.append("  model: flow left is NOT measured in fights; it is borrowed from the laboratory study (S3), read three ways")
    out.append("  reading of flow left                                  | instant | 1.6 s onset | gap to 9.0 s | inside the CI? | over threshold range")
    central = ufc_predictions(p, theta)
    instant = ufc_predictions(p, theta, ramp_s=0.0)
    early, late = ufc_predictions(p, hi_theta), ufc_predictions(p, lo_theta)
    for name, t in central.items():
        gap = "  n/a " if np.isnan(t) else f"{t - UFC_LOC_MEAN_S:+.1f} s"
        ok = (not np.isnan(t)) and lo <= t <= hi
        out.append(f"  {name:53s} | {fmt(instant[name]):7s} | {fmt(t):11s} | {gap:12s} | {str(ok):14s} | "
                   f"{fmt(early[name])} to {fmt(late[name])}")
    out.append("")
    out.append("[choke types, SECONDARY, context only] per-technique means from web write-ups of S12 (no CIs;")
    out.append("  the write-up reports no significant difference between types). The model gives ONE time for")
    out.append("  every type, because no opened source says how the types differ in what they compress.")
    a, b = list(central.values())[:2]
    out.append(f"  model, reading A: {fmt(a)}; reading B: {fmt(b)}")
    for name, t in UFC_BY_TYPE_SECONDARY_S.items():
        out.append(f"  {name:20s} {t:5.1f} s   vs A {t - a:+.1f} s   vs B {t - b:+.1f} s")
    values = np.array(list(UFC_BY_TYPE_SECONDARY_S.values()))
    out.append(f"  spread across the 11 types: {values.min()} to {values.max()} s")

    text = "\n".join(out) + "\n"
    (ROOT / "results" / "ufc_check.txt").write_text(text)
    print(text)

    # Figure: each choke type's mean, the overall measured mean, and the model.
    names = list(UFC_BY_TYPE_SECONDARY_S)[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.axvspan(lo, hi, color="C2", alpha=0.18, label=f"UFC fights, mean and 95% CI ({UFC_LOC_MEAN_S} s, n = {UFC_LOC_N})")
    ax.axvline(UFC_LOC_MEAN_S, color="C2", lw=1)
    ax.plot([UFC_BY_TYPE_SECONDARY_S[n] for n in names], range(len(names)), "o", color="0.25",
            label="mean for each choke type (secondary source, no CI)")
    for t, style, lab in ((a, "-", "model, reading A"), (b, "--", "model, reading B")):
        ax.axvline(t, color="C0", ls=style, label=f"{lab}: {t:.1f} s")
    ax.set_yticks(range(len(names)), names)
    ax.set_xlabel("time from choke established to loss of consciousness (s)")
    ax.set_xlim(4, 13)
    ax.legend(fontsize=8, loc="lower right")
    ax.set_title("Chokes in UFC fights vs the model (model gives one time for all types)", fontsize=10)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "ufc_check.png", dpi=150)


if __name__ == "__main__":
    main()
