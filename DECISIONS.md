# Five Decisions

## 1. I selected Data Science for Part 2

**Choice.** I selected Area D and focused on defining "needs a visit", testing the definition, measuring uncertainty, and explaining the cost consequences.

**Alternative.** I considered Software Development and a web API around the supplied baseline.

**Why I rejected it.** The central ambiguity is operational rather than interface-related: the brief does not define when a gateway warrants a visit. Concentrating on this decision gives the analysis enough depth and prepares for the live threshold-change exercise.

**Limitation.** The solution is a command-line workflow rather than a service. It is designed for a small operations team running one weekly ranking.

## 2. I defined a visit need as persistent change from the gateway's own normal

**Choice.** An active gateway warrants priority when offline duration, disconnections, or reboots repeatedly exceed its own 28-day behaviour during the latest seven days. The score is the number of metric breaches above three standard deviations.

**Alternative.** I considered a fixed fleet-wide threshold and a rule based only on meter-read success.

**Why I rejected them.** Gateways operate in different environments, so one fleet threshold can confuse a difficult site with a deteriorating gateway. Meter-read success is useful supporting evidence, but it is weekly and ends on 26 January 2026, so it cannot be the current signal for the scored period.

**Limitation.** A metric breach is evidence of unusual behaviour, not proof that a field repair is possible. Temporary backhaul problems can look similar to gateway faults.

## 3. I retained the supplied three-sigma threshold

**Choice.** I kept sigma at 3.0 for the submitted ranking.

**Alternative.** In the retrospective sample, 2.5 sigma selected 49 of 96 observed repaired faults, while 3.0 selected 46. Its labelled one-week proxy cost was about EUR 82 lower per week.

**Why I rejected the apparent improvement.** Only 17.3% of the three-sigma selection slots had a definitive visit outcome. The 2.5- and 3.0-sigma gateway-bootstrap ranges overlap, and their average top-15 overlap is only 64.8%. Changing the production threshold for three extra observed repairs across 22 weeks would overfit a biased sample. Three sigma is therefore a stable default rather than a claimed optimum.

**Limitation.** Hidden ground truth could show that 2.5 sigma has lower real cost. A blind one-week repeat cooldown was also tested, but it reduced observed repairs selected from 46 to 38, so repeat eligibility remains until a completed visit can be confirmed. New field outcomes should be used to revisit both decisions.

## 4. I removed exact duplicates and kept absence separate from zero

**Choice.** I normalize gateway IDs, remove one copy of each exact duplicate gateway-timestamp record, apply installation and decommission dates at the weekly cutoff, and measure missing recent hours separately.

**Alternative.** I could have summed duplicate rows or filled absent hours with zeros.

**Why I rejected it.** The 6,547 duplicate pairs have identical ranking values, so summing them would double-count the same evidence. A missing row does not say that the gateway reported zero faults. Missing hours are kept visible and used as a deterministic secondary ranking signal.

**Limitation.** The files do not identify why an hour is missing. Silence may mean a failed gateway, a transmission problem, or an inactive reporting path.

## 5. I treated historical visits as incomplete evidence

**Choice.** I evaluate the actual weekly top 15 against visits completed in that week. `Fehler behoben` is evidence of a fault, `Kein Fehler gefunden` is evidence against a persistent fault, and `Kein Zugang` remains unknown. I report label coverage, resample whole gateway histories to show a 90% range, and stress-test the fixed three-sigma rule on the later 11 weeks using a separate half of gateway IDs.

**Alternative.** I considered treating every unvisited gateway as healthy and reporting one precision and recall number.

**Why I rejected it.** Field visits contain gateways somebody already suspected. Quiet failures have no row, so unvisited gateways are unlabelled rather than negative. A single point estimate hides how much the result depends on the particular gateways observed.

**Limitation.** Even grouped resampling cannot remove the selection bias. Official fleet-wide cost can only be calculated using the held-out truth.

## What the solution cannot do

1. It cannot prove that an anomaly requires a physical repair.
2. It cannot measure faults that were never visited or otherwise labelled.
3. It cannot infer historical firmware or asset changes that are absent from the files.
4. It cannot identify the true boundary between continuous fault episodes.
5. It cannot use current meter-read results after 26 January 2026 because those records were not supplied.

With two more weeks, I would first ingest the scored-period field outcomes and recalibrate the threshold. Next, I would investigate missing-hour patterns as a separate failure signal. Finally, I would test whether individual metrics should carry different weights based on their relationship with later meter-read deterioration.
