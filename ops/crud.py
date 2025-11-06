"""CRUD operations built on top of :mod:`core.dataset`."""

from __future__ import annotations

from typing import Iterable

from core.dataset import DataSet
from core.variable import Variable

from .subset import evaluate_expression, filter_rows


def drop_var(dataset: DataSet, varlist: Iterable[str]) -> None:
    for name in list(varlist):
        dataset.drop_var(name)


def rename_var(dataset: DataSet, old: str, new: str) -> None:
    dataset.rename_var(old, new)


def generate(dataset: DataSet, newvar: str, expr: str) -> None:
    values = evaluate_expression(dataset, expr)
    dataset.add_var(newvar, data=values)


def replace(dataset: DataSet, var: str, expr: str, filter_expr: str | None = None) -> None:
    values = evaluate_expression(dataset, expr)
    target = dataset[var]
    if filter_expr is None:
        indices = range(dataset.n_obs)
    else:
        indices = filter_rows(dataset, filter_expr)
    for idx in indices:
        target[idx] = values[idx]


def keep_if(dataset: DataSet, expr: str) -> None:
    rows = filter_rows(dataset, expr)
    drop = sorted(set(range(dataset.n_obs)) - set(rows), reverse=True)
    for idx in drop:
        dataset.drop_obs(idx)


def drop_if(dataset: DataSet, expr: str) -> None:
    rows = sorted(filter_rows(dataset, expr), reverse=True)
    for idx in rows:
        dataset.drop_obs(idx)


__all__ = [
    "drop_var",
    "rename_var",
    "generate",
    "replace",
    "keep_if",
    "drop_if",
]
