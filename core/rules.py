"""
Safety rules and path constraints for Mac Cleanup Tool.

This module defines which paths are safe to scan, which are blocked,
and which personal directories require explicit opt-in.
All path checks use pathlib for consistent cross-platform behavior.
"""

from pathlib import Path

HOME = Path.home()

# ---------------------------------------------------------------------------
# SAFE_PATHS: Default scan locations that are generally safe to clean.
# These are user-space caches/logs/downloads that can be rebuilt by apps.
# ---------------------------------------------------------------------------
SAFE_PATHS = [
    HOME / "Library" / "Caches",
    HOME / "Library" / "Logs",
    HOME / "Downloads",
]

# ---------------------------------------------------------------------------
# BLOCKED_PATH_PREFIXES: Paths that must NEVER be scanned or deleted,
# even if a user tries to add them via the folder picker.
# These include system directories and critical macOS locations.
# ---------------------------------------------------------------------------
BLOCKED_PATH_PREFIXES = [
    Path("/System"),
    Path("/bin"),
    Path("/sbin"),
    Path("/usr/bin"),
    Path("/usr/sbin"),
    Path("/usr/lib"),
    Path("/usr/libexec"),
    Path("/usr/share"),
    Path("/Library"),
    Path("/private"),
    Path("/var"),
    Path("/etc"),
    Path("/tmp"),
    Path("/dev"),
    Path("/proc"),
    Path("/cores"),
    HOME / "Library" / "Application Support" / "com.apple",
    HOME / "Library" / "Keychains",
    HOME / "Library" / "Mail",
    HOME / "Library" / "Messages",
    HOME / "Library" / "Calendars",
    HOME / "Library" / "Contacts",
    HOME / "Library" / "Safari",
]

# ---------------------------------------------------------------------------
# PERSONAL_DOC_PATHS: Personal directories that are OFF by default.
# The user must explicitly opt in via a toggle AND confirm before
# these paths are included in any scan.
# ---------------------------------------------------------------------------
PERSONAL_DOC_PATHS = [
    HOME / "Documents",
    HOME / "Desktop",
    HOME / "Pictures",
    HOME / "Movies",
    HOME / "Music",
    HOME / "Library" / "Mobile Documents",  # iCloud Drive
]

# ---------------------------------------------------------------------------
# TRASH_PATH: The user's Trash directory on macOS.
# ---------------------------------------------------------------------------
TRASH_PATH = HOME / ".Trash"

# ---------------------------------------------------------------------------
# APP_DATA_DIR: Where this application stores its own logs and config.
# ---------------------------------------------------------------------------
APP_DATA_DIR = HOME / ".mac_cleanup_tool"
APP_LOG_DIR = APP_DATA_DIR / "logs"
APP_LOG_FILE = APP_LOG_DIR / "app.log"


def is_path_blocked(path: Path) -> bool:
    """Return True if the given path falls under any blocked prefix."""
    resolved = path.resolve()
    for prefix in BLOCKED_PATH_PREFIXES:
        try:
            resolved.relative_to(prefix.resolve())
            return True
        except ValueError:
            continue
    return False


def is_path_in_personal_docs(path: Path) -> bool:
    """Return True if the path falls under a personal document directory."""
    resolved = path.resolve()
    for personal in PERSONAL_DOC_PATHS:
        try:
            resolved.relative_to(personal.resolve())
            return True
        except ValueError:
            continue
    return False


def is_path_safe_for_scan(path: Path, allow_personal: bool = False) -> bool:
    """
    Check whether a path is safe to scan.

    A path is safe if:
      1. It is NOT under any blocked prefix.
      2. It is NOT a personal doc path (unless allow_personal is True).
    """
    if is_path_blocked(path):
        return False
    if not allow_personal and is_path_in_personal_docs(path):
        return False
    return True


def is_path_safe_for_deletion(path: Path, allow_personal: bool = False) -> bool:
    """
    Check whether a path is safe to delete.
    Uses the same rules as scanning, plus additional checks.
    """
    if is_path_blocked(path):
        return False
    if not allow_personal and is_path_in_personal_docs(path):
        return False
    resolved = path.resolve()
    if resolved == HOME.resolve():
        return False
    if resolved == Path("/").resolve():
        return False
    return True
