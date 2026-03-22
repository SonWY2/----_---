---
name: biotech-ranking-rubric
description: Deterministic scoring rubric for ranking final biotech candidates. Load inside the ranking agent or any agent that must explain ordering.
disable-model-invocation: true
user-invocable: false
---

# Ranking rubric

## Score components
Use these components when ranking final candidates:
- `date_certainty` (0.25)
- `catalyst_materiality` (0.20)
- `price_setup` (0.20)
- `balance_sheet_safety` (0.15)
- `tradability` (0.10)
- `historical_support` (0.10)

## Penalty
Subtract a `thesis_penalty` based on:
- `thesis_break_score`
- count and severity of `red_flags`

## Interpretation
- `>= 0.80` → high-conviction core setup
- `0.68 - 0.79` → good but caveat-heavy
- `0.55 - 0.67` → tradable only with tighter sizing / conditions
- `< 0.55` → lower-priority residual candidate

## Ranking behavior
- Prefer candidates with explicit dates over vague windows
- Prefer executable setups over merely interesting stories
- Never let historical notes dominate date certainty or risk reality
