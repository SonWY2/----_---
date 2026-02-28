# Biotech Alpha Project Guidelines

## Project Goal
FDA PDUFA(신약 승인) 및 주요 임상 발표 이벤트를 기반으로, 발표 2~3개월 전 '기대감 상승(Run-up)' 구간을 포착하여 매매 신호를 생성하는 자동화 시스템 구축.

## Architecture
- **Hierarchical Agents**: CIO(총괄) -> Leads(중간관리) -> Specialists(실무) 구조를 엄격히 준수한다.
- **Evidence-Based**: 모든 이벤트 날짜는 공식 출처(IR, FDA, ClinicalTrials.gov) 검증 없이는 사용 불가.
- **Risk Control**: 재무 리스크(현금 고갈)가 있는 기업은 기술적 지표가 좋아도 제외한다.
- **Dual-Lane Discovery**: Confirmed 이벤트는 tradable lane, Estimated 이벤트는 watchlist lane으로 분리한다.
- **Historical Annotation**: 최종 후보에 1~5년 히스토리 유의성 노트를 추가하되, 필터로 사용하지 않는다.

## Coding Standards (Python)
- 모든 날짜 처리는 `pandas.Timestamp`를 표준으로 한다.
- 주가 데이터는 `yfinance`를 사용한다.
- 에이전트 간 데이터 교환은 `.claude/memory/` 폴더 내의 JSON 파일을 통해서만 수행한다.
- 하드코딩된 날짜를 피하고 `datetime.now()`를 기준으로 상대적 기간을 계산한다.

## Memory Contracts
- Core files: `raw_events.json`, `verified_events.json`, `final_candidates.json`
- Expanded files: `watchlist_candidates.json`, `discovery_coverage.json`, `verification_log.json`
- Historical files: `historical_context.json`, `enriched_candidates.json`

## Terminal Behavior
- 사용자의 명시적 승인 없이 주식 매수/매도 주문 API를 실행하지 않는다 (현재는 분석 및 리포트 전용).
- 긴 로그는 생략하고 핵심 의사결정 과정만 출력한다.
