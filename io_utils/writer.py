"""CSV writer for :class:`core.dataset.DataSet`."""

from __future__ import annotations

import csv
from pathlib import Path

from core.dataset import DataSet


def write_csv(dataset: DataSet, path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        header = dataset.variables
        writer.writerow(header)
        for row in dataset.to_rows():
            writer.writerow([row[name] for name in header])


__all__ = ["write_csv"]
