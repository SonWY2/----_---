---
name: biotech-alpha-playbook
description: Core strategy and judgment rules for the Biotech Alpha catalyst-screening workflow. Load inside biotech research subagents as background knowledge.
disable-model-invocation: true
user-invocable: false
---

# Biotech Alpha playbook

## Primary mission
Find actionable biotech catalysts whose **run-up entry window (D-60)** begins within the next 90 days, while keeping a separate watchlist for partially verified catalysts.

## Geographic scope
- US listed biotech / biopharma
- Korean listed biotech / biopharma when a tradable equity and catalyst can be tied to a public company

## Event taxonomy
1. PDUFA / NDA / BLA action dates
2. Advisory committee meetings (AdCom / ODAC / panel dates)
3. Phase 2 / Phase 3 topline readouts
4. MFDS / Korean regulatory approval catalysts
5. CRL re-submission situations, but only if the re-filed application is evidenced

## Truth hierarchy
Prefer evidence in this order:
1. Company IR / press release / SEC filing / investor presentation / earnings call transcript
2. Regulator database or trial registry
3. Reputable third-party catalyst calendar or market data site

## Lane policy
- **Confirmed** → core tradable lane
- **Estimated** → watchlist lane
- **Rumor or invalid** → excluded lane

## Required confidence fields
Wherever verification is performed, include:
- `verification_status`
- `confidence_score` in the range `[0.0, 1.0]`
- `confidence_label` such as `High`, `Medium`, `Low`
- `reason`

## Hard exclusions
- Already approved for the same drug/indication and event thesis
- CRL with no confirmed re-submission
- Cash runway < 6 months
- Price too close to 52-week high (default red flag: within 10%)
- Exit window already passed

## Bear-case hardening
After base verification, actively search for evidence that **breaks** the thesis:
- unresolved CMC or manufacturing issues
- safety signal or trial hold overhang
- fresh financing / ATM / shelf / heavy dilution risk
- already fully priced move or other structural issues

## Tradability principles
- Prefer names with enough liquidity to scale in/out without excessive slippage
- Penalize ultra-low price, very low volume, or unstable high-volatility setups
- Tradability is a quality gate, not only an informational note

## Historical note policy
Historical context supports interpretation and ranking, but does not override the hard exclusions above.
