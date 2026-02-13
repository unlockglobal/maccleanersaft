# How to Build & Share Mac Cleanup Tool

## Quick Build (One Command)

On your Mac, open Terminal, navigate to the project folder, and run:

```bash
./build.sh
```

That's it! When it finishes, you'll have:
- **`dist/Mac Cleanup Tool.app`** — the app, ready to double-click
- **`Mac Cleanup Tool.zip`** — a ZIP file you can share with others

---

## What Your Users Do

1. Download the ZIP file
2. Unzip it (double-click the ZIP)
3. Drag **Mac Cleanup Tool** into their Applications folder
4. Double-click to launch

### First-Time Launch Note

macOS may show a warning: *"Mac Cleanup Tool can't be opened because it is from an unidentified developer."*

**Users can bypass this by:**
- Right-clicking the app → choosing **Open** → clicking **Open** in the dialog

To remove this warning permanently, you'll need an Apple Developer account to code-sign and notarize the app (see below).

---

## Manual Build Steps

If you prefer to run each step yourself:

### 1. Install Build Tools

```bash
pip3 install pyinstaller customtkinter send2trash
```

### 2. Convert the Icon

```bash
mkdir -p icon.iconset
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
iconutil -c icns icon.iconset
rm -rf icon.iconset
```

### 3. Build the App

```bash
pyinstaller MacCleanupTool.spec --noconfirm
```

### 4. Test It

```bash
open "dist/Mac Cleanup Tool.app"
```

### 5. Create a ZIP for Sharing

```bash
cd dist
zip -r "../Mac Cleanup Tool.zip" "Mac Cleanup Tool.app"
```

---

## Optional: Use a Custom Icon

Replace `icon.png` with your own 1024x1024 PNG image before building. The build script will automatically convert it to the `.icns` format that macOS uses.

---

## Optional: Code Signing & Notarization

To distribute professionally (no security warnings for users), you need an [Apple Developer account](https://developer.apple.com) ($99/year):

### Sign the App

```bash
codesign --force --deep --sign "Developer ID Application: Your Name (TEAM_ID)" \
    "dist/Mac Cleanup Tool.app"
```

### Notarize for Gatekeeper

```bash
# Create a ZIP for notarization
ditto -c -k --keepParent "dist/Mac Cleanup Tool.app" "notarize.zip"

# Submit
xcrun notarytool submit "notarize.zip" \
    --apple-id "your@apple.id" \
    --team-id "YOUR_TEAM_ID" \
    --password "app-specific-password" \
    --wait

# Staple the ticket
xcrun stapler staple "dist/Mac Cleanup Tool.app"
```

After notarization, users can open the app without any warnings.

---

## Creating a .pkg Installer (Optional)

For a traditional macOS installer experience:

```bash
productbuild --component "dist/Mac Cleanup Tool.app" /Applications \
    "Mac Cleanup Tool.pkg"
```

---

## Project Dependencies

| Package | Purpose |
|---|---|
| customtkinter | Modern UI widgets |
| send2trash | Safe trash operations |
| pyinstaller | App packaging |
| tkinter | GUI framework (included with Python) |

---

## Troubleshooting

**App won't launch (no error shown):**
Run from Terminal to see errors:
```bash
"dist/Mac Cleanup Tool.app/Contents/MacOS/Mac Cleanup Tool"
```

**"App is damaged" error:**
Run this to remove the quarantine flag:
```bash
xattr -cr "dist/Mac Cleanup Tool.app"
```

**Missing modules error during build:**
Make sure you're using the same Python that has your packages installed:
```bash
python3 -m PyInstaller MacCleanupTool.spec --noconfirm
```
