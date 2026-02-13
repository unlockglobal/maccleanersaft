"""
Confirmation dialogs for Mac Cleanup Tool.

Provides typed-confirmation dialogs for dangerous operations
like deletion and emptying trash.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class ConfirmDeleteDialog:
    """
    Modal dialog requiring the user to type 'DELETE' to confirm file deletion.
    Shows summary of what will be deleted.
    """

    def __init__(self, parent: tk.Tk, file_count: int, total_size: str, dry_run: bool):
        self.result = False
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Confirm Deletion")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        window_width, window_height = 450, 320
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        if dry_run:
            ttk.Label(
                main_frame,
                text="DRY RUN IS ON",
                font=("Helvetica", 14, "bold"),
                foreground="orange",
            ).pack(pady=(0, 10))
            ttk.Label(
                main_frame,
                text="Dry Run mode is enabled. No files will be deleted.\n"
                     "Turn off Dry Run in Settings to enable deletion.",
                wraplength=400,
                justify=tk.CENTER,
            ).pack(pady=(0, 15))
            ttk.Button(main_frame, text="OK", command=self.dialog.destroy).pack()
            parent.wait_window(self.dialog)
            return

        ttk.Label(
            main_frame,
            text="Confirm Deletion",
            font=("Helvetica", 16, "bold"),
            foreground="red",
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text=f"You are about to move {file_count} item(s) to Trash.\n"
                 f"Total size: {total_size}",
            wraplength=400,
            justify=tk.CENTER,
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text="Items will be moved to Trash (not permanently deleted).",
            foreground="gray",
            wraplength=400,
            justify=tk.CENTER,
        ).pack(pady=(0, 15))

        ttk.Label(
            main_frame,
            text='Type DELETE to confirm:',
            font=("Helvetica", 11),
        ).pack(pady=(0, 5))

        self.confirm_entry = ttk.Entry(main_frame, width=20, justify=tk.CENTER)
        self.confirm_entry.pack(pady=(0, 15))
        self.confirm_entry.focus_set()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()

        self.delete_btn = ttk.Button(
            btn_frame, text="Delete", command=self._on_confirm
        )
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame, text="Cancel", command=self._on_cancel
        ).pack(side=tk.LEFT, padx=5)

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

        window_width, window_height = 450, 280
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")

        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="Empty Trash",
            font=("Helvetica", 16, "bold"),
            foreground="red",
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame,
            text=f"This will PERMANENTLY delete all items in Trash.\n"
                 f"Trash size: {trash_size}\n\n"
                 f"This action cannot be undone!",
            wraplength=400,
            justify=tk.CENTER,
        ).pack(pady=(0, 15))

        ttk.Label(
            main_frame,
            text='Type EMPTY TRASH to confirm:',
            font=("Helvetica", 11),
        ).pack(pady=(0, 5))

        self.confirm_entry = ttk.Entry(main_frame, width=25, justify=tk.CENTER)
        self.confirm_entry.pack(pady=(0, 15))
        self.confirm_entry.focus_set()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()

        ttk.Button(
            btn_frame, text="Empty Trash", command=self._on_confirm
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame, text="Cancel", command=self._on_cancel
        ).pack(side=tk.LEFT, padx=5)

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
