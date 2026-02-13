# Mac Cleanup Tool

A safe, transparent macOS cleanup application built in Python with a Tkinter GUI.

## Safety Philosophy

**Safety is the #1 priority.** This tool is designed to never cause data loss:

- **System files are NEVER touched.** Paths under `/System`, `/bin`, `/sbin`, `/usr`, `/Library` (system-wide), `/private`, and other critical directories are permanently blocked.
- **Personal folders are OFF by default.** Documents, Desktop, Pictures, Movies, Music, and iCloud Drive are excluded unless you explicitly enable them in Settings AND confirm.
- **Dry Run mode is ON by default.** The tool shows what *would* be deleted but makes no changes until you turn Dry Run off.
- **All deletions go to Trash.** Nothing is permanently deleted — items are moved to `~/.Trash` using the `send2trash` library or a safe fallback.
- **Typed confirmation required.** You must type "DELETE" to confirm any deletion, and "EMPTY TRASH" to empty the Trash.
- **Review first, always.** Scan results are displayed in a table with full details before any action is taken.

## What It Scans

| Category | Default Location | What It Finds |
|---|---|---|
| Large Files | `~/Downloads` + custom folders | Files above size threshold (default 1 GB) |
| Caches | `~/Library/Caches` | Application caches older than threshold (default 30 days) |
| Old Downloads | `~/Downloads` | Files older than threshold (default 90 days) |
| Log Files | `~/Library/Logs` | Old log files |
| Trash Report | `~/.Trash` | Current trash size (reporting only) |

## What It Does NOT Delete

- System files (`/System`, `/bin`, `/usr`, etc.)
- Personal documents (`~/Documents`, `~/Desktop`, `~/Pictures`, etc.) unless explicitly enabled
- Running application data
- Keychains, Mail, Messages, Calendars, Contacts
- Safari data
- Anything requiring elevated (sudo) privileges

## How to Run on macOS

### Prerequisites
- macOS 10.15+ (Catalina or later)
- Python 3.11 or later
- Tkinter (included with Python on macOS)

### Quick Start

```bash
# Clone or download the project
git clone <your-repo-url>
cd mac-cleanup-tool

# Install dependencies
pip install send2trash

# Run the app
python main.py
```

### Using the App

1. **Select scan types** in the left sidebar (Large Files, Caches, etc.)
2. **Click "Scan"** to find reclaimable space
3. **Review results** in the table — sort by size, date, category
4. **Select items** by clicking the checkbox column
5. **Click "Delete Selected"** to move items to Trash
6. **Type "DELETE"** in the confirmation dialog to proceed
7. **Export results** to CSV for record-keeping

### Settings

- **Large file threshold:** Minimum file size to flag (default 1024 MB)
- **Old downloads days:** Age threshold for downloads (default 90 days)
- **Cache age days:** Age threshold for cache items (default 30 days)
- **Max results:** Maximum items to show (default 500)
- **Include hidden files:** Scan dot-files (default OFF)
- **Follow symlinks:** Follow symbolic links (default OFF, not recommended)
- **Dry Run mode:** Simulate deletion without changes (default ON)
- **Allow personal folders:** Enable scanning Documents, Desktop, etc. (default OFF)

## Project Structure

```
mac-cleanup-tool/
├── main.py                 # Application entry point
├── core/
│   ├── rules.py           # Safety rules, blocked/safe paths
│   ├── models.py          # Data models (ScanItem, ScanSettings)
│   ├── scanner.py         # Scanning engine with threading
│   ├── delete.py          # Safe deletion operations
│   └── utils.py           # Utilities (formatting, CSV, logging)
├── ui/
│   ├── app_window.py      # Main application window
│   ├── results_table.py   # Sortable results table
│   ├── settings_dialog.py # Settings configuration dialog
│   └── confirm_dialog.py  # Typed confirmation dialogs
├── tests/
│   └── test_rules.py      # Unit tests for safety rules
├── build_notes.md         # Packaging instructions
└── README.md              # This file
```

## Logging

Application logs are written to `~/.mac_cleanup_tool/logs/app.log`. This includes scan operations, deletions, errors, and blocked path attempts.

## Running Tests

```bash
python -m unittest tests/test_rules.py -v
```
