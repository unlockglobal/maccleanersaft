"""
Scanning orchestration for Mac Cleanup Tool.

Provides threaded scanning with progress callbacks and cancellation support.
Each scan type (large files, caches, downloads, logs, trash) is implemented
as a separate method for clarity and safety.
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional, List

from core.models import ScanCategory, ScanItem, ScanResult, ScanSettings
from core.rules import (
    SAFE_PATHS,
    TRASH_PATH,
    is_path_blocked,
    is_path_safe_for_scan,
    HOME,
)
from core.utils import get_directory_size

logger = logging.getLogger("mac_cleanup")


class Scanner:
    """
    Orchestrates file system scanning with safety checks.

    Uses a background thread so the UI remains responsive.
    Supports cancellation via the cancel() method.
    """

    def __init__(self, settings: ScanSettings):
        self.settings = settings
        self._cancelled = False
        self._lock = threading.Lock()
        self._progress_callback: Optional[Callable[[str, int], None]] = None
        self._items_found = 0

    def cancel(self):
        """Request cancellation of the current scan."""
        with self._lock:
            self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """Set a callback for progress updates: callback(current_path, items_found)."""
        self._progress_callback = callback

    def _report_progress(self, current_path: str):
        """Report current scanning progress to the UI."""
        if self._progress_callback:
            self._progress_callback(current_path, self._items_found)

    def scan(self) -> ScanResult:
        """
        Run all enabled scans and return aggregated results.
        This method is meant to be called from a background thread.
        """
        start_time = time.time()
        result = ScanResult()
        self._cancelled = False
        self._items_found = 0

        try:
            if self.settings.scan_large_files and not self.is_cancelled:
                self._scan_large_files(result)

            if self.settings.scan_caches and not self.is_cancelled:
                self._scan_caches(result)

            if self.settings.scan_downloads and not self.is_cancelled:
                self._scan_old_downloads(result)

            if self.settings.scan_logs and not self.is_cancelled:
                self._scan_logs(result)

            if self.settings.scan_trash and not self.is_cancelled:
                self._scan_trash(result)

        except Exception as e:
            logger.error(f"Scan error: {e}", exc_info=True)
            result.errors.append(str(e))

        result.scan_duration_seconds = time.time() - start_time
        result.was_cancelled = self.is_cancelled
        result.total_size = sum(item.size_bytes for item in result.items)

        logger.info(
            f"Scan complete: {result.item_count} items, "
            f"{result.total_size_human}, "
            f"{result.scan_duration_seconds:.1f}s"
        )
        return result

    def _scan_large_files(self, result: ScanResult):
        """Scan for large files in safe default locations and custom folders."""
        logger.info("Scanning for large files...")
        threshold = self.settings.size_threshold_mb * 1024 * 1024

        scan_roots: List[Path] = [HOME / "Downloads"]

        for folder in self.settings.custom_scan_folders:
            if is_path_safe_for_scan(folder, self.settings.allow_personal_docs):
                scan_roots.append(folder)
            else:
                msg = f"Skipped blocked/personal path: {folder}"
                logger.warning(msg)
                result.errors.append(msg)

        for root in scan_roots:
            if self.is_cancelled:
                return
            if not root.exists():
                continue
            self._walk_for_large_files(root, threshold, result)

    def _walk_for_large_files(self, root: Path, threshold: int, result: ScanResult):
        """Walk a directory tree looking for files above the size threshold."""
        try:
            iterator = root.rglob("*") if root.is_dir() else [root]
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot access {root}: {e}")
            return

        for item_path in iterator:
            if self.is_cancelled:
                return
            if len(result.items) >= self.settings.max_results:
                return

            try:
                if item_path.is_symlink():
                    if not self.settings.follow_symlinks:
                        continue

                if not item_path.name.startswith(".") or self.settings.include_hidden_files:
                    pass
                else:
                    continue

                if not is_path_safe_for_scan(item_path, self.settings.allow_personal_docs):
                    continue

                if item_path.is_file():
                    stat = item_path.stat(follow_symlinks=self.settings.follow_symlinks)
                    if stat.st_size >= threshold:
                        self._report_progress(str(item_path))
                        scan_item = ScanItem(
                            path=item_path,
                            category=ScanCategory.LARGE_FILE,
                            size_bytes=stat.st_size,
                            last_modified=datetime.fromtimestamp(stat.st_mtime),
                            is_symlink=item_path.is_symlink(),
                            recommended_action="Review — large file",
                        )
                        result.items.append(scan_item)
                        self._items_found += 1

            except (PermissionError, OSError) as e:
                logger.debug(f"Skipped {item_path}: {e}")
                continue

    def _scan_caches(self, result: ScanResult):
        """Scan ~/Library/Caches for cache items older than threshold."""
        logger.info("Scanning caches...")
        cache_dir = HOME / "Library" / "Caches"
        if not cache_dir.exists():
            return

        age_cutoff = datetime.now() - timedelta(days=self.settings.cache_age_days)

        try:
            for entry in cache_dir.iterdir():
                if self.is_cancelled:
                    return
                if len(result.items) >= self.settings.max_results:
                    return

                try:
                    if entry.is_symlink() and not self.settings.follow_symlinks:
                        continue

                    self._report_progress(str(entry))

                    if entry.is_dir():
                        size = get_directory_size(entry, self.settings.follow_symlinks)
                        mtime = datetime.fromtimestamp(entry.stat().st_mtime)
                    elif entry.is_file():
                        stat = entry.stat()
                        size = stat.st_size
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                    else:
                        continue

                    if size > 0 and mtime < age_cutoff:
                        scan_item = ScanItem(
                            path=entry,
                            category=ScanCategory.CACHE,
                            size_bytes=size,
                            last_modified=mtime,
                            is_symlink=entry.is_symlink(),
                            is_directory=entry.is_dir(),
                            recommended_action="Safe to remove — app cache",
                        )
                        result.items.append(scan_item)
                        self._items_found += 1

                except (PermissionError, OSError) as e:
                    logger.debug(f"Skipped cache entry {entry}: {e}")
                    continue

        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot read cache dir: {e}")

    def _scan_old_downloads(self, result: ScanResult):
        """Scan ~/Downloads for files older than the configured threshold."""
        logger.info("Scanning old downloads...")
        downloads_dir = HOME / "Downloads"
        if not downloads_dir.exists():
            return

        age_cutoff = datetime.now() - timedelta(days=self.settings.old_downloads_days)

        try:
            for entry in downloads_dir.iterdir():
                if self.is_cancelled:
                    return
                if len(result.items) >= self.settings.max_results:
                    return

                try:
                    if entry.is_symlink() and not self.settings.follow_symlinks:
                        continue

                    self._report_progress(str(entry))
                    stat = entry.stat(follow_symlinks=self.settings.follow_symlinks)
                    mtime = datetime.fromtimestamp(stat.st_mtime)

                    if mtime < age_cutoff:
                        if entry.is_dir():
                            size = get_directory_size(entry, self.settings.follow_symlinks)
                        else:
                            size = stat.st_size

                        scan_item = ScanItem(
                            path=entry,
                            category=ScanCategory.OLD_DOWNLOAD,
                            size_bytes=size,
                            last_modified=mtime,
                            is_symlink=entry.is_symlink(),
                            is_directory=entry.is_dir(),
                            recommended_action=f"Old download (>{self.settings.old_downloads_days} days)",
                        )
                        result.items.append(scan_item)
                        self._items_found += 1

                except (PermissionError, OSError) as e:
                    logger.debug(f"Skipped download entry {entry}: {e}")
                    continue

        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot read downloads dir: {e}")

    def _scan_logs(self, result: ScanResult):
        """Scan ~/Library/Logs for log files."""
        logger.info("Scanning logs...")
        logs_dir = HOME / "Library" / "Logs"
        if not logs_dir.exists():
            return

        age_cutoff = datetime.now() - timedelta(days=self.settings.cache_age_days)

        try:
            for entry in logs_dir.rglob("*"):
                if self.is_cancelled:
                    return
                if len(result.items) >= self.settings.max_results:
                    return

                try:
                    if entry.is_symlink() and not self.settings.follow_symlinks:
                        continue
                    if not entry.is_file():
                        continue

                    self._report_progress(str(entry))
                    stat = entry.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime)

                    if mtime < age_cutoff and stat.st_size > 0:
                        scan_item = ScanItem(
                            path=entry,
                            category=ScanCategory.LOG_FILE,
                            size_bytes=stat.st_size,
                            last_modified=mtime,
                            recommended_action="Safe to remove — old log file",
                        )
                        result.items.append(scan_item)
                        self._items_found += 1

                except (PermissionError, OSError) as e:
                    logger.debug(f"Skipped log entry {entry}: {e}")
                    continue

        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot read logs dir: {e}")

    def _scan_trash(self, result: ScanResult):
        """Report the size of ~/.Trash without deleting anything."""
        logger.info("Checking Trash size...")
        if not TRASH_PATH.exists():
            return

        self._report_progress(str(TRASH_PATH))

        try:
            total_size = get_directory_size(TRASH_PATH, follow_symlinks=False)
            item_count = sum(1 for _ in TRASH_PATH.iterdir())

            if total_size > 0:
                scan_item = ScanItem(
                    path=TRASH_PATH,
                    category=ScanCategory.TRASH,
                    size_bytes=total_size,
                    last_modified=datetime.fromtimestamp(TRASH_PATH.stat().st_mtime),
                    is_directory=True,
                    recommended_action=f"Trash contains {item_count} items — use Empty Trash",
                )
                result.items.append(scan_item)
                self._items_found += 1

        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot read Trash: {e}")
            result.errors.append(f"Cannot read Trash: {e}")
