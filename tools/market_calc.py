#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import timedelta

import pandas as pd

try:
    from tools.price_data import download_close_series
except ModuleNotFoundError:  # pragma: no cover - CLI execution from tools/ directory
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from tools.price_data import download_close_series


def analyze_ticker(ticker: str, event_date_str: str, price_ticker: str | None = None) -> dict:
    event_date = pd.Timestamp(event_date_str).normalize()
    today = pd.Timestamp.now().normalize()

    entry_date = event_date - timedelta(days=60)
    exit_date = event_date - timedelta(days=7)

    history = download_close_series(ticker, price_ticker=price_ticker, period='1y')
    close = history.close

    if close.empty:
        return {
            'ticker': ticker,
            'price_ticker': price_ticker,
            'resolved_price_ticker': None,
            'event_date': event_date.strftime('%Y-%m-%d'),
            'today_date': today.strftime('%Y-%m-%d'),
            'target_entry_date': entry_date.strftime('%Y-%m-%d'),
            'target_exit_date': exit_date.strftime('%Y-%m-%d'),
            'days_until_entry': int((entry_date - today).days),
            'current_price': None,
            'trend': 'Unknown',
            'ma20': None,
            'ma60': None,
            'fifty_two_week_high': None,
            'distance_to_52w_high_pct': None,
            'near_52w_high': None,
            'error': 'price history unavailable',
        }

    current_price = float(close.iloc[-1])
    ma20 = float(close.rolling(window=20).mean().iloc[-1]) if len(close) >= 20 else None
    ma60 = float(close.rolling(window=60).mean().iloc[-1]) if len(close) >= 60 else None
    high_52w = float(close.max()) if not close.empty else None
    dist_high = None
    near_high = None
    if high_52w and high_52w > 0:
        dist_high = float((high_52w - current_price) / high_52w)
        near_high = dist_high <= 0.10

    trend = 'Unknown'
    if ma20 is not None and ma60 is not None:
        if current_price >= ma20 >= ma60:
            trend = 'Uptrend'
        elif current_price < ma20 < ma60:
            trend = 'Downtrend'
        else:
            trend = 'Sideways'
    elif ma20 is not None:
        trend = 'Uptrend' if current_price >= ma20 else 'Downtrend'

    return {
        'ticker': ticker,
        'price_ticker': price_ticker,
        'resolved_price_ticker': history.resolved_ticker,
        'event_date': event_date.strftime('%Y-%m-%d'),
        'today_date': today.strftime('%Y-%m-%d'),
        'target_entry_date': entry_date.strftime('%Y-%m-%d'),
        'target_exit_date': exit_date.strftime('%Y-%m-%d'),
        'days_until_entry': int((entry_date - today).days),
        'days_until_event': int((event_date - today).days),
        'current_price': round(current_price, 4),
        'trend': trend,
        'ma20': round(ma20, 4) if ma20 is not None else None,
        'ma60': round(ma60, 4) if ma60 is not None else None,
        'fifty_two_week_high': round(high_52w, 4) if high_52w is not None else None,
        'distance_to_52w_high_pct': round(dist_high, 6) if dist_high is not None else None,
        'near_52w_high': near_high,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Calculate biotech catalyst entry/exit dates and price position')
    parser.add_argument('ticker')
    parser.add_argument('event_date')
    parser.add_argument('--price-ticker', default=None)
    args = parser.parse_args()

    try:
        result = analyze_ticker(args.ticker, args.event_date, args.price_ticker)
    except Exception as exc:  # pragma: no cover - CLI safety
        result = {'ticker': args.ticker, 'event_date': args.event_date, 'error': str(exc)}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
