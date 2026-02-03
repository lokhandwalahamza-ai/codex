#!/usr/bin/env python3
"""Placeholder news sentiment engine."""
from __future__ import annotations

import argparse
import json
from datetime import datetime


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute news sentiment for tickers.")
    parser.add_argument("--input", required=True, help="Input JSON with tickers.")
    parser.add_argument("--output", required=True, help="Output JSON path.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    tickers = payload.get("tickers") or list(payload.get("technical", {}).keys())
    if not tickers:
        raise ValueError("Input must include tickers or technical signals.")

    sentiment = {
        ticker: {
            "sentiment_score": 0.0,
            "summary": "No news source configured.",
            "source": "none",
        }
        for ticker in tickers
    }

    output = {
        "as_of": datetime.utcnow().isoformat(),
        "sentiment": sentiment,
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)


if __name__ == "__main__":
    main()
