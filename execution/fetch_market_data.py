#!/usr/bin/env python3
"""Fetch OHLCV market data for a universe."""
from __future__ import annotations

import argparse
import csv
import json
import random
import urllib.request
from datetime import date, datetime, timedelta
from importlib.util import find_spec
from pathlib import Path
from typing import Iterable, List, Tuple


DEFAULT_UNIVERSES = {
    "nifty 50": [
        "RELIANCE",
        "TCS",
        "HDFCBANK",
        "INFY",
        "ICICIBANK",
        "HINDUNILVR",
        "ITC",
        "SBIN",
        "LT",
        "BHARTIARTL",
        "KOTAKBANK",
        "ASIANPAINT",
        "BAJFINANCE",
        "HCLTECH",
        "MARUTI",
        "SUNPHARMA",
        "AXISBANK",
        "ULTRACEMCO",
        "WIPRO",
        "ADANIENT",
    ],
    "nifty 100": [
        "RELIANCE",
        "TCS",
        "HDFCBANK",
        "INFY",
        "ICICIBANK",
        "HINDUNILVR",
        "ITC",
        "SBIN",
        "LT",
        "BHARTIARTL",
        "KOTAKBANK",
        "ASIANPAINT",
        "BAJFINANCE",
        "HCLTECH",
        "MARUTI",
        "SUNPHARMA",
        "AXISBANK",
        "ULTRACEMCO",
        "WIPRO",
        "ADANIENT",
        "TITAN",
        "NESTLEIND",
        "POWERGRID",
        "NTPC",
        "M&M",
        "TATASTEEL",
        "BAJAJFINSV",
        "INDUSINDBK",
        "DIVISLAB",
        "ONGC",
    ],
    "nifty 500": [
        "RELIANCE",
        "TCS",
        "HDFCBANK",
        "INFY",
        "ICICIBANK",
        "HINDUNILVR",
        "ITC",
        "SBIN",
        "LT",
        "BHARTIARTL",
        "KOTAKBANK",
        "ASIANPAINT",
        "BAJFINANCE",
        "HCLTECH",
        "MARUTI",
        "SUNPHARMA",
        "AXISBANK",
        "ULTRACEMCO",
        "WIPRO",
        "ADANIENT",
        "TITAN",
        "NESTLEIND",
        "POWERGRID",
        "NTPC",
        "M&M",
        "TATASTEEL",
        "BAJAJFINSV",
        "INDUSINDBK",
        "DIVISLAB",
        "ONGC",
        "COALINDIA",
        "JSWSTEEL",
        "TECHM",
        "CIPLA",
        "DRREDDY",
        "HDFCLIFE",
        "ICICIGI",
        "IOC",
        "BPCL",
        "HEROMOTOCO",
        "EICHERMOT",
        "BRITANNIA",
        "DABUR",
        "GODREJCP",
        "SHREECEM",
        "GRASIM",
        "TATAMOTORS",
        "PIDILITIND",
        "UPL",
    ],
}


def _fetch_csv_symbols(url: str) -> List[str]:
    with urllib.request.urlopen(url, timeout=15) as response:
        content = response.read().decode("utf-8")
    reader = csv.DictReader(content.splitlines())
    symbols = [row.get("Symbol", "").strip() for row in reader]
    return [symbol for symbol in symbols if symbol]


def _load_universe(universe: str) -> Tuple[List[str], str]:
    universe_key = universe.strip().lower()
    url_map = {
        "nifty 50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        "nifty 100": "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv",
        "nifty 500": "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv",
    }
    if universe_key not in url_map:
        raise ValueError(f"Unsupported universe: {universe}")

    source = "fallback"
    symbols: List[str] = []
    try:
        symbols = _fetch_csv_symbols(url_map[universe_key])
        source = "niftyindices.com"
    except Exception:
        symbols = DEFAULT_UNIVERSES[universe_key]
        source = "embedded-fallback"

    return [f"{symbol}.NS" for symbol in symbols], source


def _parse_lookback(lookback: str) -> int:
    lookback = lookback.strip().lower()
    if lookback.endswith("mo"):
        months = int(lookback[:-2])
        return max(20, months * 21)
    if lookback.endswith("y"):
        years = int(lookback[:-1])
        return max(20, years * 252)
    if lookback.endswith("d"):
        days = int(lookback[:-1])
        return max(20, days)
    return 126


def _generate_trading_days(days: int) -> List[date]:
    today = date.today()
    trading_days: List[date] = []
    cursor = today
    while len(trading_days) < days:
        if cursor.weekday() < 5:
            trading_days.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(trading_days))


def _generate_synthetic_series(ticker: str, days: List[date]) -> List[dict]:
    seed = abs(hash(ticker)) % (2**32)
    rng = random.Random(seed)
    base_price = 80 + (seed % 120)
    price = float(base_price)
    rows = []
    for day in days:
        drift = rng.gauss(0.0005, 0.01)
        open_price = price * (1 + rng.gauss(0.0, 0.003))
        close_price = price * (1 + drift)
        high = max(open_price, close_price) * (1 + abs(rng.gauss(0.0, 0.01)))
        low = min(open_price, close_price) * (1 - abs(rng.gauss(0.0, 0.01)))
        volume = int(1_000_000 * (1 + abs(rng.gauss(0.0, 0.35))))
        rows.append(
            {
                "Date": day.isoformat(),
                "Open": round(open_price, 2),
                "High": round(high, 2),
                "Low": round(low, 2),
                "Close": round(close_price, 2),
                "Volume": volume,
            }
        )
        price = close_price
    return rows


def _write_csv(path: Path, rows: List[dict]) -> None:
    if not rows:
        return
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _download_with_yfinance(tickers: Iterable[str], lookback: str, output_dir: Path) -> Tuple[dict, dict]:
    if not (find_spec("pandas") and find_spec("yfinance")):
        raise RuntimeError("pandas and yfinance are required for live downloads.")
    import pandas as pd
    import yfinance as yf

    data = yf.download(
        tickers=" ".join(tickers),
        period=lookback,
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        threads=True,
        progress=False,
    )

    errors = {}
    output_files = {}
    for ticker in tickers:
        if ticker not in data.columns.get_level_values(0):
            errors[ticker] = "missing data"
            continue
        df = data[ticker].dropna()
        if df.empty:
            errors[ticker] = "empty data"
            continue
        df = df.rename(columns=str.title)
        df.index.name = "Date"
        file_path = output_dir / f"{ticker.replace('.', '_')}.csv"
        df.to_csv(file_path)
        output_files[ticker] = str(file_path)
    return output_files, errors


def _download_synthetic(tickers: Iterable[str], lookback: str, output_dir: Path) -> Tuple[dict, dict]:
    days = _generate_trading_days(_parse_lookback(lookback))
    output_files = {}
    errors = {}
    for ticker in tickers:
        rows = _generate_synthetic_series(ticker, days)
        if not rows:
            errors[ticker] = "no synthetic data"
            continue
        file_path = output_dir / f"{ticker.replace('.', '_')}.csv"
        _write_csv(file_path, rows)
        output_files[ticker] = str(file_path)
    return output_files, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OHLCV data for NSE/BSE tickers.")
    parser.add_argument("--input", required=True, help="Input JSON with universe or tickers.")
    parser.add_argument("--output", required=True, help="Output JSON path.")
    parser.add_argument("--lookback", default="6mo", help="Lookback period for data.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    tickers = payload.get("tickers")
    universe_source = None
    if not tickers:
        universe = payload.get("universe")
        if not universe:
            raise ValueError("Input must include 'tickers' or 'universe'.")
        tickers, universe_source = _load_universe(universe)

    output_path = Path(args.output)
    output_dir = output_path.parent / "market_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    errors: dict = {}
    output_files: dict = {}
    data_source = "synthetic"
    try:
        output_files, errors = _download_with_yfinance(tickers, args.lookback, output_dir)
        data_source = "yfinance"
    except Exception:
        output_files, errors = _download_synthetic(tickers, args.lookback, output_dir)
        data_source = "synthetic"

    result = {
        "as_of": datetime.utcnow().isoformat(),
        "tickers": tickers,
        "data_dir": str(output_dir),
        "files": output_files,
        "errors": errors,
        "data_source": data_source,
        "universe_source": universe_source,
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)


if __name__ == "__main__":
    main()
