# Claude Code 패키지 수정 사항 (v2)

## 무엇을 고쳤는가
- legacy `commands/hunt.md` 기반 구조를 **skills 기반 `/hunt`** 구조로 전환
- 모든 subagent를 **YAML frontmatter** 형식으로 재작성
- nested lead-agent 구조를 제거하고 **main-thread orchestration + flat specialists** 구조로 변경
- `.claude/settings.json`을 최신 `permissions` / `sandbox` 스키마로 교체
- `.claude/memory/*.json` 초기 산출물 제거 및 `.gitkeep`만 유지
- `memory/...` 와 `.claude/memory/...` 혼용 문제 제거
- report contract를 별도 skill로 분리
- 한국 6자리 종목코드에 대해 `.KS/.KQ` 가격티커를 자동 시도하는 유틸 추가

## 새 실행 흐름
`/hunt` -> scout -> verifier -> quant -> risk -> historical -> report

## 주요 산출물
- `.claude/memory/raw_events.json`
- `.claude/memory/verified_events.json`
- `.claude/memory/final_candidates.json`
- `.claude/memory/enriched_candidates.json`
- `outputs/report_YYYYMMDD.md`
