#!/bin/bash

# Build script for creating standalone JSON to CSV Converter.app for Intel Macs
# Can be run on Apple Silicon Macs using Rosetta 2

echo "🔨 Building JSON to CSV Converter.app (Multi-File Version) for Intel Macs..."

# Check architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
    echo "🔄 Running on Apple Silicon - will use Rosetta 2 to build Intel version"
    echo "   This will create an Intel-compatible app using x86_64 Python"
    
    # Check if Rosetta 2 is installed
    if ! arch -x86_64 /usr/bin/true 2>/dev/null; then
        echo "❌ Rosetta 2 is not installed. Please install it first:"
        echo "   softwareupdate --install-rosetta"
        exit 1
    fi
fi

# Test osascript availability (should always be available on macOS)
echo "🔍 Checking osascript availability..."
which osascript >/dev/null || {
    echo "❌ Error: osascript not found (are you running on macOS?)"
    exit 1
}

echo "✅ osascript available - this build will work!"

# Use arch command to run as x86_64 if on ARM Mac
if [ "$ARCH" = "arm64" ]; then
    PYTHON_CMD="arch -x86_64 /usr/bin/python3"
    PIP_PREFIX="arch -x86_64"
else
    PYTHON_CMD="python3"
    PIP_PREFIX=""
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv_intel" ]; then
    echo "📦 Creating Intel virtual environment..."
    $PYTHON_CMD -m venv .venv_intel
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv_intel/bin/activate

# Install pyinstaller and PyQt6 in the venv
echo "📦 Installing PyInstaller and PyQt6 for Intel..."
$PIP_PREFIX pip install pyinstaller PyQt6

# Clean previous builds
rm -rf build dist

# Build the native macOS app for Intel
echo "🏗️  Building native macOS application for Intel (x86_64)..."
$PIP_PREFIX pyinstaller \
    --name "JSON to CSV Converter" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --osx-bundle-identifier "com.jsontocsv.converter" \
    --target-arch x86_64 \
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
    echo "• Built specifically for Intel Macs (x86_64)"
    echo ""
    echo "You can now:"
    echo "1. Double-click the app to run it"
    echo "2. Drag it to Applications folder"
    echo "3. Share it with others - no Python installation needed!"
    echo ""
    echo "📊 Architecture: Intel (x86_64) only"
    echo ""
    echo "Note: This build is specifically for Intel Macs."
    echo "For Apple Silicon Macs, use build_app.sh instead."
else
    echo "❌ Build failed"
fi

# Deactivate virtual environment
deactivate