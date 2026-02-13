"""
Results table widget for Mac Cleanup Tool.

Displays scan results in a sortable Treeview with checkboxes
for selecting items for deletion.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

from core.models import ScanCategory, ScanItem
from core.utils import format_size, format_timestamp


class ResultsTable(ttk.Frame):
    """
    Treeview-based results table with per-item selection,
    category-based Select All, and sortable columns.
    """

    COLUMNS = ("selected", "category", "size", "last_modified", "path", "action", "status")
    HEADERS = ("Sel", "Category", "Size", "Last Modified", "Path", "Recommended Action", "Status")
    WIDTHS = (40, 100, 90, 130, 350, 200, 80)

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self._items: Dict[str, ScanItem] = {}
        self._selected: Dict[str, tk.BooleanVar] = {}
        self._setup_ui()

    def _setup_ui(self):
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.COLUMNS,
            show="headings",
            selectmode="extended",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)

        for col, header, width in zip(self.COLUMNS, self.HEADERS, self.WIDTHS):
            self.tree.heading(col, text=header, command=lambda c=col: self._sort_by(c))
            anchor = tk.CENTER if col in ("selected", "status") else tk.W
            self.tree.column(col, width=width, anchor=anchor, minwidth=40)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.bind("<ButtonRelease-1>", self._on_click)

        self._sort_reverse: Dict[str, bool] = {col: False for col in self.COLUMNS}

    def clear(self):
        """Remove all items from the table."""
        self.tree.delete(*self.tree.get_children())
        self._items.clear()
        self._selected.clear()

    def populate(self, items: List[ScanItem]):
        """Fill the table with scan results."""
        self.clear()
        for i, item in enumerate(items):
            iid = f"item_{i}"
            self._items[iid] = item
            self._selected[iid] = tk.BooleanVar(value=False)

            values = (
                "[ ]",
                item.category.value,
                item.size_human,
                format_timestamp(item.last_modified),
                str(item.path),
                item.recommended_action,
                item.status.value,
            )
            self.tree.insert("", tk.END, iid=iid, values=values)

    def _on_click(self, event):
        """Toggle selection checkbox when the 'Sel' column is clicked."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        col = self.tree.identify_column(event.x)
        if col != "#1":
            return

        iid = self.tree.identify_row(event.y)
        if not iid or iid not in self._selected:
            return

        var = self._selected[iid]
        var.set(not var.get())

        current = list(self.tree.item(iid, "values"))
        current[0] = "[X]" if var.get() else "[ ]"
        self.tree.item(iid, values=current)

    def select_all_category(self, category: ScanCategory, select: bool = True):
        """Select or deselect all items in a given category."""
        for iid, item in self._items.items():
            if item.category == category:
                self._selected[iid].set(select)
                current = list(self.tree.item(iid, "values"))
                current[0] = "[X]" if select else "[ ]"
                self.tree.item(iid, values=current)

    def select_all(self, select: bool = True):
        """Select or deselect all items."""
        for iid in self._items:
            self._selected[iid].set(select)
            current = list(self.tree.item(iid, "values"))
            current[0] = "[X]" if select else "[ ]"
            self.tree.item(iid, values=current)

    def get_selected_items(self) -> List[ScanItem]:
        """Return list of currently selected ScanItem objects."""
        return [
            self._items[iid]
            for iid, var in self._selected.items()
            if var.get()
        ]

    def update_item_status(self, item: ScanItem):
        """Update the status column for a specific item after deletion."""
        for iid, stored_item in self._items.items():
            if stored_item is item:
                current = list(self.tree.item(iid, "values"))
                current[6] = item.status.value
                self.tree.item(iid, values=current)
                break

    def _sort_by(self, column: str):
        """Sort the table by a given column."""
        col_index = self.COLUMNS.index(column)
        data = []
        for iid in self.tree.get_children():
            val = self.tree.item(iid, "values")[col_index]
            data.append((val, iid))

        reverse = self._sort_reverse[column]
        self._sort_reverse[column] = not reverse

        if column == "size":
            def size_key(x):
                item = self._items.get(x[1])
                return item.size_bytes if item else 0
            data.sort(key=size_key, reverse=reverse)
        else:
            data.sort(key=lambda x: x[0].lower() if isinstance(x[0], str) else x[0], reverse=reverse)

        for index, (_, iid) in enumerate(data):
            self.tree.move(iid, "", index)

    def get_all_items(self) -> List[ScanItem]:
        """Return all items in the table."""
        return list(self._items.values())
