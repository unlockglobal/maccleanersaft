"""
Settings dialog for Mac Cleanup Tool.

Allows users to configure scan parameters, thresholds,
and safety toggles.
"""

import tkinter as tk
from tkinter import ttk

from core.models import ScanSettings


class SettingsDialog:
    """Modal settings dialog for configuring scan behavior."""

    def __init__(self, parent: tk.Tk, settings: ScanSettings):
        self.settings = settings
        self.result: ScanSettings | None = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        window_width, window_height = 480, 520
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame, text="Scan Settings", font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 15))

        thresholds = ttk.LabelFrame(main_frame, text="Thresholds", padding=10)
        thresholds.pack(fill=tk.X, pady=(0, 10))

        row = ttk.Frame(thresholds)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Large file threshold (MB):").pack(side=tk.LEFT)
        self.size_var = tk.StringVar(value=str(settings.size_threshold_mb))
        ttk.Entry(row, textvariable=self.size_var, width=10).pack(side=tk.RIGHT)

        row = ttk.Frame(thresholds)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Old downloads (days):").pack(side=tk.LEFT)
        self.downloads_days_var = tk.StringVar(value=str(settings.old_downloads_days))
        ttk.Entry(row, textvariable=self.downloads_days_var, width=10).pack(side=tk.RIGHT)

        row = ttk.Frame(thresholds)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Cache age (days):").pack(side=tk.LEFT)
        self.cache_days_var = tk.StringVar(value=str(settings.cache_age_days))
        ttk.Entry(row, textvariable=self.cache_days_var, width=10).pack(side=tk.RIGHT)

        row = ttk.Frame(thresholds)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text="Max results:").pack(side=tk.LEFT)
        self.max_results_var = tk.StringVar(value=str(settings.max_results))
        ttk.Entry(row, textvariable=self.max_results_var, width=10).pack(side=tk.RIGHT)

        options = ttk.LabelFrame(main_frame, text="Options", padding=10)
        options.pack(fill=tk.X, pady=(0, 10))

        self.hidden_var = tk.BooleanVar(value=settings.include_hidden_files)
        ttk.Checkbutton(
            options, text="Include hidden files", variable=self.hidden_var
        ).pack(anchor=tk.W, pady=2)

        self.symlinks_var = tk.BooleanVar(value=settings.follow_symlinks)
        ttk.Checkbutton(
            options, text="Follow symlinks (not recommended)", variable=self.symlinks_var
        ).pack(anchor=tk.W, pady=2)

        safety = ttk.LabelFrame(main_frame, text="Safety", padding=10)
        safety.pack(fill=tk.X, pady=(0, 10))

        self.dry_run_var = tk.BooleanVar(value=settings.dry_run)
        ttk.Checkbutton(
            safety,
            text="Dry Run mode (show what would be deleted, no actual deletion)",
            variable=self.dry_run_var,
        ).pack(anchor=tk.W, pady=2)

        self.personal_var = tk.BooleanVar(value=settings.allow_personal_docs)
        ttk.Checkbutton(
            safety,
            text="Allow scanning personal folders (Documents, Desktop, etc.)",
            variable=self.personal_var,
        ).pack(anchor=tk.W, pady=2)

        ttk.Label(
            safety,
            text="Warning: Enabling personal folders will scan Documents,\n"
                 "Desktop, Pictures, Movies, Music, and iCloud Drive.",
            foreground="orange",
            font=("Helvetica", 9),
        ).pack(anchor=tk.W, pady=(5, 0))

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=(15, 0))

        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
        parent.wait_window(self.dialog)

    def _save(self):
        try:
            self.settings.size_threshold_mb = max(1, int(self.size_var.get()))
            self.settings.old_downloads_days = max(1, int(self.downloads_days_var.get()))
            self.settings.cache_age_days = max(1, int(self.cache_days_var.get()))
            self.settings.max_results = max(10, int(self.max_results_var.get()))
        except ValueError:
            pass

        self.settings.include_hidden_files = self.hidden_var.get()
        self.settings.follow_symlinks = self.symlinks_var.get()
        self.settings.dry_run = self.dry_run_var.get()
        self.settings.allow_personal_docs = self.personal_var.get()
        self.result = self.settings
        self.dialog.destroy()
