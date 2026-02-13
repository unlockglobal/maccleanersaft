"""
Main application window for Mac Cleanup Tool.

Modern UI built with CustomTkinter for a native, polished look.
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


class AppWindow:
    """Main application window with CustomTkinter UI."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Mac Cleanup Tool")
        self.root.geometry("1200x750")
        self.root.minsize(950, 600)

        self.settings = ScanSettings()
        self.scan_result: Optional[ScanResult] = None
        self._scanner: Optional[Scanner] = None
        self._scan_thread: Optional[threading.Thread] = None

        self._style_treeview()
        self._build_ui()
        self._update_dry_run_indicator()

    def _style_treeview(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="#dce4ee",
            fieldbackground="#2b2b2b",
            borderwidth=0,
            font=("Helvetica", 12),
            rowheight=30,
        )
        style.configure(
            "Treeview.Heading",
            background="#333333",
            foreground="#aab0ba",
            borderwidth=0,
            font=("Helvetica", 11, "bold"),
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", "#1f6aa5")],
            foreground=[("selected", "white")],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", "#404040")],
        )
        style.configure(
            "TScrollbar",
            background="#333333",
            troughcolor="#2b2b2b",
            borderwidth=0,
        )

    def _build_ui(self):
        header = ctk.CTkFrame(self.root, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 0))

        title_area = ctk.CTkFrame(header, fg_color="transparent")
        title_area.pack(side="left")

        ctk.CTkLabel(
            title_area,
            text="Mac Cleanup Tool",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_area,
            text="Safely reclaim disk space on your Mac",
            font=ctk.CTkFont(size=13),
            text_color=("gray60", "gray60"),
        ).pack(anchor="w")

        self.dry_run_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.dry_run_label.pack(side="right", pady=8)

        summary_card = ctk.CTkFrame(self.root, corner_radius=8, height=40)
        summary_card.pack(fill="x", padx=20, pady=(12, 0))
        summary_card.pack_propagate(False)

        self.summary_label = ctk.CTkLabel(
            summary_card,
            text="  Ready to scan. Select options and click Scan to begin.",
            font=ctk.CTkFont(size=13),
            text_color=("gray60", "gray60"),
            anchor="w",
        )
        self.summary_label.pack(side="left", fill="y", padx=10)

        content = ctk.CTkFrame(self.root, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(12, 0))

        sidebar = ctk.CTkFrame(content, width=190, corner_radius=10)
        sidebar.pack(side="left", fill="y", padx=(0, 12))
        sidebar.pack_propagate(False)

        inner_sidebar = ctk.CTkFrame(sidebar, fg_color="transparent")
        inner_sidebar.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(
            inner_sidebar,
            text="SCAN OPTIONS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray50", "gray50"),
        ).pack(anchor="w", pady=(0, 8))

        self.scan_large_var = ctk.BooleanVar(value=True)
        self.scan_cache_var = ctk.BooleanVar(value=True)
        self.scan_downloads_var = ctk.BooleanVar(value=True)
        self.scan_logs_var = ctk.BooleanVar(value=True)
        self.scan_trash_var = ctk.BooleanVar(value=True)

        checks = [
            ("Large Files", self.scan_large_var),
            ("Caches", self.scan_cache_var),
            ("Old Downloads", self.scan_downloads_var),
            ("Log Files", self.scan_logs_var),
            ("Trash Report", self.scan_trash_var),
        ]
        for text, var in checks:
            ctk.CTkCheckBox(
                inner_sidebar, text=text, variable=var,
                font=ctk.CTkFont(size=13),
                corner_radius=4, border_width=2,
                checkbox_width=20, checkbox_height=20,
            ).pack(anchor="w", pady=3)

        self._add_separator(inner_sidebar)

        ctk.CTkLabel(
            inner_sidebar,
            text="SELECT BY CATEGORY",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray50", "gray50"),
        ).pack(anchor="w", pady=(0, 6))

        for cat in ScanCategory:
            ctk.CTkButton(
                inner_sidebar,
                text=f"All {cat.value}",
                command=lambda c=cat: self.results_table.select_all_category(c, True),
                height=28, corner_radius=6,
                font=ctk.CTkFont(size=12),
                fg_color=("gray30", "gray30"),
                hover_color=("gray40", "gray40"),
            ).pack(fill="x", pady=2)

        self._add_separator(inner_sidebar)

        ctk.CTkButton(
            inner_sidebar, text="Select All",
            command=lambda: self.results_table.select_all(True),
            height=28, corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
        ).pack(fill="x", pady=2)

        ctk.CTkButton(
            inner_sidebar, text="Deselect All",
            command=lambda: self.results_table.select_all(False),
            height=28, corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
        ).pack(fill="x", pady=2)

        self._add_separator(inner_sidebar)

        ctk.CTkButton(
            inner_sidebar, text="Add Folder...",
            command=self._add_custom_folder,
            height=28, corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
        ).pack(fill="x", pady=2)

        self.custom_folders_label = ctk.CTkLabel(
            inner_sidebar,
            text="Custom folders: 0",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50"),
        )
        self.custom_folders_label.pack(anchor="w", pady=(6, 0))

        results_area = ctk.CTkFrame(content, fg_color="transparent")
        results_area.pack(side="left", fill="both", expand=True)

        self.results_table = ResultsTable(results_area)
        self.results_table.pack(fill="both", expand=True)

        bottom_area = ctk.CTkFrame(self.root, fg_color="transparent")
        bottom_area.pack(fill="x", padx=20, pady=(8, 0))

        progress_frame = ctk.CTkFrame(bottom_area, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(0, 6))

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame, mode="indeterminate", height=6, corner_radius=3,
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_frame, text="",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray50"),
        )
        self.progress_label.pack(side="left")

        btn_bar = ctk.CTkFrame(self.root, corner_radius=10, height=56)
        btn_bar.pack(fill="x", padx=20, pady=(0, 15))
        btn_bar.pack_propagate(False)

        btn_inner = ctk.CTkFrame(btn_bar, fg_color="transparent")
        btn_inner.pack(fill="both", expand=True, padx=10, pady=8)

        self.scan_btn = ctk.CTkButton(
            btn_inner, text="Scan", command=self._start_scan,
            width=100, height=36, corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.scan_btn.pack(side="left", padx=(0, 6))

        self.cancel_btn = ctk.CTkButton(
            btn_inner, text="Cancel", command=self._cancel_scan,
            width=80, height=36, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
            state="disabled",
        )
        self.cancel_btn.pack(side="left", padx=(0, 6))

        self.delete_btn = ctk.CTkButton(
            btn_inner, text="Delete Selected", command=self._delete_selected,
            width=130, height=36, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#e55a5a", hover_color="#cc4444",
        )
        self.delete_btn.pack(side="left", padx=(0, 6))

        self.trash_btn = ctk.CTkButton(
            btn_inner, text="Empty Trash", command=self._empty_trash,
            width=110, height=36, corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#e55a5a", hover_color="#cc4444",
        )
        self.trash_btn.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_inner, text="Export CSV", command=self._export_csv,
            width=100, height=36, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_inner, text="Open Folder", command=self._open_folder,
            width=100, height=36, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_inner, text="Settings", command=self._open_settings,
            width=80, height=36, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_inner, text="Help", command=self._show_help,
            width=60, height=36, corner_radius=8,
            font=ctk.CTkFont(size=13),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
        ).pack(side="right", padx=(6, 0))

    def _add_separator(self, parent):
        sep = ctk.CTkFrame(parent, height=1, fg_color=("gray35", "gray35"))
        sep.pack(fill="x", pady=10)

    def _update_dry_run_indicator(self):
        if self.settings.dry_run:
            self.dry_run_label.configure(
                text="DRY RUN MODE",
                text_color="#ffa94d",
            )
        else:
            self.dry_run_label.configure(
                text="LIVE MODE",
                text_color="#ff6b6b",
            )

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
                    text=f"Custom folders: {len(self.settings.custom_scan_folders)}"
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
        self.summary_label.configure(text="  Scanning...", text_color="#3b8ed0")

        self._scanner = Scanner(self.settings)
        self._scanner.set_progress_callback(self._on_scan_progress)

        self._scan_thread = threading.Thread(target=self._run_scan, daemon=True)
        self._scan_thread.start()

    def _run_scan(self):
        result = self._scanner.scan()
        self.root.after(0, self._on_scan_complete, result)

    def _on_scan_progress(self, current_path: str, items_found: int):
        short_path = current_path
        if len(short_path) > 50:
            short_path = "..." + short_path[-47:]
        self.root.after(
            0,
            lambda: self.progress_label.configure(
                text=f"Found {items_found} items  |  {short_path}"
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

        status = "Cancelled" if result.was_cancelled else "Complete"
        color = "#4ecdc4" if not result.was_cancelled else "#ffa94d"
        self.summary_label.configure(
            text=f"  Scan {status}:  {result.item_count} items  |  "
            f"Reclaimable: {result.total_size_human}  |  "
            f"Duration: {result.scan_duration_seconds:.1f}s",
            text_color=color,
        )

        if result.errors:
            logger.warning(f"Scan had {len(result.errors)} errors")

    def _cancel_scan(self):
        if self._scanner:
            self._scanner.cancel()
            self.cancel_btn.configure(state="disabled")
            self.summary_label.configure(text="  Cancelling scan...", text_color="#ffa94d")

    def _delete_selected(self):
        selected = self.results_table.get_selected_items()
        if not selected:
            messagebox.showinfo("No Selection", "No items selected for deletion.")
            return

        selected = [
            item for item in selected
            if item.category != ScanCategory.TRASH
        ]
        if not selected:
            messagebox.showinfo(
                "Trash Items",
                "Trash items cannot be deleted here.\n"
                "Use the 'Empty Trash' button instead.",
            )
            return

        total_size = sum(item.size_bytes for item in selected)

        dialog = ConfirmDeleteDialog(
            self.root,
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

        dialog = ConfirmTrashDialog(self.root, format_size(trash_size))
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
        dialog = SettingsDialog(self.root, self.settings)
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
        self.root.mainloop()
