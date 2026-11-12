"""One-compartment model of oxygen in brain tissue.

State: C(t), ml O2 held in the blood inside 100 ml of brain tissue.

    dC/dt = F(t) * Ca  -  F(t) * C / V  -  M(C)
            (arterial in)  (venous out)    (consumption)

F(t) is blood flow, Ca arterial O2 content, V cerebral blood volume and
M(C) oxygen consumption. The compartment is well mixed, so blood leaving it
carries O2 at concentration C / V (ASSUMPTIONS.md, A1-A2).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .params import Params


@dataclass(frozen=True)
class Choke:
    """A neck occlusion applied from t_on to t_off (seconds).

    carotid_occlusion: fraction of carotid flow removed (0 = none, 1 = all).
    vertebral_open: fraction of vertebral flow that still gets through
        (1 = vertebrals untouched, as assumed for a choke; A4).
    """

    carotid_occlusion: float
    vertebral_open: float = 1.0
    t_on: float = 0.0
    t_off: float = np.inf

    def flow_fraction(self, vertebral_share: float) -> float:
        """Fraction of baseline brain flow remaining while the occlusion is on."""
        carotid = (1.0 - vertebral_share) * (1.0 - self.carotid_occlusion)
        vertebral = vertebral_share * self.vertebral_open
        return carotid + vertebral


NO_CHOKE = Choke(carotid_occlusion=0.0)


def flow(t: float, p: Params, choke: Choke) -> float:
    """Brain blood flow at time t (ml blood / s / 100 ml tissue)."""
    if choke.t_on <= t < choke.t_off:
        return p.cbf * choke.flow_fraction(p.vertebral_share)
    return p.cbf


def consumption(c: float, p: Params) -> float:
    """O2 consumption (ml O2 / s / 100 ml), Michaelis-Menten in C.

    Scaled so consumption equals the sourced CMRO2 at baseline O2 (A5).
    """
    c = max(c, 0.0)
    k = p.kappa * p.baseline_o2
    return p.cmro2 * (1.0 + p.kappa) * c / (k + c)


def rhs(t: float, y: np.ndarray, p: Params, choke: Choke) -> list[float]:
    """Right-hand side of the ODE."""
    c = y[0]
    f = flow(t, p, choke)
    return [f * p.arterial_o2 - f * c / p.cbv - consumption(c, p)]


@dataclass(frozen=True)
class Result:
    """Solved trajectory plus the predicted loss-of-consciousness time."""

    t: np.ndarray
    o2_fraction: np.ndarray        # C(t) / C0
    t_loc: float | None            # first time C/C0 falls below the threshold
    t_recovery: float | None       # first time it rises back above, after t_loc


def simulate(
    p: Params,
    choke: Choke,
    threshold: float,
    t_end: float = 60.0,
    max_step: float = 0.05,
) -> Result:
    """Solve the ODE from baseline and find threshold crossings.

    threshold is the O2 fraction C/C0 below which LOC is predicted (A6).
    """
    c0 = p.baseline_o2

    def below(t: float, y: np.ndarray, *_: object) -> float:
        return y[0] / c0 - threshold

    below.direction = 0  # record crossings both ways

    # Split the integration at the switch times so the solver never steps
    # across a jump in flow.
    edges = sorted({0.0, t_end, *(x for x in (choke.t_on, choke.t_off) if 0 < x < t_end)})
    ts, ys, crossings = [], [], []
    y = [c0]
    for a, b in zip(edges[:-1], edges[1:]):
        sol = solve_ivp(rhs, (a, b), y, args=(p, choke), events=below,
                        max_step=max_step, rtol=1e-8, atol=1e-11)
        ts.append(sol.t)
        ys.append(sol.y[0])
        crossings.extend(sol.t_events[0])
        y = [sol.y[0, -1]]

    t = np.concatenate(ts)
    frac = np.concatenate(ys) / c0
    t_loc = next((x for x in crossings if x > 0), None)
    t_rec = None
    if t_loc is not None:
        t_rec = next((x for x in crossings if x > t_loc + 1e-9), None)
    return Result(t=t, o2_fraction=frac, t_loc=t_loc, t_recovery=t_rec)


def o2_fraction_at(p: Params, choke: Choke, t_query: float) -> float:
    """C(t_query) / C0 for a choke applied at t = 0."""
    sol = solve_ivp(rhs, (0.0, t_query), [p.baseline_o2], args=(p, choke),
                    max_step=0.05, rtol=1e-8, atol=1e-11)
    return float(sol.y[0, -1] / p.baseline_o2)


def fit_threshold(p: Params, choke: Choke, t_observed: float) -> float:
    """The threshold C/C0 that makes predicted LOC equal an observed time.

    C(t) decreases monotonically during a sustained occlusion, so the
    threshold is simply the O2 fraction reached at t_observed.
    """
    return o2_fraction_at(p, choke, t_observed)
