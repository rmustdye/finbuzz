"""
FinBuzz Pipeline v4 — flat structure, zero-editing refresh
==========================================================
Everything lives at the repo root. No subfolders required.

THE REFRESH (two downloads, one command — no editing):
  1. trends.google.com -> search your keyword -> United States ->
     Custom time range (keep under ~9 months for daily data) ->
     download arrow -> drop multiTimeline.csv here as-is.
  2. finance.yahoo.com -> NVDA -> Historical Data -> same range ->
     Download -> drop the CSV here as-is.
  3. python finbuzz_pipeline.py
  4. Push to GitHub. Done.
"""

import glob
import hashlib
import io
import json
import os
import re
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- settings
KEYWORD_DEFAULT = "AI stocks"
TICKER = "NVDA"
ASSET_NAME = "NVIDIA (NVDA)"
AUTO = ("--auto" in sys.argv) or os.environ.get("FINBUZZ_AUTO") == "1"
AUTO_LOOKBACK_DAYS = 240
HERE = os.path.dirname(os.path.abspath(__file__)) or "."
MERGED_FALLBACK = os.path.join(HERE, "FinBuzz_Merged_Data_FINAL.csv")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    xm, ym = x - x.mean(), y - y.mean()
    den = np.sqrt((xm ** 2).sum() * (ym ** 2).sum())
    if den == 0 or n < 3:
        return float("nan"), float("nan")
    r = float((xm * ym).sum() / den)
    try:
        from scipy import stats
        t = r * np.sqrt((n - 2) / max(1e-12, 1 - r ** 2))
        p = float(2 * stats.t.sf(abs(t), df=n - 2))
    except ImportError:
        p = float("nan")
    return r, p


# ------------------------------------------------- auto-fetch
def auto_fetch():
    import time
    start = date.today() - timedelta(days=AUTO_LOOKBACK_DAYS)
    stamp = date.today().strftime("%Y%m%d")
    last_err = None
    for attempt in range(1, 4):
        try:
            from pytrends.request import TrendReq
            py = TrendReq(hl="en-US", tz=0, timeout=(10, 30))
            py.build_payload([KEYWORD_DEFAULT],
                             timeframe=f"{start} {date.today()}", geo="US")
            t = py.interest_over_time()
            if t.empty:
                raise RuntimeError("Google returned no data")
            if "isPartial" in t.columns:
                t = t[~t["isPartial"].astype(bool)].drop(columns=["isPartial"])
            t = t.reset_index()
            t.columns = ["Date", "Trend Score"]
            if t["Date"].diff().dt.days.max() > 1.5:
                raise RuntimeError("Google returned non-daily granularity")
            t.to_csv(os.path.join(HERE, f"auto_trends_{stamp}.csv"), index=False)
            print(f"AUTO trends: {len(t)} days ({t.Date.min().date()} -> {t.Date.max().date()})")
            break
        except Exception as e:
            last_err = e
            print(f"AUTO trends attempt {attempt}/3 failed: {e}")
            time.sleep(20 * attempt)
    else:
        raise SystemExit(
            f"AUTO trends fetch failed after 3 attempts ({last_err}).\n"
            "Published data left untouched. Manual route always works.")
    import yfinance as yf
    hist = yf.download(TICKER, start=str(start), auto_adjust=True, progress=False)
    if hist is None or hist.empty:
        raise SystemExit("AUTO price fetch returned nothing.")
    pr = hist.reset_index()
    close = pr["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]
    pr = pd.DataFrame({"Date": pr["Date"], "Price": close})
    pr.to_csv(os.path.join(HERE, f"auto_prices_{stamp}.csv"), index=False)
    print(f"AUTO prices: {len(pr)} trading days fetched")


# ------------------------------------------------- format detection
def parse_trends_file(path):
    raw = open(path, encoding="utf-8-sig").read()
    lines = raw.splitlines()
    for i, ln in enumerate(lines):
        low = ln.lower()
        if low.startswith("week,"):
            raise SystemExit(
                f"{os.path.basename(path)} contains WEEKLY data. Re-download "
                "with a shorter custom range (under ~9 months).")
        if low.startswith("day,"):
            df = pd.read_csv(io.StringIO("\n".join(lines[i:])))
            kw_col = df.columns[1]
            kw = re.sub(r":\s*\(.*\)$", "", kw_col).strip()
            df = df.rename(columns={df.columns[0]: "Date", kw_col: "Trend Score"})
            df["Trend Score"] = (df["Trend Score"].astype(str)
                                 .str.replace("<1", "0", regex=False).astype(float))
            df["Date"] = pd.to_datetime(df["Date"])
            return df[["Date", "Trend Score"]], kw
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    cols = {c.strip().lower(): c for c in df.columns}
    if "date" in cols and "trend score" in cols:
        df = df.rename(columns={cols["date"]: "Date", cols["trend score"]: "Trend Score"})
        df["Date"] = pd.to_datetime(df["Date"])
        df["Trend Score"] = df["Trend Score"].astype(float)
        return df[["Date", "Trend Score"]], KEYWORD_DEFAULT
    return None


def parse_prices_file(path):
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    cols = {c.strip().lower(): c for c in df.columns}
    if "date" not in cols:
        return None
    if "price" in cols and "trend score" not in cols:
        df = df.rename(columns={cols["date"]: "Date", cols["price"]: "Price"})
        note = f"{os.path.basename(path)} (clean price file)"
    elif "adj close" in cols:
        df = df.rename(columns={cols["date"]: "Date", cols["adj close"]: "Price"})
        note = f"{os.path.basename(path)} (Yahoo Finance, adjusted close)"
    elif "close" in cols and "open" in cols:
        df = df.rename(columns={cols["date"]: "Date", cols["close"]: "Price"})
        note = f"{os.path.basename(path)} (Yahoo Finance, close)"
    else:
        return None
    df["Date"] = pd.to_datetime(df["Date"])
    df["Price"] = pd.to_numeric(
        df["Price"].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["Price"])
    return df[["Date", "Price"]], note


def newest(frames):
    return max(frames, key=lambda t: t[0]["Date"].max()) if frames else None


# ---------------------------------------------------------------- main
print("=" * 62)
print("FINBUZZ PIPELINE v4" + ("  [AUTO MODE]" if AUTO else ""))
print("=" * 62)

if AUTO:
    auto_fetch()

candidates = sorted(glob.glob(os.path.join(HERE, "*.csv")))
trend_hits, price_hits = [], []
for p in candidates:
    if os.path.abspath(p) == os.path.abspath(MERGED_FALLBACK):
        continue
    t = parse_trends_file(p)
    if t:
        trend_hits.append((t[0], t[1], p))
        continue
    pr = parse_prices_file(p)
    if pr:
        price_hits.append((pr[0], pr[1], p))

if not trend_hits:
    raise SystemExit("No Google Trends file found. Drop the raw "
                     "multiTimeline.csv in the same folder and re-run.")
trends, KEYWORD, trends_path = newest(trend_hits)
print(f"Trends  <- {os.path.basename(trends_path)}  "
      f"(keyword: '{KEYWORD}', {len(trends)} days, "
      f"{trends.Date.min().date()} -> {trends.Date.max().date()})")

if price_hits:
    prices, price_source, prices_path = newest(price_hits)
else:
    m = pd.read_csv(MERGED_FALLBACK, parse_dates=["Date"])
    prices, price_source, prices_path = (m[["Date", "Price"]],
        "FinBuzz_Merged_Data_FINAL.csv (original Colab export)", MERGED_FALLBACK)
print(f"Prices  <- {price_source}  ({len(prices)} rows)")

# Cross-check
cross = None
if len(trend_hits) >= 2:
    a = trend_hits[0][0].rename(columns={"Trend Score": "a"})
    b = trend_hits[1][0].rename(columns={"Trend Score": "b"})
    j = pd.merge(a, b, on="Date")
    if len(j):
        dis = (j.a != j.b).sum()
        cross = {"disagree": int(dis), "total": int(len(j)),
                 "maxDiff": int((j.a - j.b).abs().max())}
elif os.path.exists(MERGED_FALLBACK):
    m = pd.read_csv(MERGED_FALLBACK, parse_dates=["Date"])
    if "Trend Score" in m.columns:
        j = pd.merge(trends, m[["Date", "Trend Score"]], on="Date",
                     suffixes=("_a", "_b"))
        if len(j):
            dis = (j["Trend Score_a"] != j["Trend Score_b"]).sum()
            cross = {"disagree": int(dis), "total": int(len(j)),
                     "maxDiff": int((j["Trend Score_a"] - j["Trend Score_b"]).abs().max())}
if cross:
    print(f"Cross-check: two pulls disagree on {cross['disagree']}/{cross['total']} "
          f"dates (max {cross['maxDiff']} pts)")

# ---- merge + gates ----
df = pd.merge(trends, prices, on="Date", how="inner").sort_values("Date")
df = df.reset_index(drop=True)
assert len(df) >= 20, "Fewer than 20 overlapping trading days."
assert df.Date.is_monotonic_increasing and df.Date.duplicated().sum() == 0
assert df.isna().sum().sum() == 0
assert df["Trend Score"].between(0, 100).all()
assert (df.Date.dt.dayofweek < 5).all(), "Weekend rows leaked into merge"
cal_days = int((trends.Date.max() - trends.Date.min()).days) + 1
span_months = round(cal_days / 30.44, 1)
span_label = (f"{cal_days} days" if cal_days < 70
              else f"{int(round(span_months))} months")
print(f"Merged  -> {len(df)} trading days over {cal_days} calendar days  [OK]")

# ---- features ----
df["trend_ma7"] = df["Trend Score"].rolling(7, min_periods=1).mean().round(1)
df["price_ret"] = df["Price"].pct_change() * 100
df["trend_chg"] = df["Trend Score"].pct_change() * 100
df["roll_corr"] = df["Trend Score"].rolling(14).corr(df["Price"]).round(3)

t = df["Trend Score"].values
dates_arr = df["Date"].dt.strftime("%b %d").values
v_dips, i = [], 1
while i < len(t):
    if t[i - 1] >= 40 and t[i] <= 0.55 * t[i - 1]:
        for j in range(i + 1, min(i + 5, len(t))):
            if t[j] >= 0.8 * t[i - 1]:
                v_dips.append(f"{dates_arr[i]}\u2013{dates_arr[j - 1]}")
                i = j
                break
    i += 1
artifact_note = ("; ".join(v_dips[:3]) if v_dips else "")

# ---- statistics ----
r_level, p_level = pearson(df["Trend Score"], df["Price"])
d = df.dropna(subset=["price_ret", "trend_chg"])
r_chg, p_chg = pearson(d["trend_chg"], d["price_ret"])

lags = []
for k in range(0, 6):
    b = d["price_ret"].shift(-k).values
    mask = ~np.isnan(b)
    r, p = pearson(d["trend_chg"].values[mask], b[mask])
    lags.append({"lag": k, "r": round(r, 3), "p": round(p, 3), "n": int(mask.sum())})
sig = [L for L in lags if L["p"] < 0.05]
lag_noise = len(sig) == 0 or (len(sig) >= 2 and len({np.sign(L["r"]) for L in sig}) > 1)

total_ret = (df.Price.iloc[-1] / df.Price.iloc[0] - 1) * 100
peak = df.loc[df["Trend Score"].idxmax()]
below20 = int(((df["Trend Score"] < 20) &
               (df["Trend Score"].shift(1) >= 20)).sum())

print(f"Level r={r_level:+.3f} | change r={r_chg:+.3f} p={p_chg:.3f} n={len(d)} "
      f"| asset {total_ret:+.1f}%")
if v_dips:
    print(f"Probable sampling artifacts: {artifact_note}")
check = float(d["trend_chg"].corr(d["price_ret"]))
assert abs(check - r_chg) < 1e-9, "Correlation self-check FAILED."
print("Self-check: independent recomputation matches.  [OK]")

# ---- export (data.js at repo root, alongside index.html) ----
payload = {
    "meta": {
        "keyword": KEYWORD, "ticker": TICKER, "assetName": ASSET_NAME,
        "windowStart": str(df.Date.min().date()),
        "windowEnd": str(df.Date.max().date()),
        "tradingDays": int(len(df)), "calendarDays": cal_days,
        "spanLabel": span_label, "generated": str(date.today()),
        "priceSource": price_source,
        "trendsSource": f"Google Trends, US, web search ({span_label} export)",
        "hashes": {"trends": sha256(trends_path)[:16],
                   "prices": sha256(prices_path)[:16]},
    },
    "series": {
        "dates": [str(x.date()) for x in df.Date],
        "trend": [float(x) for x in df["Trend Score"]],
        "trendMa7": [float(x) for x in df["trend_ma7"]],
        "price": [round(float(x), 2) for x in df["Price"]],
        "rollCorr": [None if pd.isna(x) else float(x) for x in df["roll_corr"]],
    },
    "stats": {
        "levelR": round(r_level, 3), "levelP": round(p_level, 3),
        "chgR": round(r_chg, 3), "chgP": round(p_chg, 3),
        "totalReturn": round(total_ret, 1),
        "peakDate": str(peak.Date.date()), "peakScore": int(peak["Trend Score"]),
        "minScore": int(df["Trend Score"].min()),
        "dipsBelow20": below20,
        "rollMin": round(float(df.roll_corr.min()), 2),
        "rollMax": round(float(df.roll_corr.max()), 2),
        "lagNoise": bool(lag_noise), "sigLags": len(sig),
        "artifactNote": artifact_note, "crossCheck": cross,
    },
    "lags": lags,
}
with open(os.path.join(HERE, "data.js"), "w") as f:
    f.write("// Generated by finbuzz_pipeline.py — do not edit by hand.\n")
    f.write("window.FINBUZZ = " + json.dumps(payload, indent=2) + ";\n")
with open(os.path.join(HERE, "analysis_summary.json"), "w") as f:
    json.dump({**payload["stats"], **payload["meta"]}, f, indent=2, default=str)
print(f"\nWrote data.js — push to GitHub and the site updates itself.")
