"""
Confirmation dialogs for Mac Cleanup Tool.

Modern dashboard-style confirmation dialogs with CustomTkinter.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional


class ConfirmDeleteDialog:
    """Modal dialog requiring the user to type 'DELETE' to confirm file deletion."""

    def __init__(self, parent: ctk.CTk, file_count: int, total_size: str, dry_run: bool):
        self.result = False
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Confirm Deletion")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        window_width, window_height = 440, 340
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=28, pady=24)

        if dry_run:
            ctk.CTkLabel(
                main_frame,
                text="\u26a0\ufe0f  DRY RUN IS ON",
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color="#f59e0b",
            ).pack(pady=(20, 12))

            ctk.CTkLabel(
                main_frame,
                text="Dry Run mode is enabled. No files will be deleted.\nTurn off Dry Run in Settings to enable deletion.",
                font=ctk.CTkFont(size=13),
                text_color="#9ca3af",
                wraplength=380,
                justify="center",
            ).pack(pady=(0, 24))

            ctk.CTkButton(
                main_frame, text="Got it",
                command=self.dialog.destroy,
                width=120, height=40, corner_radius=10,
                font=ctk.CTkFont(size=14),
                fg_color="#3b82f6", hover_color="#2563eb",
            ).pack()
            parent.wait_window(self.dialog)
            return

        ctk.CTkLabel(
            main_frame,
            text="\U0001f5d1\ufe0f  Confirm Deletion",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#ef4444",
        ).pack(pady=(0, 12))

        info_card = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1a1b1e")
        info_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            info_card,
            text=f"{file_count} item(s)  \u2022  {total_size}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#e5e7eb",
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            info_card,
            text="Items will be moved to Trash (not permanent)",
            font=ctk.CTkFont(size=12),
            text_color="#6b7280",
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            main_frame,
            text="Type DELETE to confirm:",
            font=ctk.CTkFont(size=13),
            text_color="#9ca3af",
        ).pack(pady=(0, 6))

        self.confirm_entry = ctk.CTkEntry(
            main_frame, width=200, height=40,
            corner_radius=10, font=ctk.CTkFont(size=15),
            justify="center",
            placeholder_text="DELETE",
        )
        self.confirm_entry.pack(pady=(0, 16))
        self.confirm_entry.focus_set()

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame, text="Delete",
            command=self._on_confirm,
            width=110, height=40, corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c",
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="Cancel",
            command=self._on_cancel,
            width=100, height=40, corner_radius=10,
            font=ctk.CTkFont(size=14),
            fg_color="#2d2f33", hover_color="#3d3f43",
            text_color="#8b949e",
        ).pack(side="left", padx=4)

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
    """Modal dialog for emptying the Trash. Requires typing 'EMPTY TRASH' to confirm."""

    def __init__(self, parent: ctk.CTk, trash_size: str):
        self.result = False
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Empty Trash")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        window_width, window_height = 440, 320
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            main_frame,
            text="\u26a0\ufe0f  Empty Trash",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#ef4444",
        ).pack(pady=(0, 12))

        info_card = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1a1b1e")
        info_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            info_card,
            text=f"Trash size: {trash_size}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#e5e7eb",
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            info_card,
            text="This will PERMANENTLY delete everything. Cannot be undone!",
            font=ctk.CTkFont(size=12),
            text_color="#ef4444",
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            main_frame,
            text="Type EMPTY TRASH to confirm:",
            font=ctk.CTkFont(size=13),
            text_color="#9ca3af",
        ).pack(pady=(0, 6))

        self.confirm_entry = ctk.CTkEntry(
            main_frame, width=240, height=40,
            corner_radius=10, font=ctk.CTkFont(size=15),
            justify="center",
            placeholder_text="EMPTY TRASH",
        )
        self.confirm_entry.pack(pady=(0, 16))
        self.confirm_entry.focus_set()

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame, text="Empty Trash",
            command=self._on_confirm,
            width=130, height=40, corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#dc2626", hover_color="#b91c1c",
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_frame, text="Cancel",
            command=self._on_cancel,
            width=100, height=40, corner_radius=10,
            font=ctk.CTkFont(size=14),
            fg_color="#2d2f33", hover_color="#3d3f43",
            text_color="#8b949e",
        ).pack(side="left", padx=4)

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
