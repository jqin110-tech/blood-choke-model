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
    MITCHELL_VELOCITY_LEFT_LOC, MITCHELL_VELOCITY_LEFT_NO_LOC, ROSSEN_LOC_S, ROSSEN_RECOVERY_S, SECONDS_PER_MINUTE,
    UFC_ARM_IN_S, UFC_BY_TYPE_SECONDARY_S, UFC_CHOKE_FINISHES, UFC_CHOKE_LOC_SHARE, UFC_CHOKE_SHARE_OF_OUTCOMES,
    UFC_LOC_CI95_S, UFC_LOC_MEAN_S, UFC_LOC_N, UFC_NECK_ONLY_S, UFC_RNC_SHARE, Params,
)
from choke_model.uncertainty import INPUTS
from scripts.ufc_check import ufc_predictions

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "simulator"

# Mitchell 2012 (S3): "VNR was released 1-2 sec after ocular fixation".
MITCHELL_RELEASE_AFTER_FIXATION_S = 1.5


def slider(name: str, central: float, digits: int) -> dict[str, float]:
    """Slider limits for a physiological input: its sampled range in stage 4."""
    dist = INPUTS[name]
    low, high = (dist.low, dist.high) if hasattr(dist, "low") else (dist.mean - 2 * dist.sd, dist.mean + 2 * dist.sd)
    return {"value": round(central, digits), "min": round(low, digits), "max": round(high, digits)}


# The x-ray view stops a hold just past the longest one in S3 (23.3 s).
XRAY_MAX_HOLD_S = 25.0


def ufc_config(p: Params) -> dict:
    """UFC choke times (S12, S13) and the model's prediction for them (A14)."""
    a, b, c = ufc_predictions(p, central_threshold(p)).values()
    assert c != c, "reading C is expected to predict no loss of consciousness"
    return {
        "finishes": UFC_CHOKE_FINISHES,
        "shareOfOutcomes": UFC_CHOKE_SHARE_OF_OUTCOMES,
        "locShare": UFC_CHOKE_LOC_SHARE,
        "rncShare": UFC_RNC_SHARE,
        "n": UFC_LOC_N,
        # [mean, low, high] of the 95 % confidence interval, seconds.
        "measured": [
            {"name": f"All {UFC_LOC_N} chokes", "t": [UFC_LOC_MEAN_S, *UFC_LOC_CI95_S]},
            {"name": "Neck only", "t": list(UFC_NECK_ONLY_S)},
            {"name": "Arm trapped inside", "t": list(UFC_ARM_IN_S)},
        ],
        # Per-type means reached us second-hand and have no intervals.
        "byType": [{"name": name, "t": t} for name, t in sorted(UFC_BY_TYPE_SECONDARY_S.items(), key=lambda kv: kv[1])],
        "model": {"A": round(a, 1), "B": round(b, 1)},
    }


def xray_config(p: Params) -> dict:
    """Numbers for the x-ray view: two zones, each run through the same equation (A13)."""
    lost, awake = MITCHELL_VELOCITY_LEFT_LOC, MITCHELL_VELOCITY_LEFT_NO_LOC
    return {
        "threshold": round(central_threshold(p), 3),
        "rampS": MITCHELL_TIME_TO_MIN_VELOCITY_S,
        "maxHoldS": XRAY_MAX_HOLD_S,
        "longestHoldS": MITCHELL_NO_LOC_HOLD_S,
        "physiology": {"cbf": p.cbf * SECONDS_PER_MINUTE, "oef": p.oef, "cbv": p.cbv, "kappa": p.kappa},
        "fixationMean": MITCHELL_FIXATION_MEAN_S,
        "fixationSd": MITCHELL_FIXATION_SD_S,
        "fixationBeforeLoc": FIXATION_BEFORE_LOC_S,
        "rossenRecovery": ROSSEN_RECOVERY_S,
        "ufc": ufc_config(p),
        "scenarios": [
            {"id": "lost", "name": "Full compression: the 16 officers who lost consciousness",
             "frontFlow": round(sum(MITCHELL_VELOCITY_LEFT_LOC) / 2, 3), "backFlow": 1.0,
             "intro": f"In these officers, blood velocity in the brain's arteries fell to {lost[0]:.0%} and "
                      f"{lost[1]:.0%} of normal on the two sides (Mitchell 2012). Press the button to see "
                      "what the model predicts.",
             "outcome": "Measured: these officers lost consciousness."},
            {"id": "awake", "name": "Partial compression: the 4 officers who stayed conscious",
             "frontFlow": round(sum(MITCHELL_VELOCITY_LEFT_NO_LOC) / 2, 3), "backFlow": 1.0,
             "intro": f"In these officers, blood velocity only fell to {awake[0]:.0%} and {awake[1]:.0%} of "
                      "normal on the two sides (Mitchell 2012). Press the button to see what the model predicts.",
             "outcome": "Measured: these officers were still conscious when the hold ended at about 23 s "
                        "(Mitchell 2012)."},
        ],
    }


def build_config() -> dict:
    """Everything the pages need, computed from the Python model."""
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
        "xray": xray_config(p),
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


# Each page: template in simulator/ -> standalone page in simulator/.
PAGES = {"template.html": "index.html", "xray_template.html": "xray.html"}


def build_fragment(template: str = "template.html") -> str:
    """The page body with the model and the config inlined."""
    page = (SIM / template).read_text()
    page = page.replace("/*__MODEL__*/", (SIM / "model.js").read_text())
    page = page.replace("/*__HEAD3D__*/", (SIM / "head3d.js").read_text())
    return page.replace("/*__CONFIG__*/", json.dumps(build_config(), indent=2))


def build_standalone(template: str = "template.html") -> str:
    """A complete HTML document around the fragment, for opening locally."""
    return ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n<body>\n'
            + build_fragment(template) + "\n</body>\n</html>\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fragments", type=Path, help="also write each page without the document wrapper here")
    args = parser.parse_args()
    for template, page in PAGES.items():
        (SIM / page).write_text(build_standalone(template))
        print(f"wrote {SIM / page}")
        if args.fragments:
            args.fragments.mkdir(parents=True, exist_ok=True)
            (args.fragments / page).write_text(build_fragment(template))
            print(f"wrote {args.fragments / page}")


if __name__ == "__main__":
    main()
