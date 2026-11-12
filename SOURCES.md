# Sources

Every parameter value and every "observed" number used in this project must
appear in this file, with the citation, a link or DOI, and the exact value
taken. Quotes are copied from the page as opened during the stage 1 reading
session (12 Nov 2026). Where a value is *derived* (arithmetic on quoted
values), the arithmetic is shown and the entry is marked **derived**.

Status key: **opened** = text read this session; **partial** = only the
abstract or part of the text could be read; **not opened** = could not access.
S9–S11 were opened on 12 Nov 2026 by a second thread of this project that had
wider network access; its quotes are in `sources/FETCHED.md`, copied here.
A **secondary** value is one paper's report of another paper's result; it is
kept separate from values read in the original.

---

## S1. Rossen, Kabat & Anderson (1943), via the Smith reprint  — opened

- Original: Rossen R, Kabat H, Anderson JP. *Acute arrest of cerebral
  circulation in man.* Arch Neurol Psychiatry. 1943;50(5):510–528.
  (Citation as printed in S2's reference list. **The original 1943 paper
  itself was not opened.**)
- What was opened: a reprint titled "Acute Arrest of Cerebral Circulation in
  Man Revisited", presented by Brian A. Smith, National Dysautonomia Research
  Foundation, © 2007. The cover is dated "1942" (S2 gives 1943).
  Link: https://litfl.com/wp-content/uploads/2019/09/Smith-2007-Acute-Arrest-of-Cerebral-Circulation-in-Man-Revisited.pdf

| Quantity | Exact text | Value used |
|---|---|---|
| Method | "The KRA cuff was applied to the lower third of the neck and was inflated to a pressure of 600 mm of mercury" | cuff, 600 mmHg |
| Subjects | "In 341 tests made on 129 normal males in the age group 20-25 inclusive" | n = 129 men, 341 tests |
| Time to loss of consciousness (LOC), full arrest | "a lack of blood supply for as little as 4 seconds, or at most 10 seconds, led to a loss of consciousness." | **4–10 s** (no mean or SD given) |
| Eye fixation vs LOC | "At ½ to 1 second of time before losing consciousness, subject's eyes would become fixed." | LOC ≈ fixation + 0.5–1 s |
| Recovery after release | "The response to a re-supply of blood was also rapid, ranging from 3 to 11.5 seconds." | **3–11.5 s** |
| Vertebral flow | "The initial KRA cuff did not completely stop the blood supply in the vertebral artery" | qualitative: residual vertebral flow possible |

Notes: internal inconsistencies in the reprint (54 vs 53 St. Cloud subjects;
66 + 54 ≠ 129). No mean, SD or per-subject times for LOC are given.

## S2. Smith, Clayton & Robertson (2011) — opened

- Smith BA, Clayton EW, Robertson D. *Experimental arrest of cerebral blood
  flow in human subjects: the Red Wing studies revisited.* Perspect Biol Med.
  2011;54(2). doi:10.1353/pbm.2011.0018. PMID 21532128. PMCID PMC3848716.
  (Page range not shown in the text opened.)
- Link opened: https://pmc.ncbi.nlm.nih.gov/articles/PMC3848716/

| Quantity | Exact text | Value used |
|---|---|---|
| Cuff | "When activated, it inflated to 600 mmHg pressure around the neck in one-eighth of a second." | near-instant onset |
| Occlusion | "Sudden application of this high pressure shut off both venous and arterial blood flow simultaneously" | treat as near-complete arterial occlusion |
| Time to LOC | "interruption of blood supply for as little as 4 seconds, or at most 10 seconds, led to a loss of consciousness" | **4–10 s** (same data as S1) |
| Recovery | "The response to restoration of blood flow was also rapid, ranging from 3 to 11.5 seconds." | **3–11.5 s** (same data as S1) |
| Eye fixation | "At one-half to 1 second before losing consciousness, the subject's eyes would become fixed in mid-position." | |

S1 and S2 report the **same experiments**; they are not independent
confirmations.

## S3. Mitchell et al. (2012) — partial (abstract only)

- Mitchell JR, Roach DE, Tyberg JV, Belenkie I, Sheldon RS. *Mechanism of
  loss of consciousness during vascular neck restraint.* J Appl Physiol
  (1985). 2012;112(3):396–402. doi:10.1152/japplphysiol.00592.2011.
  PMID 22096121.
- Link opened: https://pubmed.ncbi.nlm.nih.gov/22096121/ (abstract).
  Full text at journals.physiology.org could **not** be opened.

| Quantity | Exact text | Value used |
|---|---|---|
| Subjects | "Twenty-four healthy police officers (age 35 ± 4 yr) were studied." | n = 24 |
| Time to ocular fixation | "Ocular fixation occurred in 16 subjects [time 9.5 ± 0.4 (SE) s]." | **9.5 ± 0.4 s (SE), n = 16** |
| Release | "VNR was released 1-2 s after ocular fixation." | subjects were released at about fixation, so full LOC was not always reached |
| Carotid pressures | "Pressures over the right (R) and left (L) carotid arteries were 257 ± 22 and 146 ± 18 mmHg, respectively." | context only |
| Middle cerebral artery velocity | "VNR decreased MCAVmean (R 45 ± 3 to 8 ± 4 cm/s; L 53 ± 2 to 10 ± 3 cm/s)" | used to bound the occlusion fraction (below) |
| Blood pressure, HR | "Mean arterial pressure (MAP), dP/dt, and HR did not change significantly." | arterial supply pressure assumed unchanged |
| Recovery | not reported in the abstract | — |

**Derived:**
- SD of fixation time = SE × √n = 0.4 × √16 = **1.6 s** (assumes the SE is
  over the 16 subjects who reached fixation).
- Residual MCA velocity: R 8/45 = **0.18**, L 10/53 = **0.19**. Velocity is
  not flow (vessel diameter may change), so this is an *indicator*, not a
  measurement, of residual flow. Mean velocities ± SD propagate to roughly
  0.09–0.27 (R) and 0.13–0.25 (L) using mean ± 1 SE on the during-VNR value.
- Ocular fixation is the endpoint measured here, not LOC. Combining with S1
  (LOC ½–1 s after fixation) gives an *inferred* LOC time of about
  **10–10.5 s**; this mixes two sources and is labelled as inferred.

**Conflict (unresolved).** Whinnery & Forster 2013 (S10) cite this same paper
as: "The mean time from vascular neck restraint ... to LOC defined by onset of
eye fixation in 24 healthy volunteer police officers was 7.9 s (range 6.3 to
12.2 s)". The abstract says 9.5 ± 0.4 (SE) s in 16 subjects. The full text
could not be opened (HTTP 403 from two environments), so **both values are
kept** and every comparison with Mitchell is reported against both.

## S4. Claassen, Thijssen, Panerai & Faraci (2021) — partial (first ~40% of text)

- Claassen JAHR, Thijssen DHJ, Panerai RB, Faraci FM. *Regulation of cerebral
  blood flow in humans: physiology and clinical implications of
  autoregulation.* Physiol Rev. 2021;101(4):1487–1559.
  doi:10.1152/physrev.00022.2020. PMID 33769101.
- Link opened: https://researchonline.ljmu.ac.uk/14708/3/REGULATION%20OF%20CEREBRAL%20BLOOD%20FLOW%20IN%20HUMANS%20PHYSIOLOGY%20AND%20CLINICAL%20IMPLICATIONS%20OF%20AUTOREGULATION..pdf
  (accepted manuscript; journal details from the PubMed listing)

| Quantity | Exact text | Value used |
|---|---|---|
| Global CBF | "Normal global CBF in awake humans is approximately 50 ml/100g/min" | 50 ml/100 g/min |
| Flow threshold for loss of function | "loss of function is observed below ~22 ml/100g/min" | ~22 ml/100 g/min (flow, not O2) |
| Speed of LOC | "often within 10 seconds after the onset of hypoperfusion or ischemia" | qualitative check |
| Share of O2 | "consuming ~20% of the available O2" | context only |

## S5. Ito et al. (2004) — partial (abstract only)

- Ito H, Kanno I, Kato C, Sasaki T, Ishii K, Ouchi Y, Iida A, Okazawa H,
  Hayashida K, Tsuyuguchi N, Ishii K, Kuwabara Y, Senda M. *Database of
  normal human cerebral blood flow, cerebral blood volume, cerebral oxygen
  extraction fraction and cerebral metabolic rate of oxygen measured by
  positron emission tomography with 15O-labelled carbon dioxide or water,
  carbon monoxide and oxygen: a multicentre study in Japan.* Eur J Nucl Med
  Mol Imaging. 2004;31(5):635–643. doi:10.1007/s00259-003-1430-8.
  PMID 14730405. (Volume, pages and PMID from the Europe PMC record.)
- Link opened: https://www.springermedicine.com/database-of-normal-human-cerebral-blood-flow-cerebral-blood-volu/20711574

| Quantity | Exact text | Value used |
|---|---|---|
| Subjects | "Subjects comprised 70 healthy volunteers (43 men and 27 women; mean age 51.8±15.1 years)." | n = 70 |
| Cortical values | "CBF=44.4±6.5 ml 100 ml−1 min−1; CBV=3.8±0.7 ml 100 ml−1; OEF=0.44±0.06; CMRO2=3.3±0.5 ml 100 ml−1 min−1." | CBF 44.4 ± 6.5; CBV 3.8 ± 0.7; OEF 0.44 ± 0.06; CMRO2 3.3 ± 0.5 |

Units are per 100 ml of tissue (PET), not per 100 g; S4 is per 100 g. Brain
density is close to 1 g/ml, but no density value has been sourced yet, so the
two are kept as stated and the difference is noted as a limitation.

**Derived (Fick principle, CMRO2 = CBF × OEF × CaO2):**
arterial O2 content CaO2 = 3.3 / (0.44 × 44.4) = **0.169 ml O2 per ml blood**
(≈ 16.9 ml/dl). This uses only S5 numbers; it has not yet been checked against
an independently sourced CaO2.

## S6. Malm et al. (2021) — partial

- Malm J, Birnefeld J, Zarrinkoob L, Wåhlin A, Eklund A. *Hemodynamic
  disturbances in posterior circulation stroke: 4D flow magnetic resonance
  imaging added to computed tomography angiography.* Front Neurosci.
  2021;15:656769. doi:10.3389/fnins.2021.656769.
- Link opened: https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2021.656769/pdf

| Quantity | Exact text / table | Value used |
|---|---|---|
| Total CBF, controls | "587 ± 169 ml/min" (controls, n = 15, healthy elderly) | 587 ± 169 ml/min |
| Flow split, controls (Table 2, % of tCBF) | ICA R+L 73.7 ± 3.7; VA R+L 26.3 ± 3.7 | **vertebral share 26.3 ± 3.7 %** |

Caveat: controls are elderly; tCBF is defined as ICA + VA flow.

## S7. Ford et al. (2005) — opened (conference abstract)

- Ford MD, Alperin N, Lee SH, Holdsworth DW, Steinman DA. *Characterization
  of normal cerebrovascular volumetric flow rate dynamics by PC-MRI.* Proc
  Intl Soc Mag Reson Med. 2005;13:1741.
- Link opened: https://cds.ismrm.org/protected/05MProceedings/PDFfiles/01741.pdf

| Quantity | Exact text | Value used |
|---|---|---|
| ICA vs VA flow | "mean flow rates in the internal carotid and vertebral arteries (274±56 ml/min vs. 89±44 ml/min)" | per-vessel means |
| Subjects | "normal subjects (16M:2F; 30±9.2 years)" | n = 18 |

**Derived:** vertebral share = 89 / (274 + 89) = **0.245**, assuming both
figures are per vessel with left/right symmetric. Not peer-reviewed in full;
used only as a second estimate beside S6.

## S8. Henry, Gauer, Kety & Kramer (1951) — opened

- Henry JP, Gauer OH, Kety SS, Kramer K. *Factors maintaining cerebral
  circulation during gravitational stress.* J Clin Invest. 1951;30(3):292–300.
  doi:10.1172/JCI102443.
- Link opened: https://www.jci.org/articles/view/102443/version/1/pdf/render.pdf

| Quantity | Exact text | Value used |
|---|---|---|
| Pressure at LOC | "Consciousness is usually lost when the mean cerebral blood pressure falls to 25 mm. Hg" | context only (pressure, not O2) |

## S9. Zarrinkoob et al. (2015) — opened (full text)

- Zarrinkoob L, Ambarki K, Wåhlin A, Birgander R, Eklund A, Malm J. *Blood
  flow distribution in cerebral arteries.* J Cereb Blood Flow Metab.
  2015;35(4):648–654. doi:10.1038/jcbfm.2014.241. PMID 25564234.
  PMCID PMC4420884.
- Link opened: https://pmc.ncbi.nlm.nih.gov/articles/PMC4420884/

| Quantity | Exact text | Value used |
|---|---|---|
| Subjects | "49 subjects included in the HY group (mean age±s.d., 25±2 years; 27 women) and 45 subjects in the HE group (mean age±s.d., 71±4 years; 23 women)" | n = 94 |
| Definition | "Total cerebral blood flow was defined as BFR in the internal carotid plus vertebral arteries" | tCBF = ICA + VA |
| Split | "Carotid/vertebral distribution was 72%/28% and was not related to age, sex, or brain volume." | 72 / 28 % |
| Split SD | "independent of age (HY: 72/28%±4%, HE: 72/28%±4%, P =0.7)" | **vertebral share 28 ± 4 %** |
| Absolute | "sum of the right and left ICA) was 515±96 mL/min ... (sum of the right and left VA), the flow rate was 202±44 mL/min (28% of tCBF)" | ICA 515 ± 96; VA 202 ± 44 mL/min |
| tCBF | "Total cerebral blood flow (717 ± 123 mL/min)" | 717 ± 123 mL/min |
| Perfusion | "(HY: 60±8 mL/min/100 mL; HE: 56±7 mL/min/100 mL, P =0.04)" | context: higher than S5's PET value |

This is the largest sample for the flow split, and its young group (25 ± 2 y)
is the closest match to Rossen's subjects (age 20–25), so it sets the central
vertebral share. Note the perfusion figure (56–60 mL/min/100 mL, MRI, whole
brain inflow / brain volume) is higher than S5's 44.4 (PET, cortical); the
model keeps S5 because CBF, OEF, CBV and CMRO2 must come from one consistent
set for the Fick derivation (A8). The disagreement is a stated limitation.

## S10. Whinnery & Forster (2013) — opened (full text). G-force study, not neck compression

- Whinnery JE, Forster EM. *The +Gz-induced loss of consciousness curve.*
  Extreme Physiol Med. 2013;2:19. doi:10.1186/2046-7648-2-19.
  PMCID PMC3710154.
- Link opened: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3710154/fullTextXML

| Quantity | Exact text | Value used |
|---|---|---|
| G-LOC time | "for onset rates ≥ 1.0 G/s, G-LOC will occur in a mean time of 9.10 s" | context only (different mechanism of flow loss) |
| Rossen mean, **secondary** | "Rossen acutely arrested cerebral circulation in 74 humans using a cervical pressure cuff with the mean time of 6.41-6.91 s" | secondary mean LOC 6.41–6.91 s (from reanalyses not opened) |
| Mitchell, **secondary** | "to LOC defined by onset of eye fixation in 24 healthy volunteer police officers was 7.9 s (range 6.3 to 12.2 s)" | secondary: 7.9 s, range 6.3–12.2 s (conflicts with S3) |
| Rossen DOI as printed | 10.1001/archneurpsyc.1943.02290230022002 | not opened |

## S11. Whinnery, Forster & Rogers (2014) — opened (full text). G-force study

- Whinnery JE, Forster EM, Rogers PB. *The +Gz recovery of consciousness
  curve.* Extreme Physiol Med. 2014;3:9. doi:10.1186/2046-7648-3-9.
  PMCID PMC4007145.
- Link opened: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4007145/fullTextXML

| Quantity | Exact text | Value used |
|---|---|---|
| G-LOC recovery | "Mean time from loss to return of consciousness for 760 episodes of consciousness recovery was 10.4 ± 5.1 s; minimum 1 s; maximum 38 s." | context for stage 5 (measured from LOC, includes time still under G) |
| Minimum recovery | "there is a minimum time (mean 8.29 ± 3.84 s) required for recovery of consciousness when complete loss of consciousness occurs." | context for stage 5 |
| Rossen recovery, **secondary** | "For their 28 LOC episodes defining their ABSINCAP equivalent, the mean was 6.14 s" | secondary mean 6.14 s, n = 28 |

## Bibliographic records only (no values taken)

- Kety SS, Schmidt CF. *The nitrous oxide method for the quantitative
  determination of cerebral blood flow in man: theory, procedure and normal
  values.* J Clin Invest. 1948;27(4):476–483. doi:10.1172/JCI101994.
  PMID 16695568.
- Kety SS, Schmidt CF. *The effects of altered arterial tensions of carbon
  dioxide and oxygen on cerebral blood flow and cerebral oxygen consumption of
  normal young men.* J Clin Invest. 1948;27(4):484–492.
  doi:10.1172/JCI101995. PMID 16695569.
- Lennox WG, Gibbs FA, Gibbs EL. *Relationship of unconsciousness to cerebral
  blood-flow and to anoxaemia.* Arch Neurol Psychiatry. 1935;34:1001.
  (Citation seen in a search listing only.)

---

## Ranges carried into the model

| Parameter | Range | From |
|---|---|---|
| Baseline CBF | 44.4 ± 6.5 (PET, per 100 ml) to ~50 (per 100 g) | S5, S4 |
| CMRO2 | 3.3 ± 0.5 ml O2/100 ml/min | S5 |
| OEF | 0.44 ± 0.06 | S5 |
| Cerebral blood volume (O2 store) | 3.8 ± 0.7 ml/100 ml | S5 |
| Vertebral share of flow | central 0.28 (S9); range 0.226 – 0.32 = union of S6 (0.263 ± 0.037), S7 (0.245) and S9 (0.28 ± 0.04) | S9, S6, S7 |
| Residual flow during neck restraint | ~0.09 – 0.27 of baseline (velocity indicator) | S3 (derived) |
| Observed time to LOC, full arrest | 4 – 10 s | S1/S2 |
| Observed time to ocular fixation, neck restraint | 9.5 ± 1.6 s (SD, derived) | S3 |
| Same study, as cited by S10 (**secondary, conflicting**) | 7.9 s, range 6.3 – 12.2 s | S10 |
| Rossen means (**secondary**) | LOC 6.41 – 6.91 s; recovery 6.14 s | S10, S11 |
| Observed recovery | 3 – 11.5 s | S1/S2 |

## Gaps (not filled; awaiting a source)

1. **LOC threshold as an oxygen level.** Still no opened source, after a
   second search from an environment with wider access. Lennox, Gibbs & Gibbs
   (1935) is the best lead and is not reachable. The threshold stays fitted
   (ASSUMPTIONS.md, A6).
2. **Mitchell (2012) full text** (HTTP 403 from two environments). Needed to
   resolve the 9.5 s vs 7.9 s conflict, and for LOC and recovery times.
3. **Kety & Schmidt (1948)** values: citations verified, PDFs not reachable.
4. **Independent arterial O2 content** to check the derived 0.169 ml/ml.
5. **Rossen (1943) original**: only the reprint (S1) and the review (S2) were
   opened.
