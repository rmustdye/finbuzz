# FinBuzz Methodology Reference

This document is the authoritative reference for every statistical and analytical method used in FinBuzz. Read this when computing statistics, writing methodology sections, answering technical questions, or verifying analysis results.

## Table of Contents

1. Why percentage changes, not raw levels
2. Pearson correlation explained
3. P-values and statistical significance
4. The dual-computation verification
5. Lag analysis (cross-correlation)
6. Multiple comparison problem
7. Rolling correlation
8. Google Trends normalization
9. Sampling variance
10. Confounding variables and causation
11. SHA-256 provenance hashing
12. Known limitations

---

## 1. Why Percentage Changes, Not Raw Levels

This is the single most important methodological decision in FinBuzz.

**The problem with raw levels:** If NVDA's price rises from $100 to $200 over 3 months, and Google search interest also trends upward during the same period, correlating the raw numbers will show a high positive correlation. But this is *meaningless* — any two quantities that both trend upward will appear correlated. This is called **spurious correlation** and it's one of the most common mistakes in data analysis.

Example of spurious correlation: the number of Nicolas Cage movies released per year correlates with the number of swimming pool drownings. The correlation is real in the data but the relationship is nonsense — they're both just things that vary over time.

**The fix:** Convert both series to daily percentage changes before correlating. This asks the right question: "On days when search interest *increased*, did the stock price also *increase*?" Rather than: "Are both numbers getting bigger over time?"

**Formula:** `pct_change = (today - yesterday) / yesterday × 100`

The first row always becomes NaN (no "yesterday" to compare to) and is dropped.

**When to use raw levels:** Only for visual display (the dual-axis chart shows raw trend scores and prices so users can see the actual values). Never for statistical calculations.

---

## 2. Pearson Correlation Explained

Pearson's r measures the *linear* relationship between two variables. It ranges from -1 to +1:

- **r = +1:** Perfect positive relationship — when one goes up, the other always goes up by a proportional amount
- **r = 0:** No linear relationship
- **r = -1:** Perfect negative relationship — when one goes up, the other always goes down

**Interpretation scale (for social science/finance contexts):**

| |r| | Interpretation |
|---|---|
| < 0.1 | Negligible |
| 0.1 – 0.3 | Weak |
| 0.3 – 0.5 | Moderate |
| 0.5 – 0.7 | Strong |
| > 0.7 | Very strong |

**What Pearson's r does NOT capture:**
- Non-linear relationships (e.g., search interest affects price only above a threshold)
- Time-delayed relationships (lag analysis handles this)
- Causal direction (correlation never implies causation)
- Relationships that change over time (rolling correlation handles this)

**FinBuzz findings:** r values of −0.151, −0.179, and −0.062 across three windows. All in the "negligible to weak" range. The negative signs suggest a very slight tendency for price to move *opposite* to search interest — but the p-values show this is indistinguishable from random noise.

---

## 3. P-values and Statistical Significance

The p-value answers: "If there were truly NO relationship between search interest and stock returns, how likely would I be to see a correlation this large (or larger) just by random chance?"

- **p < 0.05:** By convention, "statistically significant" — less than 5% chance of this being noise
- **p > 0.05:** Not statistically significant — we cannot rule out random chance
- **p < 0.01:** Strongly significant
- **p < 0.001:** Very strongly significant

**FinBuzz p-values:** 0.258, 0.175, and 0.661. All well above 0.05. Plain English: "The correlations we found are easily explained by random chance. There is no statistically significant relationship."

**Critical caveat:** Statistical significance is not the same as practical significance. A correlation of r = 0.01 with p = 0.001 (from a huge sample) is statistically significant but practically meaningless. Conversely, a moderate correlation with high p-value might be real but our sample was too small to confirm it.

**What to report:** Always report both r AND p. Saying "r = −0.15" without the p-value is incomplete. Saying "not significant" without the numbers is vague. FinBuzz reports: "r = −0.151, p = 0.258 (not statistically significant)."

---

## 4. The Dual-Computation Verification

Every correlation in FinBuzz is computed two independent ways:

1. `scipy.stats.pearsonr()` — the SciPy library's implementation (also gives p-value)
2. `pandas DataFrame.corr()` — the pandas library's implementation

If these disagree beyond floating-point rounding (tolerance: 0.001), the pipeline **refuses to publish**. This catches bugs like accidentally passing the wrong column, or a library update changing behavior.

**Why this matters:** A single computation has no check. You could pass the wrong data and get a plausible-looking number. Dual computation is a basic engineering practice — like having two pilots verify each critical checklist item.

---

## 5. Lag Analysis (Cross-Correlation)

**The question:** Does search interest *lead* stock price? If people search "AI stocks" more on Monday, does NVDA go up on Tuesday? Wednesday?

**Method:** Shift the trend data forward by N days (lag-1 through lag-5) and re-compute the correlation with unshifted price data. A significant positive correlation at lag-2, for example, would mean "today's search interest predicts the price change 2 days from now."

**What each lag means:**
- Lag 0: Same-day relationship
- Lag 1: Yesterday's search interest vs today's price change
- Lag 2: Search interest 2 days ago vs today's price change
- Lag 3–5: Same pattern, further back

**FinBuzz findings:** Sixteen lag tests across three windows produced zero consistent predictive signals. The handful of "significant" lags had opposite signs — see next section.

---

## 6. Multiple Comparison Problem

**The danger:** When you test multiple hypotheses (6 lags × 3 windows = 18 tests), some will appear "significant" by pure chance. At p < 0.05, you'd expect roughly 1 in 20 tests to be a false positive.

**The fingerprint of false positives:** If lag-1 shows a significant *positive* correlation and lag-3 shows a significant *negative* correlation, the underlying data cannot logically support both (more searching today predicts prices going UP on Tuesday but DOWN on Thursday?). This contradictory pattern is the hallmark of random noise, not a real signal.

**FinBuzz approach:** Rather than applying a formal correction (like Bonferroni, which would make the threshold p < 0.05/18 = 0.003), FinBuzz uses a transparency approach: flag opposite-sign significant lags explicitly and explain to the reader why this pattern indicates noise. This is more educational and honest than silently adjusting numbers.

---

## 7. Rolling Correlation

**The question:** Is the relationship stable over time, or does it flip-flop?

**Method:** Compute Pearson correlation over a sliding 14-trading-day window (approximately 3 calendar weeks). This produces a time series of correlation values.

**Why 14 days:** Large enough for statistical meaning (the minimum for a meaningful Pearson r is about 10 points), small enough to show variation within a 60-trading-day window.

**Typical FinBuzz finding:** The rolling correlation swings between positive and negative, showing the relationship is unstable. This instability is itself an important finding — if search interest were a reliable predictor, the rolling correlation would stay consistently positive (or negative).

---

## 8. Google Trends Normalization

**How Google Trends scoring works:**

1. Google counts how many searches matched your keyword in a given time and place
2. It divides by the total number of searches in that same time and place (normalization by search volume)
3. It scales the result so the PEAK value in your selected time window = 100
4. All other values are relative to that peak

**Critical implications:**

- **Scores are relative, not absolute.** A score of 50 means "half as much interest as the peak *within this window*" — NOT "50% of all Google users searched for this."
- **Different windows give different scores.** Querying Jan–Mar vs Jan–Jun will produce different numbers for January because the peak (= 100) is different.
- **You cannot compare scores across different query windows.** This is why FinBuzz analyzes each window independently and never mixes them.
- **Weekly vs daily granularity differs.** Daily data is more granular but noisier; weekly data is smoother but loses detail. Google Trends automatically switches between these depending on the window length.

---

## 9. Sampling Variance

**The problem:** The same Google Trends query, run on the same day with the same parameters, can return slightly different numbers each time. This is because Google samples its data rather than using the complete dataset (which would be computationally infeasible).

**FinBuzz evidence:** Cross-checking the two original CSVs (raw trends export vs Colab-merged data) revealed 31 out of 59 overlapping dates had different trend scores. This is direct evidence of sampling variance — not a bug.

**How FinBuzz handles this:**
1. Disclose it explicitly (it's in the methodology section on the site)
2. Use it as a finding (Finding 3: "Your data confirms Google Trends sampling variance")
3. Archive every pull with its SHA-256 hash so discrepancies are traceable
4. Apply smoothing (7-day rolling average) to reduce the impact on visual charts
5. Accept that any single data point could be off by several points — but the overall pattern is reliable

---

## 10. Confounding Variables and Causation

**FinBuzz's original contribution:** Every instance where search interest and NVDA price appeared to move together traces to a **confounding variable** — a news event (earnings report, Fed decision, competitive threat from DeepSeek, etc.) that independently drove both the searches and the price change.

**What a confounding variable is:** A third factor that causes both X and Y, creating the illusion that X causes Y (or vice versa).

```
APPARENT:  Search interest ──→ Stock price
                ?

ACTUAL:    News event ──→ Search interest
           News event ──→ Stock price
           (No causal link between search and price)
```

**Why this matters:** Retail trading narratives often claim "buzz drives prices." FinBuzz's finding is that buzz and prices are both driven by the same upstream events. The searches are an echo of the news; the price is a reaction to the news. Neither causes the other.

**How to talk about it:** "May reflect a shared response to news events" — never "proves" or "shows that." FinBuzz is a case study of one keyword and one stock; generalizing to all keywords and all stocks would require much more evidence.

---

## 11. SHA-256 Provenance Hashing

**What it is:** SHA-256 is a cryptographic hash function that converts any file into a fixed-length string of characters (a "hash"). Even a single changed character in the file produces a completely different hash.

**Why FinBuzz uses it:** To prove data integrity. If someone asks "how do I know you didn't cherry-pick the data?", the answer is: "Here's the SHA-256 hash of the input file. Download the same data from Google Trends and compute the hash yourself. If they match, the data is identical."

**How it appears on the site:** Every chart shows a provenance stamp: `source · date window · SHA-256: abc123...`

---

## 12. Known Limitations

Always disclose these when writing methodology sections or answering questions:

1. **One keyword, one stock, three windows.** This is a case study, not a universal finding.
2. **Google Trends is normalized and sampled.** No claim of "absolute accuracy" is valid.
3. **Pearson's r only captures linear relationships.** Non-linear patterns would be missed.
4. **Short time windows.** 59–60 trading days per daily window. Longer windows would increase statistical power.
5. **No event-study methodology.** The confounding variable thesis is argued from observation, not from formal event-study techniques (which would require identifying events, defining event windows, and computing abnormal returns).
6. **"AI stocks" is a broad keyword.** It measures general retail curiosity, not NVDA-specific interest. Testing "NVDA stock" and "Nvidia" as additional keywords would strengthen the analysis.
7. **Survivorship bias in ticker selection.** NVDA was chosen because it's the most prominent AI stock — but that prominence makes it more likely to already be efficiently priced, making search-interest effects harder to detect.
8. **No out-of-sample testing.** The correlations are measured on all available data, not tested on held-out data. This means we cannot claim predictive power even if correlations were significant.
