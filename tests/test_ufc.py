"""Tests for the UFC comparison: the constants hang together and the headline claim holds."""

from __future__ import annotations

import numpy as np

from choke_model.analysis import central_threshold
from choke_model.params import (
    UFC_ARM_IN_S, UFC_BY_TYPE_SECONDARY_S, UFC_LOC_CI95_S, UFC_LOC_MEAN_S, UFC_NECK_ONLY_S, Params,
)
from scripts.ufc_check import ufc_predictions


def test_published_intervals_contain_their_means() -> None:
    assert UFC_LOC_CI95_S[0] < UFC_LOC_MEAN_S < UFC_LOC_CI95_S[1]
    for mean, low, high in (UFC_NECK_ONLY_S, UFC_ARM_IN_S):
        assert low < mean < high


def test_eleven_choke_types_listed() -> None:
    assert len(UFC_BY_TYPE_SECONDARY_S) == 11
    assert all(5.0 < t < 12.0 for t in UFC_BY_TYPE_SECONDARY_S.values())


def test_ufc_mean_lies_between_readings_a_and_b() -> None:
    """The claim made in the write-up: the measured mean sits between the two usable readings."""
    p = Params()
    a, b, c = ufc_predictions(p, central_threshold(p)).values()
    assert a < UFC_LOC_MEAN_S < b
    assert np.isnan(c)          # reading C still predicts no LOC: the known failure (A11)


def test_slower_onset_never_gives_earlier_loc() -> None:
    p = Params()
    theta = central_threshold(p)
    fast, slow = ufc_predictions(p, theta, ramp_s=0.0), ufc_predictions(p, theta, ramp_s=1.6)
    for name in fast:
        if not np.isnan(fast[name]):
            assert slow[name] >= fast[name]


def test_page_shows_the_same_ufc_numbers_as_the_check() -> None:
    """The viewer's UFC strip is built from params and ufc_predictions, nothing else."""
    from scripts.build_simulator import build_config

    p = Params()
    ufc = build_config()["xray"]["ufc"]
    model = ufc_predictions(p, central_threshold(p))
    a, b = list(model.values())[:2]
    assert ufc["model"] == {"A": round(a, 1), "B": round(b, 1)}
    assert ufc["measured"][0]["t"] == [UFC_LOC_MEAN_S, *UFC_LOC_CI95_S]
    assert {row["name"]: row["t"] for row in ufc["byType"]} == UFC_BY_TYPE_SECONDARY_S
    times = [row["t"] for row in ufc["byType"]]
    assert times == sorted(times)
