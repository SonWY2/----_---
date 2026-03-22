#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from math import log10
from pathlib import Path

import pandas as pd

try:
    from tools.price_data import candidate_price_tickers
except ModuleNotFoundError:  # pragma: no cover - CLI execution from tools/ directory
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from tools.price_data import candidate_price_tickers


@dataclass
class HistoryResult:
    resolved_ticker: str | None
    history: pd.DataFrame


def _download_history(raw_ticker: str | None, price_ticker: str | None = None, period: str = "6mo") -> HistoryResult:
    import yfinance as yf

    for candidate in candidate_price_tickers(raw_ticker, price_ticker):
        data = yf.download(
            candidate,
            period=period,
            progress=False,
            auto_adjust=True,
        )
        if isinstance(data, pd.DataFrame) and not data.empty:
            return HistoryResult(resolved_ticker=candidate, history=data.copy())
    return HistoryResult(resolved_ticker=None, history=pd.DataFrame())


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _score_from_log_scale(value: float | None, low: float, high: float) -> float:
    if value is None or value <= 0:
        return 0.0
    log_value = log10(value)
    return _clamp((log_value - log10(low)) / (log10(high) - log10(low)))


def analyze_tradability(ticker: str, price_ticker: str | None = None) -> dict:
    history_result = _download_history(ticker, price_ticker=price_ticker)
    hist = history_result.history

    if hist.empty:
        return {
            "ticker": ticker,
            "price_ticker": price_ticker,
            "resolved_price_ticker": history_result.resolved_ticker,
            "error": "price history unavailable",
            "avg_volume_20d": None,
            "avg_dollar_volume_20d": None,
            "realized_vol_20d": None,
            "liquidity_level": "Unknown",
            "spread_risk_proxy": "Unknown",
            "tradability_score": 0.0,
            "tradability_decision": "review",
        }

    close = hist["Close"] if "Close" in hist.columns else hist.iloc[:, -1]
    volume = hist["Volume"] if "Volume" in hist.columns else pd.Series(dtype=float)
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    close = close.dropna()
    volume = volume.dropna()

    tail_close = close.tail(20)
    tail_volume = volume.tail(20)
    current_price = float(close.iloc[-1]) if not close.empty else None

    avg_volume_20d = float(tail_volume.mean()) if not tail_volume.empty else None
    median_volume_20d = float(tail_volume.median()) if not tail_volume.empty else None

    if not tail_close.empty and not tail_volume.empty:
        aligned = pd.concat([tail_close, tail_volume], axis=1).dropna()
        aligned.columns = ["close", "volume"]
        avg_dollar_volume_20d = float((aligned["close"] * aligned["volume"]).mean()) if not aligned.empty else None
    else:
        avg_dollar_volume_20d = None

    returns = close.pct_change().dropna().tail(20)
    realized_vol_20d = float(returns.std() * (252 ** 0.5)) if not returns.empty else None

    volume_score = _score_from_log_scale(avg_volume_20d, low=5e4, high=5e6)
    value_score = _score_from_log_scale(avg_dollar_volume_20d, low=5e5, high=5e7)
    price_score = _clamp((current_price or 0.0) / 10.0) if current_price is not None else 0.0

    if realized_vol_20d is None:
        vol_penalty = 0.10
    else:
        vol_penalty = _clamp((realized_vol_20d - 0.50) / 1.50) * 0.20

    tradability_score = _clamp(0.45 * volume_score + 0.35 * value_score + 0.10 * price_score + 0.10 - vol_penalty)

    if tradability_score >= 0.75:
        liquidity_level = "High"
    elif tradability_score >= 0.55:
        liquidity_level = "Medium"
    elif tradability_score >= 0.35:
        liquidity_level = "Low"
    else:
        liquidity_level = "VeryLow"

    if realized_vol_20d is None:
        spread_risk_proxy = "Unknown"
    elif realized_vol_20d >= 1.0 or tradability_score < 0.35:
        spread_risk_proxy = "High"
    elif realized_vol_20d >= 0.65:
        spread_risk_proxy = "Medium"
    else:
        spread_risk_proxy = "Low"

    if tradability_score >= 0.70:
        decision = "pass"
    elif tradability_score >= 0.45:
        decision = "caution"
    else:
        decision = "weak"

    return {
        "ticker": ticker,
        "price_ticker": price_ticker,
        "resolved_price_ticker": history_result.resolved_ticker,
        "current_price": round(current_price, 4) if current_price is not None else None,
        "avg_volume_20d": round(avg_volume_20d, 2) if avg_volume_20d is not None else None,
        "median_volume_20d": round(median_volume_20d, 2) if median_volume_20d is not None else None,
        "avg_dollar_volume_20d": round(avg_dollar_volume_20d, 2) if avg_dollar_volume_20d is not None else None,
        "realized_vol_20d": round(realized_vol_20d, 4) if realized_vol_20d is not None else None,
        "liquidity_level": liquidity_level,
        "spread_risk_proxy": spread_risk_proxy,
        "tradability_score": round(tradability_score, 4),
        "tradability_decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate tradability metrics for a biotech ticker")
    parser.add_argument("ticker")
    parser.add_argument("--price-ticker", default=None)
    args = parser.parse_args()

    try:
        result = analyze_tradability(args.ticker, args.price_ticker)
    except Exception as exc:  # pragma: no cover - CLI safety
        result = {"ticker": args.ticker, "price_ticker": args.price_ticker, "error": str(exc)}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
