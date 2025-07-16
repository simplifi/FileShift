#!/bin/bash

# Cross-platform build script for JSON to CSV Converter
# This creates separate builds for both Intel and Apple Silicon Macs

echo "🔨 Building JSON to CSV Converter.app for multiple architectures..."

# Detect current architecture
ARCH=$(uname -m)
echo "🔍 Current architecture: $ARCH"

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

# Build for current architecture
echo "🏗️  Building native macOS application for $ARCH..."
pyinstaller \
    --name "JSON to CSV Converter-$ARCH" \
    --windowed \
    --onedir \
    --noconfirm \
    --clean \
    --osx-bundle-identifier "com.jsontocsv.converter" \
    json_to_csv_multifile_pyqt.py

# Check if build was successful
if [ -d "dist/JSON to CSV Converter-$ARCH.app" ]; then
    echo "✅ Build successful for $ARCH!"
    
    # Rename to remove architecture suffix for cleaner output
    mv "dist/JSON to CSV Converter-$ARCH.app" "dist/JSON to CSV Converter.app"
    
    echo "📍 App location: dist/JSON to CSV Converter.app"
    echo ""
    echo "🎉 Build complete!"
    echo ""
    echo "📊 Architecture: $ARCH"
    echo ""
    
    if [ "$ARCH" = "arm64" ]; then
        echo "⚠️  This build is for Apple Silicon Macs (M1, M2, M3, etc.)"
        echo ""
        echo "To create an Intel-compatible version:"
        echo "1. Option A: Run this script on an Intel Mac"
        echo "2. Option B: Use a cloud CI/CD service"
        echo "3. Option C: Ask an Intel Mac user to build it"
    else
        echo "⚠️  This build is for Intel Macs"
        echo ""
        echo "To create an Apple Silicon version:"
        echo "1. Run this script on an Apple Silicon Mac"
    fi
    
    echo ""
    echo "📝 Note: PyInstaller builds are architecture-specific when the Python"
    echo "   installation is not universal. For true universal binaries, you need"
    echo "   a universal Python installation or must build on both architectures"
    echo "   and combine them using the 'lipo' tool."
else
    echo "❌ Build failed"
fi

# Deactivate virtual environment
deactivate