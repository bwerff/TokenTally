"""Lightweight hourly spend forecasting using a simple ARIMA(1,1,0) model."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from .usage_ledger import UsageLedger


def arima_forecast(series: List[float]) -> float:
    """Forecast the next value for a univariate series.

    This minimal implementation fits an ARIMA(1,1,0) model using
    ordinary least squares. It falls back to a naive diff if the
    series has constant differences.
    """
    if not series:
        raise ValueError("series must not be empty")
    if len(series) < 2:
        return series[-1]

    diffs = [series[i] - series[i - 1] for i in range(1, len(series))]
    if len(set(diffs)) == 1:
        return series[-1] + diffs[-1]

    mean = sum(diffs[:-1]) / max(len(diffs) - 1, 1)
    num = sum((diffs[i] - mean) * (diffs[i - 1] - mean) for i in range(1, len(diffs)))
    den = sum((diffs[i - 1] - mean) ** 2 for i in range(1, len(diffs)))
    phi = num / den if den else 0.0
    forecast_diff = mean + phi * (diffs[-1] - mean)
    return series[-1] + forecast_diff


def forecast_next_hour(ledger: UsageLedger, hours: int = 24) -> float:
    """Return the forecasted spend for the next hour."""
    totals = ledger.get_hourly_totals(hours)
    return arima_forecast(totals)
