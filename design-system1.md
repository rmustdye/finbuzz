# FinBuzz Design System: "Ink & Paper"

The visual language for the FinBuzz dashboard. Read this before generating or modifying any HTML/CSS.

## Design Philosophy

FinBuzz looks like a well-designed research report, not a startup landing page. Think editorial data journalism — the visual equivalent of "this person takes their work seriously." The mood board reference is "Pinterest artsy-minimal data journalism": clean, typographic, generous whitespace, every element earns its place.

**What it IS:** A financial research publication. Serious but not stuffy. Clean but not cold. Data-dense but not cluttered.

**What it is NOT:** A SaaS dashboard with gradient buttons. A dark-mode terminal aesthetic. A crypto/trading platform. A portfolio template with animated counters.

---

## Color Palette

| Name | Hex | Usage |
|---|---|---|
| Paper | #FAFAF8 | Page background — warm off-white, not clinical white |
| Ink | #1A1A1A | Primary text — not pure black (too harsh) |
| Forest | #2D5F3E | Primary accent — links, active states, key data points |
| Sage | #8BA888 | Secondary accent — borders, subtle highlights, chart gridlines |
| Stone | #C4B5A0 | Tertiary — dividers, captions, metadata text |
| Cream | #F0EDE5 | Card/panel backgrounds — slight warmth against Paper |
| Alert | #C4503A | Negative/warning states — sparingly |
| Positive | #2D5F3E | Same as Forest — positive values |
| Negative | #C4503A | Same as Alert — negative values |

### Color Rules
- **Never** use more than 3 colors in a single chart
- Forest for the primary data series (trend score), a complementary blue-gray (#5B7C99) for the secondary (stock price)
- Background is always Paper or Cream — never dark backgrounds
- Text is always Ink, Stone (for metadata), or white-on-Forest (for badges/labels)

---

## Typography

### Font Stack
```css
/* Headlines / Display */
font-family: Georgia, 'Times New Roman', serif;

/* Body text */
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;

/* Data / Monospace */
font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
```

### Type Scale
```css
/* Hero headline */
.hero-title { font-size: 2.5rem; font-weight: 700; line-height: 1.15; letter-spacing: -0.02em; }

/* Section headlines */
h2 { font-size: 1.75rem; font-weight: 600; line-height: 1.3; }

/* Subsection headlines */
h3 { font-size: 1.25rem; font-weight: 600; line-height: 1.4; }

/* Body text */
body { font-size: 1rem; font-weight: 400; line-height: 1.7; }

/* Captions and metadata */
.caption { font-size: 0.8125rem; font-weight: 400; line-height: 1.5; color: var(--stone); }

/* Data values */
.data-value { font-family: monospace; font-size: 0.9375rem; font-weight: 500; }
```

### Typography Rules
- Headlines use serif (Georgia) — gives a publication/editorial feel
- Body uses sans-serif (Inter/system) — clean readability
- Data labels and statistical values use monospace — signals precision
- Never bold body text for emphasis — use Forest color or italic instead
- Maximum line width: 680px for body text (optimal readability)

---

## Layout

### Grid
- Single column, centered, max-width 800px for text, 960px for charts
- Horizontal padding: 24px (mobile), 48px (tablet), auto (desktop — content centered)

### Spacing Scale
```css
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 40px;
--space-2xl: 64px;
--space-3xl: 96px;
```

### Section Rhythm
- Between major sections: `--space-3xl` (96px)
- Between subsections: `--space-2xl` (64px)
- Between paragraphs: `--space-lg` (24px)
- Generous whitespace is non-negotiable — it's what separates "polished" from "crowded"

---

## Components

### Navigation
- Minimal: site title left, 3–4 section links right
- Sticky on scroll, with subtle bottom border (1px Stone)
- No hamburger menu on mobile — just the title and a "↓ Methodology" link

### Provenance Stamp
Every chart includes a provenance bar below it:
```
Source: Google Trends · Window: Aug 25 – Nov 14, 2025 · SHA-256: a7ffc6f8...
```
- Font: monospace, 0.75rem, Stone color
- Separated by middle dots (·)
- Hash truncated to first 8 characters

### Stat Cards
For key metrics (r value, p-value, trading days):
```css
.stat-card {
    background: var(--cream);
    border: 1px solid var(--sage);
    border-radius: 4px;  /* subtle, not rounded */
    padding: var(--space-lg);
    text-align: center;
}
.stat-card .value {
    font-family: monospace;
    font-size: 2rem;
    font-weight: 700;
    color: var(--forest);
}
.stat-card .label {
    font-size: 0.8125rem;
    color: var(--stone);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
```

### Chart Container
```css
.chart-container {
    background: white;
    border: 1px solid var(--sage);
    border-radius: 4px;
    padding: var(--space-xl);
    margin: var(--space-xl) 0;
}
```

### Tabs (for analysis windows)
```css
.tab {
    font-family: monospace;
    font-size: 0.875rem;
    padding: var(--space-sm) var(--space-md);
    border: 1px solid var(--sage);
    background: transparent;
    cursor: pointer;
}
.tab.active {
    background: var(--forest);
    color: white;
    border-color: var(--forest);
}
```

### Callout Box (for findings)
```css
.callout {
    border-left: 3px solid var(--forest);
    background: var(--cream);
    padding: var(--space-lg);
    margin: var(--space-xl) 0;
    font-style: italic;
}
```

---

## Chart Styling

### General Rules
- Clean, minimal — no chartjunk (no 3D effects, no unnecessary gridlines, no decorative elements)
- Light gridlines in Sage (#8BA888) at 0.5 opacity
- Axis labels in monospace, Stone color
- Legend at the top of the chart, not overlapping data

### Dual-Axis Chart
- Left axis: Trend Score (0–100), Forest color line
- Right axis: Close Price ($), blue-gray (#5B7C99) line
- Both axes clearly labeled with units
- Hover tooltip shows both values for the date
- Smoothing toggle in the top-right corner of the chart

### Rolling Correlation Chart
- Single line, Forest color
- Horizontal reference line at r = 0 (dashed, Stone color)
- Shaded band at ±0.3 (very faint Sage fill) to show "weak correlation" zone

### Bar Chart (for lag analysis)
- Vertical bars, one per lag (0–5)
- Forest for positive r, Alert (#C4503A) for negative r
- Error bars showing 95% confidence interval if available
- Horizontal reference line at r = 0

---

## Responsive Design

### Breakpoints
```css
/* Mobile first */
@media (min-width: 640px)  { /* Tablet */ }
@media (min-width: 960px)  { /* Desktop */ }
@media (min-width: 1200px) { /* Large desktop */ }
```

### Mobile Adaptations
- Charts: full width, reduce padding, simplify tooltips
- Stat cards: stack vertically (1 column) instead of side-by-side
- Navigation: title only, section links below in a row
- Font sizes: reduce hero by ~20%, keep body size the same
- Tabs: horizontal scroll if they don't fit

---

## What NOT to Do

- No gradient backgrounds or gradient text
- No animated counters or "number roll-up" effects
- No dark mode (the Ink & Paper aesthetic is inherently light)
- No stock-photo hero images
- No cards with drop shadows (use borders instead)
- No rounded corners > 4px (this isn't a mobile app)
- No emoji in headings or body text
- No "Loading..." spinners (all data is embedded, not fetched)
- No footer with 50 links — just "FinBuzz · [Your name] · 2026"

---

## Visual References to Search

For mood board inspiration, search these terms on Pinterest or Dribbble:
- "editorial data visualization"
- "financial report design minimal"
- "data journalism layout"
- "academic paper beautiful typography"
- "research publication web design"

The aesthetic sits at the intersection of: a well-typeset academic paper, a Bloomberg Businessweek feature, and a clean data journalism piece from The Pudding or Reuters Graphics.
