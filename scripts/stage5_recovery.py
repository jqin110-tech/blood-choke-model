"""Stage 5: recovery after release, compared with the only timed data (Rossen).

The model was never fitted to recovery, so this is a test it can fail, and it
does. Writes results/stage5_recovery.txt and figures/stage5_recovery.png.
Run from the repo root:  python -m scripts.stage5_recovery
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from choke_model.analysis import (
    central_threshold, choke_for_flow, loc_time, recovery_time, refill_level, refill_time, rossen_cuff,
    rossen_threshold_corners, slowest_possible_recovery,
)
from choke_model.model import Choke, o2_fraction_at, simulate
from choke_model.params import (
    FIXATION_BEFORE_LOC_S, MITCHELL_RELEASE_AFTER_FIXATION_S, MITCHELL_TIME_TO_MIN_VELOCITY_S,
    MITCHELL_VELOCITY_LEFT_LOC, ROSSEN_CORNEAL_RETURN_S, ROSSEN_LOC_S, ROSSEN_MAX_ARREST_S,
    ROSSEN_RECOVERY_MEAN_SECONDARY_S, ROSSEN_RECOVERY_S, Params,
)
from choke_model.uncertainty import draw_params, rank_correlation, sample_inputs
from scripts.stage3_check import mitchell_scenarios

ROOT = Path(__file__).resolve().parents[1]
N_DRAWS = 5000
SEED = 2026
# How long the cuff stayed on after consciousness was lost is not in the texts
# opened, so it is swept from "released at once" to the longest arrest (S2).
HOLDS_AFTER_LOC_S = (0.5, 1.0, 2.0, 5.0, 10.0, 30.0, ROSSEN_MAX_ARREST_S)
FIGURE_HOLD_S = 5.0   # our choice, for the picture only
MC_HOLD_S = 5.0       # our choice: one moderate hold to show beside the slowest possible case


def rossen_cases(p: Params) -> dict[str, tuple[Choke, float]]:
    """The central Rossen fit and the four corners of what it was fitted to (A6, A7)."""
    cases = {"central (LOC 7 s, half vertebral flow left)": (rossen_cuff(0.5), central_threshold(p))}
    for (t_obs, v_open), theta in rossen_threshold_corners(p).items():
        cases[f"LOC {t_obs:.0f} s, vertebral flow left {v_open:.0f}"] = (rossen_cuff(v_open), theta)
    return cases


def monte_carlo(n: int, seed: int) -> dict[str, np.ndarray]:
    """Recovery numbers over the stage 4 input ranges (A12)."""
    inputs = sample_inputs(n, seed)
    rows = []
    for i in range(n):
        x = {k: float(v[i]) for k, v in inputs.items()}
        p, theta = draw_params(x)
        # The threshold was fitted so that this cuff causes LOC at rossen_loc_s.
        at_release = o2_fraction_at(p, rossen_cuff(x["rossen_vertebral_open"]), x["rossen_loc_s"] + MC_HOLD_S)
        rows.append({
            "slowest_s": slowest_possible_recovery(p, theta),
            "after_hold_s": refill_time(p, at_release, theta),
            "threshold": theta,
            "transit_s": p.cbv / p.cbf,
        })
    return {k: np.array([row[k] for row in rows]) for k in rows[0]}


def main() -> None:
    p = Params()
    theta = central_threshold(p)
    lo, hi = ROSSEN_RECOVERY_S
    out = ["Stage 5: recovery after release (nominal parameters unless stated)", ""]
    out.append(f"[Rossen 1943, NOT FITTED] observed: \"response to restoration of blood flow\" in {lo:g} to {hi:g} s (S1/S2);")
    out.append(f"  secondary mean {ROSSEN_RECOVERY_MEAN_SECONDARY_S} s, n = 28 (S11). The texts opened do not say how long the cuff")
    out.append("  stayed on after consciousness was lost, so that hold is swept. Release is a step (S2: deflation \"instantaneous\").")
    out.append("")
    out.append("[model recovery time, seconds from release until O2 is back above the threshold]")
    cases = rossen_cases(p)
    out.append("  hold after LOC " + " | ".join(f"{d:>5g} s" for d in HOLDS_AFTER_LOC_S) + " | slowest possible")
    for name, (cuff, th) in cases.items():
        times = [recovery_time(p, cuff, th, d) for d in HOLDS_AFTER_LOC_S]
        out.append(f"  {name}")
        out.append("                 " + " | ".join(f"{t:7.2f}" for t in times) + f" | {slowest_possible_recovery(p, th):.2f} s")
    central_slowest = slowest_possible_recovery(p, theta)
    central_fastest = recovery_time(p, cases[next(iter(cases))][0], theta, HOLDS_AFTER_LOC_S[0])
    corner_slowest = max(slowest_possible_recovery(p, th) for _, th in cases.values())
    out.append(f"  central fit: {central_fastest:.1f} to {central_slowest:.1f} s, against {lo:g} to {hi:g} s observed "
               f"-> too fast by {lo - central_slowest:.1f} to {hi - central_fastest:.1f} s")
    out.append(f"  corners of the fit: the slowest any corner can be is {corner_slowest:.1f} s, which reaches the fast end of")
    out.append(f"  the observed range only if LOC took {ROSSEN_LOC_S[0]:g} s, the cuff left the vertebral arteries fully open and the hold was long")
    out.append("")

    mc = monte_carlo(N_DRAWS, SEED)
    s5, s50, s95 = np.percentile(mc["slowest_s"], [5, 50, 95])
    a5, a50, a95 = np.percentile(mc["after_hold_s"], [5, 50, 95])
    out.append(f"[can any sourced parameter values fix it?] Monte Carlo, {N_DRAWS} draws, seed {SEED}, inputs as in stage 4")
    out.append(f"  recovery after a {MC_HOLD_S:g} s hold past LOC:          median {a50:.2f} s, 5-95 % {a5:.2f} to {a95:.2f} s")
    out.append(f"  slowest possible recovery (refill from empty): median {s50:.2f} s, 5-95 % {s5:.2f} to {s95:.2f} s, "
               f"largest in any draw {mc['slowest_s'].max():.1f} s")
    out.append("  share of draws in which even the slowest possible recovery reaches")
    for label, t in (("the fastest observed", lo), ("the secondary mean", ROSSEN_RECOVERY_MEAN_SECONDARY_S), ("the slowest observed", hi)):
        out.append(f"      {label:22s} ({t:5.2f} s): {np.mean(mc['slowest_s'] >= t):6.1%}")
    out.append(f"  after a {MC_HOLD_S:g} s hold, share of draws inside the observed {lo:g}-{hi:g} s: "
               f"{np.mean((mc['after_hold_s'] >= lo) & (mc['after_hold_s'] <= hi)):.1%}")
    out.append("  what drives the slowest possible recovery (rank correlation): "
               f"fitted threshold {rank_correlation(mc['threshold'], mc['slowest_s']):+.2f}, "
               f"blood transit time CBV/CBF {rank_correlation(mc['transit_s'], mc['slowest_s']):+.2f}")
    out.append("")

    out.append("[what the observed times would need, central fit]")
    out.append("  (a) a delay between oxygen returning and consciousness returning of about "
               f"{lo - central_slowest:.1f} to {hi - central_fastest:.1f} s, which the model does not have;")
    out.append("  (b) or a higher oxygen level for waking than for passing out. O2 level (C/C0) the model has reached")
    out.append("      after release, starting from completely empty (the slowest case):")
    for label, t in (("fastest observed", lo), ("secondary mean", ROSSEN_RECOVERY_MEAN_SECONDARY_S), ("slowest observed", hi)):
        out.append(f"        {t:5.2f} s ({label}): {refill_level(p, 0.0, t):.2f}   "
                   f"(threshold for passing out: {theta:.2f})")
    out.append("  Neither is added to the model: each needs a new number, and there is no second timed data set to test it on.")
    out.append(f"  context (S2): the corneal reflex returned {ROSSEN_CORNEAL_RETURN_S[0]:g} to {ROSSEN_CORNEAL_RETURN_S[1]:g} s after release, "
               "\"depending on the duration\" of the arrest.")
    out.append("")

    out.append("[Mitchell 2012] observed: \"recovery occurred almost immediately upon release\" (no time in seconds)")
    out.append(f"  protocol: released {MITCHELL_RELEASE_AFTER_FIXATION_S[0]:g}-{MITCHELL_RELEASE_AFTER_FIXATION_S[1]:g} s after fixation; "
               f"model LOC is {FIXATION_BEFORE_LOC_S[0]}-{FIXATION_BEFORE_LOC_S[1]:g} s after fixation,")
    holds = (max(0.0, MITCHELL_RELEASE_AFTER_FIXATION_S[0] - FIXATION_BEFORE_LOC_S[1]),
             MITCHELL_RELEASE_AFTER_FIXATION_S[1] - FIXATION_BEFORE_LOC_S[0])
    out.append(f"  so release comes {holds[0]:g} to {holds[1]:g} s after the model's LOC")
    readings = mitchell_scenarios(p, MITCHELL_VELOCITY_LEFT_LOC)
    for name, q in list(readings.items())[:2]:
        choke = choke_for_flow(p, q, MITCHELL_TIME_TO_MIN_VELOCITY_S)
        ts = [recovery_time(p, choke, theta, d) for d in holds]
        out.append(f"  {name:53s} model recovery {ts[0]:.2f} to {ts[1]:.2f} s after release")
    out.append("  This cannot be scored: \"almost immediately\" has no number. It does not contradict the model.")
    out.append("")
    out.append("[verdict] The model FAILS the recovery test. With the central fit, oxygen is back above the threshold")
    out.append(f"  within {central_slowest:.1f} s of release however long the hold; people took {lo:g} to {hi:g} s. Across the")
    out.append(f"  input ranges the model reaches the fastest observed time in {np.mean(mc['slowest_s'] >= lo):.0%} of draws at most, "
               f"and the slowest in {np.mean(mc['slowest_s'] >= hi):.0%}.")

    text = "\n".join(out) + "\n"
    (ROOT / "results" / "stage5_recovery.txt").write_text(text)
    print(text)
    plot(p, theta, cases)


def plot(p: Params, theta: float, cases: dict[str, tuple[Choke, float]]) -> None:
    """Left: one arrest and release. Right: model recovery time against the hold."""
    lo, hi = ROSSEN_RECOVERY_S
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 4.2))

    cuff = rossen_cuff(0.5)
    t_loc = loc_time(p, cuff, theta)
    t_off = t_loc + FIGURE_HOLD_S
    run = simulate(p, Choke(1.0, 0.5, t_on=0.0, t_off=t_off), theta, t_end=t_off + 14.0)
    left.plot(run.t, run.o2_fraction, color="C0", label="model: oxygen in the brain's blood")
    left.axhline(theta, color="0.4", ls="--", lw=1, label=f"fitted threshold ({theta:.2f})")
    left.axvline(t_off, color="0.6", lw=1)
    left.text(t_off + 0.15, 1.02, "release", fontsize=8, color="0.3")
    left.axvspan(t_off + lo, t_off + hi, color="C2", alpha=0.18, label=f"measured recovery, {lo:g} to {hi:g} s after release")
    left.plot([run.t_recovery], [theta], "o", color="C3",
              label=f"model recovery, {run.t_recovery - t_off:.1f} s after release")
    left.set_xlabel("time since the cuff inflated (s)")
    left.set_ylabel("oxygen, fraction of normal")
    left.set_ylim(0, 1.55)
    left.set_yticks(np.arange(0, 1.01, 0.2))
    left.set_title(f"Rossen cuff, released {FIGURE_HOLD_S:g} s after LOC (hold is our choice)", fontsize=10)
    left.legend(fontsize=8, loc="upper right")

    holds = np.concatenate([np.linspace(0.05, 10, 60), np.linspace(10.5, ROSSEN_MAX_ARREST_S, 40)])
    for i, (name, (case_cuff, th)) in enumerate(cases.items()):
        right.plot(holds, [recovery_time(p, case_cuff, th, d) for d in holds],
                   color="C0" if i == 0 else "0.6", lw=2 if i == 0 else 1,
                   label="model, central fit" if i == 0 else ("model, corners of the fit" if i == 1 else None))
    right.axhspan(lo, hi, color="C2", alpha=0.18, label=f"measured recovery, {lo:g} to {hi:g} s (Rossen)")
    right.set_xscale("log")
    right.set_xlabel("how long the cuff stayed on after LOC (s)")
    right.set_ylabel("recovery time after release (s)")
    right.set_ylim(0, hi + 1)
    right.set_title("Only one corner of the fit reaches the measured range", fontsize=10)
    right.legend(fontsize=8, loc="center left")
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "stage5_recovery.png", dpi=150)


if __name__ == "__main__":
    main()
