---
name: biotech-memory-contracts
description: Exact file and JSON contracts for the Biotech Alpha workflow. Load inside agents that read or write .claude/memory artifacts.
disable-model-invocation: true
user-invocable: false
---

# File path contract
Always use **`.claude/memory/...`** paths. Never use `memory/...` without the `.claude/` prefix.

## Required artifacts
Base discovery and verification:
- `.claude/memory/coverage_universe.json`
- `.claude/memory/raw_events.json`
- `.claude/memory/discovery_coverage.json`
- `.claude/memory/normalized_event_claims.json`
- `.claude/memory/verified_events.json`
- `.claude/memory/watchlist_candidates.json`
- `.claude/memory/excluded_events.json`
- `.claude/memory/verification_log.json`

Hardened downstream artifacts:
- `.claude/memory/red_flags.json`
- `.claude/memory/verified_events_hardened.json`
- `.claude/memory/watchlist_candidates_hardened.json`
- `.claude/memory/excluded_events_hardened.json`

Timing / execution quality:
- `.claude/memory/quant_candidates.json`
- `.claude/memory/tradability_screen.json`
- `.claude/memory/risk_screening.json`
- `.claude/memory/final_candidates.json`

Historical / ranking / reporting:
- `.claude/memory/historical_event_sets.json`
- `.claude/memory/historical_analysis_input.json`
- `.claude/memory/historical_context.json`
- `.claude/memory/enriched_candidates.json`
- `.claude/memory/ranked_candidates.json`
- `.claude/memory/report_audit.json`

## Discovery coverage contract
`.claude/memory/discovery_coverage.json` should include at minimum:
```json
{
  "query_families": ["..."],
  "source_mix": {"official": 0, "regulator": 0, "third_party": 0},
  "raw_event_count": 0,
  "deduped_event_count": 0,
  "us_count": 0,
  "kr_count": 0,
  "universe_file_used": true,
  "universe_hit_count": 0,
  "coverage_gaps": ["missing KR phase3 names"],
  "search_failures": [
    {
      "query": "...",
      "failure_type": "no_results|low_relevance|primary_source_missing",
      "attempts": 3,
      "fallback_used": "..."
    }
  ],
  "fetch_failures": [
    {
      "url": "https://...",
      "reason": "403|timeout|5xx",
      "source_was": "official_ir|regulator|third_party",
      "fallback_used": "http_research fetch"
    }
  ]
}
```

## Verification log contract
Every processed candidate should appear in `.claude/memory/verification_log.json`, including when primary-source verification fails. Include these when applicable:
- `search_attempts`
- `official_source_attempts`
- `fetch_failures`
- `fallback_used`
- `verification_status`
- `confidence_score`
- `risk_flags`
- `reason`

## Candidate minimum fields
Every tradable candidate should preserve these keys when available:
- `event_id`
- `ticker`
- `company_name`
- `event_type`
- `event_date`
- `price_ticker` or `resolved_price_ticker`
- `target_entry_date`
- `target_exit_date`
- `trend`
- `current_price`
- `tier`
- `risk_level`
- `risk_reason`
- `tradability_score`
- `confidence_score`

## Empty-input contract
If an upstream artifact is empty or missing after a recovery loop, downstream agents must still write **structurally valid empty outputs** instead of erroring.

Examples:
- empty list artifacts: `[]`
- empty audit objects: `{ "status": "pass", ... }` only when the report truly matches an empty ranked set
- minimal report still required at `outputs/report_YYYYMMDD.md`

## Reporting outputs
- Final report path: `outputs/report_YYYYMMDD.md`
- The final report must be based on `.claude/memory/ranked_candidates.json`, `.claude/memory/watchlist_candidates_hardened.json`, and `.claude/memory/excluded_events_hardened.json`
- The workflow is complete only when `.claude/memory/report_audit.json` reports `"status": "pass"`
