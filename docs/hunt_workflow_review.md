# /hunt 멀티에이전트 워크플로우 점검 리포트

## 범위
- 트리거: `.claude/commands/hunt.md`
- 오케스트레이션: `.claude/agents/00_cio.md`
- Discovery 체인: `10_discovery_lead.md` → `11_event_scout.md` → `12_fact_verifier.md`
- Analysis 체인: `20_analysis_lead.md` → `21_quant.md` → `22_risk_screener.md` → `23_historical_significance.md`
- 출력 후처리: 리포트 본문/요약표 수동 작성 품질 점검
- 훅/세션 초기화: `.claude/settings.json`, `.claude/hooks/clean_memory.py`

## 단계별 데이터 전달 포맷 검증

### 1) `/hunt` → CIO
- 입력: 사용자 `/hunt` 커맨드
- 기대: CIO가 컨텍스트를 읽고 Discovery/Analysis를 순차 위임
- 검증 포인트:
  - 보고서 출력 형식은 지정된 요약표 헤더 순서와 일치해야 함

### 2) Event Scout → Discovery Lead (`raw_events.json`, `discovery_coverage.json`)
- Scout 스키마(권장):
  - `event_id`, `ticker`, `event_type`, `event_date_raw`, `event_date`, `source_url`, `source_type`, `discovered_at`, `notes`
- 실제 메모리 샘플에는 `event`, `date`, `source` 등 단축 필드가 존재할 수 있음.
- 리스크:
  - 엄격한 파서가 들어오면 스키마 불일치로 하위 단계 실패 가능.
- 개선:
  - Discovery Lead에서 정규화 단계(별칭 매핑)를 명시하거나, Scout 출력 키를 강제.

### 3) Fact Verifier → Discovery Lead (`verified_events.json`, `watchlist_candidates.json`)
- Verifier 반환 스키마(권장):
  - `verification_status`, `confidence`, `evidence[]`, `normalized_event_date`
- Analysis 단계는 `event_date|date|normalized_event_date` 별칭을 폭넓게 허용하는 것이 안전.
- 현재 구조는 Dual-lane 개념(Confirmed/Estimated) 자체는 일관적.

### 4) Analysis Lead ↔ Quant/Risk
- Quant 산출 핵심: `target_entry_date`, `target_exit_date`, `days_until_entry`
- Risk 산출 핵심: `risk_level`, `cash_runway_months`
- 필터 규칙: `target_entry_date ∈ [Today, Today+90d]` + `risk_level != Critical`
- 리스크:
  - 기존 샘플 파일엔 `entry_date/exit_date` 필드도 존재하므로, 리포트 생성기와 동일하게 별칭 허용 필요.

### 5) Historical Significance 주석 단계
- 입력: `final_candidates.json`
- 출력: `historical_context.json`, `enriched_candidates.json`
- 규칙: 후보 제외 필터가 아닌 annotation-only
- 현재 에이전트 정의가 이 원칙을 명시하고 있어 방향 적합.

### 6) 최종 리포팅
- 최종 요약표는 코드 자동생성 없이, 아래 헤더 순서로 수동 작성해야 함:
  - `티커 | pdufa일정 | 진입일 | 매도일 | 현재상황 | 비고 | 투자등급` (투자등급은 신호등 `🟢/🟡/🔴`)
- 상위 프롬프트에서 다른 헤더를 요구하면 충돌 발생 가능.
- 개선:
  - `/hunt`와 CIO 지침에서 최종 표 헤더를 동일 기준으로 고정.

## 이번 반영 개선 사항
1. `.claude/agents/00_cio.md` 중복/상충 지시를 제거하고 단일 canonical 플로우로 정리.
2. 파일 경로 검증 시 `.claude/memory/...` 절대(레포 기준 상대) 경로로 일관화.
3. `.claude/settings.json` 훅을 `UserPromptSubmit` 전역 트리거에서 `pre_command.hunt`로 변경해, `/hunt` 실행 시점에만 메모리 청소.
4. `.claude/commands/hunt.md`의 최종 요약표 요구사항을 수동 작성 원칙과 고정 헤더 순서에 맞춤.

## 추가 권장 개선(후속)
- `tools/schema_check.py` 같은 계약 검증 도구를 추가해 `raw/verified/final/enriched` 스키마를 자동 점검.
- Discovery 단계에서 키 정규화(`date`→`event_date`, `event`→`event_type`)를 명시적 수행.
- `verification_log.json`를 리포트 부록에 링크해 근거 추적성을 강화.
