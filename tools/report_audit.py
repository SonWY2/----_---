#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from tools.report_parser import parse_report_tickers
except ModuleNotFoundError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from tools.report_parser import parse_report_tickers


REQUIRED_SECTIONS = [
    "## 1) 스크리닝 기준",
    "## 2) 핵심 매매 후보(확정형, Core Tradable)",
    "## 3) 확장 후보군(추정형, Expanded Watchlist)",
    "## 4) 역사적 유의점 노트 (Historical Significance Notes)",
    "## 5) 리스크 및 실행 규칙",
    "## 6) 제외 종목 (Excluded Events)",
    "## 7) 최종 요약표",
]

SUMMARY_HEADERS = ["티커", "pdufa일정", "진입일", "매도일", "현재상황", "비고", "투자등급"]


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def _find_sections(lines: List[str]) -> Tuple[List[str], bool]:
    found = [line.strip() for line in lines if line.strip().startswith("## ")]
    issues: List[str] = []
    missing = [section for section in REQUIRED_SECTIONS if section not in found]
    if missing:
        issues.extend([f"missing section: {section}" for section in missing])

    order_ok = True
    last_idx = -1
    for section in REQUIRED_SECTIONS:
        if section not in found:
            order_ok = False
            continue
        idx = found.index(section)
        if idx < last_idx:
            order_ok = False
        last_idx = idx

    if not order_ok:
        issues.append("required section order is incorrect")
    return issues, order_ok


def _parse_summary_table(lines: List[str]) -> Tuple[List[str], Dict[str, Dict[str, str]], List[str]]:
    issues: List[str] = []
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## 7) 최종 요약표":
            start = i
            break
    if start is None:
        issues.append("summary section missing")
        return issues, {}, []

    header_idx = None
    for i in range(start + 1, min(len(lines), start + 20)):
        if lines[i].strip().startswith("|"):
            header_idx = i
            break

    if header_idx is None:
        issues.append("summary table header missing")
        return issues, {}, []

    headers = [cell.strip() for cell in lines[header_idx].strip().strip("|").split("|")]
    if headers != SUMMARY_HEADERS:
        issues.append("summary table header is not exact")
        return issues, {}, headers

    rows: Dict[str, Dict[str, str]] = {}
    for i in range(header_idx + 2, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            if line:
                continue
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        row = dict(zip(headers, cells))
        ticker = row.get("티커", "").strip()
        if ticker:
            rows[ticker] = row
    return issues, rows, headers


def audit_report(report_path: Path, ranked_path: Path, watchlist_path: Path, excluded_path: Path) -> Dict[str, Any]:
    text = report_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    issues, order_ok = _find_sections(lines)
    summary_issues, summary_rows, summary_headers = _parse_summary_table(lines)
    issues.extend(summary_issues)

    parsed = parse_report_tickers(report_path)
    body_ticker_set = set(parsed.get("ticker_set", []))

    ranked = _load_json_list(ranked_path)
    watchlist = _load_json_list(watchlist_path)
    excluded = _load_json_list(excluded_path)

    ranked_tickers = [str(item.get("ticker", "")).upper() for item in ranked if item.get("ticker")]
    watchlist_tickers = [str(item.get("ticker", "")).upper() for item in watchlist if item.get("ticker")]
    excluded_tickers = [str(item.get("ticker", "")).upper() for item in excluded if item.get("ticker")]

    missing_core_body = [ticker for ticker in ranked_tickers if ticker not in body_ticker_set]
    missing_core_summary = [ticker for ticker in ranked_tickers if ticker not in summary_rows]
    missing_watchlist_body = [ticker for ticker in watchlist_tickers if ticker not in body_ticker_set]
    missing_watchlist_summary = [ticker for ticker in watchlist_tickers if ticker not in summary_rows]

    if missing_core_body:
        issues.append("missing ranked core tickers in body: " + ", ".join(missing_core_body))
    if missing_core_summary:
        issues.append("missing ranked core tickers in summary table: " + ", ".join(missing_core_summary))
    if missing_watchlist_body:
        issues.append("missing watchlist tickers in body: " + ", ".join(missing_watchlist_body))
    if missing_watchlist_summary:
        issues.append("missing watchlist tickers in summary table: " + ", ".join(missing_watchlist_summary))

    if len(excluded_tickers) <= 10:
        missing_excluded_body = [ticker for ticker in excluded_tickers if ticker not in body_ticker_set]
        if missing_excluded_body:
            issues.append("missing excluded tickers in body: " + ", ".join(missing_excluded_body))

    # grade sanity checks
    bad_watchlist_signals = []
    for ticker in watchlist_tickers:
        row = summary_rows.get(ticker)
        if row and row.get("투자등급", "").strip().startswith("🟢"):
            bad_watchlist_signals.append(ticker)
    if bad_watchlist_signals:
        issues.append("watchlist tickers incorrectly marked green: " + ", ".join(bad_watchlist_signals))

    bad_core_signals = []
    for item in ranked:
        ticker = str(item.get("ticker", "")).upper()
        row = summary_rows.get(ticker)
        if row and row.get("투자등급", "").strip().startswith("🔴"):
            bad_core_signals.append(ticker)
    if bad_core_signals:
        issues.append("ranked core tickers incorrectly marked red: " + ", ".join(bad_core_signals))

    result = {
        "status": "pass" if not issues else "fail",
        "report": str(report_path),
        "checks": {
            "section_order_ok": order_ok,
            "summary_header_exact": summary_headers == SUMMARY_HEADERS,
            "ranked_count": len(ranked_tickers),
            "watchlist_count": len(watchlist_tickers),
            "excluded_count": len(excluded_tickers),
        },
        "missing_core_body": missing_core_body,
        "missing_core_summary": missing_core_summary,
        "missing_watchlist_body": missing_watchlist_body,
        "missing_watchlist_summary": missing_watchlist_summary,
        "issues": issues,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Biotech Alpha report against memory artifacts")
    parser.add_argument("report")
    parser.add_argument("--ranked", required=True)
    parser.add_argument("--watchlist", required=True)
    parser.add_argument("--excluded", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    result = audit_report(
        report_path=Path(args.report),
        ranked_path=Path(args.ranked),
        watchlist_path=Path(args.watchlist),
        excluded_path=Path(args.excluded),
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
