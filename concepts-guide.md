# FinBuzz Concepts Guide

Everything you need to understand FinBuzz, written for someone starting from zero. Each concept: definition, analogy, how it appears in FinBuzz, what could go wrong.

## Table of Contents

1. The Stock Market Basics
2. Google Trends and Search Data
3. Data Science Fundamentals
4. The Statistics FinBuzz Uses
5. The Web Technology Behind the Dashboard
6. Programming Concepts for the Code Walkthrough
7. Interview Answers

---

## 1. The Stock Market Basics

### What is a stock?
A stock is a tiny piece of ownership in a company. If NVIDIA has approximately 24.6 billion shares and you own 100, you own a minuscule fraction of NVIDIA. When the company does well, your shares become more valuable. When it does poorly, they become less valuable.

**In FinBuzz:** We track NVDA, which is NVIDIA's stock ticker symbol.

### What is a ticker symbol?
A short code that identifies a company's stock. NVDA = NVIDIA. AAPL = Apple. GOOGL = Alphabet/Google. These are the abbreviations traders and data systems use instead of the full company name.

**What could go wrong:** Some companies have similar tickers. Make sure you're tracking the right one.

### What is the "price" of a stock?
At any moment during trading hours, a stock has a price — the most recent amount someone paid for one share. This changes constantly as buyers and sellers agree on different amounts. The "closing price" is the last price of the trading day (4:00 PM Eastern in the US).

### What is "adjusted close"?
Sometimes a company does a "stock split" — for example, NVIDIA did a 10-for-1 split in June 2024. Before the split, 1 share cost about $1,200. After, each share cost about $120 — but you now owned 10 shares instead of 1, so your total value was the same.

The problem: if you chart the raw price, it looks like NVDA crashed 90% overnight. That's misleading. "Adjusted close" fixes this by retroactively adjusting all historical prices as if the split had already happened, so the chart shows smooth, comparable values.

**In FinBuzz:** We always use adjusted close prices from Yahoo Finance.

### What is a trading day?
Stock markets are only open Monday through Friday, and they close on public holidays (New Year's Day, Martin Luther King Jr. Day, Presidents Day, Good Friday, Memorial Day, Independence Day, Labor Day, Thanksgiving, Christmas).

**In FinBuzz:** This is why our data has 59 trading days but covers 93 calendar days. Google Trends records data every day, but stock prices only exist on trading days. The pipeline aligns them using an "inner join" — keeping only dates where both have data.

### What is a return?
The percentage change in price over a period. If NVDA was $100 yesterday and $105 today, the daily return is +5%. If it goes from $105 to $100, that's a −4.76% return (not −5%, because the base is now $105).

**Formula:** `return = (new price - old price) / old price × 100`

**In FinBuzz:** Daily percentage returns are the core of our analysis. We correlate these with daily changes in search interest.

---

## 2. Google Trends and Search Data

### What is Google Trends?
A free tool by Google that shows how often a search term is Googled over time. Go to trends.google.com, type "AI stocks," and you'll see a chart showing interest over time.

### How does the scoring work?
Google Trends does NOT give you the actual number of searches. Instead, it gives a score from 0 to 100:
- **100** = the peak of interest within your selected time window
- **50** = half as much interest as the peak
- **0** = not enough data to register

**Analogy:** Imagine you track how full a restaurant is each day for a month. The busiest day (Saturday the 15th) gets a score of 100. A day that was half as busy gets 50. A day it was closed gets 0. You don't know the ACTUAL number of diners — just how each day compares to the busiest day.

**Critical implication:** If you query January–March, the peak might be in February (score 100). If you query January–June, the peak might be in May, making February score only 60 — even though the actual number of searches in February didn't change. The scores are relative to the window you selected.

**In FinBuzz:** This is why we disclose the query window on every chart and never compare scores across different windows.

### What is sampling variance?
When Google calculates the trend score, it doesn't use ALL searches — it uses a sample (a random subset). This means running the exact same query twice can give slightly different numbers. Think of it like polling: two polls on the same day with different random samples will give slightly different results.

**In FinBuzz:** We discovered that our two data files disagreed on 31 out of 59 dates. This is normal and expected — it's evidence of sampling variance, not a data error. We feature it as a finding.

---

## 3. Data Science Fundamentals

### What is a dataset?
A structured collection of data, usually organized in rows and columns (like a spreadsheet). Each row is one observation (one day, in our case). Each column is one variable (date, trend score, price).

### What is cleaning data?
Raw data is almost never ready to analyze. Cleaning means: removing or fixing errors, handling missing values, converting text dates to proper date formats, ensuring numbers are actually stored as numbers (not text), and removing duplicates.

**In FinBuzz:** The pipeline auto-detects the CSV format, handles Google's "<1" entries (converts to 0.5), drops weekends, and aligns dates.

### What is an inner join?
When you have two datasets with a shared column (in our case, "Date"), an inner join keeps only the rows where the value appears in BOTH datasets. If Trends has data for Saturday but Prices doesn't (market was closed), that Saturday row is dropped.

**Analogy:** You have two guest lists for a party. An inner join produces a list of people who appear on BOTH lists.

### What is a CSV file?
"Comma-Separated Values" — a plain text file where data is organized in rows, with each value separated by a comma. Example:
```
Date,Trend_Score,Close_Price
2025-08-25,45,119.72
2025-08-26,52,122.81
```
It's the simplest way to store tabular data. Almost every data tool can read and write CSV files.

### What is a hash?
A hash function takes any input (a file, a password, a message) and produces a fixed-length string of characters that uniquely represents that input. Even changing a single character in the input produces a completely different hash.

**SHA-256** (which FinBuzz uses) produces a 64-character hexadecimal string like: `a7ffc6f8bf1ed76651c14756a061d662f580ff4de43b49fa82d80a4b80f8434a`

**Analogy:** Think of a hash like a fingerprint for data. Two identical files will always have the same fingerprint. But you can't reconstruct the original file from just the fingerprint.

**In FinBuzz:** We hash every input file so anyone can verify the data is identical to what we analyzed. This is the provenance stamp on every chart.

---

## 4. The Statistics FinBuzz Uses

### Correlation
A measure of how two things move together. Pearson's r ranges from −1 to +1:
- **+1:** They move perfectly together (one goes up, the other always goes up)
- **0:** No relationship
- **−1:** They move perfectly opposite (one goes up, the other always goes down)

**Analogy:** Think of two people walking. Correlation +1 = they walk in lockstep. Correlation 0 = they walk randomly. Correlation −1 = when one walks forward, the other walks backward.

**The big trap — correlation ≠ causation:** Ice cream sales and drowning deaths are correlated (both go up in summer). Ice cream doesn't cause drowning — hot weather causes both. This is a **confounding variable**.

**In FinBuzz:** Our correlations (−0.151, −0.179, −0.062) are all near zero. The confounding variable is news events.

### P-value
"If there were truly NO relationship, how likely would I see results this extreme by random chance?" A p-value of 0.258 means there's a 25.8% chance — way too high to rule out chance.

**Analogy:** You flip a coin 10 times and get 7 heads. Is the coin biased? The p-value is about 0.17 — meaning there's a 17% chance a fair coin would produce 7+ heads in 10 flips. That's not unusual enough to conclude the coin is biased. You'd need much stronger evidence (like 9 out of 10 heads, p ≈ 0.01).

**In FinBuzz:** All our p-values are above 0.05 (the conventional threshold). We cannot reject the hypothesis that the correlation is zero.

### Lag analysis
Testing whether one variable leads another in time. "If search interest spikes today, does the stock price change tomorrow? Two days later?"

**Analogy:** Thunder and lightning. You see lightning first, then hear thunder a few seconds later. If you measured the "lag" between them, you'd find lightning leads thunder by about 5 seconds per mile of distance. In our case, we're testing whether search interest is like the "lightning" that comes before the stock price "thunder."

**In FinBuzz:** We found no consistent lead-lag relationship. Search interest is not the lightning.

### Rolling correlation
Instead of computing one correlation for the entire period, compute it over a sliding window (e.g., 14 days at a time) and track how it changes over time.

**Analogy:** Your relationship with a coworker might be great in January (you collaborate well) and terrible in March (you disagree on a project). An overall rating of "meh" hides this variation. A monthly rating shows the ups and downs.

**In FinBuzz:** The rolling correlation swings between positive and negative, showing the relationship is unstable — it's not consistently anything.

### Spurious correlation
A statistical relationship between two variables that has no meaningful connection. Usually caused by both trending in the same direction over time, or by a confounding variable.

**Classic example:** US spending on science, space, and technology correlates with suicides by hanging, strangulation and suffocation. Obviously, science funding doesn't cause hangings. They're just two things that both increased over the same period.

**In FinBuzz:** This is exactly why we correlate percentage CHANGES, not raw levels. Raw levels of NVDA price and search interest both generally increased over time — correlating them would give a spuriously high number.

---

## 5. The Web Technology Behind the Dashboard

### HTML
HyperText Markup Language — the language of web pages. It defines the STRUCTURE of a page: headings, paragraphs, images, links, buttons. Think of it as the skeleton of a building.

### CSS
Cascading Style Sheets — defines the APPEARANCE. Colors, fonts, spacing, layout. Think of it as the paint, wallpaper, and furniture.

### JavaScript
The programming language that makes web pages INTERACTIVE. In FinBuzz, JavaScript reads the data, draws the charts, handles the smoothing toggle, and responds to hover events.

### Chart.js
A free JavaScript library for creating charts. Instead of drawing every pixel ourselves, we tell Chart.js "here are the numbers, make a line chart" and it handles the rendering, tooltips, legends, and responsiveness.

### GitHub Pages
A free hosting service from GitHub. You put your HTML/CSS/JS files in a GitHub repository, enable Pages in settings, and GitHub serves your site at yourusername.github.io/reponame. No server to manage, no hosting fees, and every change is tracked in version history.

### CDN
Content Delivery Network — a network of servers around the world that host common files (like Chart.js). Instead of including Chart.js in our repo, we load it from a CDN. This makes our site load faster because the user's browser probably already has Chart.js cached from visiting another site.

---

## 6. Programming Concepts for the Code Walkthrough

Use these explanations when writing "Document A: The Code, Line by Line."

### Variable
A labeled container that holds a value. `price = 119.72` creates a box labeled "price" containing the number 119.72. You can change what's in the box later: `price = 122.81`.

**Analogy:** A labeled jar in a kitchen. The label says "Sugar" and inside is sugar. You can empty it and put flour in, but the label stays.

### Function
A reusable recipe. You define it once and then "call" it whenever you need it. `def compute_correlation(data):` defines a recipe called "compute_correlation" that takes some data and produces a result. You can call it many times with different data.

**Analogy:** A recipe card for cookies. The recipe is written once, but you can bake cookies any number of times by following it.

### Import
Loading someone else's code so you can use their tools. `import pandas as pd` loads the pandas library and gives it the nickname "pd." Now you can use pandas tools by writing `pd.read_csv()` instead of building CSV-reading code from scratch.

**Analogy:** Borrowing a tool from a neighbor. Instead of building your own power drill, you borrow theirs.

### Loop
Doing the same thing many times, once for each item in a collection. `for lag in range(0, 6):` runs the code inside it 6 times — once with lag=0, once with lag=1, through lag=5.

**Analogy:** A conveyor belt in a factory. Each item on the belt gets the same treatment (stamped, painted, packaged), one at a time.

### DataFrame
A table of data in Python (provided by the pandas library). It has rows and columns, like a spreadsheet. You can filter rows, select columns, compute statistics, and merge multiple DataFrames together.

**Analogy:** A very powerful spreadsheet that you control by typing commands instead of clicking cells.

### If / else
A decision point. `if p_value < 0.05:` checks a condition — if true, run one block of code; if false, run a different block. This is how the pipeline decides whether a result is statistically significant.

**Analogy:** A fork in the road. Go left if the sign says "highway," go right if it says "local."

### Try / except
A safety net. `try:` attempts something that might fail. If it fails, `except:` catches the error and handles it gracefully instead of crashing. The pipeline uses this for optional dependencies like yfinance.

**Analogy:** Trying to open a door. If it's locked (exception), you try the window instead. If you didn't have a try/except, you'd just stand there forever.

### f-string
A way to embed variables inside text. `f"Correlation: r = {r:.4f}"` produces "Correlation: r = -0.1510" — the `{r:.4f}` part gets replaced by the value of the variable `r`, formatted to 4 decimal places.

**Analogy:** Mad Libs. "My name is ___" becomes "My name is Claude" when you fill in the blank.

---

## 7. Interview Answers

Prepare for these questions when discussing FinBuzz in interviews.

### "Did search interest predict stock price?"
"Not reliably in my analysis window. Across three independent windows — 172 data points total — the correlations were −0.15, −0.18, and −0.06, none statistically significant. Sixteen lag tests produced zero consistent predictive signals. The instances where attention and price appeared to move together traced to shared news events — a confounding variable — rather than a causal link. I think the honest null result is more valuable than a fabricated positive, because it shows I can follow the evidence rather than fit it to a narrative."

### "Why NVDA?"
"NVDA had the highest retail attention of any AI stock in 2025-2026, which made it the strongest test case. If search attention predicted any AI stock's price, NVDA was where you'd expect to see it. The fact that even the strongest candidate showed no signal is meaningful. The keyword-asset mismatch — 'AI stocks' is broad while NVDA is specific — is itself a finding I discuss on the site."

### "What would you do differently?"
"Three things. First, multiple keywords — I'd track 'NVDA stock,' 'Nvidia,' and 'AI stocks' simultaneously and compare which (if any) correlates best. The pipeline already supports this. Second, longer windows — 60 trading days gives limited statistical power; a year of daily data would be more definitive. Third, formal event-study methodology — identifying news events in advance, defining event windows, and computing abnormal returns, rather than arguing the confounding-variable thesis from observation."

### "Is this AI / machine learning?"
"No — and calling it that would be overclaiming. It's statistical data analysis and sentiment tracking. The Python pipeline does data cleaning, correlation analysis, and visualization. No models are trained, no predictions are made. I think the distinction matters: calling everything 'AI' is a red flag in interviews, and the actual skills I demonstrated — data verification, statistical rigor, honest reporting — are what analysts actually need."

### "How do you know the data is real / hasn't been manipulated?"
"Every input file is SHA-256 hashed and the hash is displayed on every chart. Anyone can download the same data from Google Trends and Yahoo Finance, compute the hash, and verify it matches. The pipeline also runs dual-computation verification — every correlation is computed two independent ways, and the pipeline refuses to publish if they disagree. The full methodology is documented and the code is public."

### "What's the most interesting finding?"
"That the relationship is unstable, not just weak. The rolling 14-day correlation swings between positive and negative, which means there's no consistent pattern to exploit — even if the overall correlation were significant, it wouldn't be reliable. And the cross-check between my two data files revealing 31 discrepant dates was an accidental discovery that became one of the most educational parts of the project: direct evidence of Google Trends' sampling variance."

### "How would you turn this into an actual trading strategy?"
"I wouldn't — and that honesty is the point. Search interest data is too noisy, too delayed, and too broad to generate actionable trading signals for a single stock. What it CAN do is measure retail sentiment shifts at a category level, which might be useful for understanding market narratives over months, not for timing individual trades. If I were to push further, I'd combine it with more specific signals — company mention frequency in financial news, options flow data, social media sentiment — and test it on a basket of stocks, not just one."
