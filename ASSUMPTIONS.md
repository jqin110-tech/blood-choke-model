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
checked against an independently measured Ca (Gap 4). A side effect: once
Ca is tied to the other three, CMRO2 cancels out of the equation for C/C0, so
the predicted times do not depend on CMRO2 at all. That is a property of this
assumption, not a finding about the brain.

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

**A12. How the Monte Carlo samples each input (stage 4).** The sources give
a mean and an SD, not a distribution, so the shapes are our choice.
- Inputs published as mean ± SD (CBF, CMRO2, OEF, CBV from S5; vertebral
  share from S9; onset time from S3) are drawn from a normal distribution cut
  off at ± 2 SD, and at zero for durations and velocities.
- They are drawn independently. Real people's CBF, OEF and CMRO2 are linked,
  and no opened source gives the correlations, so the spread is probably too
  wide in some directions.
- The Rossen time the threshold is fitted to is drawn evenly from 4 to 10 s,
  and the vertebral flow his cuff left evenly from 0 to 1 (A7), because the
  sources give only those limits.
- κ has no source and is drawn evenly on a log scale from 0.01 to 0.5, purely
  to test whether it matters.
- The Mitchell velocities are drawn at the level of the group mean (mean ±
  SEM), because individual values are not published. This understates how
  much individuals differ.
- "Inside the observed range" means inside 6.3–12.2 s, the individual range
  read from Mitchell's Figure 6.

**A13. The x-ray view splits the brain into two zones (illustration).** To
show blood failing to reach part of the brain, `simulator/xray.html` runs the
same equation twice: once for a "front" zone fed by the carotids and once for
a "back" zone fed by the vertebrals, with no oxygen passing between them.
- Flow left in the front zone is the mean middle cerebral artery velocity
  fraction measured in S3 (0.185 for the officers who lost consciousness,
  0.43 for those who did not). Flow in the back zone stays at 100 %, because
  S3 judged vertebral compromise unlikely but could not measure it.
- Both zones use the same per-volume physiology and the same fitted
  threshold, and the model is called unconscious when the front zone crosses
  it. S3 supports that loosely: its subjects lost consciousness with carotid
  flow cut and vertebral flow believed intact.
- This is reading A of A11 applied to the carotid-fed part of the brain only.
  It is **not** used for any number in the results; stages 3 and 4 still use
  the one-box model.
- The drawing itself, the shape and position of the two zones, and the
  moving dots are schematic. No opened source maps which brain regions each
  artery supplies, and real brains share supply through connecting arteries.
- The anatomical detail (skull, teeth, neck bones, the folds of the brain and
  the fine arterial branches) is decoration. It was drawn for the page, not
  taken from an opened source, and most of the folds and fine branches are
  placed by a seeded random generator. Only two things in the picture carry
  model output: the colour of each zone (its oxygen level) and the brightness
  and dot speed of each zone's arteries (its flow).
- The eye shuts when the front zone is below the threshold and opens when it
  is back above it. It is a second display of the model's conscious or
  unconscious state, not a separate result. The sign S3 timed is the eyes
  becoming fixed (a stare), which the drawing does not show; no opened source
  gives a time for the eyes closing.

**A14. A choke in a fight cuts brain blood flow the way the laboratory neck
restraint did.** The UFC study (S12) timed loss of consciousness from video;
nobody measured blood flow in the cage. For the UFC comparison the model
borrows the flow left, and the 1.6 s it takes to get there, from the
laboratory study of police officers (S3), read the same three ways as in A11.
- The clock starts when S12's panel judged the choke "established". The
  model's clock starts when flow begins to fall. These are assumed to be the
  same moment.
- The fighters were mid-fight: breathing hard, with a raised heart rate, and
  resisting. The model uses resting physiology (S5) and lets nothing respond
  (A10). No opened source gives brain blood flow or oxygen use during a fight.
- **Every kind of choke gets the same inputs.** No opened source measures
  which vessels each technique compresses, or how much (SOURCES.md, Gap 7).
  S12 itself found nearly the same time for chokes with and without an arm
  inside (8.9 s and 9.0 s), which is what one shared mechanism would give,
  but that agreement is not evidence the model's inputs are right.
- Compression of the jugular veins and a blood-pressure reflex from the neck
  may also contribute (S15, secondary). The model has neither (A4, A10).
- Chokes that close the windpipe instead of the arteries are outside the
  model: it has no lungs and holds blood oxygen constant (Gap 8).

