# Biotech Alpha Claude Code quality package v4

## What changed
This revision incorporates search-failure-aware workflow improvements and a Python HTTP fallback path.

### Workflow / prompt changes
- Added explicit search failure taxonomy (A/B/C/D)
- Added structured `search_failures` and `fetch_failures` fields to `discovery_coverage.json`
- Added explicit Recovery loop A query families in `/hunt`
- Added degradation thresholds in `/hunt`
- Added empty-input handling and minimal-report behavior across downstream agents
- Raised `maxTurns` for search-heavy agents
- Added search fallback instructions to scout / verifier / bear-case / risk / historical-set agents

### Tooling changes
- Added `tools/http_research.py`
  - `search` mode: DuckDuckGo HTML / lite HTML fallback via `requests` + `urllib`
  - `fetch` mode: direct URL retrieval via `requests`, then `urllib`
  - optional `--try-mobile` heuristic for stubborn URLs
- Added `biotech-web-fallback` support skill
- Extended `settings.json` allowed Bash commands and network domains for regulator / IR / fallback research

## Why this matters
The prior package could recover only from coarse coverage failure. This revision explicitly handles:
- no-result search failures
- irrelevant-result search failures
- fetch failures such as 403 / timeout
- primary-source quality failures where only third-party evidence exists

## Recommended usage
- Keep using `/hunt` as the primary entrypoint
- If a user explicitly asks for direct HTTP retrieval or WebSearch is unreliable, allow the agents to use `tools/http_research.py`
- Review `.claude/memory/discovery_coverage.json` after discovery to inspect `search_failures` / `fetch_failures`
