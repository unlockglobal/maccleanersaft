"""
Deletion operations for Mac Cleanup Tool.

All deletion goes through safety checks before execution.
Default behavior is "move to Trash" — never permanent delete.
"""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

from core.models import ItemStatus, ScanItem
from core.rules import TRASH_PATH, is_path_safe_for_deletion

logger = logging.getLogger("mac_cleanup")

try:
    from send2trash import send2trash as _send2trash_func
    HAS_SEND2TRASH = True
except ImportError:
    _send2trash_func = None
    HAS_SEND2TRASH = False
    logger.info("send2trash not available; will use fallback trash method")


def _move_to_trash_fallback(path: Path) -> None:
    """
    Fallback method to move a file/dir to ~/.Trash when send2trash is unavailable.
    Handles name conflicts by appending a counter.
    """
    trash = TRASH_PATH
    trash.mkdir(exist_ok=True)

    dest = trash / path.name
    counter = 1
    while dest.exists():
        stem = path.stem
        suffix = path.suffix
        dest = trash / f"{stem}_{counter}{suffix}"
        counter += 1

    if path.is_dir():
        shutil.move(str(path), str(dest))
    else:
        shutil.move(str(path), str(dest))

    logger.info(f"Moved to trash (fallback): {path} -> {dest}")


def move_to_trash(path: Path) -> None:
    """
    Move a file or directory to the system Trash.
    Prefers send2trash library, falls back to manual move.
    """
    if HAS_SEND2TRASH and _send2trash_func is not None:
        _send2trash_func(str(path))
        logger.info(f"Moved to trash (send2trash): {path}")
    else:
        _move_to_trash_fallback(path)


def delete_items(
    items: List[ScanItem],
    allow_personal: bool = False,
    dry_run: bool = True,
) -> List[Tuple[ScanItem, bool, str]]:
    """
    Delete a list of scan items with safety checks.

    Args:
        items: List of ScanItem objects to delete.
        allow_personal: Whether personal doc paths are allowed.
        dry_run: If True, only simulate deletion (no actual changes).

    Returns:
        List of (item, success, message) tuples.
    """
    results: List[Tuple[ScanItem, bool, str]] = []

    for item in items:
        if dry_run:
            item.status = ItemStatus.SKIPPED
            results.append((item, True, "Dry run — no changes made"))
            continue

        if not is_path_safe_for_deletion(item.path, allow_personal):
            item.status = ItemStatus.FAILED
            item.failure_reason = "Path is blocked by safety rules"
            results.append((item, False, "Blocked by safety rules"))
            logger.warning(f"Blocked deletion of unsafe path: {item.path}")
            continue

        if not item.path.exists():
            item.status = ItemStatus.FAILED
            item.failure_reason = "File not found"
            results.append((item, False, "File not found"))
            continue

        try:
            move_to_trash(item.path)
            item.status = ItemStatus.TRASHED
            results.append((item, True, "Moved to Trash"))
        except PermissionError as e:
            item.status = ItemStatus.FAILED
            item.failure_reason = f"Permission denied: {e}"
            results.append((item, False, f"Permission denied: {e}"))
            logger.error(f"Permission denied deleting {item.path}: {e}")
        except OSError as e:
            item.status = ItemStatus.FAILED
            item.failure_reason = f"OS error: {e}"
            results.append((item, False, f"OS error: {e}"))
            logger.error(f"OS error deleting {item.path}: {e}")
        except Exception as e:
            item.status = ItemStatus.FAILED
            item.failure_reason = str(e)
            results.append((item, False, str(e)))
            logger.error(f"Unexpected error deleting {item.path}: {e}", exc_info=True)

    return results


def empty_trash() -> Tuple[bool, str]:
    """
    Empty the user's Trash (~/.Trash).

    This is a separate, explicit action requiring typed confirmation in the UI.
    Returns (success, message).
    """
    if not TRASH_PATH.exists():
        return True, "Trash is already empty."

    try:
        item_count = sum(1 for _ in TRASH_PATH.iterdir())
        if item_count == 0:
            return True, "Trash is already empty."

        for entry in TRASH_PATH.iterdir():
            try:
                if entry.is_dir() and not entry.is_symlink():
                    shutil.rmtree(str(entry))
                else:
                    entry.unlink()
            except (PermissionError, OSError) as e:
                logger.error(f"Failed to remove trash item {entry}: {e}")
                return False, f"Failed to remove some items: {e}"

        logger.info(f"Emptied Trash: {item_count} items removed")
        return True, f"Trash emptied: {item_count} items removed."

    except (PermissionError, OSError) as e:
        logger.error(f"Failed to empty trash: {e}")
        return False, f"Failed to empty trash: {e}"
