---
name: biotech-report-contract
description: Final report structure, section order, and exact summary-table contract for Biotech Alpha. Load inside the report-writing agent.
disable-model-invocation: true
user-invocable: false
---

# Report contract

## Mandatory section order
1. `## 1) 스크리닝 기준`
2. `## 2) 핵심 매매 후보(확정형, Core Tradable)`
3. `## 3) 확장 후보군(추정형, Expanded Watchlist)`
4. `## 4) 역사적 유의점 노트 (Historical Significance Notes)`
5. `## 5) 리스크 및 실행 규칙`
6. `## 6) 제외 종목 (Excluded Events)`
7. `## 7) 최종 요약표`

## Core candidate ordering
- Sort core candidates by `rank` ascending, then `final_score` descending
- Within section 2, split into:
  - `### Tier 1 (즉각 진입)`
  - `### Tier 2 (진입 대기)`
- For every core candidate, show `final_score`, key score drivers, and major caveats

## Final summary table
The tail section must contain a markdown table whose header is exactly:

`티커 | pdufa일정 | 진입일 | 매도일 | 현재상황 | 비고 | 투자등급`

## Signal mapping
- `🟢` = Tier 1 / confirmed / currently actionable
- `🟡` = Tier 2 or watchlist / conditional
- `🔴` = excluded / avoid

## Report writing rules
- Keep narrative sections concise but specific
- Explicitly state why each ticker is actionable now, waiting, or excluded
- Preserve important caveats such as estimated date, low sample size, near-52w-high, thin liquidity, financing risk, or thesis-break evidence


## Empty-report rule
- Even when ranked candidates are empty, the report must still include all seven mandatory sections
- Section 2 and section 3 may explicitly say `후보 없음`
- The final summary table header must still be rendered exactly, even when there are zero data rows
