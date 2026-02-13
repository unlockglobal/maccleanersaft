#!/bin/bash
set -e

APP_NAME="Mac Cleanup Tool"
BUNDLE_NAME="${APP_NAME}.app"
DMG_NAME="${APP_NAME}.dmg"
ZIP_NAME="${APP_NAME}.zip"
VOL_NAME="${APP_NAME}"
PYTHON="python3"

echo ""
echo "========================================="
echo "  ${APP_NAME} — Build Script"
echo "========================================="
echo ""

if [[ "$(uname)" != "Darwin" ]]; then
    echo "ERROR: This script must be run on macOS."
    exit 1
fi

if ! command -v $PYTHON &> /dev/null; then
    echo "ERROR: python3 not found. Install Python from python.org first."
    exit 1
fi

echo "[1/7] Installing dependencies..."
$PYTHON -m pip install --upgrade customtkinter send2trash pyinstaller
echo ""

echo "[2/7] Converting icon to .icns format..."
if [ -f "icon.png" ]; then
    mkdir -p icon.iconset
    sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png      2>/dev/null
    sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png   2>/dev/null
    sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png      2>/dev/null
    sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png   2>/dev/null
    sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png    2>/dev/null
    sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png 2>/dev/null
    sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png    2>/dev/null
    sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png 2>/dev/null
    sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png    2>/dev/null
    sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png 2>/dev/null
    iconutil -c icns icon.iconset
    rm -rf icon.iconset
    echo "  Icon created: icon.icns"
else
    echo "  No icon.png found — building without a custom icon."
fi
echo ""

echo "[3/7] Generating PyInstaller spec file..."
cat > MacCleanupTool.spec << 'SPECEOF'
# -*- mode: python ; coding: utf-8 -*-

import os
import sys

try:
    import customtkinter
    ctk_path = os.path.dirname(customtkinter.__file__)
    ctk_datas = [(ctk_path, 'customtkinter')]
except ImportError:
    print("ERROR: customtkinter is not installed.")
    print("Run: pip3 install customtkinter send2trash")
    sys.exit(1)

icon_file = 'icon.icns' if os.path.exists('icon.icns') else None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=ctk_datas,
    hiddenimports=[
        'customtkinter',
        'send2trash',
        'tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Mac Cleanup Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Mac Cleanup Tool',
)

bundle_kwargs = {
    'name': 'Mac Cleanup Tool.app',
    'bundle_identifier': 'com.maccleanuptool.app',
    'info_plist': {
        'CFBundleName': 'Mac Cleanup Tool',
        'CFBundleDisplayName': 'Mac Cleanup Tool',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
        'NSHumanReadableCopyright': 'Copyright 2026. All rights reserved.',
    },
}

if icon_file:
    bundle_kwargs['icon'] = icon_file

app = BUNDLE(
    coll,
    **bundle_kwargs,
)
SPECEOF

echo "  Spec file generated: MacCleanupTool.spec"
echo ""

echo "[4/7] Cleaning previous builds..."
rm -rf build dist "${DMG_NAME}" "${ZIP_NAME}"
echo ""

echo "[5/7] Building ${BUNDLE_NAME}..."
$PYTHON -m PyInstaller MacCleanupTool.spec --noconfirm
echo ""

echo "[6/7] Creating DMG installer..."
rm -rf /tmp/dmg-staging /tmp/temp-cleanup.dmg
mkdir -p /tmp/dmg-staging

cp -r "dist/${BUNDLE_NAME}" /tmp/dmg-staging/
ln -s /Applications /tmp/dmg-staging/Applications

hdiutil create \
    -srcfolder /tmp/dmg-staging \
    -volname "${VOL_NAME}" \
    -fs HFS+ \
    -format UDRW \
    /tmp/temp-cleanup.dmg

MOUNT_DIR="/Volumes/${VOL_NAME}"

hdiutil attach /tmp/temp-cleanup.dmg -mountpoint "${MOUNT_DIR}"

echo '
    tell application "Finder"
        tell disk "'"${VOL_NAME}"'"
            open
            set current view of container window to icon view
            set toolbar visible of container window to false
            set statusbar visible of container window to false
            set the bounds of container window to {200, 120, 760, 440}
            set viewOptions to the icon view options of container window
            set arrangement of viewOptions to not arranged
            set icon size of viewOptions to 100
            set position of item "'"${BUNDLE_NAME}"'" of container window to {140, 160}
            set position of item "Applications" of container window to {420, 160}
            update without registering applications
            delay 1
            close
        end tell
    end tell
' | osascript || true

sync
hdiutil detach "${MOUNT_DIR}"

hdiutil convert /tmp/temp-cleanup.dmg \
    -format UDZO \
    -o "${DMG_NAME}"

rm -rf /tmp/dmg-staging /tmp/temp-cleanup.dmg
echo "  DMG created: ${DMG_NAME}"
echo ""

echo "[7/7] Creating ZIP backup..."
cd dist
zip -r "../${ZIP_NAME}" "${BUNDLE_NAME}" -x "*.DS_Store"
cd ..
echo ""

echo "========================================="
echo "  BUILD COMPLETE!"
echo "========================================="
echo ""
echo "  App:  dist/${BUNDLE_NAME}"
echo "  DMG:  ${DMG_NAME}"
echo "  ZIP:  ${ZIP_NAME}"
echo ""
echo "  To test:  open \"dist/${BUNDLE_NAME}\""
echo ""
echo "  To share: Send the DMG file to your users."
echo "  They open it and drag the app to Applications."
echo ""
