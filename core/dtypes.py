"""Custom data types for the in-memory data set implementation.

The module intentionally keeps the number of supported dtypes small so that the
rest of the project can concentrate on data-structure related logic instead of
being distracted by type conversions.  Each type exposes two helpers: a
``convert`` method that is used whenever new values are appended/inserted and an
``storage`` method that returns the most compact ``array.array`` type code that
can hold the converted value.  For strings we fall back to Python lists because
``array`` does not support variable length entries.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from array import array
from typing import Any, Iterable


class DType(ABC):
    """Abstract base class for a column data type."""

    type_code: str | None = None

    @abstractmethod
    def convert(self, value: Any) -> Any:
        """Convert *value* into the dtype's canonical representation."""

    def storage(self, values: Iterable[Any] | None = None) -> Any:
        """Return an empty storage container for the dtype.

        Numeric types return :class:`array.array` instances while objects fall
        back to a Python list.
        """

        if self.type_code is None:
            return [] if values is None else list(values)
        if values is None:
            return array(self.type_code)
        return array(self.type_code, values)


class IntType(DType):
    type_code = "q"

    def convert(self, value: Any) -> int:
        if value is None or value == "":
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        return int(str(value))


class FloatType(DType):
    type_code = "d"

    def convert(self, value: Any) -> float:
        if value is None or value == "":
            return float("nan")
        if isinstance(value, (int, float)):
            return float(value)
        return float(str(value))


class StrType(DType):
    type_code = None

    def convert(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)


INT = IntType()
FLOAT = FloatType()
STR = StrType()

__all__ = [
    "DType",
    "IntType",
    "FloatType",
    "StrType",
    "INT",
    "FLOAT",
    "STR",
]
