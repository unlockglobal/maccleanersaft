"""
Utility functions for Mac Cleanup Tool.

Provides size formatting, time formatting, CSV export, and logging setup.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from core.models import ScanItem
from core.rules import APP_LOG_DIR, APP_LOG_FILE


def setup_logging() -> logging.Logger:
    """
    Set up application logging to file and console.
    Logs are stored in ~/.mac_cleanup_tool/logs/app.log
    """
    APP_LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("mac_cleanup")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler(APP_LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_fmt = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_fmt)
        logger.addHandler(console_handler)

    return logger


def format_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string."""
    if size_bytes < 0:
        return "0 B"
    size: float = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_timestamp(dt: datetime) -> str:
    """Format a datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M")


def get_directory_size(path: Path, follow_symlinks: bool = False) -> int:
    """
    Calculate total size of a directory recursively.
    Skips symlinks by default to avoid loops and unintended traversal.
    """
    total = 0
    try:
        for item in path.rglob("*"):
            try:
                if item.is_symlink() and not follow_symlinks:
                    continue
                if item.is_file():
                    total += item.stat(follow_symlinks=follow_symlinks).st_size
            except (PermissionError, OSError):
                continue
    except (PermissionError, OSError):
        pass
    return total


def export_to_csv(items: List[ScanItem], output_path: Path) -> None:
    """
    Export scan results to a CSV file.

    Columns: timestamp, category, size_bytes, size_human,
             last_modified, path, recommended_action, selected
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "category",
            "size_bytes",
            "size_human",
            "last_modified",
            "path",
            "recommended_action",
            "status",
        ])
        now = datetime.now().isoformat()
        for item in items:
            writer.writerow([
                now,
                item.category.value,
                item.size_bytes,
                item.size_human,
                format_timestamp(item.last_modified),
                str(item.path),
                item.recommended_action,
                item.status.value,
            ])
