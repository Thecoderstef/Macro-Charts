"""The handful of transformations that cover 90% of macro charts.

FRED can do some of these server-side via the `units` parameter (units="pc1"
gives year-over-year % change). Doing it in pandas is a little more code but
you keep the raw level series, which you usually want anyway.
"""

from __future__ import annotations

import pandas as pd

# How many observations make up one year, by FRED frequency code.
PERIODS_PER_YEAR = {"D": 252, "W": 52, "BW": 26, "M": 12, "Q": 4, "SA": 2, "A": 1}


def periods_per_year(series: pd.Series, frequency: str | None = None) -> int:
    """Use FRED's declared frequency if we have it, otherwise infer from gaps."""
    if frequency and frequency in PERIODS_PER_YEAR:
        return PERIODS_PER_YEAR[frequency]
    median_gap = series.index.to_series().diff().dt.days.median()
    if median_gap <= 3:
        return 252
    if median_gap <= 10:
        return 52
    if median_gap <= 45:
        return 12
    if median_gap <= 135:
        return 4
    return 1


def yoy(series: pd.Series, frequency: str | None = None) -> pd.Series:
    """Year-over-year % change. The default inflation chart."""
    n = periods_per_year(series, frequency)
    return series.pct_change(n).mul(100).dropna()


def mom_annualised(series: pd.Series, frequency: str | None = None) -> pd.Series:
    """Latest month's change, annualised. Shows turning points far earlier
    than YoY, at the cost of being noisier."""
    n = periods_per_year(series, frequency)
    return ((series / series.shift(1)) ** n - 1).mul(100).dropna()


def three_month_annualised(series: pd.Series, frequency: str | None = None) -> pd.Series:
    """The compromise most economists actually watch: 3m/3m annualised."""
    n = periods_per_year(series, frequency)
    return ((series / series.shift(3)) ** (n / 3) - 1).mul(100).dropna()


def diff(series: pd.Series, periods: int = 1) -> pd.Series:
    """Absolute change, e.g. monthly change in payrolls."""
    return series.diff(periods).dropna()


def rebase(series: pd.Series, date: str) -> pd.Series:
    """Index a level series to 100 at a chosen date, for comparing across
    units or countries."""
    base = series.asof(pd.Timestamp(date))
    return series.div(base).mul(100)


def level(series: pd.Series, frequency: str | None = None) -> pd.Series:
    """No-op, so config files can name `level` alongside the others."""
    return series


TRANSFORMS = {
    "level": level,
    "yoy": yoy,
    "mom_annualised": mom_annualised,
    # Same function as mom_annualised — on quarterly data it annualises the
    # quarter-on-quarter change, which is the headline US GDP number BEA
    # reports ("GDP grew at a 3.2% annual rate"). Aliased for readability.
    "qoq_annualised": mom_annualised,
    "three_month_annualised": three_month_annualised,
}
