# Claude Code project instructions for Biotech Alpha

## What this repository is
Biotech Alpha is a **research-only** workflow for screening biotech catalyst trades. It does not place orders. The purpose is to discover, verify, harden, rank, annotate, and report event-driven biotech candidates.

## How to use it
- Main entrypoint: `/hunt`
- `/hunt` is implemented as a **skill** at `.claude/skills/hunt/SKILL.md`
- The workflow fans out through **specialist subagents** from the main conversation context

## Architecture
This package intentionally avoids nested lead-agents. Claude Code subagents cannot spawn other subagents inside a normal subagent execution path, so the orchestration is flattened:

1. `biotech-universe-builder`
2. `biotech-event-scout`
3. `biotech-evidence-normalizer`
4. `biotech-fact-verifier`
5. `biotech-bear-case-auditor`
6. `biotech-quant-analyst`
7. `biotech-tradability-screener`
8. `biotech-risk-screener`
9. `biotech-historical-set-builder`
10. `biotech-historical-annotator`
11. `biotech-candidate-ranker`
12. `biotech-report-writer`
13. `biotech-report-auditor`

## Critical contracts
- Always use `.claude/memory/...` paths
- Do not recreate the old `memory/...` path variant
- Final report path: `outputs/report_YYYYMMDD.md`
- Final section must be `## 7) 최종 요약표`
- `report_audit.json.status` must be `pass` before the workflow is considered complete
- `discovery_coverage.json` must include `search_failures` and `fetch_failures` when search quality is weak

## Quality strategy
- Separate **discovery**, **normalization**, **verification**, **bear-case hardening**, and **ranking**
- Preserve base audit artifacts even when hardened variants are created
- Use deterministic helper scripts for price timing, tradability scoring, candidate ranking, report auditing, and direct HTTP fallback research
- Allow targeted retry when coverage or verification quality is clearly weak
- Allow graceful degradation into a truthful `후보 없음` report when discovery or verification collapses

## Scripts
- `python .claude/hooks/clean_memory.py`
- `python tools/market_calc.py <ticker> <event_date> [--price-ticker ...]`
- `python tools/tradability_calc.py <ticker> [--price-ticker ...]`
- `python tools/event_study.py .claude/memory/historical_analysis_input.json --output .claude/memory/historical_context.json`
- `python tools/rank_candidates.py .claude/memory/enriched_candidates.json --output .claude/memory/ranked_candidates.json`
- `python tools/report_finalizer.py outputs/report_YYYYMMDD.md --core .claude/memory/ranked_candidates.json --watchlist .claude/memory/watchlist_candidates_hardened.json`
- `python tools/report_audit.py outputs/report_YYYYMMDD.md --ranked .claude/memory/ranked_candidates.json --watchlist .claude/memory/watchlist_candidates_hardened.json --excluded .claude/memory/excluded_events_hardened.json --output .claude/memory/report_audit.json`
- `python tools/http_research.py search --query "PDUFA 2026 biotech" --max-results 8`
- `python tools/http_research.py fetch --url "https://www.sec.gov/..." --max-chars 6000`
