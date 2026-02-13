# Mac Cleanup Tool

## Overview
A safe macOS cleanup application built in Python with Tkinter GUI. The tool helps users find and clean up disk space by scanning for large files, old caches, stale downloads, and log files.

**Safety-first design:** System files are never touched, personal folders require opt-in, Dry Run mode is on by default, all deletions go to Trash, and typed confirmation is required.

## Current State
- All modules implemented and functional
- GUI launches via VNC display
- 18 unit tests passing for safety rules
- Application runs with `python main.py`

## Project Architecture

```
├── main.py                 # Application entry point
├── core/
│   ├── __init__.py
│   ├── rules.py           # Safety rules (SAFE_PATHS, BLOCKED_PATH_PREFIXES)
│   ├── models.py          # Data models (ScanItem, ScanSettings, ScanResult)
│   ├── scanner.py         # Threaded scanning engine
│   ├── delete.py          # Safe deletion with send2trash
│   └── utils.py           # Formatting, CSV export, logging setup
├── ui/
│   ├── __init__.py
│   ├── app_window.py      # Main application window
│   ├── results_table.py   # Sortable Treeview results table
│   ├── settings_dialog.py # Settings configuration dialog
│   └── confirm_dialog.py  # Typed confirmation dialogs
├── tests/
│   ├── __init__.py
│   └── test_rules.py      # Unit tests for path safety rules
├── README.md
├── build_notes.md         # PyInstaller packaging instructions
└── replit.md              # This file
```

## Key Dependencies
- Python 3.11+ with tkinter (python311Full nix package)
- send2trash (pip package for safe trash operations)
- tk (nix system package)

## Recent Changes
- 2026-02-13: Initial implementation of all modules
- Desktop app runs via VNC output type in workflow

## User Preferences
- None recorded yet
