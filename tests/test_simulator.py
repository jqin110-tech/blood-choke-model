"""The browser simulator must agree with the Python model and be up to date."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from choke_model.analysis import choke_for_flow, loc_time
from choke_model.model import Choke, simulate
from choke_model.params import SECONDS_PER_MINUTE, Params
from scripts.build_simulator import PAGES, anatomy_json, build_config, build_fragment, build_standalone

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


@pytest.mark.parametrize("template,page", list(PAGES.items()))
def test_built_pages_are_up_to_date(template: str, page: str) -> None:
    """Each page in simulator/ must be what build_simulator produces now."""
    assert (ROOT / "simulator" / page).read_text() == build_standalone(template)


XRAY_NODE_SCRIPT = """
const M = require(process.argv[1]);
const x = JSON.parse(process.argv[2]);
const out = x.scenarios.map((sc) => {
  // The same stepping the x-ray page does for the front of the brain.
  const s = {carotidCut: 1 - sc.frontFlow, vertebralOpen: 1, vertebralShare: 0, tOn: 0, tOff: Infinity, ramp: x.rampS};
  let c = 1, crossed = null;
  for (let k = 0; k * 0.01 < x.maxHoldS; k++) {
    const next = M.step(c, k * 0.01, 0.01, x.physiology, s);
    if (crossed === null && c >= x.threshold && next < x.threshold) crossed = (k + 1) * 0.01;
    c = next;
  }
  return {crossed, lowest: c};
});
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_xray_zones_match_python() -> None:
    """The front-of-brain zone in the x-ray view crosses when the Python model says."""
    p = Params()
    x = build_config()["xray"]
    done = subprocess.run(["node", "-e", XRAY_NODE_SCRIPT, str(MODEL_JS), json.dumps(x)],
                          capture_output=True, text=True, check=True)
    lost, awake = json.loads(done.stdout)
    for sc, js in zip(x["scenarios"], (lost, awake)):
        expected = loc_time(p, choke_for_flow(p, sc["frontFlow"], x["rampS"]), x["threshold"], t_max=x["maxHoldS"])
        if np.isnan(expected):
            assert js["crossed"] is None
            assert js["lowest"] > x["threshold"]
        else:
            assert js["crossed"] == pytest.approx(expected, abs=0.02)
    assert lost["crossed"] is not None and awake["crossed"] is None


def test_anatomy_file_is_well_formed_and_credited() -> None:
    """The 3D view's anatomy file decodes to what its headers say and keeps its credit."""
    import base64

    data = json.loads(anatomy_json())
    assert "BodyParts3D" in data["credit"] and "CC BY 4.0" in data["credit"]
    expected = {"skin", "skull", "mandible", "teeth", "spine", "cortex", "whiteMatter", "cerebellum", "brainstem", "arteries"}
    assert set(data["meshes"]) == expected
    for name, mesh in data["meshes"].items():
        points = np.frombuffer(base64.b64decode(mesh["positions"]), dtype="<u2").reshape(-1, 3)
        faces = np.frombuffer(base64.b64decode(mesh["faces"]), dtype="<u4" if mesh["wide"] else "<u2").reshape(-1, 3)
        assert len(points) == mesh["points"] and len(faces) == mesh["triangles"], name
        assert faces.max() == mesh["points"] - 1, name
        low, high = np.array(mesh["low"]), np.array(mesh["high"])
        assert np.all(low < high) and np.all(np.abs(np.concatenate([low, high])) < 450), name   # fits the 800 x 900 view
        for field in ("tag", "value"):
            if field in mesh:
                assert len(base64.b64decode(mesh[field])) == mesh["points"], name
    # Both artery groups are present, and so are both carotid trunks (tag bits 2 and 4).
    tags = np.frombuffer(base64.b64decode(data["meshes"]["arteries"]["tag"]), dtype="u1")
    assert {0, 1, 2, 4} <= set(np.unique(tags).tolist())
    # Both brain zones are present in the cortex.
    assert set(np.unique(np.frombuffer(base64.b64decode(data["meshes"]["cortex"]["tag"]), dtype="u1")).tolist()) == {0, 1}
    # The left side is the near one (+z), and the face points toward -x.
    anchors = data["anchors"]
    assert anchors["pinch"]["left"][2] > 0 > anchors["pinch"]["right"][2]
    assert {e["side"] for e in data["eyes"]} == {"left", "right"}
    assert all(e["centre"][0] < anchors["brainCentre"][0] for e in data["eyes"])


def test_built_page_carries_the_anatomy_and_its_credit() -> None:
    """The page that is published embeds the anatomy and shows the credit CC BY asks for."""
    page = build_fragment("xray_template.html")
    assert "/*__ANATOMY__*/" not in page and "/*__HEAD3D__*/" not in page
    assert '"meshes"' in page                                    # the single-file page has the data inlined
    local = build_standalone("xray_template.html")
    assert '<script src="anatomy.js"></script>' in local and '"meshes"' not in local
    assert "BodyParts3D, © The Database Center for Life Science" in page
    assert "https://creativecommons.org/licenses/by/4.0/" in page
