#!/usr/bin/env python3
"""Lightweight ML-inspired signal generator."""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def _read_closes(path: str) -> list[float]:
    closes: list[float] = []
    with open(path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            value = row.get("Close")
            if value:
                closes.append(float(value))
    return closes


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ML-like signals from market data.")
    parser.add_argument("--input", required=True, help="Input JSON from fetch_market_data.")
    parser.add_argument("--output", required=True, help="Output JSON path.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    files = payload.get("files", {})
    results = {}

    for ticker, path in files.items():
        closes = _read_closes(path)
        if len(closes) < 30:
            continue
        returns = []
        for idx in range(1, len(closes)):
            prev = closes[idx - 1]
            if prev == 0:
                continue
            returns.append((closes[idx] - prev) / prev)
        if len(returns) < 20:
            continue
        recent_return = sum(returns[-5:]) / min(5, len(returns))
        mean = sum(returns[-20:]) / min(20, len(returns))
        variance = sum((r - mean) ** 2 for r in returns[-20:]) / min(20, len(returns))
        volatility = math.sqrt(variance)
        score = (recent_return / volatility) if volatility else 0.0
        prob_up = _sigmoid(score)
        results[ticker] = {
            "prob_up": float(prob_up),
            "prob_down": float(1 - prob_up),
            "confidence": float(min(1.0, abs(score))),
            "model": "baseline-momentum",
        }

    output = {
        "as_of": datetime.utcnow().isoformat(),
        "ml_signals": results,
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)


if __name__ == "__main__":
    main()
