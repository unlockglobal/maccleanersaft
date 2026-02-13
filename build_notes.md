# Build & Packaging Notes

## Packaging with PyInstaller

### Prerequisites

```bash
pip install pyinstaller
```

### Creating a macOS .app Bundle

```bash
# Basic build (single directory)
pyinstaller --name "Mac Cleanup Tool" \
    --windowed \
    --onedir \
    --add-data "core:core" \
    --add-data "ui:ui" \
    main.py

# Single-file build (slower startup but one file)
pyinstaller --name "Mac Cleanup Tool" \
    --windowed \
    --onefile \
    --add-data "core:core" \
    --add-data "ui:ui" \
    main.py
```

### PyInstaller Options Explained

- `--name`: Sets the application name
- `--windowed`: Creates a GUI app (no terminal window)
- `--onedir`: Output is a directory containing the app and dependencies
- `--onefile`: Output is a single executable (larger, slower startup)
- `--add-data`: Includes additional data files/directories

### Output Location

After building, find the app at:
- `dist/Mac Cleanup Tool.app` (macOS app bundle)
- `dist/Mac Cleanup Tool/` (directory mode)

### Spec File Customization

For advanced builds, create a `.spec` file:

```bash
pyinstaller --name "Mac Cleanup Tool" --windowed main.py --specpath .
```

Then edit `Mac Cleanup Tool.spec` for custom settings like:
- Icon file (`.icns` format for macOS)
- Bundle identifier
- Version info
- Code signing

### Adding an Icon

1. Create a 1024x1024 PNG icon
2. Convert to `.icns` using `iconutil` or an online converter
3. Add to PyInstaller: `--icon=icon.icns`

## Creating a .pkg Installer

For distribution outside the Mac App Store:

### Using `productbuild` (built into macOS)

```bash
# First, build the .app with PyInstaller
# Then create the installer:
productbuild --component "dist/Mac Cleanup Tool.app" /Applications \
    "Mac Cleanup Tool.pkg"
```

### Using Packages.app

1. Download [Packages](http://s.sudre.free.fr/Software/Packages/about.html)
2. Create a new project
3. Add the `.app` bundle as a payload
4. Set installation destination to `/Applications`
5. Build the `.pkg`

## Code Signing (Recommended for Distribution)

```bash
# Sign the app
codesign --force --deep --sign "Developer ID Application: Your Name" \
    "dist/Mac Cleanup Tool.app"

# Notarize (required for macOS Catalina+)
xcrun altool --notarize-app \
    --primary-bundle-id "com.yourname.mac-cleanup-tool" \
    --file "Mac Cleanup Tool.pkg" \
    --username "your@apple.id"
```

## Dependencies

The application uses minimal dependencies for maximum compatibility:

| Package | Purpose | Required |
|---|---|---|
| tkinter | GUI framework | Yes (included with Python) |
| send2trash | Safe trash operations | Optional (fallback available) |
| pathlib | Path handling | Yes (stdlib) |
| threading | Background scanning | Yes (stdlib) |
| csv | Report export | Yes (stdlib) |

## Testing Before Packaging

Always test the packaged app:

```bash
# Run from the build output
open "dist/Mac Cleanup Tool.app"

# Check logs for errors
cat ~/.mac_cleanup_tool/logs/app.log
```

## Platform Requirements

- macOS 10.15 (Catalina) or later
- Python 3.11+
- Approximately 50 MB disk space for the packaged app
