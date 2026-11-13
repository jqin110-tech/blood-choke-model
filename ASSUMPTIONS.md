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
- The picture, the shape and position of the two zones, and the moving
  pulses are schematic. No opened source maps which brain regions each
  artery supplies, and real brains share supply through connecting arteries.
- The anatomy in the 3D view (skin, skull, jaw, teeth, neck bones, brain and
  arteries) is a published 3D anatomy model of a reference adult male body,
  BodyParts3D, used under CC BY 4.0 (see THIRD_PARTY.md) and cut down to the
  head and neck by `scripts/build_anatomy.mjs`. It is a picture: no number
  in the model, the results or the README comes from it. Only four things
  in the picture carry model output: the colour of each zone (its oxygen
  level), the brightness and pulse speed of each zone's arteries (its flow),
  the narrowing of the carotids (how far flow is cut) and the eyelids.
- Three parts of the picture are ours, not the source model's. (1) Which
  pieces belong to the "back" zone: the cerebellum, the brainstem and the
  piece the source names the occipital lobe; everything else is "front".
  (2) Which arteries are drawn as carotid-fed or vertebral-fed: each named
  artery takes the group of the trunk it is joined to in the 3D model
  (internal carotid, or vertebral and basilar), and the communicating
  arteries that join the two systems are drawn with the front group. This
  is a rule about touching shapes, not a measured supply map. (3) Shapes we
  added: plain tubes where the source has no artery (between the top of
  each common carotid and the bottom of the internal carotid above it, and
  the lowest part of each vertebral artery), the eyes' iris, pupil and
  lids, and the leaf pattern on the cerebellum. The skin was also smoothed.
- The eye shuts when the front zone is below the threshold and opens when it
  is back above it. It is a second display of the model's conscious or
  unconscious state, not a separate result. The sign S3 timed is the eyes
  becoming fixed (a stare), which the drawing does not show; no opened source
  gives a time for the eyes closing.
- Turning the head changes nothing in the model. The 3D view needs the
  three.js library, loaded from a public CDN; without it the page falls back
  to a flat side view that was drawn by hand for this page and is not real
  anatomy.
- Rebuilding the anatomy file needs Node and three npm packages, which is
  outside the project's Python-only dependency list. That was accepted
  because the file is committed, so the model, the page build and the tests
  never run that script.
- The strip of UFC choke times under the picture shows measured values (S12,
  with the per-type values second-hand) beside the model's times from
  `scripts/ufc_check.py`. Every choke type gets the same prediction (A14).

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



**A15. Recovery is the same threshold crossed the other way (stage 5).** The
model calls the person conscious again when C/C0 climbs back above the
threshold θ it was fitted with for passing out. Nothing else is added.
- Release is a step back to normal flow. S2 says cuff deflation was
  "instantaneous"; S3 says velocity "promptly returned" to baseline.
- How long the cuff stayed on after consciousness was lost is not in the
  texts opened, so stage 5 sweeps it from 0.5 s to 100 s (S2: arrests "up to
  100 seconds") and also reports the slowest recovery the model can produce
  at all: refilling from completely empty.
- The observed "3 to 11.5 seconds" (S1/S2) is taken to be the time from
  release to the return of consciousness. The sources do not define it.
- The model fails this test (results/stage5_recovery.txt). It has one store
  of oxygen that refills as fast as blood flows back in, and no delay between
  oxygen returning and consciousness returning. A delay, or a higher
  threshold for waking than for passing out, would each need a new number and
  there is no second timed data set to test one on, so neither is added.
