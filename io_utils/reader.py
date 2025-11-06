"""CSV reader that loads data into a :class:`core.dataset.DataSet`."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from core.dataset import DataSet
from core.dtypes import FLOAT, INT, STR


def _infer_dtype(values: Iterable[str]):
    try:
        for value in values:
            if value == "":
                continue
            int(value)
        return INT
    except ValueError:
        pass
    try:
        for value in values:
            if value == "":
                continue
            float(value)
        return FLOAT
    except ValueError:
        return STR
    return FLOAT


def read_csv(path: str | Path) -> DataSet:
    dataset = DataSet()
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        columns = [[] for _ in header]
        for row in reader:
            for idx, value in enumerate(row):
                columns[idx].append(value)
        for name, values in zip(header, columns):
            dtype = _infer_dtype(values)
            dataset.add_var(name, dtype=dtype, data=values)
    return dataset


__all__ = ["read_csv"]
