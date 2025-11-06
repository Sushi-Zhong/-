# Stata-like Toolkit (Python Standard Library Only)

This project re-implements a subset of Stata's workflow—loading rectangular datasets, transforming variables, running descriptive statistics, and estimating linear regressions—using only the Python standard library.

## Project Layout

```
core/            # Columnar in-memory dataset and type system
io_utils/        # CSV reader/writer helpers
ops/             # CRUD helpers and expression-based filtering
stats/           # Descriptive statistics and OLS regression
main.py          # Command line interface that mimics Stata commands
gui.py           # Tkinter-based dataset browser
tests/           # pytest test suite
examples/        # Sample CSV files
```

## Getting Started

1. **Create a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. **Install runtime dependencies:** this repository only uses the Python standard library, so there is nothing to install after activating the environment.
3. **Run the automated tests:**
   ```bash
   pytest
   ```

## Command Line Usage

The CLI emulates a subset of Stata's commands. Launch it with:

```bash
python main.py
```

A session looks like this:

```
. use "examples/auto_small.csv"
. describe
. summarize price mpg
. generate lprice = log(price)
. regress price mpg weight
. keep if foreign == 1
. save "examples/auto_filtered.csv"
. exit
```

* `use` loads a CSV file into the in-memory `DataSet` (the loader automatically infers column types).
* `describe` reports N, mean, SD, and range information for every variable.
* `summarize` supports optional variable lists and analytic weights.
* `generate` evaluates arithmetic expressions per observation, producing new variables.
* `regress` fits an ordinary least squares model with hand-written matrix algebra.
* `keep if`/`drop if` commands filter observations using the expression parser.
* `save` writes the current dataset back to CSV.

Any errors during command execution are caught and rendered as friendly messages so the session can continue.

## Programmatic Usage

You can also import the core pieces inside Python scripts:

```python
from core.dataset import DataSet
from io_utils.reader import read_csv
from ops.crud import generate, replace
from stats.descriptives import describe

# Load a dataset
with open("examples/auto_small.csv", "r", encoding="utf-8") as fh:
    ds = read_csv(fh)

# Create a new variable
generate(ds, "lprice", "log(price)")

# Replace values with a condition
replace(ds, "mpg", "mpg + 5", filter_expr="foreign == 1")

# Compute descriptive statistics
summary = describe(ds)
print(summary["price"]["mean"])
```

`DataSet` exposes Pythonic helpers (`ds["price"]`, slicing, adding/dropping variables, etc.), so you can extend the examples above in scripts or notebooks.

## GUI Browser

The optional Tkinter GUI provides a lightweight dataset browser:

```bash
python gui.py examples/auto_small.csv
```

You can sort columns, filter rows, and trigger summarize/regress actions through buttons. The GUI writes any modifications back to disk when you choose **Save**.

## Example Data

The repository includes `examples/auto_small.csv`, a small subset of the classic automobile dataset. Feel free to replace it with your own CSV files. Saved results from the CLI or GUI will default to CSV as well, so you can keep them alongside the original file.

## Troubleshooting

* **CSV parsing errors:** ensure the first row contains column headers and that the file is UTF-8 encoded.
* **Undo stack limit reached:** the built-in undo stack supports up to two consecutive undo operations; further changes will overwrite the oldest snapshot.
* **Performance considerations:** the implementation favours readability over raw speed. Large files (≥1M rows) may take a few seconds to load or transform, but no external dependencies are required.

## Running Tests

Execute the test suite with:

```bash
pytest
```

The tests cover dataset manipulations, expression evaluation, and statistical routines.
