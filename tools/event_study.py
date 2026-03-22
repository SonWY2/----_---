#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from datetime import timedelta
from pathlib import Path

import pandas as pd

try:
    from tools.price_data import download_close_series
except ModuleNotFoundError:  # pragma: no cover - CLI execution from tools/ directory
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from tools.price_data import download_close_series


WINDOWS = [(-60, -7), (-30, -7), (-10, 3)]


def _parse_date(value):
    if not value:
        return None
    try:
        parsed = pd.Timestamp(value)
        if parsed is pd.NaT:
            return None
        return parsed.normalize()
    except Exception:
        return None


def _price_on_or_before(series, target_date):
    idx = series.index[series.index <= target_date]
    if len(idx) == 0:
        return None
    return float(series.loc[idx[-1]])


def _price_on_or_after(series, target_date):
    idx = series.index[series.index >= target_date]
    if len(idx) == 0:
        return None
    return float(series.loc[idx[0]])


def _window_return(series, event_date, start_offset, end_offset):
    start_target = event_date + timedelta(days=start_offset)
    end_target = event_date + timedelta(days=end_offset)

    start_price = _price_on_or_after(series, start_target)
    end_price = _price_on_or_before(series, end_target)

    if start_price is None or end_price is None or start_price <= 0:
        return None
    return (end_price / start_price) - 1.0


def _iqr(values):
    if len(values) < 2:
        return 0.0
    q1 = pd.Series(values).quantile(0.25)
    q3 = pd.Series(values).quantile(0.75)
    return float(q3 - q1)


def _bootstrap_ci_mean(values, n_resamples=1000, seed=42):
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    means = []
    n = len(values)
    for _ in range(n_resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    low = means[int(0.025 * len(means))]
    high = means[int(0.975 * len(means))]
    return [float(low), float(high)]


def _annual_returns(close_series, as_of_date, max_years):
    as_of_price = _price_on_or_before(close_series, as_of_date)
    out = {}
    for years in range(1, max_years + 1):
        key = f"{years}y"
        anchor = as_of_date - pd.DateOffset(years=years)
        start_price = _price_on_or_after(close_series, anchor)
        if as_of_price is None or start_price is None or start_price <= 0:
            out[key] = None
        else:
            out[key] = float((as_of_price / start_price) - 1.0)
    return out


def _event_metrics(stock_close, bench_close, event_date):
    result = {}
    for start_offset, end_offset in WINDOWS:
        window_key = f"[{start_offset},{end_offset}]"
        stock_ret = _window_return(stock_close, event_date, start_offset, end_offset)
        bench_ret = _window_return(bench_close, event_date, start_offset, end_offset)
        rel_ret = None
        if stock_ret is not None and bench_ret is not None:
            rel_ret = stock_ret - bench_ret
        result[window_key] = {
            'stock_return': stock_ret,
            'benchmark_return': bench_ret,
            'relative_return': rel_ret,
        }
    return result


def _summarize_historical(event_window_results, min_sample_n):
    summary = {}
    for start_offset, end_offset in WINDOWS:
        window_key = f"[{start_offset},{end_offset}]"
        values = []
        for item in event_window_results:
            info = item.get(window_key, {})
            value = info.get('relative_return')
            if value is not None:
                values.append(float(value))

        if not values:
            summary[window_key] = {
                'sample_n': 0,
                'mean_relative_return': None,
                'median_relative_return': None,
                'iqr_relative_return': None,
                'positive_ratio': None,
                'ci95_mean_relative_return': None,
                'insufficient_history': True,
            }
            continue

        positive = len([v for v in values if v > 0])
        summary[window_key] = {
            'sample_n': len(values),
            'mean_relative_return': float(pd.Series(values).mean()),
            'median_relative_return': float(pd.Series(values).median()),
            'iqr_relative_return': _iqr(values),
            'positive_ratio': float(positive / len(values)),
            'ci95_mean_relative_return': _bootstrap_ci_mean(values),
            'insufficient_history': len(values) < min_sample_n,
        }
    return summary


def _make_note(summary):
    valid_windows = [
        key for key, value in summary.items() if not value.get('insufficient_history', True)
    ]
    if not valid_windows:
        return '표본 수가 충분하지 않아 과거 이벤트 패턴의 통계적 해석을 보류합니다.'

    positive_windows = 0
    for key in valid_windows:
        if summary[key].get('median_relative_return', 0.0) > 0:
            positive_windows += 1

    if positive_windows == len(valid_windows):
        return '과거 이벤트 윈도우에서 벤치마크 대비 상대수익이 반복적으로 양(+)의 방향을 보였습니다.'
    if positive_windows > 0:
        return '과거 패턴은 혼재되어 있으므로 단일 신호로 해석하지 말고 리스크 규칙과 함께 보수적으로 사용하십시오.'
    return '과거 이벤트 윈도우에서 벤치마크 대비 우위가 일관되지 않았습니다. 실행 비중을 낮추는 보수적 접근이 필요합니다.'


def analyze_candidate(candidate, benchmark, max_years, min_sample_n, as_of_date):
    ticker = candidate.get('ticker')
    event_id = candidate.get('event_id', f"{ticker}-unknown")
    event_date = _parse_date(candidate.get('event_date'))
    price_ticker = candidate.get('resolved_price_ticker') or candidate.get('price_ticker')

    if not ticker or event_date is None:
        return {
            'event_id': event_id,
            'ticker': ticker,
            'error': 'missing ticker or event_date',
            'insufficient_history': True,
        }

    history_start = min(
        event_date - timedelta(days=365 * max_years),
        as_of_date - timedelta(days=365 * max_years),
    )
    history_end = max(as_of_date, event_date) + timedelta(days=10)

    stock_download = download_close_series(ticker, price_ticker=price_ticker, start=history_start, end=history_end)
    bench_download = download_close_series(benchmark, start=history_start, end=history_end)
    stock_close = stock_download.close
    bench_close = bench_download.close

    if stock_close.empty or bench_close.empty:
        return {
            'event_id': event_id,
            'ticker': ticker,
            'price_ticker': price_ticker,
            'resolved_price_ticker': stock_download.resolved_ticker,
            'benchmark': benchmark,
            'error': 'price history unavailable',
            'insufficient_history': True,
        }

    annual = _annual_returns(stock_close, as_of_date, max_years)
    current_event = _event_metrics(stock_close, bench_close, event_date)

    historical_dates = []
    for value in candidate.get('historical_event_dates', []):
        parsed = _parse_date(value)
        if parsed is not None:
            historical_dates.append(parsed)

    event_results = []
    if historical_dates:
        for dt in historical_dates:
            event_results.append(_event_metrics(stock_close, bench_close, dt))
    else:
        event_results.append(current_event)

    summary = _summarize_historical(event_results, min_sample_n)
    note = _make_note(summary)
    insufficient = all(item.get('insufficient_history', True) for item in summary.values())

    limitations = []
    if not historical_dates:
        limitations.append('historical_event_dates가 제공되지 않아 현재 이벤트 기준 단일 표본 분석으로 대체됨')
    if insufficient:
        limitations.append('window별 sample_n이 최소 기준에 미달')

    return {
        'event_id': event_id,
        'ticker': ticker,
        'price_ticker': price_ticker,
        'resolved_price_ticker': stock_download.resolved_ticker,
        'benchmark': benchmark,
        'analysis_as_of': as_of_date.strftime('%Y-%m-%d'),
        'lookback_years': max_years,
        'windows': [f"[{a},{b}]" for a, b in WINDOWS],
        'annual_returns': annual,
        'current_event_window_metrics': current_event,
        'historical_window_summary': summary,
        'sample_n': {k: v.get('sample_n', 0) for k, v in summary.items()},
        'insufficient_history': insufficient,
        'historical_significance_note': note,
        'limitations': limitations,
    }


def run(input_path, output_path, benchmark, max_years, min_sample_n, as_of_date):
    items = json.loads(Path(input_path).read_text(encoding='utf-8'))
    if not isinstance(items, list):
        raise ValueError('Input JSON must be a list of candidate objects')

    results = [
        analyze_candidate(item, benchmark, max_years, min_sample_n, as_of_date)
        for item in items
    ]
    Path(output_path).write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return results


def main():
    parser = argparse.ArgumentParser(description='Analyze historical biotech event significance')
    parser.add_argument('input_json')
    parser.add_argument('--output', required=True)
    parser.add_argument('--benchmark', default='XBI')
    parser.add_argument('--max-years', type=int, default=5)
    parser.add_argument('--min-sample-n', type=int, default=3)
    parser.add_argument('--today', default=None)
    args = parser.parse_args()

    as_of_date = _parse_date(args.today) if args.today else pd.Timestamp.now().normalize()
    results = run(
        args.input_json,
        args.output,
        benchmark=args.benchmark,
        max_years=args.max_years,
        min_sample_n=args.min_sample_n,
        as_of_date=as_of_date,
    )
    print(json.dumps({'count': len(results), 'output': args.output}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
