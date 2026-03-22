---
name: biotech-audit-checklist
description: Checklist for auditing final biotech reports and common repair actions. Load inside the report-auditor or report-writer when debugging output quality.
disable-model-invocation: true
user-invocable: false
---

# Report audit checklist

## Blocking checks
- All 7 required sections exist and appear in the exact order
- Summary table header is exact
- All ranked core tickers appear in the report body and summary table
- Watchlist tickers are not incorrectly presented as core green signals
- Report dates in body and summary table do not contradict the ranked memory artifacts

## Common repair actions
- Missing ticker in body → add a dedicated subsection or bullet in the correct lane
- Wrong section order → rewrite headings before running `report_finalizer.py`
- Summary table mismatch → rerun `report_finalizer.py` with explicit `--core` and `--watchlist` paths
- Lane confusion → ensure hardened watchlist / excluded files are used instead of base verification files
