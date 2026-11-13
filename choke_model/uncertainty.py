"""Monte Carlo over the sourced parameter ranges (stage 4).

Each draw is one imaginary person plus one guess at the things the sources
leave open. For every draw the threshold is re-fitted to Rossen (A6), then
the model predicts the Mitchell experiment, which was never used in the fit.
The sampling choices are assumption A12 in ASSUMPTIONS.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import truncnorm

from .analysis import choke_for_flow, critical_flow_fraction, loc_time, rossen_cuff
from .model import Choke, fit_threshold
from .params import (
    FIXATION_BEFORE_LOC_S, MITCHELL_NO_LOC_HOLD_S, MITCHELL_TIME_TO_MIN_VELOCITY_S,
    MITCHELL_TIME_TO_MIN_VELOCITY_SD_S, MITCHELL_VELOCITY_LEFT_NO_LOC, ROSSEN_LOC_S,
    SECONDS_PER_MINUTE, Params,
)


@dataclass(frozen=True)
class Normal:
    """Mean and SD from a source, sampled as a normal cut off at +/- 2 SD."""

    mean: float
    sd: float
    source: str
    lower: float = -np.inf  # extra hard bound, e.g. 0 for a duration

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        lo = max(self.mean - 2 * self.sd, self.lower)
        hi = self.mean + 2 * self.sd
        a, b = (lo - self.mean) / self.sd, (hi - self.mean) / self.sd
        return truncnorm.rvs(a, b, loc=self.mean, scale=self.sd, size=n, random_state=rng)


@dataclass(frozen=True)
class Uniform:
    """A range with no preferred value inside it."""

    low: float
    high: float
    source: str
    log: bool = False

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        if self.log:
            return np.exp(rng.uniform(np.log(self.low), np.log(self.high), n))
        return rng.uniform(self.low, self.high, n)


# What gets sampled. Keys are the column names of the Monte Carlo table.
INPUTS: dict[str, Normal | Uniform] = {
    # Between-person variation, mean +/- SD as published.
    "cbf": Normal(44.4, 6.5, "S5 Ito 2004, ml/100 ml/min"),
    "cmro2": Normal(3.3, 0.5, "S5 Ito 2004, ml O2/100 ml/min"),
    "oef": Normal(0.44, 0.06, "S5 Ito 2004"),
    "cbv": Normal(3.8, 0.7, "S5 Ito 2004, ml/100 ml"),
    "vertebral_share": Normal(0.28, 0.04, "S9 Zarrinkoob 2015"),
    # No source: explored over a wide range to see whether it matters (A5).
    "kappa": Uniform(0.01, 0.5, "NO SOURCE (A5)", log=True),
    # What the threshold is fitted to (A6, A7).
    "rossen_loc_s": Uniform(*ROSSEN_LOC_S, "S1/S2: LOC after 4 to 10 s"),
    "rossen_vertebral_open": Uniform(0.0, 1.0, "S1/S2: vertebral flow left by the cuff is unknown (A7)"),
    # The Mitchell experiment (S3). Velocities are group means +/- SEM, cm/s.
    "ramp_s": Normal(MITCHELL_TIME_TO_MIN_VELOCITY_S, MITCHELL_TIME_TO_MIN_VELOCITY_SD_S,
                     "S3: time to minimum velocity, SD derived", lower=0.0),
    "fixation_lag_s": Uniform(*FIXATION_BEFORE_LOC_S, "S1/S2: fixation 0.5 to 1 s before LOC"),
    "mca_r_before": Normal(45.0, 3.0, "S3: R MCAVmean 45 +/- 3 (SEM)"),
    "mca_r_during": Normal(8.0, 4.0, "S3: R MCAVmean 8 +/- 4 (SEM)", lower=0.0),
    "mca_l_before": Normal(53.0, 2.0, "S3: L MCAVmean 53 +/- 2 (SEM)"),
    "mca_l_during": Normal(10.0, 3.0, "S3: L MCAVmean 10 +/- 3 (SEM)", lower=0.0),
}

READINGS = ("A", "B", "C")  # readings of whole-brain flow left (A11)


def sample_inputs(n: int, seed: int) -> dict[str, np.ndarray]:
    """Draw n independent sets of inputs."""
    rng = np.random.default_rng(seed)
    return {name: dist.sample(rng, n) for name, dist in INPUTS.items()}


def flow_left(reading: str, mca_left: float, vertebral_share: float) -> float:
    """Whole-brain flow fraction under one reading of the velocity data (A11)."""
    if reading == "A":
        return mca_left
    if reading == "B":
        return vertebral_share
    return (1.0 - vertebral_share) * mca_left + vertebral_share


def draw_params(x: dict[str, float]) -> tuple[Params, float]:
    """The physiology for one draw, and the threshold fitted to Rossen for it (A6)."""
    p = Params(cbf=x["cbf"] / SECONDS_PER_MINUTE, cmro2=x["cmro2"] / SECONDS_PER_MINUTE,
               oef=x["oef"], cbv=x["cbv"], vertebral_share=x["vertebral_share"], kappa=x["kappa"])
    return p, fit_threshold(p, rossen_cuff(x["rossen_vertebral_open"]), x["rossen_loc_s"])


def run_one(x: dict[str, float]) -> dict[str, float]:
    """Model outputs for one draw of the inputs."""
    p, theta = draw_params(x)
    out = {
        "threshold": theta,
        # A plain blood choke: carotids shut at once, vertebrals open.
        "loc_full_carotid_s": loc_time(p, Choke(1.0), theta),
        "critical_flow": critical_flow_fraction(p, theta),
    }
    mca = (x["mca_r_during"] / x["mca_r_before"] + x["mca_l_during"] / x["mca_l_before"]) / 2
    mca_no_loc = sum(MITCHELL_VELOCITY_LEFT_NO_LOC) / 2
    for r in READINGS:
        q = flow_left(r, mca, p.vertebral_share)
        t = loc_time(p, choke_for_flow(p, q, x["ramp_s"]), theta)
        out[f"fixation_{r}_s"] = t - x["fixation_lag_s"]
        if r != "B":  # B assumes shut carotids, which this group's velocities rule out
            q = flow_left(r, mca_no_loc, p.vertebral_share)
            t = loc_time(p, choke_for_flow(p, q, x["ramp_s"]), theta)
            out[f"no_loc_{r}"] = float(np.isnan(t) or t > MITCHELL_NO_LOC_HOLD_S)
    return out


def run_monte_carlo(n: int, seed: int) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Sample n draws and run the model on each. Returns (inputs, outputs)."""
    inputs = sample_inputs(n, seed)
    rows = [run_one({k: float(v[i]) for k, v in inputs.items()}) for i in range(n)]
    outputs = {k: np.array([row[k] for row in rows]) for k in rows[0]}
    return inputs, outputs


def rank_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation, with nan in y ("never") ranked as the largest value."""
    y = np.where(np.isnan(y), np.inf, y)
    rx, ry = (np.argsort(np.argsort(v, kind="stable"), kind="stable").astype(float) for v in (x, y))
    ry[np.isinf(y)] = ry[np.isinf(y)].mean() if np.isinf(y).any() else 0.0  # ties share a rank
    return float(np.corrcoef(rx, ry)[0, 1])
