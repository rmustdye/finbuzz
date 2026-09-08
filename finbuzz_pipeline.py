#!/usr/bin/env python3
"""
FinBuzz Analysis Pipeline
=========================
The engine that powers FinBuzz. Takes Google Trends data and stock prices,
runs verified statistical analysis, and exports everything the dashboard needs.

Usage:
    python finbuzz_pipeline.py --trends trends.csv --ticker NVDA --output data.js

What this script does, step by step:
    1. Loads Google Trends CSV (auto-detects raw export vs pre-merged format)
    2. Fetches stock prices via yfinance (or loads from local CSV as fallback)
    3. Cleans and aligns: drops weekends/holidays, matches dates
    4. Computes daily percentage changes (NOT raw levels — avoids spurious correlation)
    5. Runs statistical analysis: Pearson correlation, lag tests, rolling correlation
    6. Verifies everything: dual computation, integrity gates, SHA-256 hashes
    7. Exports a single data.js file the dashboard reads

Requirements:
    pip install pandas yfinance scipy --break-system-packages

Author: FinBuzz Project
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# ── Attempt imports for optional dependencies ──────────────────────────
try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False
    print("WARNING: yfinance not installed. Stock prices must be provided via --prices flag.")

try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("WARNING: scipy not installed. Only pandas correlation will be available (no p-values).")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 1: DATA LOADING
# ═══════════════════════════════════════════════════════════════════════

def sha256_file(filepath):
    """
    Compute SHA-256 hash of a file.
    
    Why: Every input file gets hashed so anyone can verify the data hasn't
    been tampered with. This is the provenance stamp shown on the dashboard.
    """
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def load_google_trends(filepath):
    """
    Load a Google Trends CSV, auto-detecting the format.
    
    Google Trends exports come in two formats:
    
    Format A (raw export from trends.google.com):
        First few lines are metadata like "Category: All categories"
        Then a blank line, then the actual data: "Day,keyword: (Region)"
        
    Format B (pre-merged / cleaned):
        Standard CSV with columns like "Date" and "Trend_Score"
    
    This function detects which format it is and handles both.
    """
    # Read the first few lines to detect format
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        first_lines = [f.readline() for _ in range(5)]
    
    # Format A detection: raw Google Trends export has metadata headers
    is_raw_export = any(
        line.startswith('Category:') or 
        line.startswith('Interest over time') or
        'isPartial' in line
        for line in first_lines
    )
    
    if is_raw_export:
        # Skip metadata rows — find where the actual data starts
        # Google Trends CSVs have variable header rows, then a blank line, 
        # then "Day,keyword" or "Week,keyword"
        df = pd.read_csv(filepath, skiprows=_find_data_start(filepath))
        
        # Rename columns to our standard names
        date_col = df.columns[0]  # "Day" or "Week"
        value_col = df.columns[1]  # "AI stocks: (United States)" etc
        
        df = df.rename(columns={date_col: 'Date', value_col: 'Trend_Score'})
        
        # Google sometimes puts "<1" for very low values — replace with 0.5
        df['Trend_Score'] = pd.to_numeric(
            df['Trend_Score'].replace('<1', '0.5'), 
            errors='coerce'
        )
    else:
        # Format B: standard CSV
        df = pd.read_csv(filepath)
        
        # Try to identify date and score columns by name
        date_candidates = ['Date', 'date', 'Day', 'day', 'Week', 'week']
        score_candidates = ['Trend_Score', 'trend_score', 'Interest', 'interest',
                          'AI stocks: (United States)', 'Score', 'score']
        
        date_col = _find_column(df, date_candidates, 'date')
        score_col = _find_column(df, score_candidates, 'trend score')
        
        df = df.rename(columns={date_col: 'Date', score_col: 'Trend_Score'})
    
    # Parse dates
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Drop any rows where the score is missing
    df = df.dropna(subset=['Trend_Score'])
    
    # Ensure score is numeric
    df['Trend_Score'] = pd.to_numeric(df['Trend_Score'], errors='coerce')
    df = df.dropna(subset=['Trend_Score'])
    
    return df[['Date', 'Trend_Score']].sort_values('Date').reset_index(drop=True)


def _find_data_start(filepath):
    """Find the row number where actual data begins in a raw Google Trends CSV."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        for i, line in enumerate(f):
            stripped = line.strip()
            # The data header row starts with "Day," or "Week,"
            if stripped.startswith('Day,') or stripped.startswith('Week,'):
                return i
    # Fallback: skip first 2 rows (most common case)
    return 2


def _find_column(df, candidates, description):
    """Find a column by trying multiple possible names."""
    for name in candidates:
        if name in df.columns:
            return name
    # If no candidate matches, try case-insensitive partial match
    for col in df.columns:
        for name in candidates:
            if name.lower() in col.lower():
                return col
    raise ValueError(
        f"Could not find {description} column. "
        f"Columns available: {list(df.columns)}. "
        f"Expected one of: {candidates}"
    )


def fetch_stock_prices(ticker, start_date, end_date):
    """
    Fetch adjusted closing prices from Yahoo Finance via yfinance.
    
    Why adjusted close (not regular close): Adjusted close accounts for
    stock splits and dividends. If NVDA did a 10:1 split, the raw close
    price would drop 90% overnight — which isn't a real price change.
    Adjusted close corrects for this so the numbers are comparable over time.
    """
    if not HAS_YFINANCE:
        raise ImportError(
            "yfinance is not installed. Install it with: "
            "pip install yfinance --break-system-packages\n"
            "Or provide a local CSV with --prices flag."
        )
    
    # Add buffer days to ensure we cover the full range
    # (yfinance sometimes misses the boundary dates)
    buffer_start = start_date - timedelta(days=5)
    buffer_end = end_date + timedelta(days=5)
    
    stock = yf.download(
        ticker, 
        start=buffer_start.strftime('%Y-%m-%d'),
        end=buffer_end.strftime('%Y-%m-%d'),
        progress=False
    )
    
    if stock.empty:
        raise ValueError(f"No data returned for {ticker}. Check the ticker symbol.")
    
    # Handle multi-level columns that yfinance sometimes returns
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = stock.columns.get_level_values(0)
    
    # Use Adj Close if available, otherwise Close
    price_col = 'Adj Close' if 'Adj Close' in stock.columns else 'Close'
    
    df = stock[[price_col]].reset_index()
    df.columns = ['Date', 'Close_Price']
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    
    return df.sort_values('Date').reset_index(drop=True)


def load_local_prices(filepath):
    """Load stock prices from a local CSV (fallback when yfinance is unavailable)."""
    df = pd.read_csv(filepath)
    
    date_col = _find_column(df, ['Date', 'date', 'Datetime'], 'date')
    price_candidates = ['Adj Close', 'Close', 'close', 'Close_Price', 'Price', 'price',
                       'Adj_Close', 'AdjClose']
    price_col = _find_column(df, price_candidates, 'price')
    
    df = df.rename(columns={date_col: 'Date', price_col: 'Close_Price'})
    df['Date'] = pd.to_datetime(df['Date'])
    df['Close_Price'] = pd.to_numeric(df['Close_Price'], errors='coerce')
    df = df.dropna(subset=['Close_Price'])
    
    return df[['Date', 'Close_Price']].sort_values('Date').reset_index(drop=True)


# ═══════════════════════════════════════════════════════════════════════
# SECTION 2: CLEANING AND ALIGNMENT
# ═══════════════════════════════════════════════════════════════════════

def align_data(trends_df, prices_df):
    """
    Merge trends and prices on matching dates (inner join = trading days only).
    
    Why inner join: Google Trends has data for every day (including weekends),
    but stock markets are closed on weekends and holidays. An inner join keeps
    only the days where BOTH have data — i.e., trading days. This is correct
    because we want to correlate search interest with price CHANGES, and price
    changes only happen on trading days.
    
    The difference in row counts (e.g., 93 calendar days → 59 trading days)
    is a feature, not a bug. The dashboard explains this.
    """
    # Normalize dates to midnight for clean matching
    trends_df['Date'] = pd.to_datetime(trends_df['Date']).dt.normalize()
    prices_df['Date'] = pd.to_datetime(prices_df['Date']).dt.normalize()
    
    # Inner join: only dates present in BOTH datasets
    merged = pd.merge(trends_df, prices_df, on='Date', how='inner')
    
    if len(merged) == 0:
        raise ValueError(
            "No overlapping dates between trends and prices! "
            f"Trends range: {trends_df['Date'].min()} to {trends_df['Date'].max()}. "
            f"Prices range: {prices_df['Date'].min()} to {prices_df['Date'].max()}."
        )
    
    return merged.sort_values('Date').reset_index(drop=True)


def run_integrity_gates(df):
    """
    Integrity gates — the pipeline refuses to publish if any of these fail.
    
    These are non-negotiable checks. If the data fails any gate, we stop
    and report why rather than publishing bad analysis.
    """
    errors = []
    
    # Gate 1: No duplicate dates
    dupes = df[df['Date'].duplicated()]
    if len(dupes) > 0:
        errors.append(f"DUPLICATE DATES found: {dupes['Date'].tolist()}")
    
    # Gate 2: Trend scores in valid range (0–100)
    out_of_range = df[(df['Trend_Score'] < 0) | (df['Trend_Score'] > 100)]
    if len(out_of_range) > 0:
        errors.append(
            f"TREND SCORES OUT OF RANGE (0-100): "
            f"min={df['Trend_Score'].min()}, max={df['Trend_Score'].max()}"
        )
    
    # Gate 3: Prices must be positive
    if (df['Close_Price'] <= 0).any():
        errors.append(f"NEGATIVE OR ZERO PRICES found")
    
    # Gate 4: Dates must be monotonically increasing
    if not df['Date'].is_monotonic_increasing:
        errors.append("DATES ARE NOT IN ORDER")
    
    # Gate 5: Minimum data points for meaningful statistics
    if len(df) < 20:
        errors.append(
            f"INSUFFICIENT DATA: {len(df)} points. "
            f"Need at least 20 for meaningful correlation."
        )
    
    if errors:
        print("\n" + "=" * 60)
        print("INTEGRITY GATES FAILED — REFUSING TO PUBLISH")
        print("=" * 60)
        for e in errors:
            print(f"  ✗ {e}")
        print("=" * 60 + "\n")
        sys.exit(1)
    
    print(f"  ✓ All integrity gates passed ({len(df)} data points)")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 3: STATISTICAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def compute_pct_changes(df):
    """
    Compute daily percentage changes for both trend score and price.
    
    WHY % CHANGES, NOT RAW LEVELS:
    This is the single most important methodological choice in FinBuzz.
    
    If NVDA's price goes from $100 to $200 over 3 months, and search interest
    also trends upward, the raw-level correlation will be high — but it's
    MEANINGLESS. Any two things that both trend upward will show high
    correlation. This is called "spurious correlation" and it's one of the
    most common mistakes in amateur data analysis.
    
    The fix: correlate the CHANGES. Did search interest go UP today? Did the
    price go UP today? That's the real question. Daily % changes remove the
    trend and test the actual day-to-day relationship.
    
    Formula: pct_change = (today - yesterday) / yesterday × 100
    The first row becomes NaN (no "yesterday" to compare to) and gets dropped.
    """
    df = df.copy()
    df['Trend_Change'] = df['Trend_Score'].pct_change() * 100
    df['Price_Change'] = df['Close_Price'].pct_change() * 100
    
    # Drop the first row (NaN from pct_change) and any other NaN/inf values
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=['Trend_Change', 'Price_Change'])
    
    return df


def compute_correlation(df):
    """
    Compute Pearson correlation with DUAL VERIFICATION.
    
    Two independent computations:
    1. scipy.stats.pearsonr (gives r AND p-value)
    2. pandas .corr() (independent implementation)
    
    If they disagree beyond floating-point rounding (tolerance: 0.001),
    something is wrong and we refuse to publish.
    
    Returns: dict with r, p_value, n, method, and verification status
    """
    trend_changes = df['Trend_Change'].values
    price_changes = df['Price_Change'].values
    n = len(df)
    
    # Method 1: scipy (primary — gives p-value)
    if HAS_SCIPY:
        r_scipy, p_scipy = scipy_stats.pearsonr(trend_changes, price_changes)
    else:
        r_scipy, p_scipy = None, None
    
    # Method 2: pandas (verification)
    r_pandas = df['Trend_Change'].corr(df['Price_Change'])
    
    # Dual-computation check
    if r_scipy is not None:
        if abs(r_scipy - r_pandas) > 0.001:
            print("\n" + "=" * 60)
            print("DUAL COMPUTATION CHECK FAILED — REFUSING TO PUBLISH")
            print(f"  scipy r  = {r_scipy:.6f}")
            print(f"  pandas r = {r_pandas:.6f}")
            print(f"  difference = {abs(r_scipy - r_pandas):.6f}")
            print("=" * 60 + "\n")
            sys.exit(1)
        
        r = r_scipy
        p = p_scipy
        method = 'scipy+pandas (dual verified)'
    else:
        r = r_pandas
        p = None
        method = 'pandas only (scipy unavailable, no p-value)'
    
    # Interpret significance
    if p is not None:
        if p < 0.01:
            significance = 'Statistically significant (p < 0.01)'
        elif p < 0.05:
            significance = 'Statistically significant (p < 0.05)'
        else:
            significance = f'NOT statistically significant (p = {p:.3f})'
    else:
        significance = 'p-value unavailable (scipy not installed)'
    
    # Interpret strength
    abs_r = abs(r)
    if abs_r < 0.1:
        strength = 'negligible'
    elif abs_r < 0.3:
        strength = 'weak'
    elif abs_r < 0.5:
        strength = 'moderate'
    elif abs_r < 0.7:
        strength = 'strong'
    else:
        strength = 'very strong'
    
    result = {
        'r': round(r, 4),
        'p_value': round(p, 4) if p is not None else None,
        'n': n,
        'strength': strength,
        'significance': significance,
        'method': method,
        'dual_verified': r_scipy is not None
    }
    
    p_str = f"{p:.4f}" if p is not None else "N/A"
    print(f"  ✓ Correlation: r = {r:.4f}, p = {p_str} ({strength}, {significance})")
    return result


def compute_lag_analysis(df, max_lag=5):
    """
    Test whether search interest LEADS stock price by 1–5 days.
    
    The question: if people search "AI stocks" more on Monday, does NVDA's
    price go up on Tuesday? Wednesday? That would mean search interest has
    predictive power.
    
    Method: shift the trend data forward by N days and correlate with
    unshifted price data. If lag-2 has a strong positive correlation, it
    means today's search interest correlates with the price change 2 days later.
    
    CRITICAL: Multiple comparison honesty. Testing 5 lags means 5 chances
    to find a "significant" result by random chance. If lag-1 is positive
    and lag-3 is negative, that's the fingerprint of false positives from
    multiple testing. We flag this explicitly.
    """
    lags = {}
    signs = []
    
    for lag in range(0, max_lag + 1):
        shifted = df.copy()
        if lag > 0:
            shifted['Trend_Change'] = shifted['Trend_Change'].shift(lag)
            shifted = shifted.dropna()
        
        if len(shifted) < 20:
            continue
        
        if HAS_SCIPY:
            r, p = scipy_stats.pearsonr(
                shifted['Trend_Change'].values,
                shifted['Price_Change'].values
            )
        else:
            r = shifted['Trend_Change'].corr(shifted['Price_Change'])
            p = None
        
        lags[lag] = {
            'r': round(r, 4),
            'p_value': round(p, 4) if p is not None else None,
            'n': len(shifted),
            'significant': p < 0.05 if p is not None else False
        }
        signs.append(r > 0)
    
    # Multiple comparison flag: if significant lags have opposite signs,
    # they're almost certainly false positives
    sig_lags = {k: v for k, v in lags.items() if v.get('significant', False)}
    has_opposite_signs = False
    if len(sig_lags) >= 2:
        sig_signs = [v['r'] > 0 for v in sig_lags.values()]
        has_opposite_signs = len(set(sig_signs)) > 1
    
    result = {
        'lags': lags,
        'max_lag_tested': max_lag,
        'significant_lags': list(sig_lags.keys()),
        'opposite_sign_flag': has_opposite_signs,
        'interpretation': (
            'NOISE: Significant lags have opposite signs — '
            'fingerprint of false positives from multiple comparisons.'
            if has_opposite_signs else
            f'{len(sig_lags)} significant lag(s) found.'
            if sig_lags else
            'No significant lead-lag relationship detected.'
        )
    }
    
    print(f"  ✓ Lag analysis: {result['interpretation']}")
    return result


def compute_rolling_correlation(df, window=14):
    """
    Compute rolling Pearson correlation over a sliding window.
    
    Why: The overall correlation might be near zero, but that could mean
    the relationship flip-flops between positive and negative in different
    periods. A rolling window shows this instability — which is itself
    an important finding.
    
    Window size: 14 trading days ≈ 3 calendar weeks. Large enough for
    statistical meaning, small enough to show variation.
    """
    if len(df) < window:
        return {'window': window, 'values': [], 'dates': [],
                'note': f'Insufficient data for {window}-day rolling window'}
    
    rolling_r = df['Trend_Change'].rolling(window).corr(df['Price_Change'])
    
    # Build the output arrays (skip NaN from the warm-up period)
    valid = rolling_r.dropna()
    dates = df.loc[valid.index, 'Date'].dt.strftime('%Y-%m-%d').tolist()
    values = [round(v, 4) for v in valid.tolist()]
    
    result = {
        'window': window,
        'values': values,
        'dates': dates,
        'mean': round(np.mean(values), 4) if values else None,
        'std': round(np.std(values), 4) if values else None,
        'min': round(min(values), 4) if values else None,
        'max': round(max(values), 4) if values else None,
    }
    
    print(f"  ✓ Rolling correlation ({window}-day): "
          f"mean={result['mean']}, range=[{result['min']}, {result['max']}]")
    return result


def compute_smoothed_data(df, window=7):
    """
    Compute 7-day rolling average for the smoothed view.
    
    Why: Google Trends data can be noisy day to day (sampling variance).
    A rolling average smooths this out so you can see the underlying pattern.
    The dashboard shows both raw and smoothed, with a toggle.
    """
    df = df.copy()
    df['Trend_Smoothed'] = df['Trend_Score'].rolling(window, min_periods=1).mean()
    df['Price_Smoothed'] = df['Close_Price'].rolling(window, min_periods=1).mean()
    return df


# ═══════════════════════════════════════════════════════════════════════
# SECTION 4: EXPORT
# ═══════════════════════════════════════════════════════════════════════

def build_output(df, df_with_changes, correlation, lag_analysis, 
                 rolling_corr, hashes, ticker, keyword, metadata):
    """
    Build the complete data.js output that the dashboard reads.
    
    This is a JavaScript file (not JSON) because it's loaded directly
    by the HTML page with a <script> tag — no server needed.
    """
    # Time series data for charts
    chart_data = {
        'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
        'trend_scores': df['Trend_Score'].tolist(),
        'trend_smoothed': df['Trend_Smoothed'].tolist(),
        'close_prices': [round(p, 2) for p in df['Close_Price'].tolist()],
        'price_smoothed': [round(p, 2) for p in df['Price_Smoothed'].tolist()],
    }
    
    # Analysis results
    analysis = {
        'correlation': correlation,
        'lag_analysis': lag_analysis,
        'rolling_correlation': rolling_corr,
    }
    
    # Summary statistics
    summary = {
        'ticker': ticker,
        'keyword': keyword,
        'date_range': {
            'start': df['Date'].min().strftime('%Y-%m-%d'),
            'end': df['Date'].max().strftime('%Y-%m-%d'),
        },
        'trading_days': len(df),
        'calendar_days': (df['Date'].max() - df['Date'].min()).days,
        'price_range': {
            'start': round(df['Close_Price'].iloc[0], 2),
            'end': round(df['Close_Price'].iloc[-1], 2),
            'return_pct': round(
                (df['Close_Price'].iloc[-1] / df['Close_Price'].iloc[0] - 1) * 100, 1
            ),
        },
        'trend_range': {
            'min': int(df['Trend_Score'].min()),
            'max': int(df['Trend_Score'].max()),
            'mean': round(df['Trend_Score'].mean(), 1),
        },
    }
    
    # Provenance
    provenance = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'pipeline_version': '2.0',
        'file_hashes': hashes,
        'methodology': 'Pearson correlation on daily % changes, dual-verified (scipy + pandas)',
    }
    
    output = {
        'chart_data': chart_data,
        'analysis': analysis,
        'summary': summary,
        'provenance': provenance,
        'metadata': metadata,
    }
    
    return output


class NumpyEncoder(json.JSONEncoder):
    """Handle numpy types that json.dumps can't serialize by default."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def export_data_js(output, filepath):
    """Export as a JavaScript file the dashboard can load with a <script> tag."""
    js_content = "// FinBuzz Data — Auto-generated by finbuzz_pipeline.py\n"
    js_content += f"// Generated: {output['provenance']['generated_at']}\n"
    js_content += "// Do not edit manually — re-run the pipeline instead.\n\n"
    js_content += f"const FINBUZZ_DATA = {json.dumps(output, indent=2, cls=NumpyEncoder)};\n"
    
    with open(filepath, 'w') as f:
        f.write(js_content)
    
    print(f"\n  ✓ Exported to {filepath} ({os.path.getsize(filepath):,} bytes)")


def export_summary_json(output, filepath):
    """Export a plain-language summary for non-technical readers."""
    corr = output['analysis']['correlation']
    summary = output['summary']
    
    plain = {
        'headline': (
            f"Search interest in \"{summary['keyword']}\" showed a {corr['strength']} "
            f"correlation (r = {corr['r']}) with {summary['ticker']} daily returns "
            f"over {summary['trading_days']} trading days."
        ),
        'finding': corr['significance'],
        'interpretation': (
            "The relationship between search attention and stock price movement "
            "was not statistically significant in this window. Instances where "
            "they appeared to move together likely trace to shared news events "
            "(earnings, Fed decisions, competitive announcements) that drove both "
            "searches and prices independently."
        ),
        'data_window': f"{summary['date_range']['start']} to {summary['date_range']['end']}",
        'stock_return': f"{summary['price_range']['return_pct']:+.1f}%",
        'lag_result': output['analysis']['lag_analysis']['interpretation'],
        'caveat': (
            "This is one keyword, one stock, over one time window. "
            "It is not a universal claim. Google Trends scores are normalized "
            "and sampled — different query windows produce different scores. "
            "Correlation does not imply causation."
        ),
    }
    
    with open(filepath, 'w') as f:
        json.dump(plain, f, indent=2)
    
    print(f"  ✓ Summary exported to {filepath}")


# ═══════════════════════════════════════════════════════════════════════
# SECTION 5: MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='FinBuzz Analysis Pipeline — Google Trends vs Stock Prices'
    )
    parser.add_argument('--trends', required=True, 
                       help='Path to Google Trends CSV')
    parser.add_argument('--ticker', default='NVDA',
                       help='Stock ticker symbol (default: NVDA)')
    parser.add_argument('--keyword', default='AI stocks',
                       help='Search keyword tracked (default: "AI stocks")')
    parser.add_argument('--prices', default=None,
                       help='Path to local stock prices CSV (fallback if yfinance unavailable)')
    parser.add_argument('--output', default='data.js',
                       help='Output file path (default: data.js)')
    parser.add_argument('--summary', default='analysis_summary.json',
                       help='Summary output path (default: analysis_summary.json)')
    parser.add_argument('--window-name', default='Window',
                       help='Human-readable name for this analysis window')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  FinBuzz Analysis Pipeline v2.0")
    print("=" * 60)
    
    # ── Step 1: Load data ──────────────────────────────────────────
    print("\n[1/6] Loading data...")
    
    # Hash input files for provenance
    hashes = {'trends': sha256_file(args.trends)}
    print(f"  ✓ Trends CSV: {args.trends}")
    print(f"    SHA-256: {hashes['trends'][:16]}...")
    
    trends_df = load_google_trends(args.trends)
    print(f"    {len(trends_df)} rows, {trends_df['Date'].min().date()} to {trends_df['Date'].max().date()}")
    
    # Fetch or load stock prices
    if args.prices:
        hashes['prices'] = sha256_file(args.prices)
        prices_df = load_local_prices(args.prices)
        print(f"  ✓ Prices CSV: {args.prices}")
    else:
        print(f"  ✓ Fetching {args.ticker} prices via yfinance...")
        prices_df = fetch_stock_prices(
            args.ticker,
            trends_df['Date'].min(),
            trends_df['Date'].max()
        )
        hashes['prices'] = 'fetched-via-yfinance'
    
    print(f"    {len(prices_df)} rows, {prices_df['Date'].min().date()} to {prices_df['Date'].max().date()}")
    
    # ── Step 2: Clean and align ────────────────────────────────────
    print("\n[2/6] Cleaning and aligning...")
    
    merged = align_data(trends_df, prices_df)
    print(f"  ✓ Aligned: {len(merged)} trading days "
          f"(from {len(trends_df)} calendar days)")
    
    # ── Step 3: Integrity gates ────────────────────────────────────
    print("\n[3/6] Running integrity gates...")
    run_integrity_gates(merged)
    
    # ── Step 4: Analysis ───────────────────────────────────────────
    print("\n[4/6] Running statistical analysis...")
    
    # Compute % changes
    df_changes = compute_pct_changes(merged)
    print(f"  ✓ Computed daily % changes ({len(df_changes)} valid pairs)")
    
    # Correlation (with dual verification)
    correlation = compute_correlation(df_changes)
    
    # Lag analysis
    lag_analysis = compute_lag_analysis(df_changes, max_lag=5)
    
    # Rolling correlation
    rolling_corr = compute_rolling_correlation(df_changes, window=14)
    
    # ── Step 5: Smooth and prepare chart data ──────────────────────
    print("\n[5/6] Preparing chart data...")
    
    merged_smoothed = compute_smoothed_data(merged, window=7)
    print(f"  ✓ 7-day smoothing applied")
    
    # ── Step 6: Export ─────────────────────────────────────────────
    print("\n[6/6] Exporting...")
    
    metadata = {
        'window_name': args.window_name,
        'ticker': args.ticker,
        'keyword': args.keyword,
    }
    
    output = build_output(
        merged_smoothed, df_changes, correlation, lag_analysis,
        rolling_corr, hashes, args.ticker, args.keyword, metadata
    )
    
    export_data_js(output, args.output)
    export_summary_json(output, args.summary)
    
    # ── Final summary ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Ticker:       {args.ticker}")
    print(f"  Keyword:      \"{args.keyword}\"")
    print(f"  Window:       {merged['Date'].min().date()} to {merged['Date'].max().date()}")
    print(f"  Trading days: {len(merged)}")
    print(f"  Correlation:  r = {correlation['r']}, p = {correlation['p_value']}")
    print(f"  Significance: {correlation['significance']}")
    print(f"  Lag result:   {lag_analysis['interpretation']}")
    print(f"  Output:       {args.output}")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
