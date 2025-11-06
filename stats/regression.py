"""Linear regression implementation using pure Python matrices."""

from __future__ import annotations

import math
from typing import Any, List

from core.dataset import DataSet


class Matrix:
    def __init__(self, data: List[List[float]]):
        self.data = data

    @property
    def nrows(self) -> int:
        return len(self.data)

    @property
    def ncols(self) -> int:
        return len(self.data[0]) if self.data else 0

    def T(self) -> "Matrix":
        return Matrix([[self.data[row][col] for row in range(self.nrows)] for col in range(self.ncols)])

    def __matmul__(self, other: "Matrix") -> "Matrix":
        if self.ncols != other.nrows:
            raise ValueError("incompatible shapes for matrix multiplication")
        result = [
            [sum(self.data[i][k] * other.data[k][j] for k in range(self.ncols)) for j in range(other.ncols)]
            for i in range(self.nrows)
        ]
        return Matrix(result)

    def inv(self) -> "Matrix":
        if self.nrows != self.ncols:
            raise ValueError("matrix must be square for inversion")
        n = self.nrows
        augmented = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(self.data)]
        for i in range(n):
            pivot = augmented[i][i]
            if pivot == 0:
                for j in range(i + 1, n):
                    if augmented[j][i] != 0:
                        augmented[i], augmented[j] = augmented[j], augmented[i]
                        pivot = augmented[i][i]
                        break
                else:
                    raise ValueError("matrix is singular")
            factor = pivot
            augmented[i] = [value / factor for value in augmented[i]]
            for j in range(n):
                if j == i:
                    continue
                factor = augmented[j][i]
                augmented[j] = [augmented[j][k] - factor * augmented[i][k] for k in range(2 * n)]
        inverse = [row[n:] for row in augmented]
        return Matrix(inverse)

    def column(self, idx: int) -> List[float]:
        return [row[idx] for row in self.data]


def regress(y_var: str, x_vars: List[str], dataset: DataSet) -> dict[str, Any]:
    y = Matrix([[float(dataset[y_var][i])] for i in range(dataset.n_obs)])
    x_data = []
    for i in range(dataset.n_obs):
        x_data.append([1.0] + [float(dataset[var][i]) for var in x_vars])
    X = Matrix(x_data)
    Xt = X.T()
    XtX = Xt @ X
    XtX_inv = XtX.inv()
    beta = XtX_inv @ Xt @ y
    residuals = []
    for i in range(dataset.n_obs):
        fitted = sum(beta.data[j][0] * X.data[i][j] for j in range(len(beta.data)))
        residuals.append(y.data[i][0] - fitted)
    ssr = sum(r ** 2 for r in residuals)
    y_mean = sum(row[0] for row in y.data) / dataset.n_obs
    sst = sum((row[0] - y_mean) ** 2 for row in y.data)
    r2 = 1 - ssr / sst if sst else 0.0
    se_matrix = (XtX_inv.data)
    df = dataset.n_obs - len(x_vars) - 1
    if df <= 0:
        raise ValueError("not enough observations for regression")
    sigma2 = ssr / df
    std_errors = [math.sqrt(sigma2 * se_matrix[i][i]) for i in range(len(beta.data))]
    coefficients = [row[0] for row in beta.data]
    t_stats = [coef / se for coef, se in zip(coefficients, std_errors)]
    return {
        "coefficients": coefficients,
        "std_errors": std_errors,
        "t": t_stats,
        "r2": r2,
        "N": dataset.n_obs,
        "variables": ["_cons"] + x_vars,
    }


__all__ = ["Matrix", "regress"]
