"""
Data models for Mac Cleanup Tool.

Uses dataclasses for clean, typed data structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ScanCategory(Enum):
    """Categories of items found during scanning."""
    LARGE_FILE = "Large File"
    CACHE = "Cache"
    OLD_DOWNLOAD = "Old Download"
    LOG_FILE = "Log File"
    TRASH = "Trash"


class ItemStatus(Enum):
    """Status of a scan item through its lifecycle."""
    FOUND = "Found"
    SELECTED = "Selected"
    TRASHED = "Trashed"
    FAILED = "Failed"
    SKIPPED = "Skipped"


@dataclass
class ScanItem:
    """Represents a single item found during scanning."""
    path: Path
    category: ScanCategory
    size_bytes: int
    last_modified: datetime
    is_symlink: bool = False
    is_directory: bool = False
    status: ItemStatus = ItemStatus.FOUND
    failure_reason: Optional[str] = None
    recommended_action: str = "Review"

    @property
    def size_human(self) -> str:
        """Return human-readable size string."""
        size = self.size_bytes
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if abs(size) < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"


@dataclass
class ScanSettings:
    """User-configurable scan settings."""
    size_threshold_mb: int = 1024
    max_results: int = 500
    include_hidden_files: bool = False
    old_downloads_days: int = 90
    cache_age_days: int = 30
    dry_run: bool = True
    allow_personal_docs: bool = False
    follow_symlinks: bool = False

    scan_large_files: bool = True
    scan_caches: bool = True
    scan_downloads: bool = True
    scan_logs: bool = True
    scan_trash: bool = True

    custom_scan_folders: List[Path] = field(default_factory=list)


@dataclass
class ScanResult:
    """Aggregated result of a scan operation."""
    items: List[ScanItem] = field(default_factory=list)
    total_size: int = 0
    scan_duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    was_cancelled: bool = False

    @property
    def item_count(self) -> int:
        return len(self.items)

    @property
    def total_size_human(self) -> str:
        size = self.total_size
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if abs(size) < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
