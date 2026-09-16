# LPDG Gateway Visit Ranking

This project ranks the 15 gateways that the field team should inspect each week. It uses only information available before the prediction Monday and writes the required 120-row `predictions.csv` for the eight weeks from 2 February to 23 March 2026.

## Chosen area

Part 2 area: **D - Data Science**.

The analysis defines what "needs a visit" means, compares anomaly thresholds, reports uncertainty from gateway-level resampling, and relates the result to the EUR 380 visit cost and EUR 600 weekly fault cost.

## How I approached the problem

I worked in the following order:

```text
Read the brief and data dictionary
        ↓
Run the supplied baseline
        ↓
Inspect and clean the data
        ↓
Build a repeatable weekly ranking
        ↓
Generate and validate predictions.csv
        ↓
Define what "needs a visit" means
        ↓
Backtest on earlier weeks
        ↓
Compare thresholds, uncertainty and cost
        ↓
Write the recommendation and limitations
```

I did not train a machine-learning model. The brief allows the supplied statistical baseline to be used, and the historical visit outcomes are incomplete and selected by earlier operational decisions. I therefore spent Part 2 testing the decision rule and its limitations instead of fitting a more complicated model to weak labels.

## The main idea in simple words

I treated this as a weekly ranking problem:

1. Pick a Monday and ignore everything recorded on or after that time.
2. Keep only gateways that were active on that Monday.
3. Use the previous 28 days to learn what is normal for each gateway.
4. Look at the latest seven days and count unusually high offline, disconnection and reboot readings.
5. Sort the gateways by that count and return the first 15 with a reason.

The program follows the same order:

```text
run.py
  → load_data() checks and cleans the files
  → build_predictions() loops through the eight Mondays
  → rank_week() scores and sorts one week
  → validate() checks the final predictions.csv
```

I chose this approach because it uses basic statistics, is easy to inspect, and can be changed during a live review. The score means "how often this gateway behaved unusually compared with itself"; it does not mean "probability of failure".

## How I examined the data

I first loaded every supplied file, checked its columns and dates, and decided whether it was suitable for prediction or only for later evaluation.

| Data | What I found and checked | How I used it |
| --- | --- | --- |
| Hourly telemetry | 1,426,840 cleaned rows for 320 gateways, from 1 August 2025 to 31 March 2026. I checked timestamps, gateway IDs, missing ranking values and duplicate gateway-hour records. | Main prediction input. |
| Gateway master | 332 asset records. I checked unique IDs and converted installation and decommission dates. | Keeps only gateways active on each prediction Monday. |
| Field visits | 642 visits: 223 repairs, 390 no-fault outcomes and 29 no-access outcomes. | Retrospective evidence only; not a prediction feature. |
| Meter-read success | 7,226 gateway-week rows over 26 weeks, ending 26 January 2026. I checked that reads were between zero and the expected count. | Supporting evidence about operational impact. |
| Engineer review | 120 reviewed gateways. I checked its identifiers, categories and review dates. | Loaded and validated, but not used in the ranking because it is a one-time selected review. |

### What the data audit changed

- I found and removed 6,547 exact duplicate telemetry rows. Counting them would have increased some scores twice.
- I standardised gateway IDs by removing separators and using uppercase 12-character values.
- I kept a missing telemetry hour separate from a reported zero because they do not mean the same thing.
- I applied installation and decommission dates at every weekly cutoff so inactive gateways were not ranked.
- I treated unvisited gateways as unknown rather than healthy because historical visits cover gateways that somebody already suspected.

### What I learned before choosing the final rule

- Gateways have different normal behaviour, so I compare each gateway with its own recent history instead of using one fixed fleet-wide value.
- At the retained three-sigma rule, historically selected gateways averaged 57.3% meter-read success, compared with 86.0% for the rest. This supports operational relevance, but it does not prove causation.
- Only 17.3% of the historical selected slots had a definitive visit outcome. This low coverage is why I report uncertainty and avoid claiming fleet-wide accuracy.
- A lower 2.5-sigma threshold had a slightly better historical point estimate, but the uncertainty ranges overlapped and the weekly visit lists changed substantially. I kept three sigma as the more cautious default.

## Setup

Python 3.11 or later is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Place the supplied `data` directory at the project root. The data is confidential and is excluded from Git.

## Generate and validate the submission

```powershell
python run.py --data data --out predictions.csv
```

This command loads and cleans the inputs, generates all eight weekly rankings, writes `predictions.csv`, and runs the supplied format validator. A successful run ends with `Submission validation: OK`.

To validate an existing file independently:

```powershell
python validate_submission.py predictions.csv
```

## Run the Data Science analysis

```powershell
python analyse.py --data data
```

This writes `threshold_comparison.csv`, `cooldown_comparison.csv`, and four charts under `charts/`. On the development machine, prediction took about 8 seconds and the full historical analysis took about one minute.

## Visual results

### Recommended gateways for the first week

![Recommended gateways for 2 February 2026](charts/first_week_top15.png)

The chart shows the 15 gateways selected for 2 February 2026, ordered by the number of recent telemetry readings that crossed the three-sigma threshold. A larger count means the gateway showed unusual offline time, disconnections, or reboots more often during the previous seven days.

### Threshold evidence and cost

![Observed repairs and historical cost proxy by threshold](charts/threshold_evidence_and_cost.png)

The left panel compares the percentage of observed repaired gateways captured at each threshold; its error bars show the 90% gateway-bootstrap range. The right panel compares an incomplete historical cost proxy. Although 2.5 sigma has the best point estimate, the evidence is limited and the uncertainty ranges overlap, so the final method retains the supplied three-sigma threshold.

### Stability of the weekly visit list

![Overlap with the three-sigma weekly visit list](charts/threshold_selection_stability.png)

This chart measures how much each threshold's weekly top 15 overlaps with the selected three-sigma list. The 2.5-sigma result overlaps by about 65% on average, showing that a small threshold change would replace several weekly visits.

### Cost of detecting a persistent fault late

![Cost of delayed attention to a persistent fault](charts/fault_delay_cost.png)

Under the supplied cost rule, dispatching a visit costs EUR 380 and each unresolved fault week costs EUR 600. The chart shows why earlier detection matters: every additional week before the first successful visit adds another EUR 600 to the fault episode.

## Run tests

```powershell
python -m pytest -q
```

The tests cover identifier cleaning, lifecycle filtering, strict time cutoffs, deterministic ties, silent gateways, and the supplied episode-cost rules.

## Method

For each Monday:

1. Keep gateways commissioned and not decommissioned at Monday 00:00 UTC.
2. Use telemetry strictly before that cutoff.
3. Estimate each gateway's mean and standard deviation over the previous 28 days.
4. Count metric readings in the previous seven days that exceed the gateway's own mean by more than three standard deviations.
5. Rank by metric-breach count, then missing recent hours, peak deviation, and gateway ID.
6. Return the first 15 with an operations-facing reason.

The three ranking metrics are `offline_duration_sec`, `disconnection_cnt`, and `reboot_cnt`. Exact duplicate gateway-timestamp records are removed once before scoring.

## Submission contents

| Requirement | Location |
| --- | --- |
| Validated 120-row output | `predictions.csv` |
| Code that produces the output | `run.py` and `gateway_ranker/` |
| Five decisions and chosen Part 2 area | `DECISIONS.md` |
| AI tool disclosure and one corrected issue | `AI-USAGE.md` |
| Data Science work | `analyse.py`, `analysis_report.md`, comparison CSV files, and `charts/` |
| Setup and run instructions | This README |
| Resume | `23091A32D4.pdf` in the repository root |
| Screen recording | Link in the section below |

The supplied dataset, challenge ZIP, brief, data dictionary, FAQs, and original bundle README are not committed. Reviewers should place the supplied `data` folder at the project root before running the code.

## Project structure

```text
gateway_ranker/
  config.py          thresholds, dates, costs and metrics
  data_loader.py     loading, validation, identifier and duplicate handling
  ranking.py         cutoff-safe scoring and top-15 selection
  evaluation.py      historical evidence, uncertainty and cost logic
  charts.py          report charts
tests/               small synthetic regression tests
run.py               submission entry point
analyse.py           Data Science analysis entry point
baseline_3sigma.py   supplied reference baseline
validate_submission.py supplied format validator
```

## Screen recording

[Watch the project walkthrough](https://drive.google.com/drive/folders/1ZjnCXAFgU6ycpqQoulerhW0OjwV8-Pdq?usp=sharing)

The recording demonstrates the problem, data checks, prediction generation and validation, and the main Data Science results.

## Important limitation

Historical field visits are a selected sample of already-suspected gateways. The reported evaluation measures agreement within that observed sample; it cannot establish fleet-wide precision, recall, or the official hidden-ground-truth cost. See `analysis_report.md` for the complete interpretation.
