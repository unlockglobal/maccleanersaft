"""
Main application window for Mac Cleanup Tool.

Modern dark-themed GUI with sidebar navigation, results table,
summary panel, progress indicators, and action buttons.
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

from core.delete import delete_items, empty_trash
from core.models import ScanCategory, ScanResult, ScanSettings
from core.scanner import Scanner
from core.utils import export_to_csv, format_size
from ui.confirm_dialog import ConfirmDeleteDialog, ConfirmTrashDialog
from ui.results_table import ResultsTable
from ui.settings_dialog import SettingsDialog

logger = logging.getLogger("mac_cleanup")

COLORS = {
    "bg_dark": "#1a1b2e",
    "bg_sidebar": "#222340",
    "bg_card": "#2a2b4a",
    "bg_input": "#33345a",
    "bg_table": "#1e1f38",
    "bg_row_alt": "#252647",
    "bg_hover": "#3a3b6a",
    "text_primary": "#e8e8f0",
    "text_secondary": "#9d9db5",
    "text_muted": "#6b6b85",
    "accent_blue": "#5b8def",
    "accent_green": "#4ecdc4",
    "accent_red": "#ff6b6b",
    "accent_orange": "#ffa94d",
    "accent_purple": "#9775fa",
    "border": "#3a3b5a",
    "btn_primary": "#5b8def",
    "btn_primary_hover": "#4a7de0",
    "btn_danger": "#ff6b6b",
    "btn_danger_hover": "#e55a5a",
    "btn_secondary": "#3a3b5a",
    "btn_secondary_hover": "#4a4b6a",
    "progress_bg": "#33345a",
    "progress_bar": "#5b8def",
}


class AppWindow:
    """Main application window with modern dark theme."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mac Cleanup Tool")
        self.root.geometry("1200x750")
        self.root.minsize(950, 600)
        self.root.configure(bg=COLORS["bg_dark"])

        self.settings = ScanSettings()
        self.scan_result: Optional[ScanResult] = None
        self._scanner: Optional[Scanner] = None
        self._scan_thread: Optional[threading.Thread] = None

        self._setup_styles()
        self._build_ui()
        self._update_dry_run_indicator()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=COLORS["bg_dark"], foreground=COLORS["text_primary"])
        style.configure("TFrame", background=COLORS["bg_dark"])
        style.configure("Sidebar.TFrame", background=COLORS["bg_sidebar"])
        style.configure("Card.TFrame", background=COLORS["bg_card"])
        style.configure("ButtonBar.TFrame", background=COLORS["bg_card"])

        style.configure(
            "TLabel",
            background=COLORS["bg_dark"],
            foreground=COLORS["text_primary"],
            font=("SF Pro Display", 12),
        )
        style.configure(
            "Sidebar.TLabel",
            background=COLORS["bg_sidebar"],
            foreground=COLORS["text_primary"],
            font=("SF Pro Display", 12),
        )
        style.configure(
            "Card.TLabel",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            font=("SF Pro Display", 12),
        )
        style.configure(
            "Title.TLabel",
            background=COLORS["bg_dark"],
            foreground=COLORS["text_primary"],
            font=("SF Pro Display", 20, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLORS["bg_dark"],
            foreground=COLORS["text_secondary"],
            font=("SF Pro Display", 11),
        )
        style.configure(
            "Summary.TLabel",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            font=("SF Pro Display", 12),
        )
        style.configure(
            "DryRun.TLabel",
            background=COLORS["bg_dark"],
            foreground=COLORS["accent_orange"],
            font=("SF Pro Display", 11, "bold"),
        )
        style.configure(
            "Live.TLabel",
            background=COLORS["bg_dark"],
            foreground=COLORS["accent_red"],
            font=("SF Pro Display", 11, "bold"),
        )
        style.configure(
            "SectionHeader.TLabel",
            background=COLORS["bg_sidebar"],
            foreground=COLORS["text_muted"],
            font=("SF Pro Display", 10, "bold"),
        )

        style.configure(
            "TButton",
            background=COLORS["btn_secondary"],
            foreground=COLORS["text_primary"],
            borderwidth=0,
            focuscolor="none",
            padding=(14, 8),
            font=("SF Pro Display", 11),
        )
        style.map(
            "TButton",
            background=[("active", COLORS["btn_secondary_hover"]), ("pressed", COLORS["btn_secondary_hover"])],
        )

        style.configure(
            "Primary.TButton",
            background=COLORS["btn_primary"],
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=(18, 10),
            font=("SF Pro Display", 12, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", COLORS["btn_primary_hover"]), ("pressed", COLORS["btn_primary_hover"])],
        )

        style.configure(
            "Danger.TButton",
            background=COLORS["btn_danger"],
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=(14, 8),
            font=("SF Pro Display", 11, "bold"),
        )
        style.map(
            "Danger.TButton",
            background=[("active", COLORS["btn_danger_hover"]), ("pressed", COLORS["btn_danger_hover"])],
        )

        style.configure(
            "Sidebar.TButton",
            background=COLORS["bg_input"],
            foreground=COLORS["text_primary"],
            borderwidth=0,
            focuscolor="none",
            padding=(10, 6),
            font=("SF Pro Display", 10),
        )
        style.map(
            "Sidebar.TButton",
            background=[("active", COLORS["bg_hover"]), ("pressed", COLORS["bg_hover"])],
        )

        style.configure(
            "Action.TButton",
            background=COLORS["btn_secondary"],
            foreground=COLORS["text_primary"],
            borderwidth=0,
            focuscolor="none",
            padding=(14, 8),
            font=("SF Pro Display", 11),
        )
        style.map(
            "Action.TButton",
            background=[("active", COLORS["btn_secondary_hover"]), ("pressed", COLORS["btn_secondary_hover"])],
        )

        style.configure(
            "TCheckbutton",
            background=COLORS["bg_sidebar"],
            foreground=COLORS["text_primary"],
            focuscolor="none",
            font=("SF Pro Display", 12),
        )
        style.map(
            "TCheckbutton",
            background=[("active", COLORS["bg_sidebar"])],
        )

        style.configure(
            "TEntry",
            fieldbackground=COLORS["bg_input"],
            foreground=COLORS["text_primary"],
            insertcolor=COLORS["text_primary"],
            borderwidth=1,
            relief="flat",
        )

        style.configure(
            "TProgressbar",
            background=COLORS["progress_bar"],
            troughcolor=COLORS["progress_bg"],
            borderwidth=0,
            thickness=6,
        )

        style.configure(
            "TSeparator",
            background=COLORS["border"],
        )

        style.configure(
            "TLabelframe",
            background=COLORS["bg_sidebar"],
            foreground=COLORS["text_secondary"],
            borderwidth=0,
        )
        style.configure(
            "TLabelframe.Label",
            background=COLORS["bg_sidebar"],
            foreground=COLORS["text_muted"],
            font=("SF Pro Display", 10, "bold"),
        )

        style.configure(
            "Treeview",
            background=COLORS["bg_table"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_table"],
            borderwidth=0,
            font=("SF Mono", 11),
            rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["bg_card"],
            foreground=COLORS["text_secondary"],
            borderwidth=0,
            font=("SF Pro Display", 11, "bold"),
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["accent_blue"])],
            foreground=[("selected", "white")],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", COLORS["bg_hover"])],
        )

        style.configure(
            "TScrollbar",
            background=COLORS["bg_card"],
            troughcolor=COLORS["bg_dark"],
            borderwidth=0,
            arrowsize=0,
        )

    def _build_ui(self):
        header = tk.Frame(self.root, bg=COLORS["bg_dark"], height=60)
        header.pack(fill=tk.X, padx=20, pady=(15, 0))
        header.pack_propagate(False)

        title_area = tk.Frame(header, bg=COLORS["bg_dark"])
        title_area.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(
            title_area,
            text="Mac Cleanup Tool",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            font=("SF Pro Display", 22, "bold"),
        ).pack(anchor=tk.W)

        tk.Label(
            title_area,
            text="Safely reclaim disk space on your Mac",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            font=("SF Pro Display", 11),
        ).pack(anchor=tk.W)

        right_header = tk.Frame(header, bg=COLORS["bg_dark"])
        right_header.pack(side=tk.RIGHT, fill=tk.Y)

        self.dry_run_label = tk.Label(
            right_header,
            text="",
            bg=COLORS["bg_dark"],
            font=("SF Pro Display", 11, "bold"),
        )
        self.dry_run_label.pack(side=tk.RIGHT, pady=10)

        summary_card = tk.Frame(self.root, bg=COLORS["bg_card"], height=40)
        summary_card.pack(fill=tk.X, padx=20, pady=(12, 0))
        summary_card.pack_propagate(False)

        self.summary_label = tk.Label(
            summary_card,
            text="Ready to scan. Select options and click Scan to begin.",
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            font=("SF Pro Display", 12),
            padx=15,
        )
        self.summary_label.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        content = tk.Frame(self.root, bg=COLORS["bg_dark"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(12, 0))

        sidebar = tk.Frame(content, bg=COLORS["bg_sidebar"], width=180)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        sidebar.pack_propagate(False)

        inner_sidebar = tk.Frame(sidebar, bg=COLORS["bg_sidebar"])
        inner_sidebar.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(
            inner_sidebar,
            text="SCAN OPTIONS",
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_muted"],
            font=("SF Pro Display", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 8))

        self.scan_large_var = tk.BooleanVar(value=True)
        self.scan_cache_var = tk.BooleanVar(value=True)
        self.scan_downloads_var = tk.BooleanVar(value=True)
        self.scan_logs_var = tk.BooleanVar(value=True)
        self.scan_trash_var = tk.BooleanVar(value=True)

        checks = [
            ("Large Files", self.scan_large_var),
            ("Caches", self.scan_cache_var),
            ("Old Downloads", self.scan_downloads_var),
            ("Log Files", self.scan_logs_var),
            ("Trash Report", self.scan_trash_var),
        ]
        for text, var in checks:
            ttk.Checkbutton(inner_sidebar, text=text, variable=var).pack(
                anchor=tk.W, pady=3
            )

        ttk.Separator(inner_sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        tk.Label(
            inner_sidebar,
            text="SELECT BY CATEGORY",
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_muted"],
            font=("SF Pro Display", 9, "bold"),
        ).pack(anchor=tk.W, pady=(0, 6))

        for cat in ScanCategory:
            ttk.Button(
                inner_sidebar,
                text=f"All {cat.value}",
                command=lambda c=cat: self.results_table.select_all_category(c, True),
                style="Sidebar.TButton",
            ).pack(fill=tk.X, pady=2)

        ttk.Separator(inner_sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        ttk.Button(
            inner_sidebar,
            text="Select All",
            command=lambda: self.results_table.select_all(True),
            style="Sidebar.TButton",
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            inner_sidebar,
            text="Deselect All",
            command=lambda: self.results_table.select_all(False),
            style="Sidebar.TButton",
        ).pack(fill=tk.X, pady=2)

        ttk.Separator(inner_sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=12)

        ttk.Button(
            inner_sidebar,
            text="Add Folder...",
            command=self._add_custom_folder,
            style="Sidebar.TButton",
        ).pack(fill=tk.X, pady=2)

        self.custom_folders_label = tk.Label(
            inner_sidebar,
            text="Custom folders: 0",
            bg=COLORS["bg_sidebar"],
            fg=COLORS["text_muted"],
            font=("SF Pro Display", 10),
        )
        self.custom_folders_label.pack(anchor=tk.W, pady=(6, 0))

        results_area = tk.Frame(content, bg=COLORS["bg_dark"])
        results_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.results_table = ResultsTable(results_area)
        self.results_table.pack(fill=tk.BOTH, expand=True)

        bottom_area = tk.Frame(self.root, bg=COLORS["bg_dark"])
        bottom_area.pack(fill=tk.X, padx=20, pady=(8, 0))

        progress_frame = tk.Frame(bottom_area, bg=COLORS["bg_dark"])
        progress_frame.pack(fill=tk.X, pady=(0, 6))

        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="indeterminate", length=300
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

        self.progress_label = tk.Label(
            progress_frame,
            text="",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_muted"],
            font=("SF Pro Display", 10),
        )
        self.progress_label.pack(side=tk.LEFT)

        btn_bar = tk.Frame(self.root, bg=COLORS["bg_card"], height=56)
        btn_bar.pack(fill=tk.X, padx=20, pady=(0, 15))
        btn_bar.pack_propagate(False)

        btn_inner = tk.Frame(btn_bar, bg=COLORS["bg_card"])
        btn_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        self.scan_btn = ttk.Button(
            btn_inner, text="Scan", command=self._start_scan, style="Primary.TButton"
        )
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.cancel_btn = ttk.Button(
            btn_inner,
            text="Cancel",
            command=self._cancel_scan,
            state=tk.DISABLED,
            style="Action.TButton",
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.delete_btn = ttk.Button(
            btn_inner,
            text="Delete Selected",
            command=self._delete_selected,
            style="Danger.TButton",
        )
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.trash_btn = ttk.Button(
            btn_inner,
            text="Empty Trash",
            command=self._empty_trash,
            style="Danger.TButton",
        )
        self.trash_btn.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_inner,
            text="Export CSV",
            command=self._export_csv,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_inner,
            text="Open Folder",
            command=self._open_folder,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            btn_inner,
            text="Settings",
            command=self._open_settings,
            style="Action.TButton",
        ).pack(side=tk.RIGHT, padx=(6, 0))

        ttk.Button(
            btn_inner,
            text="Help",
            command=self._show_help,
            style="Action.TButton",
        ).pack(side=tk.RIGHT, padx=(6, 0))

    def _update_dry_run_indicator(self):
        if self.settings.dry_run:
            self.dry_run_label.config(
                text="DRY RUN MODE",
                fg=COLORS["accent_orange"],
            )
        else:
            self.dry_run_label.config(
                text="LIVE MODE",
                fg=COLORS["accent_red"],
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
                self.custom_folders_label.config(
                    text=f"Custom folders: {len(self.settings.custom_scan_folders)}"
                )

    def _start_scan(self):
        self.settings.scan_large_files = self.scan_large_var.get()
        self.settings.scan_caches = self.scan_cache_var.get()
        self.settings.scan_downloads = self.scan_downloads_var.get()
        self.settings.scan_logs = self.scan_logs_var.get()
        self.settings.scan_trash = self.scan_trash_var.get()

        self.scan_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.DISABLED)
        self.progress_bar.start(10)
        self.summary_label.config(text="Scanning...", fg=COLORS["accent_blue"])

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
            lambda: self.progress_label.config(
                text=f"Found {items_found} items  |  {short_path}"
            ),
        )

    def _on_scan_complete(self, result: ScanResult):
        self.scan_result = result
        self.progress_bar.stop()
        self.scan_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.NORMAL)
        self.progress_label.config(text="")

        self.results_table.populate(result.items)

        status = "Cancelled" if result.was_cancelled else "Complete"
        self.summary_label.config(
            text=f"Scan {status}:  {result.item_count} items  |  "
            f"Reclaimable: {result.total_size_human}  |  "
            f"Duration: {result.scan_duration_seconds:.1f}s",
            fg=COLORS["accent_green"] if not result.was_cancelled else COLORS["accent_orange"],
        )

        if result.errors:
            logger.warning(f"Scan had {len(result.errors)} errors")

    def _cancel_scan(self):
        if self._scanner:
            self._scanner.cancel()
            self.cancel_btn.config(state=tk.DISABLED)
            self.summary_label.config(text="Cancelling scan...", fg=COLORS["accent_orange"])

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
        """Start the Tkinter main loop."""
        self.root.mainloop()
