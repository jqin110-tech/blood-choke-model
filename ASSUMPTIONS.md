# Model assumptions

Every simplification in the model, why it was made, and whether a source
backs it. Source tags refer to [SOURCES.md](SOURCES.md).

**A1. One well-mixed compartment.** The brain is treated as one box of
tissue with one oxygen level. Real brains have regions with different flow
and oxygen use, and the carotid and vertebral arteries feed different regions
(the vertebrals mainly feed the back of the brain). *Why:* the observed data
(S1–S3) are whole-person outcomes, so a regional model could not be checked.

**A2. The oxygen store is the blood inside the brain.** C(t) is the oxygen in
the cerebral blood volume (S5: 3.8 ml/100 ml), and blood leaving the box has
oxygen content C/V. Oxygen dissolved in tissue and bound to proteins is
ignored, and haemoglobin's S-shaped binding curve is not modelled (content is
used directly, not partial pressure). *Why:* no opened source gives a tissue
store; the blood store already accounts for most of the observed time scale.

**A3. Units per 100 ml tissue.** PET values (S5) are per 100 ml; S4 gives
global flow per 100 g. They are not converted because no brain density value
has been sourced; S5 is used for all inputs.

**A4. A choke removes carotid flow only; vertebral flow is unchanged.** Flow
during a choke is F0 × [(1 − v)(1 − α) + v·β], with v the vertebral share
(S9, S6, S7), α the fraction of carotid flow removed, and β = 1 (vertebrals
open). Blood pressure is assumed unchanged (S3: MAP did not change
significantly). Venous outflow blockage is ignored.

**A5. Consumption depends on available oxygen (Michaelis–Menten).**
M(C) = CMRO2 × (1 + κ) C / (κ C0 + C), so M equals the sourced CMRO2 at
baseline and falls toward zero as oxygen runs out. **κ = 0.1 has no source.**
It only matters once oxygen is already low, and stage 4 will test how much it
changes the predictions.

**A6. Loss of consciousness happens when C/C0 falls below a threshold θ.**
No opened source gives θ as an oxygen level (SOURCES.md, Gap 1). Following
Joshua's decision, θ is **fitted** to the Rossen full-occlusion times
(S1/S2: 4–10 s) and will be replaced if a measured value is found. The
Mitchell 2012 data (S3) are **not** used in the fit, so they are a fair test.

**A7. The Rossen cuff blocked the carotids fully and the vertebrals
partly.** S1 says the cuff "did not completely stop the blood supply in the
vertebral artery", and S2 says it shut off "both venous and arterial blood
flow". So the fraction of vertebral flow left, β, is somewhere from 0 to 1,
and the fit keeps that whole range.

**A8. Arterial oxygen content comes from the Fick principle.**
Ca = CMRO2 / (OEF × CBF) (S5 derived, about 0.169 ml O2/ml). This makes
every sampled parameter set start at a true steady state. It has not been
checked against an independently measured Ca (Gap 4).

**A9. Flow changes as a step, or as a straight-line ramp.** For Rossen the
occlusion is a step: S2 reports that the cuff inflated "in one-eighth of a
second". For neck restraint, S3 measured 1.6 ± 0.3 s (SEM) for velocity to
reach its minimum, so the Mitchell comparison is reported both with a step
and with flow falling in a straight line over 1.6 s. The straight-line shape
is our assumption; only the duration is sourced. Release is always a step
(S3: velocity "promptly returned" to baseline).

**A10. Nothing else responds.** No autoregulation, no change in heart rate,
breathing or blood oxygen during the event. S1 reports no marked pulse change
for arrests up to 30 s, and S3 reports no significant change in HR or MAP.

**A11. Whole-brain flow during neck restraint is not known, so three
readings are kept.** S3 measured velocity in the middle cerebral arteries
only, which are fed mainly by the carotids, and could not measure vertebral
flow. Velocity is also not flow (S3 lists this as a limitation). The model
needs one whole-brain number (A1), so stage 3 reports three: (A) the whole
brain falls like the measured velocity, the lowest reading; (B) carotids
shut and vertebrals normal; (C) the carotids pass the measured fraction and
the vertebrals are normal, the highest reading. No source says which is
right. Under reading C the model predicts no loss of consciousness in
subjects who did lose it, which points at A1: a one-box model cannot
represent the front of the brain running out of oxygen while the back is
still supplied.
