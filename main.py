"""
Mac Cleanup Tool — Entry Point

A safe macOS cleanup application that helps users reclaim disk space
by scanning for large files, old caches, stale downloads, and log files.

Safety is the top priority:
- System files are NEVER touched
- Personal folders require explicit opt-in
- Dry Run mode is ON by default
- All deletions go to Trash (not permanent)
- Typed confirmation required for all deletions

Run with: python main.py
"""

import sys
from core.utils import setup_logging


def main():
    logger = setup_logging()
    logger.info("Mac Cleanup Tool starting...")

    try:
        from ui.app_window import AppWindow
        app = AppWindow()
        logger.info("GUI initialized successfully")
        app.run()
    except ImportError as e:
        logger.error(f"Failed to import UI components: {e}")
        print(f"Error: {e}")
        print("Make sure tkinter is available on your system.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)

    logger.info("Mac Cleanup Tool exited.")


if __name__ == "__main__":
    main()
