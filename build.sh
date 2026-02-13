#!/bin/bash
set -e

echo ""
echo "========================================="
echo "  Mac Cleanup Tool — Build Script"
echo "========================================="
echo ""

if [[ "$(uname)" != "Darwin" ]]; then
    echo "ERROR: This script must be run on macOS."
    exit 1
fi

PYTHON="python3"

if ! command -v $PYTHON &> /dev/null; then
    echo "ERROR: python3 not found. Install Python from python.org first."
    exit 1
fi

echo "[1/5] Installing dependencies..."
$PYTHON -m pip install --upgrade customtkinter send2trash pyinstaller
echo ""

echo "[2/5] Converting icon to .icns format..."
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

echo "[3/5] Cleaning previous builds..."
rm -rf build dist
echo ""

echo "[4/5] Building Mac Cleanup Tool.app..."
$PYTHON -m PyInstaller MacCleanupTool.spec --noconfirm
echo ""

echo "[5/5] Creating distributable ZIP..."
cd dist
zip -r "../Mac Cleanup Tool.zip" "Mac Cleanup Tool.app" -x "*.DS_Store"
cd ..
echo ""

echo "========================================="
echo "  BUILD COMPLETE!"
echo "========================================="
echo ""
echo "  App:  dist/Mac Cleanup Tool.app"
echo "  ZIP:  Mac Cleanup Tool.zip"
echo ""
echo "  To test: open \"dist/Mac Cleanup Tool.app\""
echo ""
echo "  To share: Send the ZIP file to your users."
echo "  They unzip it and drag the app to Applications."
echo ""
