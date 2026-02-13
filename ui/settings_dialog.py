"""
Settings dialog for Mac Cleanup Tool.

Modern dark-themed settings configuration dialog.
"""

import tkinter as tk
from tkinter import ttk

from core.models import ScanSettings

COLORS = {
    "bg_dark": "#1a1b2e",
    "bg_card": "#2a2b4a",
    "bg_input": "#33345a",
    "text_primary": "#e8e8f0",
    "text_secondary": "#9d9db5",
    "text_muted": "#6b6b85",
    "accent_orange": "#ffa94d",
    "accent_blue": "#5b8def",
    "border": "#3a3b5a",
    "btn_primary": "#5b8def",
    "btn_secondary": "#3a3b5a",
}


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
        self.dialog.configure(bg=COLORS["bg_dark"])

        window_width, window_height = 500, 560
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = tk.Frame(self.dialog, bg=COLORS["bg_dark"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        tk.Label(
            main_frame,
            text="Settings",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            font=("SF Pro Display", 20, "bold"),
        ).pack(anchor=tk.W, pady=(0, 16))

        self._build_section(main_frame, "Thresholds", self._build_thresholds)
        self._build_section(main_frame, "Options", self._build_options)
        self._build_section(main_frame, "Safety", self._build_safety)

        btn_frame = tk.Frame(main_frame, bg=COLORS["bg_dark"])
        btn_frame.pack(fill=tk.X, pady=(16, 0))

        ttk.Button(btn_frame, text="Save", command=self._save, style="Primary.TButton").pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy, style="Action.TButton").pack(
            side=tk.LEFT
        )

        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
        parent.wait_window(self.dialog)

    def _build_section(self, parent, title, builder):
        section = tk.Frame(parent, bg=COLORS["bg_card"])
        section.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            section,
            text=title.upper(),
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"],
            font=("SF Pro Display", 9, "bold"),
        ).pack(anchor=tk.W, padx=14, pady=(10, 6))

        inner = tk.Frame(section, bg=COLORS["bg_card"])
        inner.pack(fill=tk.X, padx=14, pady=(0, 12))
        builder(inner)

    def _build_thresholds(self, parent):
        self.size_var = tk.StringVar(value=str(self.settings.size_threshold_mb))
        self.downloads_days_var = tk.StringVar(value=str(self.settings.old_downloads_days))
        self.cache_days_var = tk.StringVar(value=str(self.settings.cache_age_days))
        self.max_results_var = tk.StringVar(value=str(self.settings.max_results))

        fields = [
            ("Large file threshold (MB):", self.size_var),
            ("Old downloads (days):", self.downloads_days_var),
            ("Cache age (days):", self.cache_days_var),
            ("Max results:", self.max_results_var),
        ]
        for label_text, var in fields:
            row = tk.Frame(parent, bg=COLORS["bg_card"])
            row.pack(fill=tk.X, pady=3)
            tk.Label(
                row, text=label_text,
                bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                font=("SF Pro Display", 11),
            ).pack(side=tk.LEFT)
            entry = tk.Entry(
                row, textvariable=var, width=10,
                bg=COLORS["bg_input"], fg=COLORS["text_primary"],
                insertbackground=COLORS["text_primary"],
                relief="flat", font=("SF Mono", 11),
                highlightthickness=0,
            )
            entry.pack(side=tk.RIGHT)

    def _build_options(self, parent):
        self.hidden_var = tk.BooleanVar(value=self.settings.include_hidden_files)
        self.symlinks_var = tk.BooleanVar(value=self.settings.follow_symlinks)

        ttk.Checkbutton(parent, text="Include hidden files", variable=self.hidden_var).pack(
            anchor=tk.W, pady=2
        )
        ttk.Checkbutton(parent, text="Follow symlinks (not recommended)", variable=self.symlinks_var).pack(
            anchor=tk.W, pady=2
        )

    def _build_safety(self, parent):
        self.dry_run_var = tk.BooleanVar(value=self.settings.dry_run)
        self.personal_var = tk.BooleanVar(value=self.settings.allow_personal_docs)

        ttk.Checkbutton(
            parent, text="Dry Run mode (no actual deletion)", variable=self.dry_run_var
        ).pack(anchor=tk.W, pady=2)

        ttk.Checkbutton(
            parent, text="Allow scanning personal folders", variable=self.personal_var
        ).pack(anchor=tk.W, pady=2)

        tk.Label(
            parent,
            text="Warning: Personal folders include Documents,\nDesktop, Pictures, Movies, Music, iCloud Drive.",
            bg=COLORS["bg_card"],
            fg=COLORS["accent_orange"],
            font=("SF Pro Display", 10),
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(6, 0))

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
