"""Observation helpers for the Stata-like dataset."""

from __future__ import annotations

from typing import Any, Dict, Iterable


class Observation(dict):
    """Thin wrapper used when iterating over rows."""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


def iter_observations(variable_names: Iterable[str], columns: dict[str, list[Any]]):
    for idx in range(len(next(iter(columns.values()), []))):
        yield Observation({name: columns[name][idx] for name in variable_names})
