"""
Confirmation dialogs for Mac Cleanup Tool.

Modern dark-themed confirmation dialogs for dangerous operations.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

COLORS = {
    "bg_dark": "#1a1b2e",
    "bg_card": "#2a2b4a",
    "bg_input": "#33345a",
    "text_primary": "#e8e8f0",
    "text_secondary": "#9d9db5",
    "text_muted": "#6b6b85",
    "accent_orange": "#ffa94d",
    "accent_red": "#ff6b6b",
    "btn_danger": "#ff6b6b",
    "btn_secondary": "#3a3b5a",
}


class ConfirmDeleteDialog:
    """
    Modal dialog requiring the user to type 'DELETE' to confirm file deletion.
    """

    def __init__(self, parent: tk.Tk, file_count: int, total_size: str, dry_run: bool):
        self.result = False
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Confirm Deletion")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLORS["bg_dark"])

        window_width, window_height = 460, 340
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = tk.Frame(self.dialog, bg=COLORS["bg_dark"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=24)

        if dry_run:
            tk.Label(
                main_frame,
                text="DRY RUN IS ON",
                bg=COLORS["bg_dark"],
                fg=COLORS["accent_orange"],
                font=("SF Pro Display", 18, "bold"),
            ).pack(pady=(0, 12))
            tk.Label(
                main_frame,
                text="Dry Run mode is enabled. No files will be deleted.\n"
                     "Turn off Dry Run in Settings to enable deletion.",
                bg=COLORS["bg_dark"],
                fg=COLORS["text_secondary"],
                font=("SF Pro Display", 12),
                wraplength=400,
                justify=tk.CENTER,
            ).pack(pady=(0, 20))
            ttk.Button(main_frame, text="OK", command=self.dialog.destroy, style="Action.TButton").pack()
            parent.wait_window(self.dialog)
            return

        tk.Label(
            main_frame,
            text="Confirm Deletion",
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_red"],
            font=("SF Pro Display", 18, "bold"),
        ).pack(pady=(0, 12))

        tk.Label(
            main_frame,
            text=f"You are about to move {file_count} item(s) to Trash.\n"
                 f"Total size: {total_size}",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            font=("SF Pro Display", 12),
            wraplength=400,
            justify=tk.CENTER,
        ).pack(pady=(0, 8))

        tk.Label(
            main_frame,
            text="Items will be moved to Trash (not permanently deleted).",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_muted"],
            font=("SF Pro Display", 11),
            wraplength=400,
            justify=tk.CENTER,
        ).pack(pady=(0, 16))

        tk.Label(
            main_frame,
            text="Type DELETE to confirm:",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            font=("SF Pro Display", 11),
        ).pack(pady=(0, 6))

        self.confirm_entry = tk.Entry(
            main_frame, width=20, justify=tk.CENTER,
            bg=COLORS["bg_input"], fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat", font=("SF Mono", 13),
            highlightthickness=0,
        )
        self.confirm_entry.pack(pady=(0, 16), ipady=4)
        self.confirm_entry.focus_set()

        btn_frame = tk.Frame(main_frame, bg=COLORS["bg_dark"])
        btn_frame.pack()

        ttk.Button(
            btn_frame, text="Delete", command=self._on_confirm, style="Danger.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            btn_frame, text="Cancel", command=self._on_cancel, style="Action.TButton"
        ).pack(side=tk.LEFT, padx=4)

        self.confirm_entry.bind("<Return>", lambda e: self._on_confirm())
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        parent.wait_window(self.dialog)

    def _on_confirm(self):
        if self.confirm_entry.get().strip().upper() == "DELETE":
            self.result = True
            self.dialog.destroy()

    def _on_cancel(self):
        self.result = False
        self.dialog.destroy()


class ConfirmTrashDialog:
    """
    Modal dialog for emptying the Trash.
    Requires typing 'EMPTY TRASH' to confirm.
    """

    def __init__(self, parent: tk.Tk, trash_size: str):
        self.result = False
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Empty Trash")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLORS["bg_dark"])

        window_width, window_height = 460, 300
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = tk.Frame(self.dialog, bg=COLORS["bg_dark"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=28, pady=24)

        tk.Label(
            main_frame,
            text="Empty Trash",
            bg=COLORS["bg_dark"],
            fg=COLORS["accent_red"],
            font=("SF Pro Display", 18, "bold"),
        ).pack(pady=(0, 12))

        tk.Label(
            main_frame,
            text=f"This will PERMANENTLY delete all items in Trash.\n"
                 f"Trash size: {trash_size}\n\n"
                 f"This action cannot be undone!",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            font=("SF Pro Display", 12),
            wraplength=400,
            justify=tk.CENTER,
        ).pack(pady=(0, 16))

        tk.Label(
            main_frame,
            text="Type EMPTY TRASH to confirm:",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            font=("SF Pro Display", 11),
        ).pack(pady=(0, 6))

        self.confirm_entry = tk.Entry(
            main_frame, width=25, justify=tk.CENTER,
            bg=COLORS["bg_input"], fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat", font=("SF Mono", 13),
            highlightthickness=0,
        )
        self.confirm_entry.pack(pady=(0, 16), ipady=4)
        self.confirm_entry.focus_set()

        btn_frame = tk.Frame(main_frame, bg=COLORS["bg_dark"])
        btn_frame.pack()

        ttk.Button(
            btn_frame, text="Empty Trash", command=self._on_confirm, style="Danger.TButton"
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            btn_frame, text="Cancel", command=self._on_cancel, style="Action.TButton"
        ).pack(side=tk.LEFT, padx=4)

        self.confirm_entry.bind("<Return>", lambda e: self._on_confirm())
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        parent.wait_window(self.dialog)

    def _on_confirm(self):
        if self.confirm_entry.get().strip().upper() == "EMPTY TRASH":
            self.result = True
            self.dialog.destroy()

    def _on_cancel(self):
        self.result = False
        self.dialog.destroy()
