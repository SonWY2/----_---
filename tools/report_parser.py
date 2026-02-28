#!/usr/bin/env python3
"""Utilities for normalizing and parsing Biotech Alpha markdown reports."""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class ReportInfo:
    path: str
    filename: str
    date: str
    date_kind: str
    tags: List[str]
    family: str


REPORT_DATE_8 = re.compile(r"^\d{8}$")
REPORT_DATE_6 = re.compile(r"^\d{6}$")
TICKER_TOKEN_RE = re.compile(r"\b([A-Z]{2,6}(?:\.[A-Z]{1,2})?|\d{6})\b")
HEADING_TICKER_RE = re.compile(
    r"^\s*###\s*(?:\d+\.\s*)?.*?\b(?P<ticker>[A-Z]{2,6}(?:\.[A-Z]{1,2})?|\d{6})\b\s*(?:[—–\-:]\s+.+)$"
)

TABLE_TICKER_HEADERS = ("ticker", "symbol", "티커", "종목", "code", "코드")
FAMILY_PRIORITY = {
    "base": 4,
    "custom": 3,
    "version": 2,
    "localized": 1,
    "validation": 0,
}


def _parse_report_date(raw: str) -> date:
    if REPORT_DATE_8.fullmatch(raw):
        return datetime.strptime(raw, "%Y%m%d").date()
    if REPORT_DATE_6.fullmatch(raw):
        return datetime.strptime(f"20{raw}", "%Y%m%d").date()
    raise ValueError(f"Unsupported report date token: {raw}")


def parse_report_filename(path: str | Path) -> ReportInfo:
    p = Path(path)
    if p.suffix.lower() != ".md" or not p.stem.startswith("report_"):
        raise ValueError(f"Not a report markdown file: {path}")

    stem = p.stem[len("report_") :]
    parts = [part for part in stem.split("_") if part]

    date_idx = None
    date_token = None
    for idx in range(len(parts) - 1, -1, -1):
        token = parts[idx]
        if token.isdigit() and len(token) in (6, 8):
            date_idx = idx
            date_token = token
            break

    if date_idx is None or date_token is None:
        raise ValueError(f"Could not find report date token in filename: {p.name}")

    tags = [part.lower() for part in parts[:date_idx]]
    suffix_tags = [part.lower() for part in parts[date_idx + 1 :]]
    all_tags = tags + suffix_tags

    if not all_tags:
        family = "base"
    elif "validation" in all_tags:
        family = "validation"
    elif any(tag.startswith("v") and tag[1:].isdigit() for tag in all_tags):
        family = "version"
    elif all_tags == ["ko"]:
        family = "localized"
    else:
        family = "custom"

    parsed_date = _parse_report_date(date_token)
    return ReportInfo(
        path=str(p.resolve()),
        filename=p.name,
        date=parsed_date.isoformat(),
        date_kind="YYYYMMDD" if len(date_token) == 8 else "YYMMDD",
        tags=all_tags,
        family=family,
    )


def list_report_files(reports_dir: str | Path) -> List[ReportInfo]:
    base = Path(reports_dir)
    records: List[ReportInfo] = []
    for path in sorted(base.glob("report*.md")):
        try:
            records.append(parse_report_filename(path))
        except ValueError:
            continue
    return records


def select_previous_report(
    current_report: str | Path,
    reports_dir: str | Path = "outputs",
    include_validation: bool = False,
) -> Optional[ReportInfo]:
    current = parse_report_filename(current_report)
    current_path = str(Path(current_report).resolve())
    current_date = date.fromisoformat(current.date)

    reports = [
        info
        for info in list_report_files(reports_dir)
        if info.path != current_path
        and (include_validation or info.family != "validation")
    ]
    if not reports:
        return None

    older = [info for info in reports if date.fromisoformat(info.date) < current_date]
    candidates = older if older else reports

    def _sort_key(info: ReportInfo) -> tuple[date, int, str]:
        return (
            date.fromisoformat(info.date),
            FAMILY_PRIORITY.get(info.family, -1),
            info.filename,
        )

    candidates.sort(key=_sort_key, reverse=True)
    return candidates[0]


def _clean_cell(text: str) -> str:
    return re.sub(r"[*`]", "", text.strip())


def _is_real_ticker(token: str) -> bool:
    if token.isdigit():
        return len(token) == 6
    return bool(re.fullmatch(r"[A-Z]{2,6}(?:\.[A-Z]{1,2})?", token))


def _extract_heading_ticker(line: str) -> Optional[str]:
    match = HEADING_TICKER_RE.match(line)
    if not match:
        return None
    token = match.group("ticker")
    if _is_real_ticker(token):
        return token
    return None


def _extract_cell_ticker(text: str) -> Optional[str]:
    cleaned = _clean_cell(text)
    for token in TICKER_TOKEN_RE.findall(cleaned):
        if _is_real_ticker(token):
            return token
    return None


def _is_separator_row(cells: List[str]) -> bool:
    if not cells:
        return False
    return all(set(cell.replace(" ", "")).issubset({"-", ":"}) for cell in cells)


def _detect_ticker_col(cells: List[str]) -> Optional[int]:
    for index, cell in enumerate(cells):
        lowered = _clean_cell(cell).lower()
        if any(key in lowered for key in TABLE_TICKER_HEADERS):
            return index
    return None


def parse_report_tickers(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    report_info = parse_report_filename(p)
    lines = p.read_text(encoding="utf-8").splitlines()

    seen: Dict[str, List[Dict[str, object]]] = {}
    current_section = "summary"
    table_ticker_col: Optional[int] = None

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if line.startswith("###"):
            ticker = _extract_heading_ticker(line)
            if ticker:
                seen.setdefault(ticker, []).append(
                    {
                        "section": current_section,
                        "line": line_no,
                        "text": line,
                    }
                )
            continue

        if line.startswith("##"):
            current_section = line.lstrip("#").strip()
            table_ticker_col = None
            continue

        if "|" not in line or not line.startswith("|"):
            table_ticker_col = None
            continue

        cells = [cell.strip() for cell in line.strip("|\n ").split("|")]
        if _is_separator_row(cells):
            continue

        if table_ticker_col is None:
            table_ticker_col = _detect_ticker_col(cells)
            if table_ticker_col is not None:
                continue

        if table_ticker_col is not None and table_ticker_col < len(cells):
            ticker = _extract_cell_ticker(cells[table_ticker_col])
            if ticker:
                seen.setdefault(ticker, []).append(
                    {
                        "section": current_section,
                        "line": line_no,
                        "text": line,
                    }
                )

    return {
        "report": report_info.__dict__,
        "tickers": [
            {"ticker": ticker, "mentions": mentions}
            for ticker, mentions in sorted(seen.items(), key=lambda item: item[0])
        ],
        "ticker_set": sorted(seen.keys()),
        "ticker_count": len(seen),
    }


def parse_many(paths: Iterable[str | Path]) -> Dict[str, Any]:
    parsed_reports: List[Dict[str, Any]] = []
    ticker_to_reports: Dict[str, set[str]] = {}

    for raw in paths:
        parsed = parse_report_tickers(raw)
        parsed_reports.append(parsed)
        for ticker in parsed["ticker_set"]:
            ticker_to_reports.setdefault(ticker, set()).add(
                parsed["report"]["filename"]
            )

    overlaps = {
        ticker: sorted(report_set)
        for ticker, report_set in ticker_to_reports.items()
        if len(report_set) > 1
    }

    return {
        "reports": [parsed["report"] for parsed in parsed_reports],
        "overlapping_tickers": overlaps,
        "overlap_count": len(overlaps),
    }


def main() -> None:
    parser = ArgumentParser(description="Parse Biotech Alpha report files")
    sub = parser.add_subparsers(dest="command")

    cmd_list = sub.add_parser("list", help="Normalize report names")
    cmd_list.add_argument("reports", nargs="+", help="Report file paths")

    cmd_extract = sub.add_parser("extract", help="Extract tickers from one report")
    cmd_extract.add_argument("report", help="Report file path")

    cmd_overlap = sub.add_parser(
        "overlap", help="Find overlapping tickers across reports"
    )
    cmd_overlap.add_argument("reports", nargs="+", help="Two or more report file paths")

    cmd_previous = sub.add_parser(
        "previous", help="Select previous report for comparison"
    )
    cmd_previous.add_argument("report", help="Current report file path")
    cmd_previous.add_argument(
        "--reports-dir",
        default="outputs",
        help="Directory containing report_*.md files",
    )
    cmd_previous.add_argument(
        "--include-validation",
        action="store_true",
        help="Include validation-family reports as candidates",
    )

    args = parser.parse_args()

    if args.command == "list":
        records = [parse_report_filename(path).__dict__ for path in args.reports]
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return

    if args.command == "extract":
        print(
            json.dumps(parse_report_tickers(args.report), ensure_ascii=False, indent=2)
        )
        return

    if args.command == "overlap":
        print(json.dumps(parse_many(args.reports), ensure_ascii=False, indent=2))
        return

    if args.command == "previous":
        selected = select_previous_report(
            current_report=args.report,
            reports_dir=args.reports_dir,
            include_validation=args.include_validation,
        )
        print(
            json.dumps(
                selected.__dict__ if selected else None, ensure_ascii=False, indent=2
            )
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
