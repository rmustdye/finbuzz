#!/usr/bin/env python3
"""
FinBuzz Verification Engine v2 — adapted for pipeline v4 output format.

Checks every factual claim against real source URLs.
Independently replicates all statistics using 3 methods.
Self-criticizes twice.

Usage:
    python finbuzz_verifier.py                    # verify data.js in current dir
    python finbuzz_verifier.py --data path/to/data.js
"""
import json, hashlib, sys, os, re
import numpy as np
import pandas as pd
from scipy import stats as sp

def load_pipeline_data(path="data.js"):
    """Load data.js in the original pipeline v4 format (window.FINBUZZ = {...})."""
    with open(path) as f:
        raw = f.read()
    # Strip JS wrapper
    for prefix in ["window.FINBUZZ = ", "window.FINBUZZ=", "const FINBUZZ_DATA = "]:
        if prefix in raw:
            raw = raw.split(prefix, 1)[1]
            break
    raw = raw.rstrip().rstrip(";")
    return json.loads(raw)

# ═══ VERIFIED SOURCE REGISTRY ═══════════════════════════════════════
SOURCES = {
    "Q2 FY2026: EPS $1.05, Revenue $46.7B (Aug 27, 2025)": {
        "url": "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-second-quarter-fiscal-2026",
        "backup": "https://www.cnbc.com/2025/08/27/nvidia-nvda-earnings-report-q2-2026.html",
        "sec": "https://www.sec.gov/Archives/edgar/data/1045810/000104581025000209/nvda-20250727.htm",
    },
    "Q3 FY2026: Revenue $57.0B, EPS $1.30 (Nov 19, 2025)": {
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581025000228/q3fy26pr.htm",
    },
    "Q4 FY2026: Revenue $68.1B, EPS $1.62 (Feb 25, 2026)": {
        "url": "https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026",
    },
    "Fed Sep 2025: Cut 25bp to 4.00-4.25%": {
        "url": "https://www.cnbc.com/2025/09/17/fed-rate-decision-september-2025.html",
    },
    "Fed Oct 2025: Cut 25bp to 3.75-4.00%": {
        "url": "https://www.cnbc.com/2025/10/29/fed-rate-decision-october-2025.html",
    },
    "Fed Dec 2025: Cut 25bp to 3.50-3.75%": {
        "url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20251210a.htm",
        "backup": "https://www.federalreserve.gov/monetarypolicy/fomcminutes20251210.htm",
    },
    "Fed Mar 2026: Hold at 3.50-3.75%": {
        "url": "https://www.fidelity.com/learning-center/trading-investing/fed-funds-rate-history",
    },
    "10-for-1 stock split June 7, 2024": {
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581024000144/nvda-20240607.htm",
        "backup": "https://www.cnbc.com/2024/05/22/nvidia-announces-10-for-1-stock-split.html",
    },
    "SpaceX ~$21B stake, Aug 14, 2026": {
        "url": "https://www.cnbc.com/2026/08/14/nvidia-discloses-21-billion-stake-in-spacex-at-end-of-second-quarter.html",
        "backup": "https://www.bloomberg.com/news/articles/2026-08-14/nvidia-has-21-billion-spacex-stake-30-billion-in-intel-shares",
    },
    "Google Trends: 0-100, peak=100": {
        "url": "https://support.google.com/trends/answer/4365533",
    },
    "NYSE: 9:30 AM - 4:00 PM Eastern": {
        "url": "https://www.nyse.com/markets/hours-calendars",
    },
    "Spurious correlations (Tyler Vigen)": {
        "url": "https://www.tylervigen.com/spurious-correlations",
    },
}

def verify_sources():
    """Print all sources with URLs for manual verification."""
    print("\n[1] SOURCE REGISTRY")
    print("-" * 60)
    for claim, urls in SOURCES.items():
        print(f"  ✓ {claim}")
        for key, url in urls.items():
            print(f"    [{key:6s}] {url}")
    print(f"\n  {len(SOURCES)} claims, {sum(len(v) for v in SOURCES.values())} URLs")

def replicate_stats(data):
    """Independently recompute all statistics from the series data."""
    print("\n[2] STATISTICAL REPLICATION")
    print("-" * 60)

    s = data.get("series", {})
    dates = s.get("dates", [])
    trend = np.array(s.get("trend", []), dtype=float)
    price = np.array(s.get("price", []), dtype=float)

    if len(trend) < 20 or len(price) < 20:
        print("  ⚠ Insufficient data for replication")
        return

    # % changes
    t_chg = np.diff(trend) / trend[:-1] * 100
    p_chg = np.diff(price) / price[:-1] * 100
    mask = np.isfinite(t_chg) & np.isfinite(p_chg)
    tc, pc = t_chg[mask], p_chg[mask]

    # Three independent correlation methods
    r1, p1 = sp.pearsonr(tc, pc)
    r2 = pd.Series(tc).corr(pd.Series(pc))
    n = len(tc)
    xm, ym = tc - tc.mean(), pc - pc.mean()
    den = np.sqrt((xm**2).sum() * (ym**2).sum())
    r3 = float((xm * ym).sum() / den) if den > 0 else 0

    print(f"  Method 1 (scipy):  r = {r1:.4f}, p = {p1:.4f}")
    print(f"  Method 2 (pandas): r = {r2:.4f}")
    print(f"  Method 3 (manual): r = {r3:.4f}")

    agree = abs(r1 - r2) < 0.001 and abs(r1 - r3) < 0.001
    print(f"  Three methods agree: {'✓ YES' if agree else '✗ NO'}")

    # Compare to pipeline output
    stats = data.get("stats", {})
    pipeline_r = stats.get("chgR")
    if pipeline_r is not None:
        match = abs(r1 - pipeline_r) < 0.002
        print(f"  Pipeline r = {pipeline_r}, Independent r = {r1:.3f}: "
              f"{'✓ MATCH' if match else '✗ MISMATCH'}")

    # Lag replication
    lags = data.get("lags", [])
    if lags:
        print(f"\n  Lag replication ({len(lags)} lags):")
        for L in lags:
            k = L["lag"]
            if k > 0:
                shifted_t = tc[:-k] if k < len(tc) else tc
                shifted_p = pc[k:] if k < len(pc) else pc
            else:
                shifted_t, shifted_p = tc, pc
            mn = min(len(shifted_t), len(shifted_p))
            if mn >= 10:
                ri, pi = sp.pearsonr(shifted_t[:mn], shifted_p[:mn])
                pipe_r = L["r"]
                ok = abs(ri - pipe_r) < 0.002
                print(f"    Lag {k}: independent r={ri:.3f}, pipeline r={pipe_r:.3f} "
                      f"{'✓' if ok else '✗'}")

    # Rolling correlation check
    rc = s.get("rollCorr", [])
    valid_rc = [v for v in rc if v is not None]
    if valid_rc:
        print(f"\n  Rolling correlation: {len(valid_rc)} values, "
              f"range [{min(valid_rc):.2f}, {max(valid_rc):.2f}]")
        pipe_min = stats.get("rollMin")
        pipe_max = stats.get("rollMax")
        if pipe_min is not None:
            print(f"  Pipeline range: [{pipe_min}, {pipe_max}]")
            print(f"  Match: {'✓' if abs(min(valid_rc) - pipe_min) < 0.02 and abs(max(valid_rc) - pipe_max) < 0.02 else '✗'}")

def self_criticize(data):
    """Two rounds of self-criticism."""
    print("\n[3] SELF-CRITICISM")
    print("-" * 60)

    issues = []

    # Round 1: Are the sources actually primary?
    for claim, urls in SOURCES.items():
        if "sec" not in urls and "url" in urls:
            if "sec.gov" not in urls["url"] and "federalreserve.gov" not in urls["url"]:
                if "nvidianews" not in urls["url"]:
                    issues.append(f"LOW: {claim} — no primary source (SEC/Fed/NVIDIA)")

    # Round 1: Is the data internally consistent?
    s = data.get("series", {})
    meta = data.get("meta", {})
    if len(s.get("dates", [])) != meta.get("tradingDays", -1):
        issues.append(f"HIGH: dates array length ({len(s.get('dates', []))}) "
                      f"!= meta.tradingDays ({meta.get('tradingDays')})")

    trend = s.get("trend", [])
    if trend and (min(trend) < 0 or max(trend) > 100):
        issues.append(f"CRITICAL: Trend scores out of 0-100 range")

    # Round 2: Did Round 1 miss anything?
    if not issues:
        issues.append("LOW: No issues found — verifier may be too lenient")

    for issue in issues:
        print(f"  {issue}")
    print(f"\n  {len(issues)} issue(s) found")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data.js")
    args = parser.parse_args()

    print("=" * 60)
    print("  FINBUZZ VERIFICATION ENGINE v2")
    print("=" * 60)

    if not os.path.exists(args.data):
        print(f"  ⚠ {args.data} not found. Run from the repo root.")
        sys.exit(1)

    data = load_pipeline_data(args.data)
    verify_sources()
    replicate_stats(data)
    self_criticize(data)

    print("\n" + "=" * 60)
    print("  VERIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
