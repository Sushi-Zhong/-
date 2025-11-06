"""Command line interface that mimics a subset of Stata."""

from __future__ import annotations

import cmd
import shlex
from pathlib import Path

from core.dataset import DataSet
from io_utils.reader import read_csv
from io_utils.writer import write_csv
from ops import crud
from stats.descriptives import describe, summarize, tabulate
from stats.regression import regress


class StataLikeShell(cmd.Cmd):
    intro = "Welcome to the Stata-like shell. Type help or ? to list commands."
    prompt = "stata> "

    def __init__(self):
        super().__init__()
        self.dataset: DataSet | None = None

    def onecmd(self, line: str):  # pragma: no cover - thin wrapper
        try:
            return super().onecmd(line)
        except Exception as exc:  # noqa: BLE001 - show user errors
            print(f"Error: {exc}")
            return False

    # ------------------------------------------------------------------
    def do_use(self, arg: str) -> None:
        """use <file>: load a CSV file into memory."""

        path = Path(arg.strip("\"'"))
        self.dataset = read_csv(path)
        print(f"Loaded {len(self.dataset.variables)} vars and {self.dataset.n_obs} observations")

    def do_save(self, arg: str) -> None:
        """save <file>: write the current dataset to CSV."""

        self._require_dataset()
        path = Path(arg.strip("\"'"))
        write_csv(self.dataset, path)
        print(f"Saved to {path}")

    # ------------------------------------------------------------------
    def do_describe(self, arg: str) -> None:
        self._require_dataset()
        vars = shlex.split(arg) if arg else None
        for row in describe(self.dataset, vars):
            print(row)

    def do_summarize(self, arg: str) -> None:
        self._require_dataset()
        vars = shlex.split(arg) if arg else None
        for row in summarize(self.dataset, vars):
            print(row)

    def do_tabulate(self, arg: str) -> None:
        self._require_dataset()
        parts = shlex.split(arg)
        if not parts:
            print("tabulate requires at least one variable")
            return
        var1 = parts[0]
        var2 = parts[1] if len(parts) > 1 else None
        table = tabulate(self.dataset, var1, var2)
        print(table)

    # ------------------------------------------------------------------
    def do_generate(self, arg: str) -> None:
        self._require_dataset()
        parts = arg.split("=", 1)
        if len(parts) != 2:
            print("Usage: generate newvar = expression")
            return
        newvar = parts[0].strip()
        expr = parts[1].strip()
        crud.generate(self.dataset, newvar, expr)
        print(f"generated {newvar}")

    def do_replace(self, arg: str) -> None:
        self._require_dataset()
        parts = arg.split("=", 1)
        if len(parts) != 2:
            print("Usage: replace var = expression [if condition]")
            return
        var = parts[0].strip()
        expr_and_cond = parts[1].strip()
        if " if " in expr_and_cond:
            expr, cond = expr_and_cond.split(" if ", 1)
        else:
            expr, cond = expr_and_cond, None
        crud.replace(self.dataset, var, expr.strip(), cond.strip() if cond else None)
        print(f"replaced {var}")

    def do_drop(self, arg: str) -> None:
        self._require_dataset()
        if arg.startswith("if "):
            condition = arg[3:]
            crud.drop_if(self.dataset, condition)
        else:
            crud.drop_var(self.dataset, shlex.split(arg))
        print("drop completed")

    def do_keep(self, arg: str) -> None:
        self._require_dataset()
        if arg.startswith("if "):
            condition = arg[3:]
            crud.keep_if(self.dataset, condition)
            print("filtered dataset")
        else:
            cols = shlex.split(arg)
            drop = [name for name in self.dataset.variables if name not in cols]
            crud.drop_var(self.dataset, drop)
            print("kept subset of variables")

    def do_sort(self, arg: str) -> None:
        self._require_dataset()
        parts = shlex.split(arg)
        if not parts:
            print("sort requires variable name")
            return
        self.dataset.sort_values(parts[0], reverse=len(parts) > 1 and parts[1] == "desc")
        print("dataset sorted")

    def do_group(self, arg: str) -> None:
        self._require_dataset()
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: group byvar target [agg]")
            return
        agg = parts[2] if len(parts) > 2 else "mean"
        result = self.dataset.groupby(parts[0], parts[1], agg)
        print(result)

    def do_regress(self, arg: str) -> None:
        self._require_dataset()
        parts = shlex.split(arg)
        if len(parts) < 2:
            print("Usage: regress y x1 x2 ...")
            return
        y = parts[0]
        xs = parts[1:]
        result = regress(y, xs, self.dataset)
        for name, coef, se, t in zip(result["variables"], result["coefficients"], result["std_errors"], result["t"]):
            print(f"{name:10s} coef={coef:.4f} se={se:.4f} t={t:.2f}")
        print(f"R2={result['r2']:.4f} N={result['N']}")

    def do_lookup(self, arg: str) -> None:
        self._require_dataset()
        parts = shlex.split(arg)
        if len(parts) != 2:
            print("Usage: lookup var value")
            return
        rows = self.dataset.lookup(parts[0], parts[1])
        print(rows)

    def do_undo(self, arg: str) -> None:
        self._require_dataset()
        if self.dataset.undo():
            print("undo successful")
        else:
            print("nothing to undo")

    def do_quit(self, arg: str) -> bool:  # pragma: no cover - interactive exit
        return True

    do_exit = do_quit

    # ------------------------------------------------------------------
    def _require_dataset(self) -> None:
        if self.dataset is None:
            raise RuntimeError("no dataset loaded; run 'use <csv>' first")


def main() -> None:
    shell = StataLikeShell()
    shell.cmdloop()


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
