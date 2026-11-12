# Fetched sources (helper thread, 12 Nov 2026)

Rules followed: every quote below was copied from text actually downloaded in
this session. Nothing is filled from memory. Status key: **opened** (full
text read), **abstract only**, **record only** (bibliographic record read),
**failed** (could not open). The main repo was not edited.

Access notes: pmc.ncbi.nlm.nih.gov served one article (Zarrinkoob) and then
returned a reCAPTCHA page; I did not try to get around it. JCI PDFs redirect
to `dm5migu4zj3pb.cloudfront.net`, which is blocked by the network policy.
journals.physiology.org returns 403. europepmc.org (`?pdf=render`) and
cambridge.org are blocked. The Europe PMC REST API on www.ebi.ac.uk works.

---

## 1. Mitchell et al. (2012) — abstract only (full text failed)

- Mitchell JR, Roach DE, Tyberg JV, Belenkie I, Sheldon RS. Mechanism of loss
  of consciousness during vascular neck restraint. J Appl Physiol (1985).
  2012;112(3):396–402. doi:10.1152/japplphysiol.00592.2011. PMID 22096121.
- Full text: https://journals.physiology.org/doi/full/10.1152/japplphysiol.00592.2011
  and `/doi/pdf/...` both returned **HTTP 403**. Europe PMC lists it as
  "Subscription required"; no open copy.
- Abstract re-opened via Europe PMC REST
  (https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:22096121&resultType=core).
  It matches SOURCES.md S3 exactly. One sentence not in S3:
  - "VNR decreased MCAVmean (R 45 ± 3 to 8 ± 4 cm/s; L 53 ± 2 to 10 ± 3 cm/s) and SV (92 ± 4 to 75 ± 4 ml; P < 0.001)."
  - "The small decrease in CO (9.6 to 7.5 l/min) observed would not seem to be important as there was no change in MAP."
- **Still missing:** time to full LOC, recovery time, occlusion duration.
- **Conflict found (see item 6):** Whinnery & Forster (2013) cite Mitchell as
  "7.9 s (range 6.3 to 12.2 s)" in 24 officers, while the abstract says
  9.5 ± 0.4 (SE) s in 16. I could not open the full text to resolve this, so
  both are recorded and neither should be treated as settled.

## 2. Brain O2 level at loss of consciousness — failed (gap stays open)

- No opened source gives a tissue PO2, jugular venous PO2/saturation or O2
  content at which consciousness is lost.
- Lennox WG, Gibbs FA, Gibbs EL. "Relationship of unconsciousness to cerebral
  blood-flow and to anoxaemia." Arch Neurol Psychiatry 1935;34:1001.
  Citation seen only in a web-search listing of a Cambridge "Epitome" abstract;
  cambridge.org is blocked. **Not opened.**
- Web searches (3 queries on jugular venous O2 / SjvO2 at syncope or
  unconsciousness) returned only clinical monitoring ranges and a general
  overview page, none of which I opened or would treat as a primary source.
- Whinnery's work (item 6) defines a time ("functional buffer period"), not
  an O2 level.

## 3. Kety & Schmidt (1948) — record only (full text failed)

Both papers verified from Europe PMC records; the PDFs could not be opened
(JCI → blocked CloudFront host; PMC → reCAPTCHA; europepmc.org blocked).
**No values were taken.**

- Kety SS, Schmidt CF. The nitrous oxide method for the quantitative
  determination of cerebral blood flow in man: theory, procedure and normal
  values. J Clin Invest. 1948;27(4):476–483. doi:10.1172/JCI101994.
  PMID 16695568. PMCID PMC439518.
- Kety SS, Schmidt CF. The effects of altered arterial tensions of carbon
  dioxide and oxygen on cerebral blood flow and cerebral oxygen consumption of
  normal young men. J Clin Invest. 1948;27(4):484–492. doi:10.1172/JCI101995.
  PMID 16695569. PMCID PMC439519.

## 4. Zarrinkoob et al. (2015) — opened

- Zarrinkoob L, Ambarki K, Wåhlin A, Birgander R, Eklund A, Malm J. Blood
  flow distribution in cerebral arteries. J Cereb Blood Flow Metab.
  2015;35(4):648–654. doi:10.1038/jcbfm.2014.241. PMID 25564234. PMCID PMC4420884.
  (Author list not re-checked against the page; title, journal, volume, issue,
  pages, DOI, PMID and PMCID from the Europe PMC record.)
- Link opened: https://pmc.ncbi.nlm.nih.gov/articles/PMC4420884/

| Quantity | Exact text | Value |
|---|---|---|
| Subjects | "The final study group consisted of 49 subjects included in the HY group (mean age±s.d., 25±2 years; 27 women) and 45 subjects in the HE group (mean age±s.d., 71±4 years; 23 women)." | n = 94 (49 young, 45 elderly) |
| Definition | "Total cerebral blood flow was defined as BFR in the internal carotid plus vertebral arteries" | tCBF = ICA + VA |
| Split | "Carotid/vertebral distribution was 72%/28% and was not related to age, sex, or brain volume." | 72 / 28 % |
| Split, absolute | "The anterior cerebral BFR (sum of the right and left ICA) was 515±96 mL/min and represents 72% of tCBF. For the posterior circulation (sum of the right and left VA), the flow rate was 202±44 mL/min (28% of tCBF)." | ICA sum 515 ± 96; VA sum 202 ± 44 mL/min |
| Split SD | "independent of age (HY: 72/28%±4%, HE: 72/28%±4%, P =0.7) and sex (women: 72/28%±5% men: 72/28%±4%, P =0.7)" | **vertebral share 28 ± 4 %** (± 5 % in women) |
| tCBF | "Total cerebral blood flow (717 ± 123 mL/min)" | 717 ± 123 mL/min |
| Basilar | abstract: "20% to basilar artery" | 20 % |
| Table 1, per vessel, mean ± s.d. mL/min (all n=94 / young n=49 / elderly n=45) | "ICA 257±48 276±47 236±41"; "VA 100±22 109±23 90±17"; "BA 145±41 162±44 128±28" | per vessel |
| Perfusion | "(HY: 60±8 mL/min/100 mL; HE: 56±7 mL/min/100 mL, P =0.04)" | per 100 mL brain |

Note: phase-contrast MRI, measured at C1–C2. The young group (25 ± 2 y) is the
closest match to Rossen's 20–25-year-old men.

## 5. Ito et al. (2004) — record only (bibliographic details verified)

- From the Europe PMC record (search DOI:10.1007/s00259-003-1430-8):
  **Eur J Nucl Med Mol Imaging. 2004;31(5):635–643. PMID 14730405.**
  The abstract in the record matches SOURCES.md S5 exactly
  ("CBF=44.4+/-6.5 ml 100 ml(-1) min(-1); CBV=3.8+/-0.7 ml 100 ml(-1);
  OEF=0.44+/-0.06; CMRO(2)=3.3+/-0.5 ml 100 ml(-1) min(-1)").

## 6. Whinnery & Forster (2013) and Whinnery, Forster & Rogers (2014) — opened (new, not on the list)

Open-access full text via Europe PMC REST `fullTextXML`. These are
**G-LOC (centrifuge) studies**, not neck compression, so they are context and a
possible recovery comparison, not direct choke data.

**6a.** Whinnery JE, Forster EM. The +Gz-induced loss of consciousness curve.
Extreme Physiol Med. 2013;2:19. doi:10.1186/2046-7648-2-19. PMCID PMC3710154.
https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3710154/fullTextXML

| Quantity | Exact text |
|---|---|
| FBP definition | "The functional buffer period (FBP) is the time that the integrated neurologic function supporting consciousness is maintained following the loss of adequate energy necessary for sustaining normal function" |
| G-LOC times | "for onset rates ≥ 1.0 G/s, G-LOC will occur in a mean time of 9.10 s"; "G-LOC will occur in a mean time of 9.65 s for rapid onset rate exposures to +Gz levels ≥ +7 Gz" (888 episodes) |
| Rossen (secondary) | "Rossen acutely arrested cerebral circulation in 74 humans using a cervical pressure cuff with the mean time of 6.41-6.91 s [ 29 , 30 ]." |
| Mitchell (secondary) | "The mean time from vascular neck restraint ... to LOC defined by onset of eye fixation in 24 healthy volunteer police officers was 7.9 s (range 6.3 to 12.2 s) [ 31 ]." (ref 31 = Mitchell et al. 2012, J Appl Physiol 112:396–402) |
| Hangings | "Sauvageau et al. reported that the time to loss of consciousness in 14 filmed human hangings is 10.4 ± 3.0 s (range 8 to 18 s)" — recorded only because it is on the page; not suggested for the model. |
| Rossen ref as printed | "Rossen R, Kabat H, Anderson JP. Acute arrest of cerebral circulation in man. Arch Neurol. 1943;50:510–528. doi: 10.1001/archneurpsyc.1943.02290230022002." |

The Rossen mean 6.41–6.91 s comes from a reanalysis (refs 29, 30: Forster &
Whinnery technical reports), which I did not open. Rossen's own text (S1/S2)
gives only the 4–10 s range.

**6b.** Whinnery JE, Forster EM, Rogers PB. The +Gz recovery of consciousness
curve. Extreme Physiol Med. 2014;3:9. doi:10.1186/2046-7648-3-9. PMCID PMC4007145.
https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4007145/fullTextXML

| Quantity | Exact text |
|---|---|
| Recovery, G-LOC | "Mean time from loss to return of consciousness for 760 episodes of consciousness recovery was 10.4 ± 5.1 s; minimum 1 s; maximum 38 s." |
| Minimum recovery | "there is a minimum time (mean 8.29 ± 3.84 s) required for recovery of consciousness when complete loss of consciousness occurs." |
| Rossen recovery (secondary) | "Rossen, Kabat, and Anderson ... found no significant correlation between time of recovery with time of eye fixation or with duration of anoxia [ 28 ]. For their 28 LOC episodes defining their ABSINCAP equivalent, the mean was 6.14 s [ 29 ]." |

Caveat: G-LOC "recovery" is measured from LOC, and the time includes the
unconscious period while G is still high, so it isn't directly comparable to
recovery after a cuff is released.

## 7. Rossen, Kabat & Anderson (1943) original — failed

- DOI as printed in Whinnery 2013/2014 reference lists:
  10.1001/archneurpsyc.1943.02290230022002 (not opened; JAMA Network not tried
  because it is not on the allowed host list, and the paper is paywalled).
- The open reprint (SOURCES.md S1) remains the only primary text opened.

---

## Summary for the main thread

| Item | Status | Usable new values |
|---|---|---|
| Mitchell 2012 full text | failed (403) | none; conflict flagged with Whinnery's 7.9 s citation |
| O2 level at LOC | failed | none; gap stays open |
| Kety & Schmidt 1948 (both) | record only | citations verified; no values |
| Zarrinkoob 2015 | opened | vertebral share 28 ± 4 %, n = 94; per-vessel flows |
| Ito 2004 | record only | 31(5):635–643, PMID 14730405 |
| Whinnery 2013/2014 | opened | G-LOC recovery 10.4 ± 5.1 s; secondary Rossen means |
| Rossen 1943 original | failed | DOI as printed in a reference list |

To unblock Kety and Mitchell, the network policy would need
`dm5migu4zj3pb.cloudfront.net` (JCI PDFs) and a working route to the APS full
text, or Joshua could upload the PDFs.
