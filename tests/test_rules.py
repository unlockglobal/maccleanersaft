"""
Unit tests for safety rules and path blocking logic.
"""

import unittest
from pathlib import Path

from core.rules import (
    HOME,
    BLOCKED_PATH_PREFIXES,
    SAFE_PATHS,
    PERSONAL_DOC_PATHS,
    is_path_blocked,
    is_path_in_personal_docs,
    is_path_safe_for_scan,
    is_path_safe_for_deletion,
)


class TestBlockedPaths(unittest.TestCase):
    """Test that system and critical paths are always blocked."""

    def test_system_paths_blocked(self):
        blocked = [
            Path("/System/Library/something"),
            Path("/bin/bash"),
            Path("/sbin/fsck"),
            Path("/usr/bin/python"),
            Path("/usr/lib/libSystem.B.dylib"),
            Path("/Library/Application Support/something"),
            Path("/private/var/log/something"),
        ]
        for p in blocked:
            self.assertTrue(
                is_path_blocked(p),
                f"Expected {p} to be blocked",
            )

    def test_safe_paths_not_blocked(self):
        safe = [
            HOME / "Library" / "Caches" / "com.example.app",
            HOME / "Library" / "Logs" / "old.log",
            HOME / "Downloads" / "file.zip",
        ]
        for p in safe:
            self.assertFalse(
                is_path_blocked(p),
                f"Expected {p} to NOT be blocked",
            )

    def test_home_itself_not_blocked(self):
        self.assertFalse(is_path_blocked(HOME))

    def test_root_slash_not_in_blocked(self):
        self.assertFalse(is_path_blocked(Path("/")))


class TestPersonalDocPaths(unittest.TestCase):
    """Test that personal document paths are correctly identified."""

    def test_documents_is_personal(self):
        self.assertTrue(is_path_in_personal_docs(HOME / "Documents" / "file.txt"))

    def test_desktop_is_personal(self):
        self.assertTrue(is_path_in_personal_docs(HOME / "Desktop" / "file.txt"))

    def test_pictures_is_personal(self):
        self.assertTrue(is_path_in_personal_docs(HOME / "Pictures" / "photo.jpg"))

    def test_downloads_not_personal(self):
        self.assertFalse(is_path_in_personal_docs(HOME / "Downloads" / "file.zip"))

    def test_caches_not_personal(self):
        self.assertFalse(
            is_path_in_personal_docs(HOME / "Library" / "Caches" / "something")
        )


class TestSafeScan(unittest.TestCase):
    """Test the combined safe-for-scan logic."""

    def test_cache_path_safe(self):
        self.assertTrue(
            is_path_safe_for_scan(HOME / "Library" / "Caches" / "test")
        )

    def test_system_path_unsafe(self):
        self.assertFalse(is_path_safe_for_scan(Path("/System/Library/test")))

    def test_personal_blocked_by_default(self):
        self.assertFalse(
            is_path_safe_for_scan(HOME / "Documents" / "file.txt")
        )

    def test_personal_allowed_with_flag(self):
        self.assertTrue(
            is_path_safe_for_scan(
                HOME / "Documents" / "file.txt", allow_personal=True
            )
        )

    def test_system_blocked_even_with_personal_flag(self):
        self.assertFalse(
            is_path_safe_for_scan(
                Path("/System/Library/test"), allow_personal=True
            )
        )


class TestSafeDeletion(unittest.TestCase):
    """Test the safe-for-deletion logic."""

    def test_cache_deletion_safe(self):
        self.assertTrue(
            is_path_safe_for_deletion(HOME / "Library" / "Caches" / "old")
        )

    def test_system_deletion_blocked(self):
        self.assertFalse(
            is_path_safe_for_deletion(Path("/usr/bin/python"))
        )

    def test_home_root_blocked(self):
        self.assertFalse(is_path_safe_for_deletion(HOME))

    def test_root_blocked(self):
        self.assertFalse(is_path_safe_for_deletion(Path("/")))


if __name__ == "__main__":
    unittest.main()
