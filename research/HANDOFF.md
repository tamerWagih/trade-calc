# Handoff: edge research on the trainer-lib candles

Everything below was run on the 20 coins in `trainer-lib/` (15m candles, Jan 2021 to Oct 2026).
Fees are 0.05% per side (0.1% round trip) unless stated. "bp" = 0.01%. "R" = profit in units of the stop distance.

## Setup

```bash
pip install numpy pandas scikit-learn
cd research
python trend2.py          # any script; each prints its own results
```

`load.py` reads `../trainer-lib/` by default (set `LIB=/path/to/trainer-lib` to override).
Prices in the files are scaled integers (e.g. DOGE's low is stored as 423, roughly 0.24% steps),
so anything at 15m resolution is coarse; most tests resample to 1h, 4h or 1D.

Scripts that read other scripts (`trend2.py`, `newideas.py`, `expect4h.py`, `spotcoins.py`, `mlcheck.py`,
`diprule.py`) must be run from inside `research/`. `mlcheck.py` needs `ml_preds.pkl`, made by `ml1h.py` (~10 min).

## Rules used for every test

- Write the rule down before running it. No tuning after seeing results.
- Split time: an early period to find the idea, a later period to check it (see each script).
- Fees included. Check neighbouring settings; an edge that exists only at one setting is luck.

## What was tested and what happened

| Script | Idea | Result |
|---|---|---|
| `study.py`, `study2.py` | Cross-sectional momentum, time-series momentum, BTC lead-lag, hour/day seasonality, squeeze breakout, fading/following spikes, residual reversal (1h) | **All failed** out of sample or after fees. Only slow trend (30-90 days) stayed slightly positive. Output: `results_study*.txt` |
| `hsd.py` | Port of the HSD Align (Hull + Supertrend + Donchian) Pine strategy | 15m and 1h lose after fees. 4h "ride" +0.06 R/trade, longs carry it, shorts ~0. TP 2R weaker than riding |
| `trend.py`, `trend2.py` | **Donchian ensemble** (Zarattini, Pagani, Barbon 2025): 9 channels 5..360 days, long on N-day high, flat below channel middle, vol-scaled, long-only, daily | Positive, Sharpe ~0.77, mainly avoids crashes |
| `newideas.py` | Same + **BTC filter** (only hold when BTC score >= 5/9) + top 5 coins. Also intraday momentum (first 30 min -> last 30 min) | Ensemble+BTC filter: +33%/yr, worst drop -25%, positive every year 2022-26 (scaled to 25% avg invested). **20 of 20** neighbouring settings positive. Intraday momentum: fails (-9 to -10 bp after fees) |
| `pine_replica.py` | Python copy of `pine/trend-ensemble-btc-filter.pine` per coin | 18/20 coins profitable from 2022, median 1000 -> 1684 vs buy & hold 619 |
| `daytrade.py` | Day trading in the daily-trend direction, both ways (prior-day break, first-hour break, bias at 00:00) | **No edge**; first-hour break clearly loses |
| `ls_tf.py` | Ensemble long/short on 1D, 4h, 1h | Shorts lose on every timeframe (even 2022). 1D long +33%/yr, 4h long +23%/yr, 1h everything loses |
| `discrete.py` | Ensemble as discrete trades with labels: enter score >= 5, exit < 3, futures SL = trailing k x ATR, TP or ride | 4h spot +0.25 R/trade; futures 5xATR ride +0.10-0.15 R. TP 3R always worse |
| `expect4h.py`, `spotcoins.py` | Per-coin expected results for `pine/trend-ensemble-signals.pine` on 4h | Consistent in both halves: BTC, ETH, SOL, BNB, AVAX (+TRX). Avoid LINK, UNI, AAVE, FIL, LTC, ATOM |
| `ml1h.py`, `mlcheck.py` | **Walk-forward ML** (HistGradientBoosting, 20 features, retrained quarterly on past data only), forecast next 4h on 1h bars, long and short | Strong long forecasts: **+17 to +22 bp/trade after fees** (random long: -8 bp). Shorts ~0. Edge is buying panic dips. **Fading**: forecast/actual correlation 2023 0.048, 2024 0.059, 2025 0.019, 2026 ~0 |
| `diprule.py` | ML pattern turned into fixed rules, checked on 2021-22 (not used by the ML test) | Weak, +2 to +15 bp, near noise. Shorting euphoric spikes loses -23 to -34 bp |

## What we learned

1. Price-only edges here are **slow, long-only trend following**. Shorts and fast timeframes lost every time.
2. On 1h, 0.1% fees eat almost every signal. Maker (limit) orders at ~0.04% round trip are the biggest lever.
3. The only 1h edge found is ML-driven **long-only panic-dip buying**, and it is weakening in 2025-26.
4. Next places to look for a two-way intraday edge: **funding rates, open interest, liquidations, basis**.
   These exchange APIs were blocked in the cloud session; they are free from Binance on your own machine
   (`fapi.binance.com/fapi/v1/fundingRate`, `/futures/data/openInterestHist`, or `data.binance.vision`).

## Pine scripts (in `../pine/`)

- `trend-ensemble-btc-filter.pine` - daily, sizes continuously, long-only.
- `trend-ensemble-signals.pine` - 4h, BUY/EXIT labels; Spot mode, or Futures mode with trailing 5xATR SL and optional R:R TP.

## Suggested next step on your machine

1. Download funding rate + open interest history for the 20 coins (1h), align to the candles.
2. Add them as features to `ml1h.py` (e.g. funding z-score, OI change 4h/24h, OI change vs price change).
3. Re-run the same walk-forward test and check **shorts separately**; that is where the new data should help.
4. Evaluate with maker fees too (set fee to 0.0002 per side) to see what limit-order execution changes.
