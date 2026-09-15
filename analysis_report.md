# Which Gateways Should We Visit?

## Recommendation

Use the three-sigma ranking as the weekly starting list: inspect the 15 active gateways with the highest count of unusual offline, disconnection, or reboot readings relative to their own recent history. Treat the ranking as a prioritisation tool, not a diagnosis. The evidence supports using telemetry to concentrate visits, but it is not strong enough to justify fine-tuning the threshold away from the supplied default.

## What "needs a visit" means

For this analysis, a gateway warrants priority when its latest seven days contain persistent metric readings more than three standard deviations above its own 28-day behaviour. Comparing a gateway with itself reduces the risk of repeatedly penalising sites that are naturally noisier than the fleet.

The score is a **metric-breach count**. One hour can contribute more than one breach if several metrics are unusual. The score is ordinal: a larger score means higher priority; it is not a fault probability.

Exact duplicate gateway-timestamp rows are removed before scoring. Only gateways active at the Monday cutoff are considered. Missing telemetry hours are recorded separately and used as a secondary ranking signal rather than being silently replaced with healthy zeros.

![Recommended visits for the first scored week](charts/first_week_top15.png)

## Historical evidence

The retrospective check covers 22 Mondays from 1 September 2025 through 26 January 2026. For each Monday, the ranking uses only earlier telemetry. Completed visits during that Monday-to-Sunday week provide later evidence about the selection.

At three sigma:

- 57 of 330 selected slots had a definitive visit outcome, giving 17.3% labelled coverage.
- 46 selected gateway-weeks had a recorded repair and 11 had "no fault found".
- Precision within that observed subset was 80.7%; the gateway-bootstrap 90% range was 72.3% to 88.7%.
- The top 15 contained 46 of the 96 repaired gateway-weeks observed across the fleet in those weeks: 47.9%, with a gateway-bootstrap 90% range of 39.6% to 56.0%.

These figures are not fleet-wide precision and recall. Engineers visited gateways they already suspected, and undetected faults have no row. The range resamples complete gateway histories, which exposes device dependence but does not remove that selection bias.

As separate supporting evidence, gateways selected at three sigma averaged 57.3% meter-read success in the same historical weeks, compared with 86.0% for other gateways. That relationship is consistent with operational harm, but it does not prove the gateway caused every missing meter read.

## Threshold decision

The 2.5-sigma point estimate selected 49 of 96 observed repairs, compared with 46 at three sigma. It also produced the lowest labelled one-week cost proxy. I did not adopt it because the improvement is three observed repairs over 22 weeks, label coverage is low, and the uncertainty ranges overlap.

Moving the threshold changes the actual visit list substantially. The 2.5-sigma top 15 shared only 64.8% of its gateways with the three-sigma list on average. That is too large an operational change to justify from a small, selected outcome sample.

![Observed repaired faults across thresholds](charts/threshold_observed_recall.png)

![Top-15 stability across thresholds](charts/threshold_selection_stability.png)

Three sigma is therefore a conservative, reproducible default. It is not claimed to be statistically optimal. The threshold should be reconsidered after new visit outcomes become available.

## Cost interpretation

Every valid submission contains 15 visits for eight weeks, so its dispatched-visit cost is fixed:

`15 visits x 8 weeks x EUR 380 = EUR 45,600`

The economic benefit comes from finding real fault episodes early. Under the brief's scoring rule, a gateway first visited in the second week of a four-week episode incurs two fault weeks plus one visit: `2 x EUR 600 + EUR 380 = EUR 1,580`. With no visit, the episode costs `4 x EUR 600 = EUR 2,400`. Later recommendations during the same episode do not reduce the cost further.

![Cost of delayed attention](charts/fault_delay_cost.png)

The supplied data does not contain the official fault episodes. The threshold table therefore reports a clearly labelled proxy: fixed visit cost plus EUR 600 for each observed repaired gateway-week outside the top 15. It understates total cost because unobserved faults are missing and does not reconstruct episode boundaries.

## What could change this recommendation

The recommendation would change if new field outcomes showed that 2.5 sigma consistently catches faults earlier without using too many slots on temporary anomalies. The first next step is to record the outcome of every recommended visit and feed it back by gateway and week. A second useful test is whether sustained telemetry silence predicts later repair after controlling for installation and decommission dates.

The largest remaining uncertainty is not the third decimal place of the score. It is the state of gateways that were never visited.

