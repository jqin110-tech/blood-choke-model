"""Stage 4 tests: sampling, the fast LOC solver, and the Monte Carlo run."""

from __future__ import annotations

import numpy as np
import pytest

from choke_model.analysis import central_threshold, loc_time, time_to_loc
from choke_model.model import Choke
from choke_model.params import Params
from choke_model.uncertainty import INPUTS, Normal, rank_correlation, run_monte_carlo, sample_inputs


def test_samples_stay_inside_their_ranges() -> None:
    draws = sample_inputs(2000, seed=1)
    for name, dist in INPUTS.items():
        x = draws[name]
        if isinstance(dist, Normal):
            assert x.min() >= max(dist.mean - 2 * dist.sd, dist.lower)
            assert x.max() <= dist.mean + 2 * dist.sd
        else:
            assert dist.low <= x.min() and x.max() <= dist.high


def test_same_seed_gives_same_draws() -> None:
    a, b = sample_inputs(100, seed=7), sample_inputs(100, seed=7)
    assert all(np.array_equal(a[k], b[k]) for k in a)


@pytest.mark.parametrize("choke", [Choke(1.0), Choke(0.9), Choke(1.0, ramp_s=1.6), Choke(1.0, vertebral_open=0.0)])
def test_fast_loc_time_matches_full_simulation(choke: Choke) -> None:
    p = Params()
    theta = central_threshold(p)
    assert loc_time(p, choke, theta) == pytest.approx(time_to_loc(p, choke, theta), abs=1e-4)


def test_fast_loc_time_agrees_on_never() -> None:
    p = Params()
    theta = central_threshold(p)
    assert np.isnan(loc_time(p, Choke(0.5), theta))
    assert np.isnan(time_to_loc(p, Choke(0.5), theta))


def test_cmro2_cancels_out() -> None:
    """With Ca derived from Fick (A8), predicted times do not depend on CMRO2."""
    p = Params()
    theta = central_threshold(p)
    times = [loc_time(p.with_(cmro2=p.cmro2 * k), Choke(1.0), theta) for k in (0.7, 1.0, 1.3)]
    assert times == pytest.approx([times[0]] * 3, rel=1e-6)


def test_rank_correlation() -> None:
    x = np.arange(10.0)
    assert rank_correlation(x, x**3) == pytest.approx(1.0)
    assert rank_correlation(x, -x) == pytest.approx(-1.0)
    y = x.copy()
    y[-2:] = np.nan  # "never" counts as the longest time
    assert rank_correlation(x, y) > 0.95


def test_small_monte_carlo_run() -> None:
    inputs, out = run_monte_carlo(40, seed=3)
    assert all(len(v) == 40 for v in inputs.values())
    assert np.all((out["threshold"] > 0) & (out["threshold"] < 1))
    assert np.all((out["critical_flow"] > 0) & (out["critical_flow"] < 1))
    t = out["loc_full_carotid_s"]
    assert np.all(t[~np.isnan(t)] > 0)
    # Reading C always leaves more flow than reading A, so it is never faster.
    a, c = out["fixation_A_s"], out["fixation_C_s"]
    both = ~np.isnan(a) & ~np.isnan(c)
    assert np.all(c[both] >= a[both])
    assert not np.any(np.isnan(a) & ~np.isnan(c))
