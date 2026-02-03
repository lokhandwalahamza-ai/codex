#!/usr/bin/env python3
"""Compute technical indicators for each ticker."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from datetime import datetime
from typing import Dict, List


def _read_rows(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            rows.append(
                {
                    "Date": row.get("Date"),
                    "Open": float(row.get("Open", 0) or 0),
                    "High": float(row.get("High", 0) or 0),
                    "Low": float(row.get("Low", 0) or 0),
                    "Close": float(row.get("Close", 0) or 0),
                    "Volume": float(row.get("Volume", 0) or 0),
                }
            )
    return rows


def _rolling_mean(values: List[float], period: int) -> List[float | None]:
    means: List[float | None] = []
    for idx in range(len(values)):
        if idx + 1 < period:
            means.append(None)
            continue
        window = values[idx + 1 - period : idx + 1]
        means.append(sum(window) / period)
    return means


def _rolling_std(values: List[float], period: int) -> List[float | None]:
    stds: List[float | None] = []
    for idx in range(len(values)):
        if idx + 1 < period:
            stds.append(None)
            continue
        window = values[idx + 1 - period : idx + 1]
        stds.append(statistics.pstdev(window))
    return stds


def _ema(values: List[float], period: int) -> List[float | None]:
    ema_values: List[float | None] = []
    if not values:
        return ema_values
    multiplier = 2 / (period + 1)
    ema = values[0]
    for idx, value in enumerate(values):
        if idx == 0:
            ema = value
        else:
            ema = (value - ema) * multiplier + ema
        ema_values.append(ema)
    return ema_values


def _rsi(values: List[float], period: int = 14) -> List[float | None]:
    gains: List[float] = []
    losses: List[float] = []
    rsi_values: List[float | None] = [None]
    for idx in range(1, len(values)):
        delta = values[idx] - values[idx - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
        if idx < period:
            rsi_values.append(None)
            continue
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))
    return rsi_values


def _macd(values: List[float]) -> List[float | None]:
    ema12 = _ema(values, 12)
    ema26 = _ema(values, 26)
    macd = [(a - b) if a is not None and b is not None else None for a, b in zip(ema12, ema26)]
    signal = _ema([v if v is not None else 0.0 for v in macd], 9)
    histogram: List[float | None] = []
    for macd_value, signal_value in zip(macd, signal):
        if macd_value is None or signal_value is None:
            histogram.append(None)
        else:
            histogram.append(macd_value - signal_value)
    return histogram


def _atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[float | None]:
    true_ranges: List[float] = []
    for idx in range(len(highs)):
        if idx == 0:
            true_ranges.append(highs[idx] - lows[idx])
        else:
            high_low = highs[idx] - lows[idx]
            high_close = abs(highs[idx] - closes[idx - 1])
            low_close = abs(lows[idx] - closes[idx - 1])
            true_ranges.append(max(high_low, high_close, low_close))
    return _rolling_mean(true_ranges, period)


def _vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float]) -> List[float | None]:
    vwap_values: List[float | None] = []
    cumulative_volume = 0.0
    cumulative_vp = 0.0
    for high, low, close, volume in zip(highs, lows, closes, volumes):
        typical_price = (high + low + close) / 3
        cumulative_volume += volume
        cumulative_vp += typical_price * volume
        vwap_values.append(cumulative_vp / cumulative_volume if cumulative_volume else None)
    return vwap_values


def _bollinger(closes: List[float], period: int = 20) -> List[tuple[float | None, float | None, float | None]]:
    sma = _rolling_mean(closes, period)
    stds = _rolling_std(closes, period)
    bands: List[tuple[float | None, float | None, float | None]] = []
    for mean, std in zip(sma, stds):
        if mean is None or std is None:
            bands.append((None, None, None))
        else:
            bands.append((mean + 2 * std, mean - 2 * std, mean))
    return bands


def _last_valid(values: List[float | None], default: float = 0.0) -> float:
    for value in reversed(values):
        if value is not None and not math.isnan(value):
            return float(value)
    return default


def _score_signal(latest: dict) -> float:
    score = 0.0
    score += (latest["rsi"] - 50) / 50
    score += latest["macd_histogram"]
    if latest["bollinger_sma"]:
        score += (latest["close"] - latest["bollinger_sma"]) / latest["bollinger_sma"]
    if latest["close"]:
        score -= latest["atr"] / latest["close"]
    return float(score)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute technical indicators for tickers.")
    parser.add_argument("--input", required=True, help="Input JSON from fetch_market_data.")
    parser.add_argument("--output", required=True, help="Output JSON path.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    files = payload.get("files", {})
    results: Dict[str, dict] = {}

    for ticker, path in files.items():
        rows = _read_rows(path)
        if not rows:
            continue
        closes = [row["Close"] for row in rows]
        highs = [row["High"] for row in rows]
        lows = [row["Low"] for row in rows]
        volumes = [row["Volume"] for row in rows]

        rsi_values = _rsi(closes)
        macd_histogram = _macd(closes)
        atr_values = _atr(highs, lows, closes)
        vwap_values = _vwap(highs, lows, closes, volumes)
        bollinger = _bollinger(closes)

        latest = {
            "close": closes[-1],
            "rsi": _last_valid(rsi_values, 50.0),
            "macd_histogram": _last_valid(macd_histogram, 0.0),
            "atr": _last_valid(atr_values, 0.0),
            "vwap": _last_valid(vwap_values, closes[-1]),
            "bollinger_sma": next((mean for _, _, mean in reversed(bollinger) if mean is not None), closes[-1]),
        }

        results[ticker] = {
            "technical_score": _score_signal(latest),
            "latest": {
                "close": float(latest["close"]),
                "rsi": float(latest["rsi"]),
                "macd_histogram": float(latest["macd_histogram"]),
                "atr": float(latest["atr"]),
                "vwap": float(latest["vwap"]),
                "bollinger_sma": float(latest["bollinger_sma"]),
            },
        }

    output = {
        "as_of": datetime.utcnow().isoformat(),
        "technical": results,
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)


if __name__ == "__main__":
    main()
