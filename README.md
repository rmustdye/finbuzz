# FinBuzz - Testing what the market actually listens to

A self-built narrative-testing engine. It takes the most popular retail trading belief of 2025-2026 - that search attention moves stock prices - tests it against a year of verified data, identifies the confounding variable most sentiment trackers miss, and publishes the result honestly.

**Live site:** [rmustdye.github.io/finbuzz](https://rmustdye.github.io/finbuzz/)

## The finding

Three independent analysis windows, 172 data points, two granularities, three market conditions. The correlations between daily changes in Google search interest for "AI stocks" and NVDA price returns: -0.151, -0.179, -0.062. None statistically significant. Sixteen lag tests produced zero consistent predictive signals.

The original contribution: every instance where attention and price appeared to move together traces to a confounding variable - a news event (earnings, Fed decision, competitive threat) that drove both the searches and the price. The searches are an echo. The price is a reaction. Neither causes the other.

## Three analysis windows

| Window | Period | Granularity | Days | r | p | NVDA return |
|--------|--------|-------------|------|---|---|-------------|
| 1 | Aug-Nov 2025 | Daily | 59 | -0.151 | 0.258 | +5.9% |
| 2 | Apr-Jul 2026 | Daily | 60 | -0.179 | 0.175 | -0.4% |
| Full year | Jul 2025-Jul 2026 | Weekly | 53 wk | -0.062 | 0.661 | +18.8% |

## What's in the repo

| File | What it is |
|------|-----------|
| `index.html` | The live dashboard - three data windows, 13 sourced events, interactive charts, methodology |
| `data.js` | Backup of the embedded data (also baked into index.html) |
| `DECISIONS.md` | Every analytical choice documented with reasoning |
| `finbuzz_pipeline.py` | The Python analysis engine - auto-detects raw file formats |
| `.nojekyll` | Tells GitHub Pages to serve plain HTML |
| `README.md` | This file |
| `FinBuzz_Trends_Data.csv` | Raw Google Trends data (Window 1) |
| `FinBuzz_Merged_Data_FINAL.csv` | Original merged dataset from Colab |
| `analysis_summary.json` | Plain-language stats summary |

## Event sources

All 13 events on the timeline are sourced from primary documents:

- **NVDA earnings:** SEC EDGAR 8-K filings (Q2-Q4 FY2026, Q1-Q2 FY2027)
- **Fed rate decisions:** federalreserve.gov FOMC statements
- **AI regulation:** Federal Register executive orders, EU Parliament agreements
- **Industry events:** NVIDIA newsroom, Reuters, CNBC

Five consecutive NVDA earnings beats across the analysis period. The stock fell after three of them. Search interest spiked around every earnings date. Price direction was inconsistent. This is the confounding variable in action.

## Methodology

- Correlations on daily percentage changes, not raw levels (avoids spurious correlation)
- Every correlation computed two independent ways (scipy + pandas); pipeline refuses to publish if they disagree
- Rolling correlation shows relationship instability (+0.84 to -0.85)
- Lag tests with multiple-comparison honesty (opposite-sign results flagged as noise)
- Google Trends normalization disclosed (scores are relative per window)
- All raw files SHA-256 hashed for provenance
- Event context timeline identifies confounding variables behind every co-movement

## Deploy from scratch

1. Create a public repo on GitHub named `finbuzz`
2. Upload all files (drag-and-drop on the repo page)
3. Settings > Pages > Branch: main > Folder: / (root) > Save
4. Wait 2 minutes. Live at `https://[username].github.io/finbuzz/`

## Refresh the data

1. Download a Google Trends CSV (US, "AI stocks", 3-month custom range)
2. Run the Colab script (fetches NVDA prices automatically via yfinance)
3. Paste the new data into `index.html`
4. Commit. Site updates in 2 minutes.

See `DECISIONS.md` for the reasoning behind every analytical choice.

## Not investment advice

Educational research project. Not a trading system. Not a universal claim. One keyword, one stock, three windows. The finding is narrow, honest, and reproducible.
