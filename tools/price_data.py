from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class PriceDownloadResult:
    requested_ticker: str | None
    resolved_ticker: str | None
    close: pd.Series


def candidate_price_tickers(raw_ticker: str | None, price_ticker: str | None = None) -> list[str]:
    seen: list[str] = []

    def add(value: str | None) -> None:
        if value is None:
            return
        token = str(value).strip()
        if not token:
            return
        if token not in seen:
            seen.append(token)

    add(price_ticker)
    if raw_ticker is None:
        return seen

    ticker = str(raw_ticker).strip().upper()
    if not ticker:
        return seen

    add(ticker)
    if ticker.isdigit() and len(ticker) == 6:
        add(f"{ticker}.KS")
        add(f"{ticker}.KQ")
    return seen


def _extract_close(data: pd.DataFrame | pd.Series | None) -> pd.Series:
    if data is None:
        return pd.Series(dtype=float)
    if isinstance(data, pd.Series):
        return data.dropna()
    if data.empty:
        return pd.Series(dtype=float)
    if 'Close' in data.columns:
        close = data['Close']
    else:
        close = data.iloc[:, -1]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna()


def download_close_series(
    raw_ticker: str | None,
    *,
    price_ticker: str | None = None,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
    period: str | None = None,
) -> PriceDownloadResult:
    candidates = candidate_price_tickers(raw_ticker, price_ticker)
    for candidate in candidates:
        kwargs = {
            'progress': False,
            'auto_adjust': True,
        }
        if period is not None:
            kwargs['period'] = period
        else:
            if start is None or end is None:
                raise ValueError('start/end or period is required')
            kwargs['start'] = start.strftime('%Y-%m-%d')
            kwargs['end'] = end.strftime('%Y-%m-%d')

        import yfinance as yf

        data = yf.download(candidate, **kwargs)
        close = _extract_close(data)
        if not close.empty:
            return PriceDownloadResult(
                requested_ticker=raw_ticker,
                resolved_ticker=candidate,
                close=close,
            )

    return PriceDownloadResult(
        requested_ticker=raw_ticker,
        resolved_ticker=None,
        close=pd.Series(dtype=float),
    )
