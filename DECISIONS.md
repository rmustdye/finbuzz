# DECISIONS.md - FinBuzz Analytical Choice Log

Every analytical decision in FinBuzz is documented here with its reasoning.
This is the document that proves human judgment, not just automated output.

## Data decisions

### Why "AI stocks" as the keyword?
It's the broadest retail search term for the AI investment theme. Choosing a
broad term was deliberate: if even a general sentiment signal doesn't predict
the flagship AI stock, narrower signals are unlikely to work either. The
limitation (keyword breadth) is disclosed on the site.

### Why NVDA as the stock?
NVIDIA is the highest-profile pure-play AI stock. If retail attention moves
any AI stock, it would be this one. Choosing the most favourable test case
makes the null result stronger, not weaker.

### Why three windows instead of one?
One null result could be a fluke. Three null results across different market
conditions (rising +5.9%, flat -0.4%, rallying +18.8%) constitute evidence.
The replication was designed to be non-overlapping and separated by months.

### Why both daily and weekly granularity?
Daily data catches short-term noise. Weekly data smooths it and reveals
macro trends. If the signal existed at one granularity but not the other,
that would be informative. Both showed the same null result, ruling out
the possibility that daily noise was hiding a weekly signal.

## Statistical decisions

### Why percentage changes instead of raw levels?
Two series that both trend upward will produce a positive correlation even
if they are unrelated. This is spurious correlation. Converting to daily
percentage changes removes the shared trend and isolates the day-to-day
co-movement, which is the actual question. This is the standard method
in financial econometrics.

### Why Pearson correlation?
Pearson measures linear relationships, which is the simplest and most
interpretable test. If there is no linear relationship, more complex
methods (Spearman, mutual information) are unlikely to find anything
meaningful in a dataset this small. Starting simple is methodologically
correct.

### Why dual computation (scipy + pandas)?
The pipeline computes every correlation using scipy.stats.pearsonr AND
pandas .corr() independently. If they disagree, the pipeline refuses to
publish. This catches implementation bugs and floating-point edge cases.
It's a verifiable integrity gate.

### Why 14-day rolling window (8-week for weekly)?
14 trading days is approximately two weeks, long enough to compute a
meaningful correlation but short enough to show instability. The choice
was proportional: 14 days for daily data, 8 weeks for weekly data, both
representing roughly the same fraction of the total window.

### Why report lag-4 and lag-5 from Window 1 as noise?
Two lags crossed p < .05 with opposite signs (lag-4: r = +0.289,
lag-5: r = -0.294). A real predictive signal would show consistent
direction. Opposite signs across adjacent lags is the textbook fingerprint
of multiple-comparison false positives. With 6 tests at p < .05, ~0.3
false positives are expected by chance. Reporting these as "significant"
would be dishonest.

## Event context decisions

### Why include the event timeline?
The quantitative analysis shows no correlation. The event timeline explains
WHY apparent co-movements occur: they are caused by confounding variables
(earnings reports, Fed decisions, competitive events). Without this context,
the project is a correlation exercise. With it, the project demonstrates
causal reasoning.

### Why source every event?
Each event cites a primary source: SEC EDGAR for earnings, federalreserve.gov
for FOMC statements, the Federal Register for executive orders, NVIDIA's
official newsroom for product announcements. This makes every claim verifiable
and distinguishes the project from opinion.

### The confounding variable thesis
This is the original analytical contribution. The thesis: every instance
where search attention and NVDA price appeared to move together can be
traced to a shared causal event. The searches are an echo of the news.
The price is a reaction to the news. Neither causes the other. This is
a testable, falsifiable claim supported by the event-by-event analysis.

## Design decisions

### Why not the default Claude palette?
AI-generated designs cluster around three looks: cream+terracotta,
dark+acid-green, or broadsheet+hairlines. All are legitimate but
recognisable. FinBuzz uses Newsreader (editorial serif), Source Sans 3
(professional sans), JetBrains Mono (data), with a palette of warm paper,
institutional blue, burnt sienna, and muted teal. The design rationale
is documented because "why does it look like this?" is an interview question.

### Why not a dark hero section?
Dark heroes signal "tech product." FinBuzz is a research publication, not a
product. The editorial layout on warm paper signals "I understand financial
media." The blue rule, dense stat bar, and serif headlines reference the FT
and Bloomberg without copying either.

## Honest limitations (stated, not hidden)

- One keyword, one stock, three windows. Not a universal finding.
- Google Trends scores are relative per window and re-sampled per request.
- 172 data points is adequate for correlation but not for complex models.
- The confounding variable analysis is qualitative, not quantified.
- The pipeline does not currently control for confounders statistically
  (e.g., partial correlation with event indicators). This is a future step.
