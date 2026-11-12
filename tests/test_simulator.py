"""The browser simulator must agree with the Python model and be up to date."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from choke_model.model import Choke, simulate
from choke_model.params import SECONDS_PER_MINUTE, Params
from scripts.build_simulator import build_config, build_standalone

ROOT = Path(__file__).resolve().parents[1]
MODEL_JS = ROOT / "simulator" / "model.js"

# (carotid cut, vertebral flow left open, ramp s, hold s, threshold)
CASES = [
    (1.0, 1.0, 0.0, 15.0, 0.241),
    (1.0, 0.5, 0.0, 10.0, 0.241),
    (1.0, 1.0, 1.6, 11.0, 0.241),
    (0.79, 1.0, 1.6, 23.3, 0.241),
    (1.0, 0.0, 0.0, 8.0, 0.05),
    (0.9, 1.0, 0.5, 30.0, 0.4),
]

NODE_SCRIPT = """
const M = require(process.argv[1]);
const cases = JSON.parse(process.argv[2]);
const out = cases.map(([cut, open, ramp, hold, threshold, p]) => {
  const s = {carotidCut: cut, vertebralOpen: open, vertebralShare: p.vertebralShare, tOn: 2, tOff: 2 + hold, ramp};
  const run = M.simulate(p, s, 2 + hold + 15, 0.01);
  const marks = M.crossings(run, threshold);
  return {loc: marks.loc, recovery: marks.recovery, last: run.c[run.c.length - 1], atRelease: run.c[Math.round((2 + hold) / 0.01)]};
});
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_javascript_model_matches_python() -> None:
    p = Params()
    js_params = {"cbf": p.cbf * SECONDS_PER_MINUTE, "oef": p.oef, "cbv": p.cbv,
                 "kappa": p.kappa, "vertebralShare": p.vertebral_share}
    cases = [[*case, js_params] for case in CASES]
    done = subprocess.run(["node", "-e", NODE_SCRIPT, str(MODEL_JS), json.dumps(cases)],
                          capture_output=True, text=True, check=True)
    for (cut, v_open, ramp, hold, threshold), js in zip(CASES, json.loads(done.stdout)):
        choke = Choke(cut, v_open, t_on=2.0, t_off=2.0 + hold, ramp_s=ramp)
        py = simulate(p, choke, threshold, t_end=2.0 + hold + 15.0)
        for name, expected in (("loc", py.t_loc), ("recovery", py.t_recovery)):
            if expected is None:
                assert js[name] is None
            else:
                assert js[name] == pytest.approx(expected, abs=2e-3)
        assert js["last"] == pytest.approx(py.o2_fraction[-1], abs=1e-5)


def test_config_values_come_from_the_model() -> None:
    cfg = build_config()
    p = Params()
    assert cfg["physiology"]["vertebralShare"]["value"] == pytest.approx(p.vertebral_share)
    assert cfg["threshold"]["min"] < cfg["threshold"]["value"] < cfg["threshold"]["max"]
    for spec in cfg["physiology"].values():
        assert spec["min"] < spec["value"] < spec["max"]
    for s in cfg["scenarios"]:
        assert 0 <= s["carotidCut"] <= 1 and 0 <= s["vertebralOpen"] <= 1 and s["hold"] > 0


def test_built_page_is_up_to_date() -> None:
    """simulator/index.html must be what build_simulator produces now."""
    assert (ROOT / "simulator" / "index.html").read_text() == build_standalone()
