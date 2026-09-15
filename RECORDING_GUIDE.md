# Screen Recording Guide (6-8 minutes)

Use this as a speaking guide. Explain the ideas in your own words and pause briefly after each command so the output is visible.

## 0:00-0:45 - The problem

Show `README.md`.

Explain:

> LPDG has about 320 gateways carrying meter readings. A failing gateway can remain unnoticed, while the field team can make only 15 visits each week. This project ranks those 15 using only information available before each Monday.

Mention the EUR 380 visit cost and recurring EUR 600 weekly fault cost.

## 0:45-1:30 - Project structure

Show the project tree and briefly point to:

- `run.py` as the one-command entry point;
- `gateway_ranker/data_loader.py` for input checks and cleaning;
- `gateway_ranker/ranking.py` for the top-15 logic;
- `validate_submission.py` as the supplied validator;
- `DECISIONS.md` and `AI-USAGE.md` as required documentation.

## 1:30-2:45 - Run Part 1

Open a terminal at the repository root and run:

```powershell
python run.py --data data --out predictions.csv
```

Point out these lines:

- 6,547 exact telemetry duplicates removed;
- 120 rows written for eight weeks;
- `Submission validation: OK`.

Then run the supplied validator independently:

```powershell
python validate_submission.py predictions.csv
```

## 2:45-3:45 - Show one weekly result

Open `predictions.csv` and filter or scroll to `2026-02-02`.

Explain:

> Every week contains ranks 1 to 15. The score is a metric-breach count rather than a probability. Each reason tells the operations manager how many breaches occurred and which signal changed most.

## 3:45-5:00 - Explain the ranking

Show `gateway_ranker/ranking.py` and explain:

1. Monday 00:00 UTC is the cutoff.
2. Only active gateways are considered.
3. Each gateway is compared with its own previous 28 days.
4. The latest seven days are checked for unusual offline time, disconnections, and reboots.
5. Sorting is deterministic when scores tie.

Mention that exact duplicates are removed once and missing hours are kept separate from healthy zero values.

## 5:00-6:00 - Decisions and limitations

Show `DECISIONS.md`.

Explain why Data Science was selected and why the supplied three-sigma threshold was retained. State one limitation clearly:

> Historical visits cover gateways somebody already suspected. They cannot reveal faults that were never visited, so I do not claim fleet-wide recall from them.

## 6:00-7:00 - Demonstrate changeability

Show `gateway_ranker/config.py`, then explain that the threshold can be changed from one setting or through the command line.

Run a temporary alternative without replacing the submission:

```powershell
python run.py --data data --out predictions-2_5.csv --sigma 2.5
```

Explain that the live-session change is straightforward, while the decision to adopt it would still require outcome evidence.

Delete the temporary `predictions-2_5.csv` after the recording; it is not part of the submission.

## 7:00-7:30 - Close

Finish with:

> The result is a reproducible weekly priority list, not an automatic diagnosis. Its strongest feature is that the data cutoff, score, uncertainty, and limitations are explicit and can be changed without rewriting the project.

## Before adding the link

1. Upload the recording as unlisted YouTube/Vimeo or a shareable Drive/OneDrive file.
2. Open the link in a private browser window.
3. Confirm it does not request access.
4. Replace `[RECORDING LINK TO BE ADDED]` in `README.md`.
5. Commit the README update.

