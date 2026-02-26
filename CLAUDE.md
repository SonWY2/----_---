# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**Biotech Alpha**: FDA 신약 승인 이벤트(PDUFA) 및 임상시험 결과 발표를 활용한 바이오 주식 자동 매매 시스템. 주요 이벤트 발표 60일 전부터 발생하는 "기대감 상승(Run-up)" 구간을 포착하여 최적의 매매 타이밍을 계산합니다.

**핵심 전략**: FDA 승인 이벤트 60일 전 매수, 7일 전 매도로 이진 리스크(승인/거부) 회피. 계층적 멀티 에이전트 구조로 종목 발굴 → 검증 → 분석 → 리스크 스크리닝을 자동화합니다.

## 프로젝트 구조

```
biotech_alpha/
├── .claude/
│   ├── CLAUDE.md              # 에이전트 코딩 규칙 및 아키텍처 원칙
│   ├── settings.json          # 커맨드 정의, 샌드박스 설정, 훅 설정
│   ├── commands/hunt.md       # 워크플로우 시작점 (/hunt 명령어)
│   ├── agents/                # 7개의 전문 에이전트 정의 파일 (00-22)
│   ├── context/strategy_pdufa.md  # PDUFA Run-up 트레이딩 전략 로직
│   ├── hooks/clean_memory.py  # 실행 전 메모리 초기화 스크립트
│   └── memory/                # 에이전트 간 JSON 기반 데이터 교환 폴더
├── tools/market_calc.py       # 날짜 계산 및 주가 트렌드 분석 유틸리티
├── outputs/                   # 최종 분석 리포트 저장소 (report_YYYYMMDD.md)
└── requirements.txt           # Python 의존성 라이브러리
```

## 개발 환경 설정

**의존성 설치:**
```bash
cd biotech_alpha
pip install -r requirements.txt
```

**필수 라이브러리**: pandas, yfinance, requests, beautifulsoup4

## 메인 워크플로우

**주요 명령어**: `/hunt`

이 명령어는 계층적 에이전트 워크플로우를 트리거합니다:

1. **CIO (00_cio.md)**: 전체 프로세스 총괄 및 오케스트레이션
2. **Discovery Lead (10)** → **Event Scout (11)**: 향후 이벤트 탐색 → **Fact Verifier (12)**: 공식 소스에서 날짜 검증
3. **Analysis Lead (20)** → **Quant (21)**: 매수/매도 날짜 계산 → **Risk Screener (22)**: 현금 보유량 체크
4. 결과는 `.claude/memory/`에 JSON 파일로 저장되며, 최종 리포트는 `outputs/`에 생성됨

**Pre-command 훅**: `/hunt` 실행 전 자동으로 `clean_memory.py`를 실행하여 이전 데이터 삭제

## 아키텍처 원칙

**계층적 에이전트 시스템 (Hierarchical Agents)**:
- CIO(총괄)가 Lead 에이전트에게 업무 위임
- Lead 에이전트가 Specialist 에이전트를 조율
- CIO는 직접 작업 수행하지 않음 - 오케스트레이션만 담당
- 모든 데이터는 `.claude/memory/*.json` 파일을 통해 전달

**증거 기반 필터링 (Evidence-Based)**:
- 모든 이벤트 날짜는 공식 소스에서 검증 필수 (기업 IR, FDA.gov, ClinicalTrials.gov)
- 서드파티 캘린더 사이트는 "추정(Estimated)" 리스크로 표시
- 신뢰할 수 있는 출처 없는 루머는 제외

**리스크 관리 (Risk Control)**:
- 현금 보유 기간(Cash Runway) < 6개월 = CRITICAL (유상증자 리스크)
- 현금 보유 기간 > 12개월 = SAFE
- 52주 최고점 근처 거래되는 종목은 제외 (이미 가격 반영됨)

## 핵심 기술 세부사항

**날짜 처리**:
- 모든 날짜는 `pandas.Timestamp` 사용 (문자열이나 datetime 객체 직접 사용 금지)
- `datetime.now()`를 기준으로 상대적 계산 - 하드코딩된 날짜 사용 금지
- 매수일 = 이벤트 날짜 - 60일
- 매도일 = 이벤트 날짜 - 7일

**주가 데이터**:
- `yfinance` 라이브러리 사용
- 20일 이동평균선으로 트렌드 판단
- 3개월 히스토리 데이터 분석

**에이전트 간 통신**:
- JSON 파일을 통한 데이터 교환 (`.claude/memory/` 폴더)
- 표준 파일명: `raw_events.json`, `verified_events.json`, `final_candidates.json`
- 각 에이전트는 입력 JSON 읽기 → 처리 → 출력 JSON 작성

**샌드박스 제약사항**:
- 네트워크: finance.yahoo.com, fda.gov, clinicaltrials.gov, biopharmcatalyst.com만 허용
- 파일시스템: `.claude/memory/`, `./outputs/`, `./tools/`만 접근 가능
- 사용자의 명시적 승인 없이 실제 거래 API 실행 금지

## 개별 컴포넌트 테스트

**주가 계산기 테스트:**
```bash
python tools/market_calc.py <티커> <이벤트_날짜>
# 예시: python tools/market_calc.py AAPL 2026-06-01
```

**메모리 수동 초기화:**
```bash
python .claude/hooks/clean_memory.py
```

**에이전트 정의 확인:**
```bash
ls -la .claude/agents/
# 확인 내용: 00_cio.md, 10_discovery_lead.md, 11_event_scout.md,
#           12_fact_verifier.md, 20_analysis_lead.md, 21_quant.md, 22_risk_screener.md
```

## 데이터 흐름 예시

1. **Event Scout** → `memory/raw_events.json`: `[{ticker, event, date, source}]`
2. **Fact Verifier** → 원본 이벤트 필터링 → **Discovery Lead** → `memory/verified_events.json`
3. **Quant Analyst** → `market_calc.py` 사용 → `target_entry_date`, `trend` 추가
4. **Risk Screener** → `cash_runway`, `risk_level` 추가
5. **Analysis Lead** → 90일 이내 매수일 필터링 → `memory/final_candidates.json`
6. **CIO** → `outputs/report_YYYYMMDD.md` 생성

## 핵심 규칙 (biotech_alpha/.claude/CLAUDE.md 기반)

- 계층적 에이전트 구조 엄격히 준수
- 모든 이벤트 날짜는 공식 출처 검증 필수
- 현금 보유 기간 6개월 미만 기업은 제외
- 날짜 처리는 `pandas.Timestamp` 전용
- 주가 데이터는 `yfinance`로 조회
- 에이전트 간 데이터 교환은 `.claude/memory/` JSON 파일로만 수행
- 하드코딩된 날짜 금지 - `datetime.now()` 기준 상대 계산
- 실제 매매 주문 실행 금지 - 분석 및 리포팅 전용
