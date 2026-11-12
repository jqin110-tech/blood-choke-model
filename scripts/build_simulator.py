"""Build the interactive simulator page from the repo's own numbers.

Every number the page shows is injected here from choke_model/, so the page
cannot drift from the Python model. Writes simulator/index.html, a single
self-contained file you can open in a browser.
Run from the repo root:  python -m scripts.build_simulator
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from choke_model.analysis import carotid_cut_for_flow, central_threshold, loc_time, rossen_threshold_corners
from choke_model.model import Choke
from choke_model.params import (
    FIXATION_BEFORE_LOC_S, MITCHELL_FIXATION_MEAN_S, MITCHELL_FIXATION_RANGE_S,
    MITCHELL_FIXATION_SD_S, MITCHELL_NO_LOC_HOLD_S, MITCHELL_TIME_TO_MIN_VELOCITY_S,
    MITCHELL_VELOCITY_LEFT_NO_LOC, ROSSEN_LOC_S, ROSSEN_RECOVERY_S, SECONDS_PER_MINUTE, Params,
)
from choke_model.uncertainty import INPUTS

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "simulator"

# Mitchell 2012 (S3): "VNR was released 1-2 sec after ocular fixation".
MITCHELL_RELEASE_AFTER_FIXATION_S = 1.5


def slider(name: str, central: float, digits: int) -> dict[str, float]:
    """Slider limits for a physiological input: its sampled range in stage 4."""
    dist = INPUTS[name]
    low, high = (dist.low, dist.high) if hasattr(dist, "low") else (dist.mean - 2 * dist.sd, dist.mean + 2 * dist.sd)
    return {"value": round(central, digits), "min": round(low, digits), "max": round(high, digits)}


def build_config() -> dict:
    """Everything the page needs, computed from the Python model."""
    p = Params()
    corners = rossen_threshold_corners(p)
    no_loc_flow = sum(MITCHELL_VELOCITY_LEFT_NO_LOC) / 2
    mitchell_hold = MITCHELL_FIXATION_MEAN_S + MITCHELL_RELEASE_AFTER_FIXATION_S
    mitchell_model_loc = loc_time(p, Choke(1.0, ramp_s=MITCHELL_TIME_TO_MIN_VELOCITY_S), central_threshold(p))
    return {
        "physiology": {
            "cbf": slider("cbf", p.cbf * SECONDS_PER_MINUTE, 1),
            "oef": slider("oef", p.oef, 2),
            "cbv": slider("cbv", p.cbv, 1),
            "vertebralShare": slider("vertebral_share", p.vertebral_share, 2),
            "kappa": slider("kappa", p.kappa, 2),
        },
        "threshold": {
            "value": round(central_threshold(p), 3),
            "min": round(min(corners.values()), 3),
            "max": round(max(corners.values()), 3),
        },
        "observed": {
            "rossenLoc": ROSSEN_LOC_S,
            "rossenRecovery": ROSSEN_RECOVERY_S,
            "mitchellFixationMean": MITCHELL_FIXATION_MEAN_S,
            "mitchellFixationSd": MITCHELL_FIXATION_SD_S,
            "mitchellFixationRange": MITCHELL_FIXATION_RANGE_S,
            "fixationBeforeLoc": FIXATION_BEFORE_LOC_S,
        },
        # Each scenario sets the four occlusion sliders. Hold times marked
        # "illustrative" are our choice; the others come from the study.
        "scenarios": [
            {"id": "carotid", "name": "Carotids shut, vertebrals open",
             "note": "Both carotids fully closed and the vertebral arteries untouched (assumption A4). "
                     "Hold time is illustrative.",
             "carotidCut": 1.0, "vertebralOpen": 1.0, "ramp": 0.0, "hold": 15.0},
            {"id": "rossen", "name": "Rossen 1943 neck cuff",
             "note": "Cuff at 600 mmHg. How much vertebral flow it left is unknown, so half is assumed. "
                     "Hold time is illustrative.",
             "carotidCut": 1.0, "vertebralOpen": 0.5, "ramp": 0.0, "hold": ROSSEN_LOC_S[1]},
            {"id": "mitchell-loc", "name": "Mitchell 2012, lost consciousness",
             "note": "Reading B: carotids shut, vertebrals normal. The real hold ended 1 to 2 s after eye "
                     f"fixation, at about {mitchell_hold:.1f} s. The model would cross at {mitchell_model_loc:.1f} s, "
                     "so it runs a little late here.",
             "carotidCut": 1.0, "vertebralOpen": 1.0, "ramp": MITCHELL_TIME_TO_MIN_VELOCITY_S,
             "hold": mitchell_hold},
            {"id": "mitchell-awake", "name": "Mitchell 2012, stayed conscious",
             "note": "Reading A: whole-brain flow falls like the measured velocity in the four "
                     "officers who did not lose consciousness.",
             "carotidCut": round(carotid_cut_for_flow(p, no_loc_flow), 2), "vertebralOpen": 1.0,
             "ramp": MITCHELL_TIME_TO_MIN_VELOCITY_S, "hold": MITCHELL_NO_LOC_HOLD_S},
        ],
    }


def build_fragment() -> str:
    """The page body with the model and the config inlined."""
    page = (SIM / "template.html").read_text()
    page = page.replace("/*__MODEL__*/", (SIM / "model.js").read_text())
    return page.replace("/*__CONFIG__*/", json.dumps(build_config(), indent=2))


def build_standalone() -> str:
    """A complete HTML document around the fragment, for opening locally."""
    return ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n<body>\n'
            + build_fragment() + "\n</body>\n</html>\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragment", type=Path, help="also write the page without the document wrapper")
    args = parser.parse_args()
    (SIM / "index.html").write_text(build_standalone())
    print(f"wrote {SIM / 'index.html'}")
    if args.fragment:
        args.fragment.parent.mkdir(parents=True, exist_ok=True)
        args.fragment.write_text(build_fragment())
        print(f"wrote {args.fragment}")


if __name__ == "__main__":
    main()
