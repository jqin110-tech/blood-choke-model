"""Helpers shared by the check, uncertainty and recovery scripts."""

from __future__ import annotations

import itertools

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from .model import Choke, consumption, fit_threshold, rhs, simulate
from .params import ROSSEN_LOC_S, Params


def rossen_cuff(vertebral_open: float) -> Choke:
    """The Rossen cuff: carotids fully occluded, vertebrals partly (A7)."""
    return Choke(carotid_occlusion=1.0, vertebral_open=vertebral_open)


def rossen_threshold_corners(p: Params) -> dict[tuple[float, float], float]:
    """Fitted threshold at each corner of (observed LOC time, vertebral flow left)."""
    return {
        (t_obs, v_open): fit_threshold(p, rossen_cuff(v_open), t_obs)
        for t_obs, v_open in itertools.product(ROSSEN_LOC_S, (0.0, 1.0))
    }


def central_threshold(p: Params) -> float:
    """Central fit: midpoint of Rossen's 4-10 s, half of vertebral flow left."""
    return fit_threshold(p, rossen_cuff(0.5), sum(ROSSEN_LOC_S) / 2)


def time_to_loc(p: Params, choke: Choke, threshold: float, t_end: float = 120.0) -> float:
    """Predicted time from choke onset to LOC, or nan if it never happens."""
    r = simulate(p, choke, threshold, t_end=t_end)
    return np.nan if r.t_loc is None else r.t_loc - choke.t_on


def steady_o2_fraction(p: Params, flow_fraction: float) -> float:
    """Long-run C/C0 if flow is held at flow_fraction of baseline."""
    f = p.cbf * flow_fraction

    def net(c: float) -> float:
        return f * p.arterial_o2 - f * c / p.cbv - consumption(c, p)

    if flow_fraction <= 0:
        return 0.0
    return brentq(net, 1e-15, p.cbv * p.arterial_o2) / p.baseline_o2


def critical_flow_fraction(p: Params, threshold: float) -> float:
    """Smallest sustained flow fraction that keeps C/C0 at or above threshold."""
    lowest = 1e-9
    if steady_o2_fraction(p, lowest) >= threshold:
        return lowest  # threshold so low that any trickle of flow is enough
    return brentq(lambda q: steady_o2_fraction(p, q) - threshold, lowest, 1.0)


def carotid_cut_for_flow(p: Params, flow_fraction: float) -> float:
    """Carotid occlusion that leaves this total flow fraction, vertebrals open."""
    v = p.vertebral_share
    return 1.0 - (flow_fraction - v) / (1.0 - v)


def choke_for_flow(p: Params, flow_fraction: float, ramp_s: float = 0.0) -> Choke:
    """A choke that leaves the given total flow fraction.

    Above the vertebral share, only carotid flow is cut (A4). Below it, the
    carotids are fully cut and vertebral flow must also be reduced.
    """
    v = p.vertebral_share
    if flow_fraction >= v:
        return Choke(carotid_occlusion=carotid_cut_for_flow(p, flow_fraction), ramp_s=ramp_s)
    return Choke(carotid_occlusion=1.0, vertebral_open=flow_fraction / v, ramp_s=ramp_s)


def loc_time(p: Params, choke: Choke, threshold: float, t_max: float = 3600.0) -> float:
    """Time from onset to LOC for a sustained choke starting at t = 0, or nan.

    Faster than time_to_loc and exact about "never": during a sustained choke
    C(t) falls steadily toward its steady state, so LOC happens if and only
    if that steady state lies below the threshold.
    """
    q = choke.flow_fraction(p.vertebral_share)
    if steady_o2_fraction(p, q) >= threshold:
        return np.nan

    def crossed(t: float, y: np.ndarray, *_: object) -> float:
        return y[0] / p.baseline_o2 - threshold

    crossed.terminal = True
    t, y = 0.0, [p.baseline_o2]
    for t_stop in (choke.ramp_s, t_max) if choke.ramp_s > 0 else (t_max,):
        sol = solve_ivp(rhs, (t, t_stop), y, args=(p, choke), events=crossed, rtol=1e-8, atol=1e-11)
        if sol.t_events[0].size:
            return float(sol.t_events[0][0])
        t, y = t_stop, [sol.y[0, -1]]
    return np.nan
