from core.dataset import DataSet
from core.dtypes import INT, FLOAT


def build_dataset() -> DataSet:
    ds = DataSet()
    ds.add_var("id", INT, [1, 2, 3])
    ds.add_var("value", FLOAT, [1.0, 2.0, 3.0])
    return ds


def test_add_drop_obs():
    ds = build_dataset()
    ds.add_obs({"id": 4, "value": 4.0})
    assert ds.n_obs == 4
    ds.drop_obs(0)
    assert ds.n_obs == 3
    assert ds["id"][0] == 2


def test_undo():
    ds = build_dataset()
    ds.add_obs({"id": 4, "value": 4.0})
    ds.undo()
    assert ds.n_obs == 3


def test_index_lookup():
    ds = build_dataset()
    ds.create_index("id")
    assert ds.lookup("id", 2) == [1]
