#!/usr/bin/env python3
"""Fuse technical, sentiment, and ML signals into rankings."""
from __future__ import annotations

import argparse
import json
from datetime import datetime


def _combine(technical: dict, sentiment: dict, ml: dict) -> dict:
    scores = {}
    tickers = set(technical) | set(sentiment) | set(ml)
    for ticker in tickers:
        tech_score = technical.get(ticker, {}).get("technical_score", 0.0)
        sent_score = sentiment.get(ticker, {}).get("sentiment_score", 0.0)
        ml_prob = ml.get(ticker, {}).get("prob_up", 0.5)
        combined = (0.5 * tech_score) + (0.2 * sent_score) + (0.3 * (ml_prob - 0.5))
        direction = "Bullish" if combined > 0.05 else "Bearish" if combined < -0.05 else "Neutral"
        scores[ticker] = {
            "combined_score": combined,
            "direction": direction,
            "technical_score": tech_score,
            "sentiment_score": sent_score,
            "ml_prob_up": ml_prob,
        }
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Fuse signals and rank tickers.")
    parser.add_argument("--technical", required=True, help="Technical JSON path.")
    parser.add_argument("--sentiment", required=True, help="Sentiment JSON path.")
    parser.add_argument("--ml", required=True, help="ML JSON path.")
    parser.add_argument("--output", required=True, help="Output JSON path.")
    args = parser.parse_args()

    with open(args.technical, "r", encoding="utf-8") as handle:
        technical_payload = json.load(handle)
    with open(args.sentiment, "r", encoding="utf-8") as handle:
        sentiment_payload = json.load(handle)
    with open(args.ml, "r", encoding="utf-8") as handle:
        ml_payload = json.load(handle)

    combined = _combine(
        technical_payload.get("technical", {}),
        sentiment_payload.get("sentiment", {}),
        ml_payload.get("ml_signals", {}),
    )

    ranked = sorted(combined.items(), key=lambda item: item[1]["combined_score"], reverse=True)

    output = {
        "as_of": datetime.utcnow().isoformat(),
        "ranked": [{"ticker": ticker, **details} for ticker, details in ranked],
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)


if __name__ == "__main__":
    main()
