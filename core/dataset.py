"""In-memory representation of a Stata-like dataset."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, MutableMapping

from .dtypes import DType, FLOAT, INT, STR
from .variable import Variable


class BPlusTree:
    """A tiny B+ tree implementation for equality lookups.

    The implementation is intentionally small – it only supports inserts and
    equality searches which is sufficient for the interactive data analysis
    workflow we target.  The tree order is fixed at four which keeps the code
    compact while still providing logarithmic lookups.
    """

    ORDER = 4

    @dataclass
    class Node:
        leaf: bool
        keys: List[Any] = field(default_factory=list)
        children: List[Any] = field(default_factory=list)
        next_leaf: "BPlusTree.Node | None" = None

    def __init__(self) -> None:
        self.root = BPlusTree.Node(leaf=True)

    # ------------------------------------------------------------------
    def search(self, key: Any) -> List[int]:
        node = self.root
        while not node.leaf:
            idx = self._find_index(node.keys, key)
            node = node.children[idx]
        idx = self._find_index(node.keys, key)
        if idx < len(node.keys) and node.keys[idx] == key:
            return list(node.children[idx])
        return []

    def insert(self, key: Any, value: int) -> None:
        node = self.root
        path: List[tuple[BPlusTree.Node, int]] = []
        while not node.leaf:
            idx = self._find_index(node.keys, key)
            path.append((node, idx))
            node = node.children[idx]
        idx = self._find_index(node.keys, key)
        if idx < len(node.keys) and node.keys[idx] == key:
            node.children[idx].append(value)
        else:
            node.keys.insert(idx, key)
            node.children.insert(idx, [value])
        self._split_leaf(node, path)

    # ------------------------------------------------------------------
    @staticmethod
    def _find_index(keys: List[Any], key: Any) -> int:
        lo, hi = 0, len(keys)
        while lo < hi:
            mid = (lo + hi) // 2
            if keys[mid] < key:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def _split_leaf(self, node: "BPlusTree.Node", path: List[tuple["BPlusTree.Node", int]]):
        if len(node.keys) < self.ORDER:
            return
        mid = len(node.keys) // 2
        new_leaf = BPlusTree.Node(leaf=True)
        new_leaf.keys = node.keys[mid:]
        new_leaf.children = node.children[mid:]
        node.keys = node.keys[:mid]
        node.children = node.children[:mid]
        new_leaf.next_leaf = node.next_leaf
        node.next_leaf = new_leaf

        promoted_key = new_leaf.keys[0]
        if not path:
            new_root = BPlusTree.Node(leaf=False)
            new_root.keys = [promoted_key]
            new_root.children = [node, new_leaf]
            self.root = new_root
            return
        parent, idx = path.pop()
        parent.keys.insert(idx, promoted_key)
        parent.children.insert(idx + 1, new_leaf)
        self._split_internal(parent, path)

    def _split_internal(self, node: "BPlusTree.Node", path: List[tuple["BPlusTree.Node", int]]):
        if len(node.keys) < self.ORDER:
            return
        mid = len(node.keys) // 2
        promoted = node.keys[mid]
        left_keys = node.keys[:mid]
        right_keys = node.keys[mid + 1 :]
        left_children = node.children[: mid + 1]
        right_children = node.children[mid + 1 :]

        new_node = BPlusTree.Node(leaf=False)
        new_node.keys = right_keys
        new_node.children = right_children
        node.keys = left_keys
        node.children = left_children

        if not path:
            new_root = BPlusTree.Node(leaf=False)
            new_root.keys = [promoted]
            new_root.children = [node, new_node]
            self.root = new_root
            return
        parent, idx = path.pop()
        parent.keys.insert(idx, promoted)
        parent.children.insert(idx + 1, new_node)
        self._split_internal(parent, path)


class DataSet:
    """Container that mimics the core Stata in-memory table."""

    def __init__(self) -> None:
        self._vars: "OrderedDict[str, Variable]" = OrderedDict()
        self._n_obs = 0
        self._indexes: dict[str, BPlusTree] = {}
        self._undo_stack: List[dict[str, tuple[DType, list[Any]]]] = []

    # ------------------------------------------------------------------
    # Internal helpers
    def _invalidate_indexes(self) -> None:
        self._indexes.clear()

    def _push_undo(self) -> None:
        snapshot: dict[str, tuple[DType, list[Any]]] = {}
        for name, var in self._vars.items():
            snapshot[name] = (var.dtype, var.materialize())
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > 2:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        snapshot = self._undo_stack.pop()
        self._vars = OrderedDict(
            (name, Variable(name, dtype, data)) for name, (dtype, data) in snapshot.items()
        )
        self._n_obs = len(next(iter(self._vars.values()), []))
        self._invalidate_indexes()
        return True

    def _check_consistency(self) -> None:
        expected = None
        for variable in self._vars.values():
            if expected is None:
                expected = len(variable)
            elif len(variable) != expected:
                raise ValueError("Column length mismatch")
        self._n_obs = expected or 0

    def _ensure_var(self, name: str) -> Variable:
        try:
            return self._vars[name]
        except KeyError as exc:  # pragma: no cover - simple guard
            raise KeyError(f"variable '{name}' not found") from exc

    # ------------------------------------------------------------------
    # Column operations
    def add_var(self, name: str, dtype: DType | None = None, data: Iterable[Any] | None = None) -> None:
        if name in self._vars:
            raise ValueError(f"variable '{name}' already exists")
        if data is not None and not isinstance(data, list):
            data = list(data)
        dtype = dtype or self._guess_dtype(data)
        variable = Variable(name, dtype, data)
        if self._vars:
            expected = self.n_obs
            if len(variable) not in (0, expected):
                raise ValueError("new variable has incompatible number of observations")
            if len(variable) == 0:
                for _ in range(expected):
                    variable.append(self._default_value(dtype))
        self._push_undo()
        self._vars[name] = variable
        self._check_consistency()
        self._invalidate_indexes()

    def drop_var(self, name: str) -> None:
        if name not in self._vars:
            raise KeyError(name)
        self._push_undo()
        del self._vars[name]
        self._check_consistency()
        self._invalidate_indexes()

    def rename_var(self, old: str, new: str) -> None:
        if old not in self._vars:
            raise KeyError(old)
        if new in self._vars:
            raise ValueError(f"variable '{new}' already exists")
        self._push_undo()
        variable = self._vars.pop(old)
        variable.name = new
        self._vars[new] = variable
        self._invalidate_indexes()

    # ------------------------------------------------------------------
    # Row operations
    def add_obs(self, row: MutableMapping[str, Any]) -> None:
        if not self._vars:
            raise ValueError("cannot add observation to empty dataset; create variables first")
        self._push_undo()
        for name, variable in self._vars.items():
            value = row.get(name, self._default_value(variable.dtype))
            variable.append(value)
        self._n_obs += 1
        self._invalidate_indexes()

    def drop_obs(self, idx: int) -> None:
        if idx < 0 or idx >= self._n_obs:
            raise IndexError(idx)
        self._push_undo()
        for variable in self._vars.values():
            variable.delete(idx)
        self._n_obs -= 1
        self._invalidate_indexes()

    # ------------------------------------------------------------------
    def sort_values(self, by: str, reverse: bool = False) -> None:
        variable = self._ensure_var(by)
        order = sorted(range(self._n_obs), key=lambda i: variable[i], reverse=reverse)
        self._push_undo()
        for name, column in self._vars.items():
            values = column.materialize()
            reordered = [values[i] for i in order]
            self._vars[name] = Variable(name, column.dtype, reordered)
        self._invalidate_indexes()

    def groupby(self, by: str, target: str, agg: str = "mean") -> Dict[Any, float]:
        groups: Dict[Any, List[float]] = {}
        group_var = self._ensure_var(by)
        target_var = self._ensure_var(target)
        for idx in range(self._n_obs):
            key = group_var[idx]
            groups.setdefault(key, []).append(float(target_var[idx]))
        result: Dict[Any, float] = {}
        for key, values in groups.items():
            if agg == "mean":
                result[key] = sum(values) / len(values)
            elif agg == "sum":
                result[key] = sum(values)
            elif agg == "count":
                result[key] = float(len(values))
            else:
                raise ValueError(f"unknown aggregation '{agg}'")
        return result

    # ------------------------------------------------------------------
    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, str):
            return self._ensure_var(key)
        if isinstance(key, tuple) and len(key) == 2:
            row_selector, col_selector = key
            rows = self._resolve_rows(row_selector)
            cols = self._resolve_cols(col_selector)
            return [
                {name: self._vars[name][row_idx] for name in cols}
                for row_idx in rows
            ]
        raise TypeError("invalid key")

    def _resolve_rows(self, selector: Any) -> List[int]:
        if selector is None:
            return list(range(self._n_obs))
        if isinstance(selector, slice):
            return list(range(*selector.indices(self._n_obs)))
        if isinstance(selector, list):
            return selector
        if isinstance(selector, int):
            return [selector]
        raise TypeError("unsupported row selector")

    def _resolve_cols(self, selector: Any) -> List[str]:
        if selector is None:
            return list(self._vars.keys())
        if isinstance(selector, list):
            return selector
        if isinstance(selector, str):
            return [selector]
        raise TypeError("unsupported column selector")

    # ------------------------------------------------------------------
    def create_index(self, var: str) -> None:
        variable = self._ensure_var(var)
        tree = BPlusTree()
        for idx, value in enumerate(variable):
            tree.insert(value, idx)
        self._indexes[var] = tree

    def lookup(self, var: str, value: Any) -> List[int]:
        if var not in self._indexes:
            self.create_index(var)
        return self._indexes[var].search(self._vars[var].dtype.convert(value))

    # ------------------------------------------------------------------
    @property
    def variables(self) -> List[str]:  # pragma: no cover - trivial accessor
        return list(self._vars.keys())

    @property
    def n_obs(self) -> int:  # pragma: no cover - trivial accessor
        return self._n_obs

    def to_rows(self) -> List[Dict[str, Any]]:
        cols = list(self._vars.keys())
        return [
            {name: self._vars[name][idx] for name in cols}
            for idx in range(self._n_obs)
        ]

    # ------------------------------------------------------------------
    @staticmethod
    def _default_value(dtype: DType) -> Any:
        if dtype is INT:
            return 0
        if dtype is FLOAT:
            return float("nan")
        return ""

    def _guess_dtype(self, data: Iterable[Any] | None) -> DType:
        if data is None:
            return FLOAT
        preview = list(data)
        if not preview:
            return FLOAT
        try:
            for value in preview:
                int(value)
            return INT
        except (ValueError, TypeError):
            pass
        try:
            for value in preview:
                float(value)
            return FLOAT
        except (ValueError, TypeError):
            return STR

        return STR


__all__ = ["DataSet", "BPlusTree"]
