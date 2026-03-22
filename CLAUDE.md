# Biotech Alpha

A Claude Code workflow for collecting, hardening, ranking, and reporting biotech catalyst-driven trading ideas.

## Entry point
Use `/hunt` inside Claude Code. The skill will:

1. clear old workflow memory
2. build a coverage universe
3. discover catalyst events
4. normalize discovery evidence
5. verify event truth and timing
6. run bear-case / negative-thesis hardening
7. score timing and price position
8. screen tradability and balance-sheet risk
9. build historical event sets
10. add historical context
11. rank final candidates deterministically
12. write and audit `outputs/report_YYYYMMDD.md`

## Implementation notes
- Skills live in `.claude/skills/`
- Subagents live in `.claude/agents/`
- Shared runtime artifacts live in `.claude/memory/`
- Python helper scripts live in `tools/`
- WebSearch/WebFetch failure handling is supplemented with `tools/http_research.py`

## Included scopes
- US and Korean biotech names
- FDA / AdCom / NDA / BLA / Phase 2-3 / MFDS catalyst research
- Research-only output; no order execution
