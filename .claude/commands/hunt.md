이제부터 'Biotech Alpha' 워크플로우를 시작합니다.

1. **Role**: 당신은 지금부터 **CIO(Chief Investment Officer)** 에이전트(`agents/00_cio.md`)로서 행동해야 합니다.
2. **Context**: `.claude/context/strategy_pdufa.md`의 전략을 로드하십시오.
3. **Objective**: 
   - 오늘 날짜를 확인하십시오.
   - 오늘부터 **향후 3개월(90일)** 이내에 '매집(Buy)' 타이밍이 오는 핵심 후보를 찾으십시오.
   - 이벤트 날짜 자체가 아니라, **Run-up 시작일(D-60)**이 이 기간에 포함되는지가 핵심입니다.
   - 동시에 확장 후보군(추정형 watchlist)을 별도로 유지하십시오.
   - 핵심 후보에 대해 1~5년 히스토리 기반 유의성 노트를 추가하십시오.
4. **Output**: 최종 결과는 `outputs/report_YYYYMMDD.md`에 저장하고 요약본을 터미널에 출력하십시오.
5. **Finalization (Mandatory)**:
   - 본문 작성 후 반드시 아래 명령으로 리포트를 최종화하십시오.
   - `python tools/report_finalizer.py outputs/report_YYYYMMDD.md --core .claude/memory/enriched_candidates.json --watchlist .claude/memory/watchlist_candidates.json --reports-dir outputs`
   - 최종화 단계에서 이전 최신 리포트와 비교하여 기존 종목 변경사항을 반영하고, 리포트 맨 마지막에 최종 요약표를 강제 출력해야 합니다.

리포트에는 아래 섹션을 반드시 포함하십시오:
- `## 2) 핵심 매매 후보(확정형, Core Tradable)`
- `## 3) 확장 후보군(추정형, Expanded Watchlist)`
- `## 4) 역사적 유의점 노트 (Historical Significance Notes)`
- `## 6) 최종 요약표 (자동 생성)`

최종 요약표는 리포트의 마지막에 있어야 하며, 헤더는 아래 순서를 반드시 유지하십시오.
- `티커 / pdufa일정 / 진입일 / 매도일 / 현재상황 / 비고 / 투자등급`

지금 바로 하위 리드 에이전트들을 소집하여 작업을 시작하십시오.
