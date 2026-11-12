"""Stage 2 tests: steady state, units, and the solver against an exact solution."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from choke_model.model import NO_CHOKE, Choke, consumption, rhs, simulate
from choke_model.params import Params


def test_steady_state_without_choke() -> None:
    """With no choke, dC/dt is zero at baseline and C stays put."""
    p = Params()
    assert rhs(0.0, np.array([p.baseline_o2]), p, NO_CHOKE)[0] == pytest.approx(0.0, abs=1e-12)
    r = simulate(p, NO_CHOKE, threshold=0.5, t_end=120.0)
    assert np.allclose(r.o2_fraction, 1.0, atol=1e-8)
    assert r.t_loc is None


def test_consumption_equals_cmro2_at_baseline() -> None:
    p = Params()
    assert consumption(p.baseline_o2, p) == pytest.approx(p.cmro2)


def test_fick_principle_units() -> None:
    """Ca from Fick gives back CMRO2 = CBF x OEF x Ca, and a plausible content.

    Ca should be below the O2 capacity of blood, about 0.2 ml/ml, and positive.
    """
    p = Params()
    assert p.cbf * p.oef * p.arterial_o2 == pytest.approx(p.cmro2)
    assert 0.1 < p.arterial_o2 < 0.25
    # Per-minute values convert back to the sourced per-minute numbers.
    assert p.cbf * 60 == pytest.approx(44.4)
    assert p.cmro2 * 60 == pytest.approx(3.3)


def test_flow_fraction() -> None:
    assert Choke(1.0, 1.0).flow_fraction(0.25) == pytest.approx(0.25)
    assert Choke(1.0, 0.0).flow_fraction(0.25) == pytest.approx(0.0)
    assert Choke(0.0).flow_fraction(0.25) == pytest.approx(1.0)


def test_solver_matches_exact_solution() -> None:
    """With kappa -> 0, consumption is constant M while C >> 0, and the ODE

        dC/dt = q F Ca - q F C / V - M

    is linear with exact solution C(t) = C* + (C0 - C*) exp(-q F t / V),
    where C* = V (Ca - M / (q F)).
    """
    p = Params(kappa=1e-9)
    q = 0.6
    choke = Choke(carotid_occlusion=1 - (q - p.vertebral_share) / (1 - p.vertebral_share))
    assert choke.flow_fraction(p.vertebral_share) == pytest.approx(q)

    t_eval = np.linspace(0, 3.0, 31)  # short enough that C stays far above 0
    sol = solve_ivp(rhs, (0, 3.0), [p.baseline_o2], args=(p, choke),
                    t_eval=t_eval, rtol=1e-10, atol=1e-13)
    f = q * p.cbf
    c_star = p.cbv * (p.arterial_o2 - p.cmro2 / f)
    exact = c_star + (p.baseline_o2 - c_star) * np.exp(-f * t_eval / p.cbv)
    assert np.allclose(sol.y[0], exact, rtol=1e-6)
