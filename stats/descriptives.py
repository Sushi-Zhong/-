"""Descriptive statistics for the Stata-like toolkit."""

from __future__ import annotations

import math
from collections import Counter
from statistics import mean
from typing import Any, Dict, Iterable, List

from core.dataset import DataSet


def _select_vars(dataset: DataSet, vars: Iterable[str] | None) -> List[str]:
    if vars is None:
        return dataset.variables
    return list(vars)


def describe(dataset: DataSet, vars: Iterable[str] | None = None) -> List[Dict[str, float]]:
    output: List[Dict[str, float]] = []
    for name in _select_vars(dataset, vars):
        column = dataset[name]
        values = [float(v) for v in column.materialize() if isinstance(v, (int, float)) and not math.isnan(float(v))]
        if not values:
            stats = {"var": name, "N": 0, "mean": math.nan, "sd": math.nan, "min": math.nan, "p50": math.nan, "max": math.nan}
        else:
            sorted_vals = sorted(values)
            mid = len(sorted_vals) // 2
            if len(sorted_vals) % 2:
                median = sorted_vals[mid]
            else:
                median = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
            stats = {
                "var": name,
                "N": len(values),
                "mean": sum(values) / len(values),
                "sd": math.sqrt(sum((v - mean(values)) ** 2 for v in values) / (len(values) - 1 or 1)),
                "min": sorted_vals[0],
                "p50": median,
                "max": sorted_vals[-1],
            }
        output.append(stats)
    return output


def summarize(dataset: DataSet, vars: Iterable[str] | None = None, weight: Iterable[float] | None = None) -> List[Dict[str, float]]:
    weights = list(weight) if weight is not None else None
    output: List[Dict[str, float]] = []
    for name in _select_vars(dataset, vars):
        column = dataset[name]
        numeric = []
        for idx, value in enumerate(column):
            try:
                numeric.append(float(value))
            except (TypeError, ValueError):
                numeric.append(math.nan)
        if weights is None:
            w = [1.0] * len(numeric)
        else:
            w = list(weights)
        pairs = [(val, wt) for val, wt in zip(numeric, w) if not math.isnan(val)]
        if not pairs:
            stats = {"var": name, "N": len(numeric), "mean": math.nan, "sd": math.nan, "min": math.nan, "max": math.nan}
        else:
            total_w = sum(wt for _, wt in pairs)
            weighted_mean = sum(val * wt for val, wt in pairs) / total_w
            variance = sum(((val - weighted_mean) ** 2) * wt for val, wt in pairs) / total_w
            values = [val for val, _ in pairs]
            stats = {
                "var": name,
                "N": len(numeric),
                "mean": weighted_mean,
                "sd": math.sqrt(variance),
                "min": min(values),
                "max": max(values),
            }
        output.append(stats)
    return output


def tabulate(dataset: DataSet, var1: str, var2: str | None = None) -> Dict:
    if var2 is None:
        counts = Counter(dataset[var1])
        total = sum(counts.values())
        return {k: {"count": v, "percent": v / total * 100} for k, v in counts.items()}
    else:
        table: Dict[Any, Counter] = {}
        for a, b in zip(dataset[var1], dataset[var2]):
            table.setdefault(a, Counter())[b] += 1
        return {row_key: dict(counter) for row_key, counter in table.items()}


__all__ = ["describe", "summarize", "tabulate"]
