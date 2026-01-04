# Biotech Alpha Project Guidelines

## Project Goal
FDA PDUFA(신약 승인) 및 주요 임상 발표 이벤트를 기반으로, 발표 2~3개월 전 '기대감 상승(Run-up)' 구간을 포착하여 매매 신호를 생성하는 자동화 시스템 구축.

## Architecture
- **Hierarchical Agents**: CIO(총괄) -> Leads(중간관리) -> Specialists(실무) 구조를 엄격히 준수한다.
- **Evidence-Based**: 모든 이벤트 날짜는 공식 출처(IR, FDA, ClinicalTrials.gov) 검증 없이는 사용 불가.
- **Risk Control**: 재무 리스크(현금 고갈)가 있는 기업은 기술적 지표가 좋아도 제외한다.

## Coding Standards (Python)
- 모든 날짜 처리는 `pandas.Timestamp`를 표준으로 한다.
- 주가 데이터는 `yfinance`를 사용한다.
- 에이전트 간 데이터 교환은 `.claude/memory/` 폴더 내의 JSON 파일을 통해서만 수행한다.
- 하드코딩된 날짜를 피하고 `datetime.now()`를 기준으로 상대적 기간을 계산한다.

## Terminal Behavior
- 사용자의 명시적 승인 없이 주식 매수/매도 주문 API를 실행하지 않는다 (현재는 분석 및 리포트 전용).
- 긴 로그는 생략하고 핵심 의사결정 과정만 출력한다.
