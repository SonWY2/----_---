---
name: biotech-web-fallback
description: WebSearch/WebFetch failure taxonomy, retry ladders, and Python HTTP fallback usage for biotech research agents. Load in any agent that must recover from search, fetch, or primary-source failures.
disable-model-invocation: true
user-invocable: false
---

# Web fallback protocol

Use this skill when any of the following occurs:
- **Type A / no_results**: WebSearch returns no useful results
- **Type B / low_relevance**: results exist but are mostly irrelevant or low quality
- **Type C / fetch_failed**: WebFetch or direct page access returns 403 / timeout / 5xx
- **Type D / primary_source_missing**: only third-party sources are found and official / regulator sources are still missing

## Retry ladder
For a single claim or query family, attempt up to **3 formulations** before declaring it unresolved:
1. **Primary**: exact company name + exact event type + direct date wording
2. **Fallback 1**: ticker + event type + year or half-year
3. **Fallback 2**: broader catalyst phrase or regulator-specific wording

Examples:
- `BridgeBio PDUFA May 2026 press release`
- `BBIO PDUFA 2026`
- `FDA action date 2026 site:sec.gov biotech`

For Korean names:
- `회사명 품목허가 2026`
- `티커 임상 3상 결과 2026`
- `식품의약품안전처 바이오 품목허가 2026`

## Python HTTP fallback helper
If WebSearch or WebFetch is weak or the user explicitly asks for direct HTTP retrieval, use:

```bash
python tools/http_research.py search --query "PDUFA 2026 biotech" --max-results 8
python tools/http_research.py search --query "PDUFA 2026 biotech" --site sec.gov --max-results 8
python tools/http_research.py fetch --url "https://www.sec.gov/..." --max-chars 6000
python tools/http_research.py fetch --url "https://example.com/..." --try-mobile --max-chars 6000
```

### Expected output shape
Search output:
```json
{
  "mode": "search",
  "query": "...",
  "results": [
    {"rank": 1, "title": "...", "url": "https://...", "snippet": "..."}
  ],
  "errors": []
}
```

Fetch output:
```json
{
  "mode": "fetch",
  "url": "https://...",
  "final_url": "https://...",
  "status_code": 200,
  "title": "...",
  "excerpt": "...",
  "text": "...",
  "method": "requests|urllib",
  "errors": []
}
```

## Logging requirements
Whenever fallback is used, keep a structured audit trail.

For search failures, append objects like:
```json
{
  "query": "KOSDAQ 바이오 임상 3상 2026",
  "failure_type": "no_results|low_relevance|primary_source_missing",
  "attempts": 3,
  "fallback_used": "ticker+event+year or http_research search",
  "notes": "optional explanation"
}
```

For fetch failures, append objects like:
```json
{
  "url": "https://...",
  "reason": "403|timeout|5xx|blocked",
  "source_was": "official_ir|regulator|third_party",
  "attempted_alt_fetch": true,
  "fallback_used": "http_research fetch"
}
```

## Degradation rules
- Never fabricate evidence.
- If all 3 query formulations fail, keep the evidence array empty and mark the claim or candidate as unresolved / low confidence.
- If only third-party evidence survives, lower confidence and add `primary_source_unverified` to risk flags.
- Prefer a truthful incomplete record over an invented complete record.
