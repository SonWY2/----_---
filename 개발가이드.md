
# 🧬 FDA Event-Driven Trading System 구축 가이드

이 시스템은 **"Biotech Alpha"** 프로젝트로 명명합니다. 사용자가 `/hunt` 명령어를 입력하면, 3개월 내 급등 가능한 바이오 종목을 발굴-검증-분석하여 리포트를 제출합니다.

## 📂 1. 전체 프로젝트 구조 (Directory Structure)

먼저 터미널에서 프로젝트 폴더를 만들고 아래 구조를 잡습니다.

```text
biotech_alpha/
├── .claude/
│   ├── CLAUDE.md                  # [핵심] 프로젝트 헌법 및 코딩 규칙
│   ├── settings.json              # [설정] 권한, 샌드박스, 훅 설정
│   ├── commands/
│   │   └── hunt.md                # [명령] 워크플로우 시작용 커스텀 커맨드
│   ├── hooks/
│   │   └── clean_memory.py        # [훅] 실행 전 이전 메모리 초기화 스크립트
│   ├── agents/                    # [에이전트] 전문가 페르소나 정의
│   │   ├── 00_cio.md
│   │   ├── 10_discovery_lead.md
│   │   ├── 11_event_scout.md
│   │   ├── 12_fact_verifier.md
│   │   ├── 20_analysis_lead.md
│   │   ├── 21_quant.md
│   │   └── 22_risk_screener.md
│   ├── context/                   # [지식] 전략 및 데이터 스키마
│   │   └── strategy_pdufa.md
│   └── memory/                    # [기억] 에이전트 간 데이터 공유용 (자동생성)
├── tools/                         # [도구] Python 유틸리티
│   └── market_calc.py
├── outputs/                       # [결과] 최종 리포트 저장소
└── requirements.txt               # 의존성 라이브러리

```

---

## ⚙️ 2. 루트 설정 및 환경 구성

### 2.1. `requirements.txt`

필요한 Python 라이브러리를 정의합니다.

```text
pandas
yfinance
requests
beautifulsoup4
datetime

```

### 2.2. `.claude/CLAUDE.md`

프로젝트의 '헌법'입니다. 에이전트들이 공통적으로 따라야 할 규칙을 정의합니다.

```markdown
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

```

### 2.3. `.claude/settings.json`

보안 설정, 허용 도구, 훅 트리거를 정의합니다.

```json
{
  "commands": {
    "hunt": {
      "description": "향후 3개월 내 유망 바이오 종목 발굴 워크플로우 시작",
      "prompt_file": "commands/hunt.md"
    }
  },
  "sandbox": {
    "enabled": true,
    "mode": "hybrid", 
    "allow_network": ["finance.yahoo.com", "google.com", "fda.gov", "clinicaltrials.gov", "biopharmcatalyst.com"],
    "allow_filesystem": ["./.claude/memory", "./outputs", "./tools"]
  },
  "hooks": {
    "pre_command": {
      "hunt": "python .claude/hooks/clean_memory.py"
    }
  },
  "tools": {
    "allowed": ["bash", "read_file", "write_file", "edit_file", "grep", "ls", "agent"]
  }
}

```

---

## 🎣 3. 커스텀 커맨드 및 훅 (Automation)

### 3.1. `.claude/commands/hunt.md`

터미널에서 `/hunt`라고 쳤을 때 실행될 프롬프트입니다.

```markdown
이제부터 'Biotech Alpha' 워크플로우를 시작합니다.

1. **Role**: 당신은 지금부터 **CIO(Chief Investment Officer)** 에이전트(`agents/00_cio.md`)로서 행동해야 합니다.
2. **Context**: `.claude/context/strategy_pdufa.md`의 전략을 로드하십시오.
3. **Objective**: 
   - 오늘 날짜를 확인하십시오.
   - 오늘부터 **향후 3개월(90일)** 이내에 '매집(Buy)' 타이밍이 오는 종목을 찾으십시오.
   - 후보군은 **미국/국내(한국) 바이오 기업**을 모두 포함하십시오.
   - 이벤트 날짜 자체가 아니라, **Run-up 시작일(D-60)**이 이 기간에 포함되는지가 핵심입니다.
   - 최종 유망 후보는 **최근 3개년 주가 히스토리**를 검증해 임상/규제 모멘텀과 실제 상승 이력 정합성을 재확인하십시오.
4. **Output**: 최종 결과는 `outputs/report_YYYYMMDD.md`에 저장하고 요약본을 터미널에 출력하십시오.
   - 보고서 최종 결과를 Markdown 테이블로 정리하고 `기업명, 관련정보, 매수예상일(진입일), 매도예상일, PDUFA/임상 일정, 투자 위험도(🟢/🟡/🔴)` 컬럼을 포함하십시오.

지금 바로 하위 리드 에이전트들을 소집하여 작업을 시작하십시오.

```

### 3.2. `.claude/hooks/clean_memory.py`

새로운 사냥(Hunt)을 시작할 때 이전 데이터를 청소하는 스크립트입니다.

```python
import os
import glob

MEMORY_DIR = ".claude/memory"

def clean_memory():
    print("🧹 [Hook] Cleaning up previous session memory...")
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)
        return

    files = glob.glob(os.path.join(MEMORY_DIR, "*.json"))
    for f in files:
        try:
            os.remove(f)
            print(f"   - Removed: {os.path.basename(f)}")
        except Exception as e:
            print(f"   - Error removing {f}: {e}")
    print("✨ Memory clean complete.")

if __name__ == "__main__":
    clean_memory()

```

---

## 🧠 4. 에이전트 정의 (Agents Definition)

### 4.1. `.claude/agents/00_cio.md` (총괄)

```markdown
name: cio-orchestrator
description: 전체 트레이딩 시스템을 총괄하는 CIO입니다. 직접 작업하지 않고 Discovery Lead와 Analysis Lead에게 업무를 위임하고 결과를 승인합니다.
tools: AgentTool, Read, Write, Bash

You are the Chief Investment Officer.
**Mission**: Find the best risk-adjusted biotech trades for the next 3 months.

## Workflow
1. **Initialize**: Check today's date using `date` command.
2. **Discovery Phase**: 
   - Call `discovery-lead`.
   - Command: "Identify FDA PDUFA, MFDS approval, or Phase 3 events occurring in the next 5 months across US and KR biotech markets."
   - Verify `memory/verified_events.json` is created.
3. **Analysis Phase**:
   - Call `analysis-lead`.
   - Command: "Analyze the verified events. Calculate entry dates. Filter out high-risk stocks. Select only those where the Entry Date is within [Today, Today+90days]. Include 3-year historical price/catalyst validation for top picks."
   - Verify `memory/final_candidates.json` is created.
4. **Reporting Phase**:
   - Read the final candidates.
   - Write a professional markdown report to `outputs/` folder.
   - Explain *why* each stock was chosen (e.g., "Event is on June 1st, so Run-up starts April 1st").

```

### 4.2. `.claude/agents/10_discovery_lead.md` (탐색 리더)

```markdown
name: discovery-lead
description: 정보 수집 단계를 관리합니다. 스카우트와 검증가를 조율하여 'Fact'만 남깁니다.
tools: AgentTool, Read, Write

You are the Discovery Team Lead.
**Goal**: Produce `verified_events.json`.

## Process
1. **Scout**: Invoke `event-scout`. Ask for a broad list of upcoming catalysts.
2. **Review**: Read `memory/raw_events.json`. If empty, ask Scout to retry with different search terms.
3. **Verify**: Loop through each raw event.
   - Invoke `fact-verifier` for each ticker.
   - Only keep events marked as "Confirmed" by the verifier.
4. **Save**: Save the final cleaned list to `memory/verified_events.json`.

```

### 4.3. `.claude/agents/11_event_scout.md` (스카우트)

```markdown
name: event-scout
description: 웹을 검색하여 바이오 이벤트를 수집합니다.
tools: WebSearch, WebFetch, Write

You are a Biotech Event Scout.
**Goal**: Find tickers and event dates.

## Instructions
- 나스닥 중심에서 확장해 NYSE/NASDAQ + KOSPI/KOSDAQ을 모두 검색합니다.
- Search for "FDA PDUFA calendar [Current Year]", "Biotech catalyst calendar [Next 6 months]", "한국 바이오 임상 3상 결과 발표 예정", "식약처 허가 일정 바이오 기업".
- Look for: PDUFA dates, Advisory Committee meetings, Phase 3 Top-line data, NDA/BLA filing, MFDS 허가/심사 모멘텀.
- **Output Schema** (`memory/raw_events.json`):
```json
[
  {"ticker": "ABC", "company_name": "ABC Bio", "market": "NASDAQ|KOSDAQ", "event": "PDUFA|Phase3|MFDS", "date": "2026-05-20", "source": "url..."}
]

```

```

### 4.4. `.claude/agents/12_fact_verifier.md` (검증가 - 핵심)

```markdown
name: fact-verifier
description: 특정 이벤트가 진짜인지 공식 소스로 교차 검증합니다.
tools: WebSearch, WebFetch

You are a Skeptical Auditor.
**Input**: Ticker, Event Type, Date.
**Goal**: Confirm if this is real or a rumor.

## Verification Steps
1. Search query (US): `"[Ticker]" investor relations press release PDUFA date`
2. Search query (KR): `"[기업명]" 공시 임상 일정 결과`, `DART [기업명] 임상`
3. Search query: `"[Ticker]" clinicaltrials.gov results expectation`
3. **Judgment**:
   - "Confirmed": Company PR explicitly states the date.
   - "Estimated": Only third-party sites mention it (Mark as High Risk).
   - "Rumor": No credible source found.
4. Return structured JSON including `verification`, `confidence`, `market`, `company_name`, `source_quality`.

```

### 4.5. `.claude/agents/20_analysis_lead.md` (분석 리더)

```markdown
name: analysis-lead
description: 검증된 이벤트를 매매 전략으로 변환합니다. Quant와 Risk 에이전트를 지휘합니다.
tools: AgentTool, Read, Write

You are the Head of Strategy.
**Goal**: Produce `memory/final_candidates.json`.

## Process
1. Load `memory/verified_events.json`.
2. **Quant Analysis**: 
   - Invoke `quant-analyst` for each stock.
   - Get "Target Buy Date" (D-60) and "Target Sell Date" (D-7).
   - For top picks, add 3-year historical price validation around similar catalysts.
3. **Filtering**:
   - Select stocks where "Target Buy Date" is close to Now (within 2 weeks) or in the future (within 3 months).
   - Discard stocks where the run-up has already finished.
4. **Risk Check**:
   - For the surviving candidates, invoke `risk-screener`.
   - Remove any stock flagged as "Critical Financial Risk".
5. **Finalize**: Save the result to `memory/final_candidates.json` with report-ready fields (`company_name`, `market`, `related_info`, `entry_date`, `exit_date`, `event_schedule`, `risk_signal`).

```

### 4.6. `.claude/agents/21_quant.md` (퀀트)

```markdown
name: quant-analyst
description: 날짜 계산 및 기술적 위치를 분석합니다.
tools: Python, Read, Write, WebSearch, WebFetch

You are a Quantitative Analyst.
**Task**: Calculate strategic dates, check trend, and validate 3-year historical catalyst reactions.

## Logic (Refer to `context/strategy_pdufa.md`)
1. **Dates**:
   - `Entry_Start`: Event Date - 60 days
   - `Exit_Target`: Event Date - 7 days
2. **Code Execution**:
   - Use `tools/market_calc.py` (or inline python) to check current price vs 60-day moving average.
   - Determine if the stock is currently in an "uptrend" or "downtrend".
3. **3-Year Validation**: 유망 후보는 최근 3개년 주가/이벤트를 웹에서 확인해 pre-event run-up 재현성을 기록합니다.
4. **Output**: Return a JSON with calculated dates, trend status, and historical validation summary.

```

### 4.7. `.claude/agents/22_risk_screener.md` (리스크)

```markdown
name: risk-screener
description: 기업의 재무 상태를 점검하여 유상증자 위험을 경고합니다.
tools: WebSearch, WebFetch

You are a Risk Manager.
**Goal**: Identify "Cash Crunch" risk.

## Checks
1. Search: `"[Ticker]" cash and cash equivalents last quarter`
2. Search: `"[Ticker]" burn rate per quarter`
3. **Calculation**:
   - Runway = Cash / Burn Rate
   - If Runway < 6 months: **CRITICAL RISK** (High chance of offering before approval).
   - If Runway > 12 months: SAFE.
4. Return: Risk Level (Low, Medium, Critical).

```

---

## 📚 5. 컨텍스트 및 도구 (Context & Tools)

### 5.1. `.claude/context/strategy_pdufa.md`

전략 로직 파일입니다.

```markdown
# PDUFA Run-up Strategy Logic

## The Golden Rule
"Buy the rumor (anticipation), Sell the news (before release)."

## Timeline Parameters
1. **Observation Start**: Event - 90 Days
2. **Accumulation Zone (Buy)**: Event - 60 Days to - 45 Days
   - Why? Institutional money starts positioning ~2 months prior.
3. **Distribution Zone (Sell)**: Event - 7 Days to - 3 Days
   - Why? Avoid binary event risk (Approval vs CRL).

## Failure Conditions (Do Not Buy)
- Company has < 6 months of cash (Dilution risk).
- Phase 2 data was mixed/weak.
- Stock is already trading at 52-week highs (Priced in).

```

### 5.2. `tools/market_calc.py`

퀀트 에이전트가 사용할 계산기입니다.

```python
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import sys
import json

def analyze_ticker(ticker, event_date_str):
    """
    Calculates entry/exit dates and fetches current price data.
    """
    try:
        event_date = pd.to_datetime(event_date_str)
        today = pd.Timestamp.now()
        
        # Strategy Rules
        entry_date = event_date - timedelta(days=60)
        exit_date = event_date - timedelta(days=7)
        
        # Fetch Data (Last 3 months)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        
        current_price = "N/A"
        trend = "Unknown"
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            # Simple Trend: Above 20-day MA?
            ma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            trend = "Uptrend" if current_price > ma_20 else "Downtrend"

        result = {
            "ticker": ticker,
            "event_date": event_date.strftime('%Y-%m-%d'),
            "today_date": today.strftime('%Y-%m-%d'),
            "target_entry_date": entry_date.strftime('%Y-%m-%d'),
            "target_exit_date": exit_date.strftime('%Y-%m-%d'),
            "days_until_entry": (entry_date - today).days,
            "current_price": round(current_price, 2) if isinstance(current_price, float) else current_price,
            "trend": trend
        }
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    # CLI Usage: python tools/market_calc.py AAPL 2026-06-01
    if len(sys.argv) > 2:
        analyze_ticker(sys.argv[1], sys.argv[2])
    else:
        print('{"error": "Insufficient arguments"}')

```

---

## 🚀 실행 방법 (Execution)

모든 파일이 생성되었다면, 이제 시스템을 가동할 차례입니다.

1. **터미널 접속**: `biotech_alpha` 폴더로 이동.
2. **Claude Code 실행**:
```bash
claude

```


3. **명령어 입력**:
```text
/hunt

```



**예상되는 동작:**

1. `pre_command` 훅이 작동하여 `.claude/memory` 폴더를 깨끗이 비웁니다.
2. `00_cio` 에이전트가 로드되어 사용자의 지시를 확인합니다.
3. `discovery-lead` -> `event-scout`가 웹을 검색하여 이벤트 리스트를 만듭니다.
4. `fact-verifier`가 루머를 걸러냅니다.
5. `analysis-lead` -> `quant`가 `market_calc.py`를 실행해 D-Day를 계산합니다.
6. `risk-screener`가 재무제표를 확인하여 위험 종목을 탈락시킵니다.
7. 최종적으로 `outputs/report_YYYYMMDD.md` 파일에 **"지금 사야 할 종목"** 리스트가 생성됩니다.

이 가이드는 멀티에이전트 시스템의 **Best Practice**를 모두 포함하고 있습니다. 