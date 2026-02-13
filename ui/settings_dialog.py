"""
Settings dialog for Mac Cleanup Tool.

Modern CustomTkinter-based settings dialog.
"""

import tkinter as tk
import customtkinter as ctk

from core.models import ScanSettings


class SettingsDialog:
    """Modal settings dialog for configuring scan behavior."""

    def __init__(self, parent: ctk.CTk, settings: ScanSettings):
        self.settings = settings
        self.result: ScanSettings | None = None

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Settings")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        window_width, window_height = 480, 540
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            main_frame,
            text="Settings",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", pady=(0, 16))

        self._build_thresholds(main_frame)
        self._build_options(main_frame)
        self._build_safety(main_frame)

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(16, 0))

        ctk.CTkButton(
            btn_frame, text="Save", command=self._save,
            width=100, height=36, corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="Cancel", command=self.dialog.destroy,
            width=100, height=36, corner_radius=8,
            font=ctk.CTkFont(size=14),
            fg_color=("gray30", "gray30"),
            hover_color=("gray40", "gray40"),
        ).pack(side="left")

        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
        parent.wait_window(self.dialog)

    def _build_thresholds(self, parent):
        section = ctk.CTkFrame(parent, corner_radius=8)
        section.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner, text="THRESHOLDS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray50", "gray50"),
        ).pack(anchor="w", pady=(0, 8))

        self.size_var = ctk.StringVar(value=str(self.settings.size_threshold_mb))
        self.downloads_days_var = ctk.StringVar(value=str(self.settings.old_downloads_days))
        self.cache_days_var = ctk.StringVar(value=str(self.settings.cache_age_days))
        self.max_results_var = ctk.StringVar(value=str(self.settings.max_results))

        fields = [
            ("Large file threshold (MB):", self.size_var),
            ("Old downloads (days):", self.downloads_days_var),
            ("Cache age (days):", self.cache_days_var),
            ("Max results:", self.max_results_var),
        ]
        for label_text, var in fields:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=label_text,
                font=ctk.CTkFont(size=13),
            ).pack(side="left")
            ctk.CTkEntry(
                row, textvariable=var, width=80, height=30,
                corner_radius=6, font=ctk.CTkFont(size=13),
            ).pack(side="right")

    def _build_options(self, parent):
        section = ctk.CTkFrame(parent, corner_radius=8)
        section.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner, text="OPTIONS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray50", "gray50"),
        ).pack(anchor="w", pady=(0, 8))

        self.hidden_var = ctk.BooleanVar(value=self.settings.include_hidden_files)
        self.symlinks_var = ctk.BooleanVar(value=self.settings.follow_symlinks)

        ctk.CTkCheckBox(
            inner, text="Include hidden files", variable=self.hidden_var,
            font=ctk.CTkFont(size=13), corner_radius=4,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor="w", pady=3)

        ctk.CTkCheckBox(
            inner, text="Follow symlinks (not recommended)", variable=self.symlinks_var,
            font=ctk.CTkFont(size=13), corner_radius=4,
            checkbox_width=20, checkbox_height=20,
        ).pack(anchor="w", pady=3)

    def _build_safety(self, parent):
        section = ctk.CTkFrame(parent, corner_radius=8)
        section.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(section, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(
            inner, text="SAFETY",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("gray50", "gray50"),
        ).pack(anchor="w", pady=(0, 8))

        self.dry_run_var = ctk.BooleanVar(value=self.settings.dry_run)
        self.personal_var = ctk.BooleanVar(value=self.settings.allow_personal_docs)

        ctk.CTkSwitch(
            inner, text="Dry Run mode (no actual deletion)",
            variable=self.dry_run_var,
            font=ctk.CTkFont(size=13),
            switch_width=40, switch_height=20,
        ).pack(anchor="w", pady=4)

        ctk.CTkSwitch(
            inner, text="Allow scanning personal folders",
            variable=self.personal_var,
            font=ctk.CTkFont(size=13),
            switch_width=40, switch_height=20,
        ).pack(anchor="w", pady=4)

        ctk.CTkLabel(
            inner,
            text="Warning: Personal folders include Documents,\nDesktop, Pictures, Movies, Music, iCloud Drive.",
            font=ctk.CTkFont(size=11),
            text_color="#ffa94d",
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

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
