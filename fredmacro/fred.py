"""Minimal FRED API client.

We talk to the REST API directly with `requests` instead of using a wrapper
library. It is ~50 lines, has no extra dependencies, and means you actually
understand what is going on when something breaks.

API docs: https://fred.stlouisfed.org/docs/api/fred/
Get a free key: https://fredaccount.stlouisfed.org/apikeys
"""

from __future__ import annotations

import os
import time

import pandas as pd
import requests

BASE_URL = "https://api.stlouisfed.org/fred"
_SESSION = requests.Session()


class FredError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("FRED_API_KEY")
    if not key:
        raise FredError(
            "FRED_API_KEY is not set.\n"
            "  Local:  copy .env.example to .env and put your key in it\n"
            "  CI:     add it as a GitHub Actions secret named FRED_API_KEY\n"
            "  Key:    https://fredaccount.stlouisfed.org/apikeys (free, instant)"
        )
    return key


def _get(endpoint: str, **params) -> dict:
    """GET a FRED endpoint as JSON, with a couple of polite retries."""
    params.update(api_key=_api_key(), file_type="json")
    last_error = None
    for attempt in range(3):
        try:
            response = _SESSION.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
            if response.status_code == 429:  # rate limited
                time.sleep(2 * (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise FredError(f"FRED request to /{endpoint} failed: {last_error}")


def get_series(series_id: str, start: str = "1990-01-01") -> pd.Series:
    """Download one series as a float pandas Series indexed by date.

    FRED encodes missing observations as the string ".", which is why we
    coerce to numeric and drop rather than calling float() directly.
    """
    payload = _get(
        "series/observations",
        series_id=series_id,
        observation_start=start,
    )
    observations = payload.get("observations", [])
    if not observations:
        raise FredError(f"No observations returned for {series_id!r}")

    frame = pd.DataFrame(observations)
    values = pd.to_numeric(frame["value"], errors="coerce")
    series = pd.Series(values.values, index=pd.to_datetime(frame["date"]), name=series_id)
    return series.dropna().sort_index()


def get_metadata(series_id: str) -> dict:
    """Title, units, frequency, seasonal adjustment and last-updated stamp."""
    payload = _get("series", series_id=series_id)
    info = payload["seriess"][0]
    return {
        "id": info["id"],
        "title": info["title"],
        "units": info["units_short"],
        "frequency": info["frequency_short"],  # D, W, M, Q, A
        "seasonal_adjustment": info["seasonal_adjustment_short"],
        "last_updated": info["last_updated"],
        "observation_end": info["observation_end"],
    }


def search(text: str, limit: int = 10) -> pd.DataFrame:
    """Find series IDs without leaving your editor.

    >>> search("core PCE price index")
    """
    payload = _get("series/search", search_text=text, limit=limit, order_by="popularity",
                   sort_order="desc")
    rows = [
        {
            "id": s["id"],
            "title": s["title"],
            "freq": s["frequency_short"],
            "sa": s["seasonal_adjustment_short"],
            "units": s["units_short"],
        }
        for s in payload.get("seriess", [])
    ]
    return pd.DataFrame(rows)
