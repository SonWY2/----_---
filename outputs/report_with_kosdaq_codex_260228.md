# Biotech Alpha CIO Report (with KOSDAQ)
**Generated**: 2026-02-28 (KST)
**Method**: DuckDuckGo MCP 기반 이벤트 검증 + 공식 IR/PR 우선 필터링
**Strategy**: PDUFA Run-up (D-60 Entry, D-7 Exit)

---

## 1) 스크리닝 기준 (CIO 규칙 적용)

- 기준일(Today): **2026-02-28**
- 매집 타이밍 조건: **D-60(= Event Date - 60일)** 이 향후 90일 이내
- 매집 윈도우: **2026-02-28 ~ 2026-05-29**
- 역산 이벤트 윈도우: **2026-04-29 ~ 2026-07-28**

> 즉, 이벤트 날짜 자체가 아니라 **Run-up 시작일(D-60)** 이 현재부터 90일 내에 들어오는지로 선별.

---

## 2) 최종 리스트업 (확정 이벤트 중심)

### A. Core Candidates (공식 소스에서 날짜 확정)

| Market | Ticker | Company | Event Type | Event Date | D-60 Buy Start | D-7 Exit Deadline | Confidence |
|---|---|---|---|---|---|---|---|
| NASDAQ | VRDN | Viridian Therapeutics | FDA PDUFA | 2026-06-30 | 2026-05-01 | 2026-06-23 | Confirmed |
| NASDAQ | CELC | Celcuity | FDA PDUFA | 2026-07-17 | 2026-05-18 | 2026-07-10 | Confirmed |
| KOSDAQ | 028300 | HLB (via Elevar) | FDA PDUFA | 2026-07-23 | 2026-05-24 | 2026-07-16 | Confirmed |
| NASDAQ | MNKD | MannKind | FDA PDUFA | 2026-07-26 | 2026-05-27 | 2026-07-19 | Confirmed |

### 투자 포인트 요약

1. **VRDN**: BLA 접수 + Priority Review + PDUFA 2026-06-30이 회사 IR에 명시되어 D-60(5/1) 진입 타이밍이 명확함.
2. **CELC**: NDA 접수 + Priority Review + PDUFA 2026-07-17 확정으로 D-60(5/18) 캘린더 매매 가능성이 높음.
3. **HLB(코스닥)**: 자회사 Elevar 공식 발표에서 PDUFA 2026-07-23을 명시. 본 리포트의 KOSDAQ 핵심 편입 종목.
4. **MNKD**: sNDA 검토와 PDUFA 2026-07-26이 공시되어 D-60(5/27) 시점이 룰에 정확히 부합.

---

## 3) KOSDAQ 추가 분석 (추정/워치리스트)

> 아래는 **이벤트 시점이 확정일이 아닌 윈도우(estimated)** 라서, Core와 분리해 관리.

| Ticker | Company | Catalyst | Public Guidance | D-60 적합성 | Confidence |
|---|---|---|---|---|---|
| 298380 | ABL Bio | ABL209/ABL206 미국 Phase 1 개시 | "mid-2026 시작" (회사 뉴스) | 이벤트를 2026-06-15로 가정 시 D-60=2026-04-16 (조건 충족) | Estimated |
| 298380 | ABL Bio | ABL111 확장 코호트 데이터 | "1H 2026 공개 예상" (회사 뉴스) | 상반기 말(6/30) 가정 시 D-60=2026-05-01 (조건 충족) | Estimated |
| 950160 | Kolon TissueGene | TG-C Disc 임상 환자 투약 개시 | "2026년 하반기 시작" (회사 PR) | 7월 개시 가정 시 조건 충족 가능, 단 날짜 미확정 | Estimated-Low |

### KOSDAQ 해석

- **확정형(Confirmed)**: 현재는 HLB가 가장 명확.
- **추정형(Estimated)**: ABL Bio, Kolon TissueGene은 시점이 월/반기 수준이라 실제 진입일 변동 리스크가 큼.
- 따라서 KOSDAQ은 **HLB 중심 + 추정형은 이벤트 확정 공시 후 승격**이 합리적.

---

## 4) 제외/보류 기준

다음 항목은 이번 코어 리스트에서 제외 또는 보류:

- 공식 소스에서 정확한 이벤트 날짜를 찾지 못한 케이스
- 서드파티 캘린더만 존재하고 IR/규제 문서가 없는 케이스
- 루머/블로그 기반 정보만 존재하는 케이스

---

## 5) 리스크 스크리닝 코멘트 (실행 전 필수)

전략 원칙상 아래 조건을 실행 직전에 재검증해야 함:

1. **현금 런웨이 < 6개월 기업 제외** (KOSDAQ은 DART 분기보고서 기반 재확인 필요)
2. **이미 52주 고점 부근 과열 종목 제외**
3. **D-7 강제 청산 규칙 준수**
4. **PDUFA/데이터 발표일 변경 공지 모니터링**

---

## 6) 소스 (DuckDuckGo MCP 통해 수집, 공식 우선)

### Confirmed 후보 핵심 소스

- Viridian IR (BLA Acceptance / PDUFA 2026-06-30)
  - https://investors.viridiantherapeutics.com/news/news-details/2025/Viridian-Therapeutics-Announces-BLA-Acceptance-and-Priority-Review-for-Veligrotug-for-the-Treatment-of-Thyroid-Eye-Disease/default.aspx
- Celcuity IR (NDA Acceptance / PDUFA 2026-07-17)
  - https://ir.celcuity.com/news-releases/news-release-details/celcuity-announces-fda-acceptance-new-drug-application
- Elevar Therapeutics PR (HLB 자회사, PDUFA 2026-07-23)
  - https://www.globenewswire.com/news-release/2026/01/30/3229623/0/en/Elevar-Therapeutics-Announces-FDA-Acceptance-of-New-Drug-Application-Resubmission-for-Rivoceranib-in-Combination-with-Camrelizumab-as-a-First-line-Systemic-Treatment-for-Unresectable-Hepatocellular-Carcinoma
- MannKind PR (PDUFA 2026-07-26)
  - https://www.globenewswire.com/news-release/2025/12/23/3209855/0/en/MannKind-Shares-FUROSCIX-Business-Updates.html

### KOSDAQ 추정형/보조 소스

- ABL Bio News (mid-2026 임상 개시, 1H 2026 데이터 가이던스)
  - https://www.ablbio.com/en/company/news_view/923
  - https://www.ablbio.com/en/company/news_view/863
- Kolon TissueGene PR (2026 하반기 임상 투약 가이던스)
  - https://www.tissuegene.com/en_US/investors/pr/detail/35/
  - https://www.tissuegene.com/en_US/investors/pr/detail/39/tg-c

---

## 7) CIO 결론

- 이번 90일 매집 기준에서 **즉시 실행 가능한 확정형 후보**는: **VRDN, CELC, HLB(KOSDAQ), MNKD**.
- 사용자 요청사항인 **코스닥 한국 바이오 포함 요건**은 **HLB(확정형) + ABL Bio/코오롱티슈진(추정형 분석)**으로 반영 완료.
- 실제 주문 실행 전에는 각 종목의 최신 공시로 일정 변경 여부와 현금 런웨이(6개월 규칙)를 최종 점검해야 한다.

---

**Disclaimer**: 본 문서는 정보 제공 목적이며 투자 자문이 아닙니다. 바이오 이벤트 트레이딩은 높은 변동성과 이진 리스크를 수반합니다.
