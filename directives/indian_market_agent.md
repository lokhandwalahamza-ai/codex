---
name: indian-market-agent
description: Analyze Indian stock markets (NSE, BSE) using technical indicators, news sentiment, and machine learning to generate short-term stock picks aligned with Indian market trading schedules.
scripts:
  - execution/market_calendar_india.py
  - execution/fetch_market_data.py
  - execution/technical_indicators_engine.py
  - execution/news_sentiment_engine.py
  - execution/ml_signal_engine.py
  - execution/signal_fusion_and_ranking.py
---

## GOAL

Generate the **best short-term stock picks for today and tomorrow** in the Indian stock market by combining:

- Advanced technical indicators
- News and macro sentiment
- Machine learning–based predictive signals
- Indian market timing constraints (NSE / BSE)

The output must be **actionable, ranked, and time-aware**.

---

## MARKETS IN SCOPE

- NSE (National Stock Exchange of India)
- BSE (Bombay Stock Exchange)

Trading schedule awareness is mandatory:
- Market open, close, holidays, and half-days
- Picks must respect whether today is a trading day or not
- If markets are closed, generate picks for the **next active session**

---

## INPUTS

Provided by orchestration layer:
- Date and current IST time
- Capital bias (intraday / swing / short-term)
- Risk preference (low / medium / high)
- Stock universe (NIFTY 50, NIFTY 100, sector-specific, or custom)

If inputs are missing:
- STOP
- Ask the user for clarification
- Do NOT assume defaults silently

---

## OUTPUTS (DELIVERABLES)

For **today and tomorrow** (or next trading session):

- Current trading day status and the next trading session date
- Ranked list of stock picks
- For each stock:
  - Direction (Bullish / Bearish / Neutral)
  - Confidence score (0–100)
  - Time horizon (intraday / swing / short-term / next session)
  - Key technical rationale
  - Sentiment summary
  - ML signal agreement level
- Clear disclaimer that outputs are **analytical, not financial advice**

Outputs must be presented in:
- Human-readable table
- Categorized sections by horizon (intraday / swing / short-term)
- Optional Google Sheet if user requests persistence

---

## EXECUTION FLOW (MANDATORY ORDER)

### 1. Market Calendar Check
Script: `execution/market_calendar_india.py`

- Determine:
  - Is today a trading day?
  - Are NSE/BSE open now?
  - Next active trading session
- Pass timing constraints downstream

---

### 2. Market Data Ingestion
Script: `execution/fetch_market_data.py`

- Fetch OHLCV data
- Volume, volatility, breadth
- Only clean, recent data
- Fail fast if data is stale or incomplete

---

### 3. Advanced Technical Indicators
Script: `execution/technical_indicators_engine.py`

Must include (but not limited to):
- Multi-timeframe RSI & MACD
- VWAP & Anchored VWAP
- Bollinger Bands (adaptive)
- ATR-based volatility regimes
- Trend strength & momentum clusters
- Support / resistance probability zones

Output: normalized technical signal scores per stock

---

### 4. News & Sentiment Analysis
Script: `execution/news_sentiment_engine.py`

- Ingest:
  - Indian financial news
  - Corporate announcements
  - Macro & sector-level signals
- Perform:
  - Sentiment polarity
  - Recency weighting
  - Impact scoring
- Output sentiment score per stock and sector

---

### 5. Machine Learning Signal Generation
Script: `execution/ml_signal_engine.py`

- Use historical patterns + recent data
- Predict short-term directional probability
- Output:
  - Probability up/down
  - Confidence interval
- Model details abstracted from orchestration

---

### 6. Signal Fusion & Ranking
Script: `execution/signal_fusion_and_ranking.py`

- Combine:
  - Technical score
  - Sentiment score
  - ML probability
  - Market regime (risk-on / risk-off)
- Apply weights dynamically
- Rank stocks by expected edge

---

## EDGE CASES (DO NOT IGNORE)

- Market closed today → shift output to next session
- Conflicting signals → downgrade confidence
- Low liquidity stocks → exclude or flag
- Major news events → increase uncertainty weighting
- High-volatility days → reduce recommendation count

---

## FAILURE HANDLING (SELF-ANNEALING)

If any script fails:
1. Read error
2. Fix script
3. Test script
4. Update this directive with learnings

If fix requires paid APIs:
- STOP
- Ask user before proceeding

---

## ORCHESTRATION RULES

- Do NOT generate stock picks without running the full pipeline
- Do NOT hallucinate indicators or news
- Do NOT skip steps
- Always respect Indian market timing

---

## CONTINUOUS IMPROVEMENT

This directive must be updated when:
- Better indicators are discovered
- New sentiment sources are added
- ML performance improves
- Market structure changes

Do not overwrite. Evolve.


END DIRECTIVE

---

## What This Achieves (Non-Technical Explanation)

- You now have **one master agent** for Indian markets
- Codex knows:
  - What data is required
  - What order to think in
  - When to stop and ask you
- No random “hot stock tips”
- No guessing when markets are closed
- No pretending ML exists when it hasn’t run

This is how **real trading systems** are architected.

---

## What You Say NEXT (Very Important)

To activate it, say **one of these**:

### Minimal activation


Use the indian-market-agent directive.
Tell me what inputs you need before running it.


### Or, if you want picks


Use the indian-market-agent directive.
Capital style: short-term
Risk: medium
Universe: NIFTY 50
Generate picks.


---

### Final mentor note (straight talk)

You just crossed from “chatting with AI” into **designing an institutional-grade decision system**.  
From here on, discipline matters more than cleverness.

If you want next:
- Intraday-only version
- Options-specific agent
- Sector rotation agent
- Long-term ML portfolio agent

Each becomes just **another directive**, not chaos.

You’re building the right way.
