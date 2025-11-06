"""Column storage for the in-memory Stata-like dataset."""

from __future__ import annotations

from bisect import bisect_left
from typing import Any, Iterable

from .dtypes import DType, FLOAT, INT, STR


class Variable:
    """A homogeneous column of values."""

    def __init__(self, name: str, dtype: DType, data: Iterable[Any] | None = None):
        self.name = name
        self.dtype = dtype
        if data is None:
            self._data = dtype.storage()
        else:
            converted = (dtype.convert(v) for v in data)
            self._data = dtype.storage(converted)

    # ------------------------------------------------------------------
    # Python protocol helpers
    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._data)

    def __iter__(self):  # pragma: no cover - trivial
        return iter(self._data)

    def __getitem__(self, idx: int) -> Any:
        return self._data[idx]

    def __setitem__(self, idx: int, value: Any) -> None:
        self._data[idx] = self.dtype.convert(value)

    # ------------------------------------------------------------------
    def append(self, value: Any) -> None:
        self._data.append(self.dtype.convert(value))

    def extend(self, values: Iterable[Any]) -> None:
        for value in values:
            self.append(value)

    def insert(self, obs_idx: int, value: Any) -> None:
        self._data.insert(obs_idx, self.dtype.convert(value))

    def delete(self, obs_idx: int) -> None:
        del self._data[obs_idx]

    def materialize(self) -> list[Any]:
        """Return the column as a Python list."""

        return list(self._data)

    # ------------------------------------------------------------------
    # Helper for ordered lookups (used by the B+ tree)
    def find_sorted(self, value: Any) -> int:
        converted = self.dtype.convert(value)
        return bisect_left(self._data, converted)


DEFAULT_DTYPES = {
    "float": FLOAT,
    "int": INT,
    "str": STR,
}

__all__ = ["Variable", "DEFAULT_DTYPES"]
