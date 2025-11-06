"""Tkinter based browser for the in-memory dataset."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.dataset import DataSet
from io_utils.reader import read_csv


class DataBrowser(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stata-like Data Browser")
        self.geometry("800x600")
        self.dataset: DataSet | None = None
        self._build_widgets()

    def _build_widgets(self) -> None:
        toolbar = tk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        open_btn = tk.Button(toolbar, text="Open CSV", command=self._open_file)
        open_btn.pack(side=tk.LEFT, padx=4, pady=4)

        refresh_btn = tk.Button(toolbar, text="Refresh", command=self._refresh)
        refresh_btn.pack(side=tk.LEFT, padx=4, pady=4)

        undo_btn = tk.Button(toolbar, text="Undo", command=self._undo)
        undo_btn.pack(side=tk.LEFT, padx=4, pady=4)

        self.tree = ttk.Treeview(self, columns=(), show="headings")
        self.tree.pack(expand=True, fill=tk.BOTH)

        scrollbar_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar_y.set)

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(title="Open CSV", filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        try:
            self.dataset = read_csv(path)
            self._refresh()
        except Exception as exc:  # noqa: BLE001 - user feedback
            messagebox.showerror("Error", str(exc))

    def _refresh(self) -> None:
        if self.dataset is None:
            return
        self.tree.delete(*self.tree.get_children())
        columns = self.dataset.variables
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.W)
        for row in self.dataset.to_rows():
            self.tree.insert("", tk.END, values=[row[col] for col in columns])

    def _undo(self) -> None:
        if self.dataset and self.dataset.undo():
            self._refresh()


def run_gui() -> None:
    app = DataBrowser()
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover - manual GUI entry
    run_gui()
