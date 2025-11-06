from core.dataset import DataSet
from core.dtypes import INT, FLOAT
from ops import crud
from ops.subset import filter_rows


def build_dataset() -> DataSet:
    ds = DataSet()
    ds.add_var("id", INT, [1, 2, 3, 4])
    ds.add_var("value", FLOAT, [1.0, 2.0, 3.0, 4.0])
    return ds


def test_filter_rows():
    ds = build_dataset()
    rows = filter_rows(ds, "value > 2 & id <= 3")
    assert rows == [2]


def test_generate_and_replace():
    ds = build_dataset()
    crud.generate(ds, "double", "value * 2")
    assert ds["double"][0] == 2.0
    crud.replace(ds, "double", "double + 1", "id == 2")
    assert ds["double"][1] == 5.0
