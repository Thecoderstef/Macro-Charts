# FRED macro dashboard

A small, self-updating set of US macro charts built from the St. Louis Fed's
FRED API. Push it to GitHub, add one secret, and it redraws itself on the 14th
of every month without you touching anything.

---

## 1. Get a key (2 minutes)

Register at **https://fredaccount.stlouisfed.org/apikeys**. It is free, instant,
and needs no card. You get a 32-character lower-case string.

```bash
cp .env.example .env      # then paste your key into .env
```

`.env` is in `.gitignore`. Never commit a key — if you do, revoke it on that
page immediately, because GitHub history is forever.

## 2. Run it locally

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python update.py
```

Charts land in `charts/`, the underlying data in `data/`, and the gallery below
gets rewritten with fresh numbers. To iterate on a single chart while you fiddle
with styling:

```bash
python update.py cpi_inflation
```

## 3. Make it update itself

1. Push the repo to GitHub.
2. Go to **Settings → Secrets and variables → Actions → New repository secret**.
   Name it `FRED_API_KEY`, paste your key.
3. Go to the **Actions** tab and hit *Run workflow* on "Refresh macro charts" to
   confirm it works.

From then on `.github/workflows/monthly-update.yml` runs on the 14th at 07:00
UTC, regenerates everything, and commits the result back to the repo. CPI is
released around the 10th–13th of each month, PCE at month-end, so the 14th
catches CPI the same month and PCE from the month before.

---

## Adding your own chart

Everything lives in `config/series.yaml`. Copy a block, change the IDs:

```yaml
  - id: retail_sales
    title: "The consumer keeps spending"
    subtitle: "Advance retail sales, year-over-year % change"
    ylabel: "% YoY"
    transform: yoy
    zero_line: true
    series:
      - {fred_id: RSAFS, label: "Retail sales"}
```

To find a series ID, search the FRED website, or from Python:

```python
from fredmacro.fred import search
print(search("core pce price index"))
```

Available `transform` values, from `fredmacro/transform.py`:

| Name | What it does | When to use it |
|---|---|---|
| `level` | nothing | rates, ratios, anything already in % |
| `yoy` | year-over-year % change | the default inflation view |
| `three_month_annualised` | 3m/3m annualised | spotting turning points early |
| `mom_annualised` | 1m annualised | fastest, noisiest |

### Series IDs worth knowing

| ID | Series |
|---|---|
| `CPIAUCSL` / `CPILFESL` | CPI, headline / core (SA, monthly) |
| `PCEPI` / `PCEPILFE` | PCE price index, headline / core |
| `UNRATE` / `PAYEMS` | unemployment rate / nonfarm payrolls |
| `FEDFUNDS` / `DFF` | effective fed funds, monthly / daily |
| `DGS2` / `DGS10` / `T10Y2Y` | 2y, 10y Treasury yields, 10y–2y spread |
| `T10YIE` | 10-year breakeven inflation |
| `GDPC1` | real GDP (quarterly) |
| `USREC` | NBER recession dummy — used for the grey shading |

Add `NSA` variants only if you know why you want them; nearly every macro chart
you have seen uses seasonally adjusted data.

---

## Why the charts look the way they do

The styling is the part people assume takes talent. It is really five decisions,
all of them in `fredmacro/style.py`:

1. **Kill the frame.** No box, no vertical gridlines, no y-axis tick marks. Soft
   horizontal grid only.
2. **Label lines directly** at their right-hand end, with the latest value. A
   legend makes the reader's eye bounce between key and line; a direct label
   doesn't. This is the single biggest upgrade over default matplotlib.
3. **One protagonist colour**, everything else muted. The palette has five
   colours and you should rarely use more than three.
4. **Real subtitle and source footer.** "Year-over-year % change" under the
   title means the axis needs no explaining, and the source line means the chart
   survives being screenshotted into someone's slide deck.
5. **Recession shading** for context — grey bands from `USREC`, drawn behind
   everything at 6% opacity so they never compete with the data.

The one thing to watch: when two lines end at similar values their right-hand
labels overlap. Either nudge one with `xytext` in `charts.py` or pick a shorter
label.

---

## Layout

```
config/series.yaml            what to plot — the only file you edit day to day
fredmacro/fred.py             FRED API client (~50 lines, no wrapper library)
fredmacro/transform.py        YoY, 3m annualised, rebasing
fredmacro/style.py            the house style
fredmacro/charts.py           chart construction, recession shading, labels
update.py                     entrypoint: fetch → transform → plot → update README
.github/workflows/            the monthly cron job
charts/  data/                generated output, committed so the README renders
```

Raw series are written to `data/` as CSV on every run. That means anyone can
check your numbers, and you get a git history of revisions — CPI and especially
payrolls get revised, and the diff on those CSVs is a free record of it.

---

## Charts

<!-- CHARTS:START -->
_Last rebuilt 30 July 2026, 12:55 UTC._

## 1. Leading indicators

### US Yield Curve
`10y minus 3m` — latest **0.8** (Jul 2026)

![US Yield Curve](charts/yield_curve.png)

### US Initial Jobless Claims
`Initial claims` — latest **197000.0** (Jul 2026)

![US Initial Jobless Claims](charts/jobless_claims.png)

### US Building Permits
`Building permits` — latest **1374.0** (Jun 2026)

![US Building Permits](charts/building_permits.png)

## 2. Growth and activity

### US GDP Growth
`QoQ annualised` — latest **2.1** (Jan 2026)

![US GDP Growth](charts/gdp_growth.png)

## 3. Labour market

### US Unemployment Rate
`Unemployment rate` — latest **4.2** (Jun 2026)

![US Unemployment Rate](charts/labour_market.png)

## 4. Inflation - realised

### US CPI
`Headline CPI` — latest **3.7** (Jun 2026)

![US CPI](charts/cpi_inflation.png)

### US PCE
`Headline PCE` — latest **4.1** (May 2026)

![US PCE](charts/pce_inflation.png)

### US Core CPI Momentum
`YoY` — latest **2.8** (Jun 2026)

![US Core CPI Momentum](charts/cpi_momentum.png)

## 5. Inflation - expected

### US Inflation Expectations
`10y breakeven` — latest **2.3** (Jul 2026)

![US Inflation Expectations](charts/inflation_expectations.png)

### US Breakevens vs Realised CPI
`10y breakeven` — latest **2.3** (Jul 2026)

![US Breakevens vs Realised CPI](charts/expected_vs_realised.png)

## 6. Rates and policy

### US Policy Rate vs Core PCE
`Fed funds rate` — latest **3.6** (Jun 2026)

![US Policy Rate vs Core PCE](charts/policy_vs_inflation.png)

### US Treasury Yields
`10-year` — latest **4.6** (Jul 2026)

![US Treasury Yields](charts/treasury_yields.png)

### US Real vs Nominal 10-Year Yield
`Nominal 10y` — latest **4.6** (Jul 2026)

![US Real vs Nominal 10-Year Yield](charts/real_yields.png)

## 7. Financial conditions

### US Credit Spreads
`High yield` — latest **2.8** (Jul 2026)

![US Credit Spreads](charts/credit_spreads.png)

### US Dollar Index
`Broad dollar` — latest **120.7** (Jul 2026)

![US Dollar Index](charts/dollar.png)

### Fed Balance Sheet
`Fed total assets` — latest **6747378.0** (Jul 2026)

![Fed Balance Sheet](charts/fed_balance_sheet.png)

### Fed Overnight Reverse Repo
`ON RRP` — latest **2.6** (Jul 2026)

![Fed Overnight Reverse Repo](charts/reverse_repo.png)

### US Money Supply (M2)
`M2 (nominal)` — latest **5.5** (Jun 2026)

![US Money Supply (M2)](charts/money_supply.png)

## 8. Switzerland

### Swiss CPI
`Swiss HICP` — latest **0.7** (Jun 2026)

![Swiss CPI](charts/ch_inflation.png)

### Swiss Unemployment Rate
`Unemployment rate` — latest **5.1** (Jan 2026)

![Swiss Unemployment Rate](charts/ch_unemployment.png)

### Swiss GDP Growth
`QoQ annualised` — latest **2.6** (Jan 2026)

![Swiss GDP Growth](charts/ch_gdp.png)

### CHF/USD Exchange Rate
`CHF per USD` — latest **0.8** (Jul 2026)

![CHF/USD Exchange Rate](charts/chf_usd.png)

## 9. Euro area

### Euro Area CPI
`Euro area HICP` — latest **2.8** (Jun 2026)

![Euro Area CPI](charts/ea_inflation.png)

### Euro Area Unemployment Rate
`Unemployment rate` — latest **6.6** (Oct 2022)

![Euro Area Unemployment Rate](charts/ea_unemployment.png)

### Euro Area GDP Growth
`QoQ annualised` — latest **1.8** (Apr 2026)

![Euro Area GDP Growth](charts/ea_gdp.png)

<!-- CHARTS:END -->

---

*This product uses the FRED® API but is not endorsed or certified by the Federal
Reserve Bank of St. Louis.*
