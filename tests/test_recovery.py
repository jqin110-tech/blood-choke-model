"""Stage 5 tests: the recovery helpers behave, and the reported failure is real."""

from __future__ import annotations

import numpy as np
import pytest

from choke_model.analysis import (
    central_threshold, recovery_time, refill_level, refill_time, rossen_cuff, slowest_possible_recovery,
)
from choke_model.model import Choke
from choke_model.params import ROSSEN_RECOVERY_S, Params


def test_no_refill_needed_at_or_above_the_target() -> None:
    p = Params()
    assert refill_time(p, 0.5, 0.5) == 0.0
    assert refill_time(p, 0.8, 0.5) == 0.0


def test_baseline_stays_at_baseline() -> None:
    assert refill_level(Params(), 1.0, 30.0) == pytest.approx(1.0, abs=1e-8)


@pytest.mark.parametrize("start,seconds", [(0.0, 3.0), (0.1, 1.0), (0.3, 6.0)])
def test_refill_time_and_level_are_inverses(start: float, seconds: float) -> None:
    """The solver against a case with a known answer: time to reach the level reached after t is t."""
    p = Params()
    level = refill_level(p, start, seconds)
    assert start < level < 1.0
    assert refill_time(p, start, level) == pytest.approx(seconds, abs=1e-4)


def test_longer_hold_never_recovers_faster_and_stays_under_the_limit() -> None:
    p = Params()
    theta = central_threshold(p)
    times = np.array([recovery_time(p, rossen_cuff(0.5), theta, d) for d in (0.5, 1, 2, 5, 10, 30, 100)])
    assert np.all(np.diff(times) >= -1e-6)
    assert times[0] > 0
    assert times[-1] <= slowest_possible_recovery(p, theta) + 1e-6


def test_no_recovery_time_without_loss_of_consciousness() -> None:
    p = Params()
    assert np.isnan(recovery_time(p, Choke(0.2), central_threshold(p), 5.0))


def test_central_model_recovers_faster_than_anyone_measured() -> None:
    """The stage 5 headline. If this ever fails, the write-up is out of date."""
    p = Params()
    assert slowest_possible_recovery(p, central_threshold(p)) < ROSSEN_RECOVERY_S[0]
