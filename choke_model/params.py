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
VERTEBRAL_SHARE = Range(
    0.263, 0.245, 0.263 + 0.037,
    "S6 Malm 2021: VA 26.3 +/- 3.7 % of tCBF; low end S7 Ford 2005 derived 0.245",
)

# Observed values the model is compared with (never used as inputs, except
# the Rossen LOC times, which are used to FIT the threshold; see A6).
ROSSEN_LOC_S = (4.0, 10.0)            # S1/S2: "as little as 4 seconds, or at most 10 seconds"
ROSSEN_RECOVERY_S = (3.0, 11.5)       # S1/S2: "ranging from 3 to 11.5 seconds"
MITCHELL_FIXATION_MEAN_S = 9.5        # S3: 9.5 +/- 0.4 (SE) s, n = 16
MITCHELL_FIXATION_SD_S = 0.4 * 4.0    # S3 derived: SE x sqrt(16)
MITCHELL_RESIDUAL_VELOCITY = (8 / 45, 10 / 53)  # S3 derived: R and L MCA velocity ratios
FIXATION_BEFORE_LOC_S = (0.5, 1.0)    # S1/S2: eyes fixed 1/2 to 1 s before LOC


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
