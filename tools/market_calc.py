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
