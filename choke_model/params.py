"""Model parameters, each tagged with the source in SOURCES.md it comes from.

Units throughout the model: volumes and flows are per 100 ml of brain tissue,
oxygen is in ml O2, and time is in seconds. PET values in S5 are per 100 ml;
S4's 50 ml/100 g/min is kept only as a range note (see ASSUMPTIONS.md, A3).
"""

from __future__ import annotations

from dataclasses import dataclass, replace

SECONDS_PER_MINUTE = 60.0


@dataclass(frozen=True)
class Range:
    """A sourced central value with a lower and upper bound."""

    central: float
    low: float
    high: float
    source: str


# Each range is mean +/- 1 SD as reported, unless the note says otherwise.
CBF = Range(44.4, 44.4 - 6.5, 44.4 + 6.5, "S5 Ito 2004: CBF 44.4 +/- 6.5 ml/100 ml/min")
CMRO2 = Range(3.3, 3.3 - 0.5, 3.3 + 0.5, "S5 Ito 2004: CMRO2 3.3 +/- 0.5 ml O2/100 ml/min")
OEF = Range(0.44, 0.44 - 0.06, 0.44 + 0.06, "S5 Ito 2004: OEF 0.44 +/- 0.06")
CBV = Range(3.8, 3.8 - 0.7, 3.8 + 0.7, "S5 Ito 2004: CBV 3.8 +/- 0.7 ml/100 ml")
# Central from the largest study (S9, n = 94). The range is the union of the
# three sources' mean +/- 1 SD: S6 0.263 +/- 0.037, S7 0.245, S9 0.28 +/- 0.04.
VERTEBRAL_SHARE = Range(
    0.28, 0.263 - 0.037, 0.28 + 0.04,
    "S9 Zarrinkoob 2015: VA 28 +/- 4 % of tCBF; low end S6 Malm 2021 26.3 - 3.7 %",
)

# Observed values the model is compared with (never used as inputs, except
# the Rossen LOC times, which are used to FIT the threshold; see A6).
ROSSEN_LOC_S = (4.0, 10.0)            # S1/S2: "as little as 4 seconds, or at most 10 seconds"
ROSSEN_RECOVERY_S = (3.0, 11.5)       # S1/S2: "ranging from 3 to 11.5 seconds"
# Mitchell 2012 (S3), full text. Held out from the threshold fit.
MITCHELL_FIXATION_MEAN_S = 9.5                   # Table 2: 9.5 +/- 0.4 (SEM) s, n = 16
MITCHELL_FIXATION_SD_S = 0.4 * 4.0               # derived: SEM x sqrt(16)
MITCHELL_FIXATION_RANGE_S = (6.3, 12.2)          # individual points, read from Figure 6
MITCHELL_VELOCITY_LEFT_LOC = (1 - 0.83, 1 - 0.80)     # R, L: "R 83%, L 80%" decrease
MITCHELL_VELOCITY_LEFT_NO_LOC = (1 - 0.74, 1 - 0.40)  # R, L: "74% ... only a 40% reduction"
MITCHELL_NO_LOC_HOLD_S = 23.3                    # Table 2: Instructor Stop, 23.3 +/- 2.1 (SEM) s, n = 4
MITCHELL_TIME_TO_MIN_VELOCITY_S = 1.6            # Table 2: 1.6 +/- 0.3 (SEM) s, n = 16
MITCHELL_TIME_TO_MIN_VELOCITY_SD_S = 0.3 * 4.0   # derived: SEM x sqrt(16)
NJEMANZE_VELOCITY_THRESHOLD = 0.5                # secondary, via S3: LOC if velocity falls > 50 %
ROSSEN_LOC_MEAN_SECONDARY_S = (6.41, 6.91)       # S10: secondary mean, reanalysis not opened
ROSSEN_RECOVERY_MEAN_SECONDARY_S = 6.14          # S11: secondary mean, n = 28
FIXATION_BEFORE_LOC_S = (0.5, 1.0)    # S1/S2: eyes fixed 1/2 to 1 s before LOC
# Recovery (stage 5). Rossen's 3-11.5 s above is the only timed recovery data.
ROSSEN_MAX_ARREST_S = 100.0           # S2 abstract: "cessation of blood flow for up to 100 seconds"
ROSSEN_CORNEAL_RETURN_S = (5.0, 10.0)  # S2: corneal reflex "returned within 5 to 10 seconds after cuff release"
MITCHELL_RELEASE_AFTER_FIXATION_S = (1.0, 2.0)   # S3: released "1-2 sec after ocular fixation"

# Chokes in UFC fights, timed from video (S12, abstract). Held out from the fit.
UFC_LOC_MEAN_S = 9.0                  # "mean time from the establishment of a choke to LOC of 9.0 s"
UFC_LOC_CI95_S = (8.3, 9.9)           # "[95% CI = 8.3, 9.9]", n = 81 chokes
UFC_LOC_N = 81
UFC_NECK_ONLY_S = (8.9, 8.0, 10.2)    # mean, 95 % CI low, high: "neck-only M = 8.9 s [95% CI = 8.0-10.2]"
UFC_ARM_IN_S = (9.0, 8.1, 10.3)       # "arm-in M = 9.0 s [8.1-10.3]"
# Per-technique means from web write-ups of S12, NOT from an opened journal
# page. No confidence intervals. Shown for context, never used as a test.
UFC_BY_TYPE_SECONDARY_S = {
    "Bulldog choke": 6.2, "Arm triangle": 7.2, "D'Arce choke": 8.6, "Headlock": 8.8, "Guillotine": 8.9,
    "Rear naked choke": 8.9, "North-south choke": 9.4, "Anaconda choke": 9.5, "Triangle choke": 9.5,
    "Arm-in guillotine": 10.2, "Von Flue choke": 10.5,
}
# Fight-ending chokes in UFC history (S13, abstract). Context only.
UFC_CHOKE_FINISHES = 904              # "there were 904 such chokes"
UFC_CHOKE_SHARE_OF_OUTCOMES = 0.155   # "comprising 15.5% of fight outcomes"
UFC_CHOKE_LOC_SHARE = 0.11            # "11% resulted in loss of consciousness"
UFC_RNC_SHARE = 0.491                 # rear naked choke: "49.1% of the total choke finishes"


@dataclass(frozen=True)
class Params:
    """One set of physiological parameters (per 100 ml tissue, seconds)."""

    cbf: float = CBF.central / SECONDS_PER_MINUTE        # ml blood / s
    cmro2: float = CMRO2.central / SECONDS_PER_MINUTE    # ml O2 / s
    oef: float = OEF.central                             # dimensionless
    cbv: float = CBV.central                             # ml blood
    vertebral_share: float = VERTEBRAL_SHARE.central     # fraction of flow
    kappa: float = 0.1  # A5: half-saturation as a fraction of baseline O2. NO SOURCE.

    @property
    def arterial_o2(self) -> float:
        """Arterial O2 content (ml O2 / ml blood), from the Fick principle (S5 derived)."""
        return self.cmro2 / (self.oef * self.cbf)

    @property
    def baseline_o2(self) -> float:
        """Baseline O2 in the brain compartment (ml O2 / 100 ml tissue).

        Equal to CBV x venous O2 content, where venous content = Ca (1 - OEF).
        """
        return self.cbv * self.arterial_o2 * (1.0 - self.oef)

    def with_(self, **changes: float) -> "Params":
        """Return a copy with some fields changed."""
        return replace(self, **changes)
