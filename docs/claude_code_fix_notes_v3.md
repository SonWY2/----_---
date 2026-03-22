# Claude Code 패키지 수정 사항 (v3)

## 왜 v3가 필요한가
v2는 Claude Code 최신 규약에 맞는 **실행 가능한 구조**로 정리하는 데 초점을 두었다.
v3는 그 위에 **결과 품질 향상용 단계**를 추가했다.

핵심 방향:
- discovery와 verification 사이에 **정규화 계층** 추가
- verification 이후 **bear-case / negative thesis 하드닝** 추가
- quant 이후 **tradability 단계** 추가
- historical 분석 전에 **historical event set 구축** 추가
- 최종 보고서 전에 **deterministic ranking + report audit** 추가

## 새 실행 흐름
`/hunt`
-> universe-builder
-> scout
-> evidence-normalizer
-> fact-verifier
-> bear-case-auditor
-> quant
-> tradability
-> risk
-> historical-set-builder
-> historical-annotator
-> candidate-ranker
-> report-writer
-> report-auditor

## 새 메모리 산출물
- `.claude/memory/coverage_universe.json`
- `.claude/memory/normalized_event_claims.json`
- `.claude/memory/red_flags.json`
- `.claude/memory/verified_events_hardened.json`
- `.claude/memory/watchlist_candidates_hardened.json`
- `.claude/memory/excluded_events_hardened.json`
- `.claude/memory/tradability_screen.json`
- `.claude/memory/historical_event_sets.json`
- `.claude/memory/historical_analysis_input.json`
- `.claude/memory/ranked_candidates.json`
- `.claude/memory/report_audit.json`

## 새 Python helper
- `tools/tradability_calc.py`
- `tools/rank_candidates.py`
- `tools/report_audit.py`

## 품질적으로 좋아진 점
1. **중복/충돌된 discovery evidence를 정리하고 나서 verification**
2. **좋은 근거뿐 아니라 thesis를 깨는 근거도 수집**
3. **실제로 매매 가능한 유동성인지 별도 판정**
4. **historical_event_dates 부재로 인한 단일 표본 fallback 감소**
5. **최종 후보 순위가 더 재현 가능하게 정리**
6. **리포트 섹션/요약표/티커 누락을 자동 감사**
