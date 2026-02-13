"""
Main application window for Mac Cleanup Tool.

Modern dashboard-style UI built with CustomTkinter.
Grid-based responsive layout with card components.
"""

import logging
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from core.delete import delete_items, empty_trash
from core.models import ScanCategory, ScanResult, ScanSettings
from core.scanner import Scanner
from core.utils import export_to_csv, format_size
from ui.confirm_dialog import ConfirmDeleteDialog, ConfirmTrashDialog
from ui.results_table import ResultsTable
from ui.settings_dialog import SettingsDialog

logger = logging.getLogger("mac_cleanup")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AppWindow(ctk.CTk):
    """Main application window with modern dashboard layout."""

    def __init__(self):
        super().__init__()

        self.title("Mac Cleanup Tool")
        self.geometry("1250x780")
        self.minsize(1000, 650)

        self.settings = ScanSettings()
        self.scan_result: Optional[ScanResult] = None
        self._scanner: Optional[Scanner] = None
        self._scan_thread: Optional[threading.Thread] = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._style_treeview()
        self._build_sidebar()
        self._build_header()
        self._build_main_content()
        self._build_footer()
        self._update_dry_run_indicator()

    def _style_treeview(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#1d1e1e",
            foreground="#dce4ee",
            fieldbackground="#1d1e1e",
            borderwidth=0,
            font=("Helvetica", 12),
            rowheight=32,
        )
        style.configure(
            "Treeview.Heading",
            background="#2a2d2e",
            foreground="#8b949e",
            borderwidth=0,
            font=("Helvetica", 11, "bold"),
            relief="flat",
            padding=(8, 6),
        )
        style.map(
            "Treeview",
            background=[("selected", "#1f6aa5")],
            foreground=[("selected", "white")],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", "#343a40")],
        )
        style.configure("TScrollbar", background="#2a2d2e", troughcolor="#1d1e1e", borderwidth=0)

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1a1b1e")
        sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")
        sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(24, 4))

        ctk.CTkLabel(
            logo_frame,
            text="\U0001f9f9",
            font=ctk.CTkFont(size=28),
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Mac Cleanup",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff",
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            logo_frame,
            text="Disk Space Manager",
            font=ctk.CTkFont(size=11),
            text_color="#6b7280",
        ).pack(anchor="w")

        sep = ctk.CTkFrame(sidebar, height=1, fg_color="#2d2f33")
        sep.pack(fill="x", padx=16, pady=(16, 16))

        scan_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        scan_section.pack(fill="x", padx=16)

        ctk.CTkLabel(
            scan_section,
            text="SCAN TARGETS",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#6b7280",
        ).pack(anchor="w", pady=(0, 10))

        self.scan_large_var = ctk.BooleanVar(value=True)
        self.scan_cache_var = ctk.BooleanVar(value=True)
        self.scan_downloads_var = ctk.BooleanVar(value=True)
        self.scan_logs_var = ctk.BooleanVar(value=True)
        self.scan_trash_var = ctk.BooleanVar(value=True)

        checks = [
            ("\U0001f4c1  Large Files", self.scan_large_var),
            ("\U0001f5c4\ufe0f  Caches", self.scan_cache_var),
            ("\u2b07\ufe0f  Old Downloads", self.scan_downloads_var),
            ("\U0001f4c4  Log Files", self.scan_logs_var),
            ("\U0001f5d1\ufe0f  Trash", self.scan_trash_var),
        ]
        for text, var in checks:
            ctk.CTkCheckBox(
                scan_section, text=text, variable=var,
                font=ctk.CTkFont(size=13),
                corner_radius=6, border_width=2,
                checkbox_width=22, checkbox_height=22,
                fg_color="#3b82f6", hover_color="#2563eb",
            ).pack(anchor="w", pady=4)

        sep2 = ctk.CTkFrame(sidebar, height=1, fg_color="#2d2f33")
        sep2.pack(fill="x", padx=16, pady=(16, 16))

        sel_section = ctk.CTkFrame(sidebar, fg_color="transparent")
        sel_section.pack(fill="x", padx=16)

        ctk.CTkLabel(
            sel_section,
            text="QUICK SELECT",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#6b7280",
        ).pack(anchor="w", pady=(0, 8))

        btn_grid = ctk.CTkFrame(sel_section, fg_color="transparent")
        btn_grid.pack(fill="x")

        ctk.CTkButton(
            btn_grid, text="Select All",
            command=lambda: self.results_table.select_all(True),
            height=30, corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="#2d2f33", hover_color="#3d3f43",
            text_color="#c9d1d9",
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            btn_grid, text="Deselect All",
            command=lambda: self.results_table.select_all(False),
            height=30, corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="#2d2f33", hover_color="#3d3f43",
            text_color="#c9d1d9",
        ).pack(fill="x", pady=2)

        for cat in ScanCategory:
            ctk.CTkButton(
                btn_grid,
                text=f"All {cat.value}",
                command=lambda c=cat: self.results_table.select_all_category(c, True),
                height=28, corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color="transparent", hover_color="#2d2f33",
                text_color="#8b949e",
                anchor="w",
            ).pack(fill="x", pady=1)

        sep3 = ctk.CTkFrame(sidebar, height=1, fg_color="#2d2f33")
        sep3.pack(fill="x", padx=16, pady=(16, 16))

        ctk.CTkButton(
            sidebar, text="\U0001f4c2  Add Folder...",
            command=self._add_custom_folder,
            height=32, corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="#2d2f33", hover_color="#3d3f43",
            text_color="#c9d1d9",
        ).pack(fill="x", padx=16, pady=(0, 4))

        self.custom_folders_label = ctk.CTkLabel(
            sidebar,
            text="0 custom folders",
            font=ctk.CTkFont(size=11),
            text_color="#6b7280",
        )
        self.custom_folders_label.pack(anchor="w", padx=20)

        bottom_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=16, pady=16)

        ctk.CTkButton(
            bottom_frame, text="\u2699\ufe0f  Settings",
            command=self._open_settings,
            height=36, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color="transparent", hover_color="#2d2f33",
            text_color="#8b949e",
            anchor="w",
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            bottom_frame, text="\u2753  Help",
            command=self._show_help,
            height=36, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color="transparent", hover_color="#2d2f33",
            text_color="#8b949e",
            anchor="w",
        ).pack(fill="x", pady=2)

    def _build_header(self):
        header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=1, sticky="new", padx=24, pady=(16, 0))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", fill="y")

        ctk.CTkLabel(
            left,
            text="Dashboard",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#ffffff",
        ).pack(anchor="w")

        self.summary_label = ctk.CTkLabel(
            left,
            text="Ready to scan. Select targets and click Scan.",
            font=ctk.CTkFont(size=13),
            text_color="#6b7280",
        )
        self.summary_label.pack(anchor="w", pady=(2, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", fill="y")

        self.dry_run_badge = ctk.CTkLabel(
            right,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=6,
            width=120, height=28,
        )
        self.dry_run_badge.pack(side="right", pady=12)

    def _build_main_content(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=1, sticky="nsew", padx=24, pady=(12, 0))
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        stats_frame = ctk.CTkFrame(main, fg_color="transparent", height=90)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_items = self._make_stat_card(stats_frame, 0, "Items Found", "0", "#3b82f6")
        self.stat_size = self._make_stat_card(stats_frame, 1, "Reclaimable", "0 B", "#10b981")
        self.stat_selected = self._make_stat_card(stats_frame, 2, "Selected", "0", "#f59e0b")
        self.stat_duration = self._make_stat_card(stats_frame, 3, "Scan Time", "--", "#8b5cf6")

        table_card = ctk.CTkFrame(main, corner_radius=10, fg_color="#1a1b1e")
        table_card.grid(row=1, column=0, sticky="nsew")

        table_header = ctk.CTkFrame(table_card, fg_color="transparent", height=44)
        table_header.pack(fill="x", padx=16, pady=(12, 0))

        ctk.CTkLabel(
            table_header,
            text="Scan Results",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e5e7eb",
        ).pack(side="left")

        table_actions = ctk.CTkFrame(table_header, fg_color="transparent")
        table_actions.pack(side="right")

        ctk.CTkButton(
            table_actions, text="Export CSV",
            command=self._export_csv,
            width=90, height=30, corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color="#2d2f33", hover_color="#3d3f43",
            text_color="#c9d1d9",
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            table_actions, text="Open Folder",
            command=self._open_folder,
            width=95, height=30, corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color="#2d2f33", hover_color="#3d3f43",
            text_color="#c9d1d9",
        ).pack(side="left", padx=4)

        self.results_table = ResultsTable(table_card)
        self.results_table.pack(fill="both", expand=True, padx=8, pady=(8, 8))

    def _make_stat_card(self, parent, col, title, value, color):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1a1b1e", height=80)
        card.grid(row=0, column=col, sticky="nsew", padx=4)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            inner,
            text=title.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#6b7280",
        ).pack(anchor="w")

        val_label = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=color,
        )
        val_label.pack(anchor="w", pady=(2, 0))

        return val_label

    def _build_footer(self):
        footer = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color="#1a1b1e")
        footer.grid(row=2, column=1, sticky="sew", padx=24, pady=(8, 16))
        footer.pack_propagate(False)

        inner = ctk.CTkFrame(footer, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=10)

        left_btns = ctk.CTkFrame(inner, fg_color="transparent")
        left_btns.pack(side="left")

        self.scan_btn = ctk.CTkButton(
            left_btns, text="\u25b6  Scan",
            command=self._start_scan,
            width=120, height=40, corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3b82f6", hover_color="#2563eb",
        )
        self.scan_btn.pack(side="left", padx=(0, 8))

        self.cancel_btn = ctk.CTkButton(
            left_btns, text="Cancel",
            command=self._cancel_scan,
            width=80, height=40, corner_radius=10,
            font=ctk.CTkFont(size=13),
            fg_color="#2d2f33", hover_color="#3d3f43",
            text_color="#8b949e",
            state="disabled",
        )
        self.cancel_btn.pack(side="left", padx=(0, 16))

        self.delete_btn = ctk.CTkButton(
            left_btns, text="\U0001f5d1  Delete Selected",
            command=self._delete_selected,
            width=150, height=40, corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c",
        )
        self.delete_btn.pack(side="left", padx=(0, 8))

        self.trash_btn = ctk.CTkButton(
            left_btns, text="Empty Trash",
            command=self._empty_trash,
            width=110, height=40, corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c",
        )
        self.trash_btn.pack(side="left")

        right_progress = ctk.CTkFrame(inner, fg_color="transparent")
        right_progress.pack(side="right", fill="y")

        self.progress_label = ctk.CTkLabel(
            right_progress, text="",
            font=ctk.CTkFont(size=11),
            text_color="#6b7280",
        )
        self.progress_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            right_progress, mode="indeterminate",
            width=200, height=4, corner_radius=2,
            progress_color="#3b82f6",
        )
        self.progress_bar.pack(side="right", padx=(0, 10), pady=14)
        self.progress_bar.set(0)

    def _update_dry_run_indicator(self):
        if self.settings.dry_run:
            self.dry_run_badge.configure(
                text=" DRY RUN ",
                text_color="#f59e0b",
                fg_color="#422006",
            )
        else:
            self.dry_run_badge.configure(
                text=" LIVE ",
                text_color="#ef4444",
                fg_color="#450a0a",
            )

    def _update_stats(self):
        if self.scan_result:
            self.stat_items.configure(text=str(self.scan_result.item_count))
            self.stat_size.configure(text=self.scan_result.total_size_human)
            self.stat_duration.configure(text=f"{self.scan_result.scan_duration_seconds:.1f}s")
        selected = self.results_table.get_selected_items()
        self.stat_selected.configure(text=str(len(selected)))

    def _add_custom_folder(self):
        folder = filedialog.askdirectory(title="Select folder to scan")
        if folder:
            path = Path(folder)
            from core.rules import is_path_blocked
            if is_path_blocked(path):
                messagebox.showwarning(
                    "Blocked Path",
                    f"This path is blocked by safety rules:\n{path}\n\n"
                    "System directories cannot be scanned.",
                )
                return
            if path not in self.settings.custom_scan_folders:
                self.settings.custom_scan_folders.append(path)
                self.custom_folders_label.configure(
                    text=f"{len(self.settings.custom_scan_folders)} custom folder(s)"
                )

    def _start_scan(self):
        self.settings.scan_large_files = self.scan_large_var.get()
        self.settings.scan_caches = self.scan_cache_var.get()
        self.settings.scan_downloads = self.scan_downloads_var.get()
        self.settings.scan_logs = self.scan_logs_var.get()
        self.settings.scan_trash = self.scan_trash_var.get()

        self.scan_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.delete_btn.configure(state="disabled")
        self.progress_bar.start()
        self.summary_label.configure(text="Scanning your system...", text_color="#3b82f6")

        self._scanner = Scanner(self.settings)
        self._scanner.set_progress_callback(self._on_scan_progress)

        self._scan_thread = threading.Thread(target=self._run_scan, daemon=True)
        self._scan_thread.start()

    def _run_scan(self):
        result = self._scanner.scan()
        self.after(0, self._on_scan_complete, result)

    def _on_scan_progress(self, current_path: str, items_found: int):
        short_path = current_path
        if len(short_path) > 40:
            short_path = "..." + short_path[-37:]
        self.after(
            0,
            lambda: self.progress_label.configure(
                text=f"{items_found} items  \u2022  {short_path}"
            ),
        )

    def _on_scan_complete(self, result: ScanResult):
        self.scan_result = result
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.scan_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.delete_btn.configure(state="normal")
        self.progress_label.configure(text="")

        self.results_table.populate(result.items)
        self._update_stats()

        status = "Cancelled" if result.was_cancelled else "Complete"
        color = "#10b981" if not result.was_cancelled else "#f59e0b"
        self.summary_label.configure(
            text=f"Scan {status} \u2014 {result.item_count} items found, "
            f"{result.total_size_human} reclaimable",
            text_color=color,
        )

        if result.errors:
            logger.warning(f"Scan had {len(result.errors)} errors")

    def _cancel_scan(self):
        if self._scanner:
            self._scanner.cancel()
            self.cancel_btn.configure(state="disabled")
            self.summary_label.configure(text="Cancelling scan...", text_color="#f59e0b")

    def _delete_selected(self):
        selected = self.results_table.get_selected_items()
        if not selected:
            messagebox.showinfo("No Selection", "No items selected for deletion.")
            return

        selected = [item for item in selected if item.category != ScanCategory.TRASH]
        if not selected:
            messagebox.showinfo(
                "Trash Items",
                "Trash items cannot be deleted here.\nUse 'Empty Trash' instead.",
            )
            return

        total_size = sum(item.size_bytes for item in selected)

        dialog = ConfirmDeleteDialog(
            self,
            file_count=len(selected),
            total_size=format_size(total_size),
            dry_run=self.settings.dry_run,
        )

        if not dialog.result:
            return

        results = delete_items(
            selected,
            allow_personal=self.settings.allow_personal_docs,
            dry_run=self.settings.dry_run,
        )

        success_count = sum(1 for _, ok, _ in results if ok)
        fail_count = sum(1 for _, ok, _ in results if not ok)

        for item, _, _ in results:
            self.results_table.update_item_status(item)

        msg = f"Processed {len(results)} items: {success_count} succeeded"
        if fail_count:
            msg += f", {fail_count} failed"
        if self.settings.dry_run:
            msg += " (dry run - no actual changes)"

        messagebox.showinfo("Deletion Complete", msg)
        self._update_stats()

    def _empty_trash(self):
        from core.rules import TRASH_PATH
        from core.utils import get_directory_size

        if not TRASH_PATH.exists():
            messagebox.showinfo("Trash", "Trash is already empty.")
            return

        trash_size = get_directory_size(TRASH_PATH)
        if trash_size == 0:
            messagebox.showinfo("Trash", "Trash is already empty.")
            return

        dialog = ConfirmTrashDialog(self, format_size(trash_size))
        if not dialog.result:
            return

        success, message = empty_trash()
        if success:
            messagebox.showinfo("Trash Emptied", message)
        else:
            messagebox.showerror("Error", message)

    def _export_csv(self):
        items = self.results_table.get_all_items()
        if not items:
            messagebox.showinfo("No Data", "No scan results to export.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="mac_cleanup_report.csv",
        )

        if output_path:
            try:
                export_to_csv(items, Path(output_path))
                messagebox.showinfo("Export Complete", f"Report saved to:\n{output_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {e}")

    def _open_folder(self):
        selected = self.results_table.get_selected_items()
        if not selected:
            messagebox.showinfo("No Selection", "Select an item to open its folder.")
            return

        item = selected[0]
        folder = item.path.parent if item.path.is_file() else item.path

        try:
            if sys.platform == "darwin":
                subprocess.run(["open", str(folder)], check=True)
            elif sys.platform == "linux":
                subprocess.run(["xdg-open", str(folder)], check=True)
            else:
                os.startfile(str(folder))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def _open_settings(self):
        dialog = SettingsDialog(self, self.settings)
        if dialog.result:
            self.settings = dialog.result
            self._update_dry_run_indicator()

    def _show_help(self):
        help_text = (
            "Mac Cleanup Tool\n"
            "=================\n\n"
            "Safely find and reclaim disk space on your Mac.\n\n"
            "SAFETY:\n"
            "  - System files are NEVER touched\n"
            "  - Personal folders excluded by default\n"
            "  - Dry Run mode ON by default\n"
            "  - All deletions go to Trash\n"
            "  - Type 'DELETE' to confirm\n\n"
            "HOW TO USE:\n"
            "  1. Select scan types in sidebar\n"
            "  2. Click Scan\n"
            "  3. Review results\n"
            "  4. Select items to remove\n"
            "  5. Click Delete Selected\n\n"
            "SCAN TYPES:\n"
            "  - Large Files (default >1 GB)\n"
            "  - Caches (>30 days old)\n"
            "  - Old Downloads (>90 days)\n"
            "  - Log Files\n"
            "  - Trash Report\n\n"
            "SETTINGS:\n"
            "  Adjust thresholds, Dry Run, and\n"
            "  personal folder access."
        )
        messagebox.showinfo("Help", help_text)

    def run(self):
        """Start the main loop."""
        self.mainloop()
