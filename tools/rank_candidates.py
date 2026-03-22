#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def _clamp(value: float | None, low: float = 0.0, high: float = 1.0) -> float:
    if value is None:
        return low
    return max(low, min(high, float(value)))


def _load_items(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    raise ValueError("Input JSON must be a list of candidate objects")


def _confidence_score(item: Dict[str, Any]) -> float:
    if item.get("confidence_score") is not None:
        return _clamp(item.get("confidence_score"))
    if isinstance(item.get("confidence"), (int, float)):
        return _clamp(item.get("confidence"))
    status = str(item.get("verification_status", "")).lower()
    if "confirmed" in status:
        return 0.90
    if "estimated" in status:
        return 0.60
    return 0.35


def _materiality_score(item: Dict[str, Any]) -> float:
    if item.get("materiality_score") is not None:
        return _clamp(item.get("materiality_score"))
    event_type = str(item.get("event_type", "")).lower()
    mapping = {
        "pdufa": 0.95,
        "adcom": 0.85,
        "nda/bla": 0.82,
        "phase3topline": 0.80,
        "phase 3": 0.80,
        "phase2topline": 0.66,
        "phase 2": 0.66,
        "mfds": 0.62,
    }
    for key, value in mapping.items():
        if key in event_type:
            return value
    return 0.60


def _price_setup_score(item: Dict[str, Any]) -> float:
    score = 0.45

    tier = str(item.get("tier", "")).lower()
    if "tier 1" in tier:
        score += 0.22
    elif "tier 2" in tier:
        score += 0.12

    trend = str(item.get("trend", "")).lower()
    if "uptrend" in trend:
        score += 0.14
    elif "sideways" in trend:
        score += 0.05
    elif "downtrend" in trend:
        score -= 0.12

    days_until_event = item.get("days_until_event")
    if isinstance(days_until_event, (int, float)):
        days_until_event = float(days_until_event)
        if 7 <= days_until_event <= 60:
            score += 0.08
        elif days_until_event < 7:
            score -= 0.05
        elif days_until_event > 120:
            score -= 0.05

    near_52w_high = item.get("near_52w_high")
    if near_52w_high is True:
        score -= 0.25

    distance = item.get("distance_to_52w_high_pct")
    if isinstance(distance, (int, float)):
        distance = float(distance)
        if 0.10 < distance <= 0.35:
            score += 0.08
        elif distance > 0.50:
            score -= 0.03

    return _clamp(score)


def _balance_sheet_score(item: Dict[str, Any]) -> float:
    runway = item.get("cash_runway_months")
    if isinstance(runway, (int, float)):
        runway = float(runway)
        score = _clamp((runway - 3.0) / 21.0)
    else:
        score = 0.45

    risk_level = str(item.get("risk_level", "")).lower()
    if risk_level == "critical":
        score = min(score, 0.10)
    elif risk_level == "medium":
        score = min(score, 0.60)
    elif risk_level == "low":
        score = max(score, 0.75)
    return _clamp(score)


def _tradability_score(item: Dict[str, Any]) -> float:
    if item.get("tradability_score") is not None:
        return _clamp(item.get("tradability_score"))
    decision = str(item.get("tradability_decision", "")).lower()
    if decision == "pass":
        return 0.75
    if decision == "caution":
        return 0.55
    if decision == "weak":
        return 0.25
    return 0.40


def _historical_support_score(item: Dict[str, Any]) -> float:
    context = item.get("historical_context") or {}
    summary = context.get("historical_window_summary") or context.get("historical_window_summary".replace("_", "")) or {}
    if not isinstance(summary, dict):
        summary = {}

    values: List[float] = []
    for window in summary.values():
        if not isinstance(window, dict):
            continue
        if window.get("insufficient_history"):
            continue
        positive_ratio = window.get("positive_ratio")
        median_rel = window.get("median_relative_return")
        score = 0.50
        if isinstance(positive_ratio, (int, float)):
            score += (float(positive_ratio) - 0.5) * 0.6
        if isinstance(median_rel, (int, float)):
            score += max(-0.15, min(0.15, float(median_rel)))
        values.append(_clamp(score))

    if values:
        return round(sum(values) / len(values), 4)

    insufficient = bool(item.get("insufficient_history"))
    if insufficient:
        return 0.40
    return 0.50


def _thesis_penalty(item: Dict[str, Any]) -> float:
    break_score = _clamp(item.get("thesis_break_score"))
    flags = item.get("red_flags")
    flag_count = len(flags) if isinstance(flags, list) else 0
    penalty = break_score * 0.15 + min(0.10, flag_count * 0.02)
    return round(_clamp(penalty, 0.0, 0.30), 4)


def _investment_grade(final_score: float) -> str:
    if final_score >= 0.80:
        return "A"
    if final_score >= 0.68:
        return "B"
    if final_score >= 0.55:
        return "C"
    return "D"


def rank_candidates(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []

    for item in items:
        date_certainty = _confidence_score(item)
        catalyst_materiality = _materiality_score(item)
        price_setup = _price_setup_score(item)
        balance_sheet_safety = _balance_sheet_score(item)
        tradability = _tradability_score(item)
        historical_support = _historical_support_score(item)
        thesis_penalty = _thesis_penalty(item)

        final_score = (
            0.25 * date_certainty
            + 0.20 * catalyst_materiality
            + 0.20 * price_setup
            + 0.15 * balance_sheet_safety
            + 0.10 * tradability
            + 0.10 * historical_support
            - thesis_penalty
        )
        final_score = round(_clamp(final_score), 4)

        enriched = dict(item)
        enriched["score_breakdown"] = {
            "date_certainty": round(date_certainty, 4),
            "catalyst_materiality": round(catalyst_materiality, 4),
            "price_setup": round(price_setup, 4),
            "balance_sheet_safety": round(balance_sheet_safety, 4),
            "tradability": round(tradability, 4),
            "historical_support": round(historical_support, 4),
            "thesis_penalty": round(thesis_penalty, 4),
        }
        enriched["final_score"] = final_score
        enriched["investment_grade"] = _investment_grade(final_score)
        enriched["ranking_note"] = (
            f"certainty={date_certainty:.2f}, price_setup={price_setup:.2f}, "
            f"runway={balance_sheet_safety:.2f}, tradability={tradability:.2f}, "
            f"history={historical_support:.2f}, penalty={thesis_penalty:.2f}"
        )
        ranked.append(enriched)

    ranked.sort(
        key=lambda item: (
            -float(item.get("final_score", 0.0)),
            0 if str(item.get("tier", "")).lower() == "tier 1" else 1,
            str(item.get("ticker", "")),
        )
    )

    for idx, item in enumerate(ranked, start=1):
        item["rank"] = idx
    return ranked


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank biotech candidates deterministically")
    parser.add_argument("input", help="Path to enriched_candidates.json")
    parser.add_argument("--output", required=True, help="Output path for ranked_candidates.json")
    args = parser.parse_args()

    items = _load_items(Path(args.input))
    ranked = rank_candidates(items)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(ranked, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output_path), "count": len(ranked)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
