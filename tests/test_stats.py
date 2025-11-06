from core.dataset import DataSet
from core.dtypes import INT, FLOAT
from stats.descriptives import describe, summarize, tabulate
from stats.regression import regress


def build_dataset() -> DataSet:
    ds = DataSet()
    ds.add_var("x", FLOAT, [1.0, 2.0, 3.0, 4.0])
    ds.add_var("y", FLOAT, [2.0, 4.0, 6.0, 8.0])
    ds.add_var("group", INT, [1, 1, 2, 2])
    return ds


def test_describe():
    ds = build_dataset()
    stats = describe(ds, ["x"])[0]
    assert stats["N"] == 4


def test_summarize():
    ds = build_dataset()
    stats = summarize(ds, ["x"])[0]
    assert round(stats["mean"], 2) == 2.5


def test_tabulate():
    ds = build_dataset()
    table = tabulate(ds, "group")
    assert table[1]["count"] == 2


def test_regression():
    ds = build_dataset()
    result = regress("y", ["x"], ds)
    assert result["N"] == 4
    assert abs(result["coefficients"][1] - 2.0) < 1e-6
