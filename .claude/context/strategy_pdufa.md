# Biotech Alpha Run-up Strategy

## Core thesis
- Buy the rumor, sell the news.
- Canonical trading window: accumulate around **D-60**, reduce/exit around **D-7**.
- The workflow should screen for events whose **entry window starts within the next 90 days**.

## Covered catalyst types
- FDA PDUFA / NDA / BLA action dates
- FDA AdCom / ODAC / advisory committee meetings
- Confirmed or strongly estimated Phase 2 / Phase 3 topline readouts
- MFDS / Korean regulatory approval catalysts when the company is publicly tradable
- CRL resubmission situations only if a verified re-filing exists

## Lane rules
- **Confirmed lane (core tradable)**: official IR, regulator, SEC filing, or equivalent primary-source evidence confirms the event date
- **Estimated lane (watchlist)**: date only appears in third-party calendars, conference decks, earnings-call hints, or indirect company guidance
- **Excluded lane**: rumor only, already approved, CRL without re-submission, invalid ticker, or event already passed outside the tradable logic

## Hardening rules
- Run a negative-thesis pass after base verification
- Downgrade or exclude when fresh evidence shows manufacturing issues, safety overhang, capital raise pressure, or already-fully-priced conditions that invalidate a clean run-up thesis
- Preserve the base verification files as audit history and write hardened variants for downstream stages

## Failure / exclusion conditions
- Cash runway < 6 months
- Already-approved product/indication for the same regulatory event
- CRL with no confirmed re-submission
- Current price is too close to the 52-week high (default red flag: within 10%)
- Exit window already passed (`D-7 < today`)
- Tradability score too weak for practical execution

## Timing rules
- Keep a candidate only if `target_exit_date >= today`
- Keep a candidate only if `target_entry_date <= today + 90 days`
- Tier 1: `target_entry_date <= today <= target_exit_date`
- Tier 2: `today < target_entry_date <= today + 90 days`

## Historical annotation layer
- Historical analysis is **annotation only**, not a hard filter
- Fixed windows: `[-60,-7]`, `[-30,-7]`, `[-10,+3]`
- Compare to `XBI` benchmark to reduce regime distortion
- If sample size is insufficient, mark `insufficient_history=true` and keep the candidate if the core rules still pass

## Ranking layer
- Rank final candidates after historical annotation
- Blend date certainty, catalyst materiality, price setup, balance-sheet safety, tradability, and historical support
- Apply a penalty for bear-case / thesis-break evidence
