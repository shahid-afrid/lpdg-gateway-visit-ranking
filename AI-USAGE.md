# AI Usage

## Tools and tasks

I used an AI coding assistant to:

- review the challenge brief, data dictionary, and both FAQ documents;
- propose a compact project structure;
- draft the data-loading, ranking, evaluation, chart, and test code;
- identify claims in the initial analysis that needed verification;
- help rewrite the README, decisions, and operations report from measured outputs.

I did not upload the supplied dataset to an external service. The analysis and code ran locally against the provided `data` directory.

## A mistake that was found and corrected

The assistant initially used `reindex(..., fill_value=0)` after adding gateways with baseline history but no recent telemetry. With the installed Pandas version, that attempted to insert numeric zero into the string `worst_metric` column and the full historical analysis failed.

The failure appeared only during the end-to-end analysis. The fix fills numeric and string columns separately, and `test_gateway_with_history_but_no_recent_rows_remains_visible` was added to preserve the case.

## Verification performed

- The submission was regenerated from the supplied data using `run.py`.
- The supplied `validate_submission.py` accepted all 120 rows.
- The focused test suite passed.
- The threshold analysis was rerun across 22 historical weeks after the fix.
- The generated charts were visually inspected for readable titles, labels, and values.

The reported historical metrics remain limited by the selection bias and incomplete coverage of field-visit outcomes, as described in `analysis_report.md`.

