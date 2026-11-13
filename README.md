# Why a blood choke causes unconsciousness in seconds: a small, honest oxygen model

> **Educational modelling project only. This is not medical advice and must not
> be used for safety, training or medical decisions.**

Work in progress. Stage 1 (reading): [SOURCES.md](SOURCES.md),
[PHYSIOLOGY.md](PHYSIOLOGY.md). Stage 2 (model): `choke_model/`,
[ASSUMPTIONS.md](ASSUMPTIONS.md), `python -m scripts.stage2_model`.
Stage 3 (checks): `python -m scripts.stage3_check`.
Stage 4 (uncertainty): `python -m scripts.stage4_uncertainty` (about 3 minutes).
UFC check (model vs chokes timed in UFC fights): `python -m scripts.ufc_check`.
Interactive pages, both built by `python -m scripts.build_simulator` from the
same parameters, with a test that checks their JavaScript copy of the equation
against the Python model:
- `simulator/xray.html`: a schematic x-ray of the head and neck showing blood
  flow to the brain being cut and the front of the brain going dark (A13).
- `simulator/index.html`: sliders and an oxygen trace.
Tests: `pytest` (also run by GitHub Actions).
