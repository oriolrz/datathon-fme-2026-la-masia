# La MasIA · Datathon FME 2026 🏆

**UPC Sostenible × AED** · **FME Tukey side challenge** · 14–15 November 2026

> **Battery scheduling under uncertainty.** We combine forecasting, safe Model Predictive Control (MPC), temporal validation and an interactive decision-support dashboard to reduce the campus's electricity emissions and costs.

**Team:** Oriol · Dani · David · Cesc  
**Competition:** [Datathon FME 2026](https://www.datathon.cat/)  
**Official challenge / evaluator:** [UPC Sostenible × AED](https://repteupc.datathon.cat/)

## Project overview

The campus has photovoltaic generation, electricity demand that changes over time, and a battery. At each hour our agent chooses a charging or discharging action to reduce **CO₂ emissions (70% of the score)** and **electricity cost (30%)**, respecting physical constraints.

We explored both competition modes:

| | Standard mode | Hard mode |
|---|---:|---:|
| Battery energy capacity | 2,000 kWh | 6,000 kWh |
| Charge/discharge power | ±500 kW | ±1,500 kW |
| Solar | Original | 12× original |
| Known price and CO₂ horizon | 24 hours | 3 hours |
| Challenge focus | Energy scheduling | Forecasting, uncertainty and stochastic control |
| Reported public score | **6.43** | **23.32** (team-reported final agent) |

**These are public-leaderboard scores, not private-test estimates.** Public and private rankings must not be conflated. Hard is the prize-relevant mode according to the organizer's announcement on November 15.

## What we built

### 1 — Forecasting and stochastic MPC

Our Hard controller forecasts electricity demand, PV generation, price and grid CO₂ intensity. It repeatedly optimizes a rolling horizon, applies only the first feasible action and replans with the next observation. The reference Dani v2 includes **five net-load uncertainty scenarios**; subsequent versions were separately evaluated. A precise version-to-version comparison requires using the corresponding frozen files.

- Battery capacity and power constraints are enforced on every action.
- The agent only relies on information available at the decision time: observed market values and previous-hour telemetry, plus models trained on authorized training data.
- The Hard evaluator limits confirmed price/CO₂ observations to the current and next two hours.
- The agent must run within the organizer's 60-second evaluation limit.

### 2 — Scientific evaluation, not just leaderboard tuning

We audited model provenance and numerical training reproducibility, reconstructed v2's forecast fitting, and ran temporally excluded validation blocks. We also tested forecast changes, uncertainty calibration, history initialization and inter-block timing. Several seemingly promising variants **did not improve consistently** and were rejected rather than submitted.

**Limitation:** Most local data have been explored during development. Even a temporally withheld replay is not a fully blind private-test result. We therefore report leaderboard scores, retrospective experiments and truly retrained-withheld-block tests separately.

See [Technical methodology](docs/FINAL_TECHNICAL.md).

### 3 — Energy decision dashboard · FME Tukey

We built a decision-support interface intended to compare **Standard** and **Hard** operation, including:

- Load and solar production over time;
- Battery state of charge and hourly charge/discharge decisions;
- Electricity imports, CO₂ emissions and financial savings against a no-battery baseline;
- Forecast uncertainty, operational constraints and explanations of decisions.

Dashboard development is maintained on the [David Tukey branch](../../tree/feat/david-tukey). A presentation handoff is in [Dashboard & demo](docs/TUKEY_DEMO.md). Data shown in the dashboard must be labeled as historical training replay, public score or illustrative data.

## Repository contents

| Location | Purpose |
|---|---|
| [`docs/FINAL_TECHNICAL.md`](docs/FINAL_TECHNICAL.md) | Challenge specification, algorithm and validation caveats |
| [`docs/TUKEY_DEMO.md`](docs/TUKEY_DEMO.md) | Dashboard walkthrough, Normal/Hard comparison and pitch |
| [`docs/SUBMISSION.md`](docs/SUBMISSION.md) | Exact deliverables and verification checklist |
| [`prototypes/upc/`](prototypes/upc/) | Early Standard-mode prototype, **not** the final submitted agent |
| [`feat/david-tukey`](../../tree/feat/david-tukey) | Ongoing dashboard code |
| [`feat/oriol-integration`](../../tree/feat/oriol-integration) | Integration and validation tooling |
| [`codex/oriol-hard-mode-20261114`](../../tree/codex/oriol-hard-mode-20261114) | Earlier Hard research experiments |

**Source packaging note:** the challenge submission ZIPs are managed separately from the legacy planning documents. Before the jury reviews this repository, the final Hard agent's source and parameter files should be placed at `submissions/hard_final/` with the exact SHA recorded in [Submission](docs/SUBMISSION.md). Do not mistake the prototype on `main` for the final controller.

## Methodological principles

1. **Causality.** No hidden-test data or future true load/PV values at decision time.
2. **Valid physical actions.** SOC, inverter power, round-trip efficiency and zero-violation safety clamps.
3. **Temporal validation.** Retrain preprocessing and predictors without the evaluated periods when estimating out-of-sample behavior.
4. **Transparent labeling.** Public leaderboard, train replay and held-out results are different quantities.
5. **Decision utility.** The dashboard explains why an action is useful, not just what the score is.

## Acknowledgements and data

Challenge organized by **UPC Sostenible × AED**, within Datathon FME 2026. Training data and the evaluator originate from the [official participant package](https://repteupc.datathon.cat/). Original data are **not mirrored in this repository**; obtain them from the official source and observe their usage restrictions.

All numeric claims refer to the corresponding recorded experiment or official submission; nothing here predicts the hidden private ranking.

---
*Built by La MasIA at Datathon FME 2026.*
