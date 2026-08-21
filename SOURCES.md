# SOURCES.md — Complete Citation Registry

Every factual claim in FinBuzz with its primary source URL. All verified August 2026.

## NVIDIA Earnings

| Claim | Source | URL |
|-------|--------|-----|
| Q2 FY2026 (Aug 27, 2025): EPS $1.05, Revenue $46.7B, +56% YoY | NVIDIA Investor Relations | https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2026/default.aspx |
| Q2 FY2026 SEC filing (10-Q) | SEC EDGAR | https://www.sec.gov/Archives/edgar/data/1045810/000104581025000209/nvda-20250727.htm |
| Q2 FY2026 CNBC coverage: beat estimates, stock slipped | CNBC | https://www.cnbc.com/2025/08/27/nvidia-nvda-earnings-report-q2-2026.html |
| Q3 FY2026 (Nov 19, 2025): Revenue $57.0B, EPS $1.30, +62% YoY | SEC EDGAR | https://www.sec.gov/Archives/edgar/data/1045810/000104581025000228/q3fy26pr.htm |
| Q4 FY2026 (Feb 25, 2026): Revenue $68.1B, EPS $1.62 | NVIDIA Newsroom | https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026 |
| Q1 FY2026 (May 28, 2025): Revenue $44.1B, EPS $0.81, H20 charge | SEC EDGAR | https://www.sec.gov/Archives/edgar/data/1045810/000104581025000115/q1fy26pr.htm |
| Q2 FY2027 earnings date: Aug 26, 2026 | NVIDIA IR | https://investor.nvidia.com/events-and-presentations/events-and-presentations/event-details/2026/NVIDIA-2nd-Quarter-FY27-Financial-Results/default.aspx |
| 24.3 billion shares outstanding (as of Aug 22, 2025) | SEC 10-Q | https://www.sec.gov/Archives/edgar/data/1045810/000104581025000209/nvda-20250727.htm |

## Federal Reserve Decisions

| Claim | Source | URL |
|-------|--------|-----|
| Sep 17, 2025: Cut 25bp to 4.00-4.25%. Vote 11-1 (Miran dissented for 50bp) | CNBC | https://www.cnbc.com/2025/09/17/fed-rate-decision-september-2025.html |
| Oct 29, 2025: Cut 25bp to 3.75-4.00%. Vote 10-2 | CNBC | https://www.cnbc.com/2025/10/29/fed-rate-decision-october-2025.html |
| Dec 10, 2025: Cut 25bp to 3.50-3.75%. Vote 9-3. Three dissenters | Federal Reserve (official statement) | https://www.federalreserve.gov/newsevents/pressreleases/monetary20251210a.htm |
| Dec 10, 2025: FOMC minutes | Federal Reserve | https://www.federalreserve.gov/monetarypolicy/fomcminutes20251210.htm |
| Three consecutive 25bp cuts in 2025 (Sep, Oct, Dec) ending at 3.50-3.75% | Congress.gov (CRS report) | https://www.congress.gov/crs-product/IN12635 |
| Mar 18, 2026: Fed holds at 3.50-3.75%, citing Iran conflict (11-1 vote) | Fidelity | https://www.fidelity.com/learning-center/trading-investing/fed-funds-rate-history |
| Jun 2026: Fed holds again under new Chair Kevin Warsh. Vote 9-3 | Charles Schwab | https://www.schwab.com/learn/story/fomc-meeting |
| FOMC meeting calendar | Federal Reserve | https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm |

## NVIDIA Corporate Events

| Claim | Source | URL |
|-------|--------|-----|
| 10-for-1 stock split effective June 7, 2024 | SEC EDGAR 8-K | https://www.sec.gov/Archives/edgar/data/1045810/000104581024000144/nvda-20240607.htm |
| 10-for-1 split announcement | CNBC | https://www.cnbc.com/2024/05/22/nvidia-announces-10-for-1-stock-split.html |
| ~$21B SpaceX stake disclosed Aug 14, 2026 (122.8M shares) | CNBC | https://www.cnbc.com/2026/08/14/nvidia-discloses-21-billion-stake-in-spacex-at-end-of-second-quarter.html |
| SpaceX stake (Bloomberg confirmation) | Bloomberg | https://www.bloomberg.com/news/articles/2026-08-14/nvidia-has-21-billion-spacex-stake-30-billion-in-intel-shares |
| OpenAI PORTS-Pike data center Ohio, Aug 17, 2026 | CNN Markets | https://www.cnn.com/markets/stocks/NVDA |
| 52-week high $236.54 (May 14, 2026) | StockScan | https://stockscan.io/stocks/NVDA/price-history |
| 52-week low $164.07 (Sep 5, 2025) | Robinhood | https://robinhood.com/us/en/stocks/NVDA/ |
| Close $219.74 (Aug 18, 2026) | Macrotrends | https://www.macrotrends.net/stocks/charts/NVDA/nvidia/stock-price-history |

## Data Methodology

| Claim | Source | URL |
|-------|--------|-----|
| Google Trends: scores 0-100, peak=100 within window | Google Support | https://support.google.com/trends/answer/4365533 |
| NYSE regular session: 9:30 AM - 4:00 PM Eastern | NYSE | https://www.nyse.com/markets/hours-calendars |
| Pearson correlation: ranges -1 to +1 | Wikipedia (reference) | https://en.wikipedia.org/wiki/Pearson_correlation_coefficient |
| Spurious correlations examples | Tyler Vigen | https://www.tylervigen.com/spurious-correlations |
| GitHub Pages: free for public repos | GitHub Docs | https://docs.github.com/en/pages |

## Statistical Results (computed, not sourced — independently replicated)

| Value | Window | Method |
|-------|--------|--------|
| r = -0.151, p = 0.258 | Window 1 (Aug-Nov 2025, 59 days) | Pearson on daily % changes, dual-verified scipy+pandas |
| r = -0.179, p = 0.175 | Window 2 (Apr-Jul 2026, 60 days) | Pearson on daily % changes, dual-verified scipy+pandas |
| r = -0.062, p = 0.661 | Full Year (Jul 2025-Jul 2026, 53 weeks) | Pearson on weekly % changes, dual-verified |
| 31/59 dates disagree between two CSV pulls | Cross-check | Two independent Google Trends exports compared |
| 0 of 16 lag tests show consistent predictive signal | All windows | Lags 0-5 tested per window, opposite-sign flagging |
