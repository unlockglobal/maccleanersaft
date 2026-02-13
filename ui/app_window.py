"""
Main application window for Mac Cleanup Tool.

Provides the primary GUI with sidebar navigation, results table,
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


class AppWindow:
    """Main application window with all UI components."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mac Cleanup Tool")
        self.root.geometry("1100x700")
        self.root.minsize(900, 500)

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
        style.configure("Sidebar.TButton", padding=(10, 8))
        style.configure("Action.TButton", padding=(12, 6))
        style.configure(
            "DryRun.TLabel",
            foreground="orange",
            font=("Helvetica", 11, "bold"),
        )
        style.configure(
            "Live.TLabel",
            foreground="red",
            font=("Helvetica", 11, "bold"),
        )
        style.configure("Summary.TLabel", font=("Helvetica", 12))
        style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))

    def _build_ui(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(top_frame, text="Mac Cleanup Tool", style="Title.TLabel").pack(
            side=tk.LEFT
        )

        self.dry_run_label = ttk.Label(top_frame, text="", style="DryRun.TLabel")
        self.dry_run_label.pack(side=tk.RIGHT, padx=10)

        summary_frame = ttk.Frame(self.root)
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.summary_label = ttk.Label(
            summary_frame,
            text="Ready to scan. Configure options and click Scan.",
            style="Summary.TLabel",
        )
        self.summary_label.pack(side=tk.LEFT)

        content = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        sidebar = ttk.LabelFrame(content, text="Scan Options", padding=10)
        content.add(sidebar, weight=0)

        self.scan_large_var = tk.BooleanVar(value=True)
        self.scan_cache_var = tk.BooleanVar(value=True)
        self.scan_downloads_var = tk.BooleanVar(value=True)
        self.scan_logs_var = tk.BooleanVar(value=True)
        self.scan_trash_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            sidebar, text="Large Files", variable=self.scan_large_var
        ).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(
            sidebar, text="Caches", variable=self.scan_cache_var
        ).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(
            sidebar, text="Old Downloads", variable=self.scan_downloads_var
        ).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(
            sidebar, text="Log Files", variable=self.scan_logs_var
        ).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(
            sidebar, text="Trash Report", variable=self.scan_trash_var
        ).pack(anchor=tk.W, pady=3)

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(sidebar, text="Select per category:").pack(anchor=tk.W, pady=(0, 5))

        cat_btns = ttk.Frame(sidebar)
        cat_btns.pack(fill=tk.X)

        for cat in ScanCategory:
            btn_frame = ttk.Frame(cat_btns)
            btn_frame.pack(fill=tk.X, pady=1)
            ttk.Button(
                btn_frame,
                text=f"All {cat.value}",
                command=lambda c=cat: self.results_table.select_all_category(c, True),
                style="Sidebar.TButton",
            ).pack(fill=tk.X)

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Button(
            sidebar,
            text="Select All",
            command=lambda: self.results_table.select_all(True),
            style="Sidebar.TButton",
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            sidebar,
            text="Deselect All",
            command=lambda: self.results_table.select_all(False),
            style="Sidebar.TButton",
        ).pack(fill=tk.X, pady=2)

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Button(
            sidebar,
            text="Add Folder...",
            command=self._add_custom_folder,
            style="Sidebar.TButton",
        ).pack(fill=tk.X, pady=2)

        self.custom_folders_label = ttk.Label(
            sidebar, text="Custom folders: 0", foreground="gray"
        )
        self.custom_folders_label.pack(anchor=tk.W, pady=(5, 0))

        results_frame = ttk.Frame(content)
        content.add(results_frame, weight=1)

        self.results_table = ResultsTable(results_frame)
        self.results_table.pack(fill=tk.BOTH, expand=True)

        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="indeterminate", length=300
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.progress_label = ttk.Label(progress_frame, text="", foreground="gray")
        self.progress_label.pack(side=tk.LEFT)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.scan_btn = ttk.Button(
            btn_frame, text="Scan", command=self._start_scan, style="Action.TButton"
        )
        self.scan_btn.pack(side=tk.LEFT, padx=3)

        self.cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel Scan",
            command=self._cancel_scan,
            state=tk.DISABLED,
            style="Action.TButton",
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=3)

        self.delete_btn = ttk.Button(
            btn_frame,
            text="Delete Selected",
            command=self._delete_selected,
            style="Action.TButton",
        )
        self.delete_btn.pack(side=tk.LEFT, padx=3)

        self.trash_btn = ttk.Button(
            btn_frame,
            text="Empty Trash",
            command=self._empty_trash,
            style="Action.TButton",
        )
        self.trash_btn.pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_frame,
            text="Export CSV",
            command=self._export_csv,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_frame,
            text="Open Folder",
            command=self._open_folder,
            style="Action.TButton",
        ).pack(side=tk.LEFT, padx=3)

        ttk.Button(
            btn_frame,
            text="Settings",
            command=self._open_settings,
            style="Action.TButton",
        ).pack(side=tk.RIGHT, padx=3)

        ttk.Button(
            btn_frame,
            text="Help",
            command=self._show_help,
            style="Action.TButton",
        ).pack(side=tk.RIGHT, padx=3)

    def _update_dry_run_indicator(self):
        if self.settings.dry_run:
            self.dry_run_label.config(
                text="DRY RUN MODE (no files will be deleted)",
                style="DryRun.TLabel",
            )
        else:
            self.dry_run_label.config(
                text="LIVE MODE (deletions are real)",
                style="Live.TLabel",
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
        self.summary_label.config(text="Scanning...")

        self._scanner = Scanner(self.settings)
        self._scanner.set_progress_callback(self._on_scan_progress)

        self._scan_thread = threading.Thread(target=self._run_scan, daemon=True)
        self._scan_thread.start()

    def _run_scan(self):
        result = self._scanner.scan()
        self.root.after(0, self._on_scan_complete, result)

    def _on_scan_progress(self, current_path: str, items_found: int):
        short_path = current_path
        if len(short_path) > 60:
            short_path = "..." + short_path[-57:]
        self.root.after(
            0,
            lambda: self.progress_label.config(
                text=f"Found {items_found} items | {short_path}"
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
            text=f"Scan {status}: {result.item_count} items | "
            f"Total reclaimable: {result.total_size_human} | "
            f"Duration: {result.scan_duration_seconds:.1f}s"
        )

        if result.errors:
            logger.warning(f"Scan had {len(result.errors)} errors")

    def _cancel_scan(self):
        if self._scanner:
            self._scanner.cancel()
            self.cancel_btn.config(state=tk.DISABLED)
            self.summary_label.config(text="Cancelling scan...")

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
            msg += " (dry run — no actual changes)"

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
            "Mac Cleanup Tool — Help\n"
            "========================\n\n"
            "This tool helps you safely find and clean up space on your Mac.\n\n"
            "SAFETY FIRST:\n"
            "- System files are NEVER touched.\n"
            "- Personal folders (Documents, Desktop, etc.) are excluded by default.\n"
            "- Dry Run mode is ON by default — nothing is deleted until you turn it off.\n"
            "- All deletions go to Trash (not permanent).\n"
            "- You must type 'DELETE' to confirm any deletion.\n\n"
            "HOW TO USE:\n"
            "1. Select scan types in the left sidebar.\n"
            "2. Click 'Scan' to find reclaimable space.\n"
            "3. Review results and select items to remove.\n"
            "4. Click 'Delete Selected' to move items to Trash.\n\n"
            "SCAN TYPES:\n"
            "- Large Files: Files above the size threshold (default 1 GB).\n"
            "- Caches: Application caches older than threshold.\n"
            "- Old Downloads: Files in Downloads older than threshold.\n"
            "- Log Files: Old log files from ~/Library/Logs.\n"
            "- Trash Report: Shows current Trash size.\n\n"
            "SETTINGS:\n"
            "- Adjust thresholds, toggle hidden files, and manage Dry Run.\n"
            "- 'Allow personal folders' enables scanning Documents, etc.\n\n"
            "EXPORTING:\n"
            "- Click 'Export CSV' to save a report of all scan results."
        )
        messagebox.showinfo("Help", help_text)

    def run(self):
        """Start the Tkinter main loop."""
        self.root.mainloop()
