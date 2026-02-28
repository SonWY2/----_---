#!/usr/bin/env python3
"""Append a deterministic final summary table to Biotech Alpha reports."""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

try:
    from tools.report_parser import parse_report_tickers, select_previous_report
except ModuleNotFoundError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from tools.report_parser import parse_report_tickers, select_previous_report


REQUIRED_HEADERS = [
    "티커",
    "pdufa일정",
    "진입일",
    "매도일",
    "현재상황",
    "비고",
    "투자등급",
]


@dataclass
class SummaryRow:
    ticker: str
    pdufa_date: str
    entry_date: str
    exit_date: str
    status: str
    note: str
    grade: str
    lane: str


def _parse_date(value: Any) -> Optional[pd.Timestamp]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "nat", "n/a", "-"}:
        return None
    try:
        parsed = pd.Timestamp(text)
    except Exception:
        return None
    if not isinstance(parsed, pd.Timestamp):
        return None
    return parsed.normalize()


def _format_date(value: Any) -> str:
    parsed = _parse_date(value)
    if parsed is None:
        return "-"
    return parsed.strftime("%Y-%m-%d")


def _clean_text(text: Any) -> str:
    if text is None:
        return ""
    cleaned = str(text).replace("|", "/").replace("\n", " ").strip()
    return " ".join(cleaned.split())


def _pick_first(item: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def _derive_status(
    today: pd.Timestamp,
    event_date: Any,
    entry_date: Any,
    exit_date: Any,
    estimated: bool,
) -> str:
    event_ts = _parse_date(event_date)
    entry_ts = _parse_date(entry_date)
    exit_ts = _parse_date(exit_date)

    if estimated:
        return "추정형(확정필요)"

    if entry_ts is None or exit_ts is None:
        return "일정미완성"

    if today < entry_ts:
        return f"진입대기(D-{int((entry_ts - today).days)})"

    if entry_ts <= today <= exit_ts:
        if event_ts is not None:
            return f"진입구간(D-{int((event_ts - today).days)})"
        return "진입구간"

    if today > exit_ts:
        if event_ts is not None and today <= event_ts:
            return f"매도시점도달(D-{int((event_ts - today).days)})"
        if event_ts is not None and today > event_ts:
            return "이벤트경과"
        return "매도기한경과"

    return "관찰필요"


def _derive_grade(item: Dict[str, Any], lane: str) -> str:
    recommendation = _clean_text(item.get("recommendation"))
    if recommendation:
        return recommendation.upper()

    risk_level = _clean_text(item.get("risk_level")).lower()
    risk_map = {
        "low": "BUY",
        "medium": "HOLD",
        "critical": "AVOID",
    }
    if risk_level in risk_map:
        return risk_map[risk_level]

    if lane == "watchlist":
        confidence = item.get("confidence")
        if isinstance(confidence, (float, int)):
            if confidence >= 0.8:
                return "WATCHLIST-HIGH"
            if confidence >= 0.5:
                return "WATCHLIST-MID"
        return "WATCHLIST"

    return "REVIEW"


def _build_note(item: Dict[str, Any], lane: str) -> str:
    parts: List[str] = []

    if lane == "core":
        parts.append("확정형")
    else:
        verification = _clean_text(item.get("verification_status"))
        if verification:
            parts.append(verification)
        else:
            parts.append("추정형")

    for key in (
        "reason",
        "risk_reason",
        "historical_significance_note",
        "rationale",
    ):
        value = _clean_text(item.get(key))
        if value:
            parts.append(value)

    if lane == "watchlist":
        risk_flags = item.get("risk_flags")
        if isinstance(risk_flags, list):
            cleaned_flags = [
                _clean_text(flag) for flag in risk_flags if _clean_text(flag)
            ]
            if cleaned_flags:
                parts.append("flags: " + ", ".join(cleaned_flags))

    merged: List[str] = []
    seen = set()
    for part in parts:
        if part not in seen:
            merged.append(part)
            seen.add(part)
    return "; ".join(merged)


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        candidates = data.get("candidates")
        if isinstance(candidates, list):
            return [item for item in candidates if isinstance(item, dict)]
    return []


def _build_row(
    item: Dict[str, Any], lane: str, today: pd.Timestamp
) -> Optional[SummaryRow]:
    ticker = _clean_text(item.get("ticker")).upper()
    if not ticker:
        return None

    event_raw = _pick_first(item, ("event_date", "normalized_event_date", "date"))
    entry_raw = _pick_first(item, ("target_entry_date", "entry_date", "entry_start"))
    exit_raw = _pick_first(item, ("target_exit_date", "exit_date", "exit_target"))

    event_date = _parse_date(event_raw)
    entry_date = _parse_date(entry_raw)
    exit_date = _parse_date(exit_raw)

    if lane == "watchlist" and event_date is not None:
        if entry_date is None:
            entry_date = event_date - pd.Timedelta(days=60)
        if exit_date is None:
            exit_date = event_date - pd.Timedelta(days=7)

    status = _derive_status(
        today=today,
        event_date=event_date,
        entry_date=entry_date,
        exit_date=exit_date,
        estimated=(lane == "watchlist"),
    )

    return SummaryRow(
        ticker=ticker,
        pdufa_date=_format_date(event_date),
        entry_date=_format_date(entry_date),
        exit_date=_format_date(exit_date),
        status=status,
        note=_build_note(item, lane=lane),
        grade=_derive_grade(item, lane=lane),
        lane=lane,
    )


def _merge_rows(rows: List[SummaryRow]) -> List[SummaryRow]:
    by_ticker: Dict[str, SummaryRow] = {}

    for row in rows:
        existing = by_ticker.get(row.ticker)
        if existing is None:
            by_ticker[row.ticker] = row
            continue

        existing_rank = 2 if existing.lane == "core" else 1
        current_rank = 2 if row.lane == "core" else 1

        if current_rank > existing_rank:
            by_ticker[row.ticker] = row
            continue

        if current_rank == existing_rank:
            existing_event = _parse_date(existing.pdufa_date)
            current_event = _parse_date(row.pdufa_date)
            if existing_event is None and current_event is not None:
                by_ticker[row.ticker] = row
                continue
            if (
                existing_event is not None
                and current_event is not None
                and current_event < existing_event
            ):
                by_ticker[row.ticker] = row
                continue

            if row.note and row.note not in existing.note:
                if existing.note:
                    existing.note = f"{existing.note}; {row.note}"
                else:
                    existing.note = row.note

    output = list(by_ticker.values())

    def _sort_key(row: SummaryRow) -> tuple[pd.Timestamp, str]:
        parsed = _parse_date(row.pdufa_date)
        if parsed is None:
            return (pd.Timestamp.max.normalize(), row.ticker)
        return (parsed, row.ticker)

    output.sort(key=_sort_key)
    return output


def _split_table_row(line: str) -> List[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: List[str]) -> bool:
    if not cells:
        return False
    return all(set(cell.replace(" ", "")).issubset({"-", ":"}) for cell in cells)


def _find_required_table(lines: List[str]) -> Optional[tuple[int, List[str]]]:
    required = [item.lower() for item in REQUIRED_HEADERS]
    for index in range(len(lines) - 1, -1, -1):
        line = lines[index].strip()
        if not line.startswith("|"):
            continue
        cells = [cell.lower() for cell in _split_table_row(line)]
        if all(header in cells for header in required):
            return index, cells
    return None


def _extract_previous_rows(report_path: Path) -> Dict[str, Dict[str, str]]:
    lines = report_path.read_text(encoding="utf-8").splitlines()
    located = _find_required_table(lines)
    if located is None:
        ticker_data = parse_report_tickers(report_path)
        return {ticker: {} for ticker in ticker_data.get("ticker_set", [])}

    start_idx, headers = located
    col_map = {header: idx for idx, header in enumerate(headers)}
    required_map = {header.lower(): header for header in REQUIRED_HEADERS}

    rows: Dict[str, Dict[str, str]] = {}
    for line in lines[start_idx + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break
        cells = _split_table_row(stripped)
        if _is_separator(cells):
            continue

        ticker_idx = col_map.get("티커")
        if ticker_idx is None or ticker_idx >= len(cells):
            continue

        ticker = _clean_text(cells[ticker_idx]).upper()
        if not ticker:
            continue

        mapped: Dict[str, str] = {}
        for lowered, original in required_map.items():
            idx = col_map.get(lowered)
            if idx is not None and idx < len(cells):
                mapped[original] = _clean_text(cells[idx])
        rows[ticker] = mapped

    if rows:
        return rows

    ticker_data = parse_report_tickers(report_path)
    return {ticker: {} for ticker in ticker_data.get("ticker_set", [])}


def _build_delta(
    rows: List[SummaryRow],
    previous_rows: Dict[str, Dict[str, str]],
) -> List[str]:
    removed = sorted(set(previous_rows.keys()) - {row.ticker for row in rows})

    for row in rows:
        previous = previous_rows.get(row.ticker)
        if previous is None:
            delta = "신규종목"
        elif not previous:
            delta = "기존종목 업데이트(세부비교불가)"
        else:
            comparisons = [
                ("pdufa일정", previous.get("pdufa일정", "-"), row.pdufa_date),
                ("진입일", previous.get("진입일", "-"), row.entry_date),
                ("매도일", previous.get("매도일", "-"), row.exit_date),
                ("현재상황", previous.get("현재상황", "-"), row.status),
                ("투자등급", previous.get("투자등급", "-"), row.grade),
            ]
            changed = [
                f"{field} {before}->{after}"
                for field, before, after in comparisons
                if _clean_text(before) != _clean_text(after)
            ]
            if changed:
                delta = "기존종목 변경: " + ", ".join(changed)
            else:
                delta = "기존종목 유지"

        if row.note:
            row.note = f"{delta}; {row.note}"
        else:
            row.note = delta

    return removed


def _render_table(rows: List[SummaryRow]) -> str:
    lines = [
        "| 티커 | pdufa일정 | 진입일 | 매도일 | 현재상황 | 비고 | 투자등급 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {ticker} | {pdufa} | {entry} | {exit} | {status} | {note} | {grade} |".format(
                ticker=_clean_text(row.ticker) or "-",
                pdufa=_clean_text(row.pdufa_date) or "-",
                entry=_clean_text(row.entry_date) or "-",
                exit=_clean_text(row.exit_date) or "-",
                status=_clean_text(row.status) or "-",
                note=_clean_text(row.note) or "-",
                grade=_clean_text(row.grade) or "-",
            )
        )
    return "\n".join(lines)


def _drop_existing_final_section(text: str) -> str:
    lines = text.splitlines()
    marker = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("##") and "최종 요약표" in line:
            marker = idx
            break
    if marker is None:
        return text.rstrip()
    return "\n".join(lines[:marker]).rstrip()


def _render_final_section(
    rows: List[SummaryRow],
    previous_report: Optional[str],
    previous_date: Optional[str],
    removed: List[str],
) -> str:
    header = "## 6) 최종 요약표 (자동 생성)"
    if previous_report:
        compare_line = f"- 비교 기준 이전 리포트: `{previous_report}` ({previous_date})"
    else:
        compare_line = "- 비교 기준 이전 리포트: 없음 (최초 생성)"

    if removed:
        removed_line = "- 이전 대비 제외 종목: " + ", ".join(removed)
    else:
        removed_line = "- 이전 대비 제외 종목: 없음"

    return "\n".join(
        [
            header,
            compare_line,
            removed_line,
            "",
            _render_table(rows),
        ]
    )


def finalize_report(
    report_path: Path,
    core_path: Path,
    watchlist_path: Path,
    reports_dir: Path,
    include_validation: bool,
    today: pd.Timestamp,
) -> Dict[str, Any]:
    core_items = _load_json_list(core_path)
    watchlist_items = _load_json_list(watchlist_path)

    rows: List[SummaryRow] = []
    for item in core_items:
        built = _build_row(item, lane="core", today=today)
        if built is not None:
            rows.append(built)
    for item in watchlist_items:
        built = _build_row(item, lane="watchlist", today=today)
        if built is not None:
            rows.append(built)

    rows = _merge_rows(rows)

    previous = select_previous_report(
        current_report=report_path,
        reports_dir=reports_dir,
        include_validation=include_validation,
    )
    previous_rows: Dict[str, Dict[str, str]] = {}
    if previous is not None:
        previous_rows = _extract_previous_rows(Path(previous.path))

    removed = _build_delta(rows, previous_rows)

    original_text = report_path.read_text(encoding="utf-8")
    base_text = _drop_existing_final_section(original_text)
    final_section = _render_final_section(
        rows=rows,
        previous_report=(previous.filename if previous else None),
        previous_date=(previous.date if previous else None),
        removed=removed,
    )

    report_path.write_text(f"{base_text}\n\n{final_section}\n", encoding="utf-8")

    return {
        "report": str(report_path),
        "core_count": len(core_items),
        "watchlist_count": len(watchlist_items),
        "summary_row_count": len(rows),
        "previous_report": previous.filename if previous else None,
        "removed_tickers": removed,
    }


def main() -> None:
    parser = ArgumentParser(
        description="Finalize Biotech Alpha report with summary table"
    )
    parser.add_argument("report", help="Path to markdown report to finalize")
    parser.add_argument(
        "--core",
        default=".claude/memory/enriched_candidates.json",
        help="Path to enriched core candidates JSON",
    )
    parser.add_argument(
        "--watchlist",
        default=".claude/memory/watchlist_candidates.json",
        help="Path to expanded watchlist candidates JSON",
    )
    parser.add_argument(
        "--reports-dir",
        default="outputs",
        help="Directory containing past reports",
    )
    parser.add_argument(
        "--include-validation",
        action="store_true",
        help="Include validation reports as previous-report candidates",
    )
    parser.add_argument(
        "--today",
        default=None,
        help="Optional override date (YYYY-MM-DD) for deterministic tests",
    )
    args = parser.parse_args()

    today = _parse_date(args.today) if args.today else pd.Timestamp.now().normalize()
    if today is None:
        raise ValueError("Invalid --today value. Use YYYY-MM-DD format.")

    result = finalize_report(
        report_path=Path(args.report),
        core_path=Path(args.core),
        watchlist_path=Path(args.watchlist),
        reports_dir=Path(args.reports_dir),
        include_validation=args.include_validation,
        today=today,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
