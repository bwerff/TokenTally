"""Parsing helpers for Nvidia DCGM metrics."""

from __future__ import annotations

import csv
from typing import Iterable


def parse_dcgm_gpu_minutes(lines: Iterable[str]) -> float:
    """Return total GPU minutes from a DCGM CSV export.

    The input should be an iterable of strings representing CSV rows with at
    least ``timestamp`` and either ``gpu_util`` or ``sm_util`` columns. GPU
    minutes are calculated as ``utilization_percent * duration`` across
    consecutive rows.
    """
    reader = csv.DictReader(lines)
    last_ts: int | None = None
    last_util: float | None = None
    total_util_seconds: float = 0.0

    for row in reader:
        try:
            ts = int(row["timestamp"])
            util = float(row.get("gpu_util", row.get("sm_util", 0)))
        except (KeyError, ValueError):
            continue
        if last_ts is not None and last_util is not None:
            dur = ts - last_ts
            total_util_seconds += dur * (last_util / 100.0)
        last_ts = ts
        last_util = util

    return total_util_seconds / 60.0

__all__ = ["parse_dcgm_gpu_minutes"]
