---
name: hunt
description: Run the end-to-end Biotech Alpha workflow to discover biotech catalysts, normalize and verify evidence, harden against bear cases, score tradability, rank candidates, and write an audited markdown report. Use when the user asks for biotech catalyst screening or biotech event-driven trade ideas.
argument-hint: [optional focus, market, or exclusions]
allowed-tools: Agent, Read, Write, Bash(python .claude/hooks/clean_memory.py*), Bash(python3 .claude/hooks/clean_memory.py*), Bash(python tools/market_calc.py *), Bash(python3 tools/market_calc.py *), Bash(python tools/tradability_calc.py *), Bash(python3 tools/tradability_calc.py *), Bash(python tools/event_study.py *), Bash(python3 tools/event_study.py *), Bash(python tools/rank_candidates.py *), Bash(python3 tools/rank_candidates.py *), Bash(python tools/report_finalizer.py *), Bash(python3 tools/report_finalizer.py *), Bash(python tools/report_audit.py *), Bash(python3 tools/report_audit.py *), Bash(python tools/http_research.py *), Bash(python3 tools/http_research.py *), Bash(date +%F)
effort: high
---

# Biotech Alpha Hunt

Previous memory cleanup:
!`python .claude/hooks/clean_memory.py`

Today:
!`date +%F`

Run the workflow in the **main conversation context**, not through nested lead-agents. Subagents must not attempt to spawn other subagents.

## Optional user focus
User-supplied focus or constraints: `$ARGUMENTS`
- If arguments are empty, run the default global biotech screen
- If arguments mention a region, event type, ticker family, or exclusions, apply them while preserving the same output contracts

## Execution order
1. Use `biotech-universe-builder` to create `.claude/memory/coverage_universe.json`
2. Use `biotech-event-scout` to create:
   - `.claude/memory/raw_events.json`
   - `.claude/memory/discovery_coverage.json`
3. Recovery loop A:
   - Trigger: `raw_event_count < 12`, or `us_count == 0`, or `kr_count == 0`
   - Read `.claude/memory/discovery_coverage.json` and inspect `coverage_gaps`, `search_failures`, and `fetch_failures`
   - Rerun `biotech-event-scout` once with **targeted recovery queries** based on the weak area
   - Recovery query families to emphasize:
     - US weak coverage:
       - `FDA action date 2026 site:sec.gov biotech`
       - `PDUFA date NDA BLA 2026 biotech press release`
       - `advisory committee 2026 FDA calendar oncology`
     - KR weak coverage:
       - `식품의약품안전처 품목허가 2026 바이오`
       - `KOSDAQ 바이오텍 임상 3상 topline 2026`
       - `한국 제약 바이오 규제 승인 일정 2026`
     - Phase / readout weak coverage:
       - `phase 3 topline data expected H1 2026 biotech`
       - `clinical trial results anticipated 2026 biotech`
   - On the retry pass, explicitly mention which recovery family is being targeted
4. Use `biotech-evidence-normalizer` to create `.claude/memory/normalized_event_claims.json`
5. Use `biotech-fact-verifier` to create:
   - `.claude/memory/verified_events.json`
   - `.claude/memory/watchlist_candidates.json`
   - `.claude/memory/excluded_events.json`
   - `.claude/memory/verification_log.json`
6. Use `biotech-bear-case-auditor` to create:
   - `.claude/memory/red_flags.json`
   - `.claude/memory/verified_events_hardened.json`
   - `.claude/memory/watchlist_candidates_hardened.json`
   - `.claude/memory/excluded_events_hardened.json`
7. Recovery loop B:
   - If `verified_events_hardened.json` contains fewer than 3 candidates, do one targeted rediscovery pass focused on high-confidence watchlist names, then rerun normalization → verification → bear-case hardening once
8. Degradation thresholds:
   - If after Recovery loop A both `us_count == 0` and `kr_count == 0`, abort and surface a discovery failure summary to the user
   - If only one region is available, continue in single-region mode and ensure the final report warns about regional coverage limits in section 1
   - If `verified_events_hardened.json` is still empty after Recovery loop B, continue the downstream pipeline with **valid empty artifacts** and instruct the report writer to emit a minimal "후보 없음" report instead of crashing the workflow
9. Use `biotech-quant-analyst` to create `.claude/memory/quant_candidates.json`
10. Use `biotech-tradability-screener` to create `.claude/memory/tradability_screen.json`
11. Use `biotech-risk-screener` to create:
    - `.claude/memory/risk_screening.json`
    - `.claude/memory/final_candidates.json`
12. Use `biotech-historical-set-builder` to create `.claude/memory/historical_event_sets.json`
13. Use `biotech-historical-annotator` to create:
    - `.claude/memory/historical_analysis_input.json`
    - `.claude/memory/historical_context.json`
    - `.claude/memory/enriched_candidates.json`
14. Use `biotech-candidate-ranker` to create `.claude/memory/ranked_candidates.json`
15. Use `biotech-report-writer` to create `outputs/report_YYYYMMDD.md`
16. Use `biotech-report-auditor` to create `.claude/memory/report_audit.json`
17. Repair loop:
    - If audit status is `fail`, run `biotech-report-writer` one repair pass using the audit issues, then rerun `biotech-report-auditor`
    - Stop after one repair loop and surface remaining issues honestly

## Global constraints
- Respect `.claude/context/strategy_pdufa.md`
- Keep US and Korean biotech coverage unless the user explicitly narrows scope
- Core lane must be based on confirmed-and-hardened events only
- Watchlist lane may include estimated dates but must label uncertainty
- Historical context is annotation only, never the sole reason to discard a core candidate
- Use hardened watchlist and excluded files for the final report
- Prefer truthful degradation over forced completeness when search quality collapses

## Final response to user
After the report is written and audited, briefly summarize:
- report path
- audit status
- 1 to 5 top ranked core candidates
- key reasons any major names were excluded or downgraded
- whether the workflow ran in full-coverage mode, single-region fallback mode, or empty-candidate degradation mode
