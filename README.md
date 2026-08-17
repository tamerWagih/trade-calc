# Trade Calculator

A single-file position sizer and trade journal for USDT-M perpetual futures.
No build step, no dependencies, no network calls - `index.html` is the whole thing.

**Live:** https://tamerwagih.github.io/trade-calc/

## Tabs

- **Trade** - size a position from your stop distance. Give it risk in USDT, the
  current price, the stop loss and a reward:risk ratio; it returns the order
  value, quantity, the leverage needed to stay under a margin cap, and the take
  profit. Exchange fees are included on both sides, so the loss at your stop is
  the risk you actually typed. Warns when the stop sits near liquidation, when
  the order is under the exchange minimum, or when the leverage is impossible.
- **Journal** - log each trade as a win or a loss. Keeps win rate, net PnL,
  total and average R, worst drawdown, current streak and an equity curve.
  Export and import CSV.
- **Losing run** - what a string of consecutive losses does to the account at a
  given risk per trade, including the gain needed to get back to even. Risk is
  taken off the remaining balance, not the starting capital.
- **Compounding** - a fixed monthly percentage compounded over months or years,
  with an optional cap: above it the trading balance is held flat and the profit
  is banked instead of compounded.

## Where the data lives

The journal is kept in the browser's `localStorage`, on the device you used.
Nothing is uploaded and there is no server - this repo is static hosting only.
That also means the journal does not follow you between devices or browsers.
Use **Export CSV** on one and **Import CSV** on the other.

If the browser blocks storage (some do on `file://` pages), the Journal tab says
so in orange and keeps the trades in memory until the tab closes, rather than
dropping them silently. Export before you close it.

## Running it without the web

Download `index.html` and open it. It works offline and behaves identically,
though it gets its own separate journal because the browser treats a local file
as a different site.

## Checks

The page runs its own assertions on load and logs `self-check ok` to the console.
They cover the position maths against fees, the journal statistics, CSV quoting
and round trips, the losing-run compounding, and the compounding cap.
