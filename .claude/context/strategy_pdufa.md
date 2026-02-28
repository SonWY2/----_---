# PDUFA Run-up Strategy Logic

## The Golden Rule
"Buy the rumor (anticipation), Sell the news (before release)."

## Timeline Parameters
1. **Observation Start**: Event - 90 Days
2. **Accumulation Zone (Buy)**: Event - 60 Days to - 45 Days
   - Why? Institutional money starts positioning ~2 months prior.
3. **Distribution Zone (Sell)**: Event - 7 Days to - 3 Days
   - Why? Avoid binary event risk (Approval vs CRL).

## Failure Conditions (Do Not Buy)
- Company has < 6 months of cash (Dilution risk).
- Phase 2 data was mixed/weak.
- Stock is already trading at 52-week highs (Priced in).

## Historical Context Layer (Annotation-Only)
- Add a historical context note after tradable filtering.
- Use fixed event windows: `[-60,-7]`, `[-30,-7]`, `[-10,+3]`.
- Compare stock return to benchmark return to avoid regime distortion.
- If sample size is too small, label `insufficient_history` instead of forcing conclusion.
- Historical context supports interpretation and ranking, but does not override core risk rules.
