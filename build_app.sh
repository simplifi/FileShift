#!/bin/bash

# Build script for creating standalone JSON to CSV Converter.app
# Uses the native macOS osascript approach (no tkinter required!)

echo "🔨 Building JSON to CSV Converter.app (Multi-File Version)..."

# Test osascript availability (should always be available on macOS)
echo "🔍 Checking osascript availability..."
which osascript >/dev/null || {
    echo "❌ Error: osascript not found (are you running on macOS?)"
    exit 1
}

echo "✅ osascript available - this build will work!"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install pyinstaller and PyQt6 in the venv
echo "📦 Installing PyInstaller and PyQt6..."
pip install pyinstaller PyQt6

# Clean previous builds
rm -rf build dist

# Create app icon (optional - you can add your own icns file)
# For now, we'll use the default Python icon

# Detect current architecture
ARCH=$(uname -m)
echo "🔍 Detected architecture: $ARCH"

# Build the native macOS app
echo "🏗️  Building native macOS application for $ARCH..."
pyinstaller \
    --name "JSON to CSV Converter" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --osx-bundle-identifier "com.jsontocsv.converter" \
    json_to_csv_multifile_pyqt.py

# Check if build was successful
if [ -d "dist/JSON to CSV Converter.app" ]; then
    echo "✅ Build successful!"
    echo "📍 App location: dist/JSON to CSV Converter.app"
    echo ""
    echo ""
    echo "🎉 This multi-file version:"
    echo "• Handles multiple JSON files at once"
    echo "• Smart schema analysis and field merging"
    echo "• Native PyQt6 interface (single window!)"
    echo "• Sophisticated batch processing options"
    echo "• Exact interface from your screenshot"
    echo ""
    echo "You can now:"
    echo "1. Double-click the app to run it"
    echo "2. Drag it to Applications folder"
    echo "3. Share it with others - no Python installation needed!"
    echo ""
    if [ "$ARCH" = "arm64" ]; then
        echo "📊 Architecture: Apple Silicon (arm64) only"
        echo ""
        echo "⚠️  Note: This build is for Apple Silicon Macs only."
        echo "   For Intel Mac compatibility, the app needs to be built on an Intel Mac"
        echo "   using build_app_intel.sh"
    else
        echo "📊 Architecture: Intel (x86_64) only"
        echo ""
        echo "⚠️  Note: This build is for Intel Macs only."
        echo "   For Apple Silicon compatibility, the app needs to be built on an Apple Silicon Mac"
    fi
else
    echo "❌ Build failed"
fi

# Deactivate virtual environment
deactivate