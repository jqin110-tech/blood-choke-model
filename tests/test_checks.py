"""Stage 3 tests: steady state across parameter extremes, monotonic behaviour."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from choke_model.analysis import (
    carotid_cut_for_flow, central_threshold, critical_flow_fraction, steady_o2_fraction, time_to_loc,
)
from choke_model.model import NO_CHOKE, Choke, simulate
from choke_model.params import CBF, CBV, CMRO2, OEF, VERTEBRAL_SHARE, Params, SECONDS_PER_MINUTE


@pytest.mark.parametrize(
    "cbf,cmro2,oef,cbv,v",
    list(itertools.product((CBF.low, CBF.high), (CMRO2.low, CMRO2.high), (OEF.low, OEF.high),
                           (CBV.low, CBV.high), (VERTEBRAL_SHARE.low, VERTEBRAL_SHARE.high))),
)
def test_steady_state_at_parameter_extremes(cbf: float, cmro2: float, oef: float, cbv: float, v: float) -> None:
    p = Params(cbf=cbf / SECONDS_PER_MINUTE, cmro2=cmro2 / SECONDS_PER_MINUTE, oef=oef, cbv=cbv, vertebral_share=v)
    r = simulate(p, NO_CHOKE, threshold=0.2, t_end=60.0)
    assert np.allclose(r.o2_fraction, 1.0, atol=1e-8)


def test_time_to_loc_falls_as_occlusion_rises() -> None:
    """Above the weakest occlusion that causes LOC at all, more is always faster."""
    p = Params()
    theta = central_threshold(p)
    weakest = carotid_cut_for_flow(p, critical_flow_fraction(p, theta))
    assert 0.0 < weakest < 1.0
    times = np.array([time_to_loc(p, Choke(c), theta) for c in np.linspace(weakest + 0.01, 1.0, 16)])
    assert not np.isnan(times).any()
    assert np.all(np.diff(times) < 0)


def test_mild_occlusion_never_causes_loc() -> None:
    p = Params()
    assert np.isnan(time_to_loc(p, Choke(0.3), central_threshold(p)))


def test_steady_o2_rises_with_flow() -> None:
    p = Params()
    levels = [steady_o2_fraction(p, q) for q in (0.2, 0.4, 0.6, 0.8, 1.0)]
    assert np.all(np.diff(levels) > 0)
    assert levels[-1] == pytest.approx(1.0, rel=1e-6)


def test_critical_flow_is_consistent_with_steady_state() -> None:
    p = Params()
    theta = central_threshold(p)
    q = critical_flow_fraction(p, theta)
    assert steady_o2_fraction(p, q) == pytest.approx(theta, rel=1e-6)
