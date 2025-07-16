#!/bin/bash

# Optimized build script for smaller app size
echo "🔨 Building optimized JSON to CSV Converter.app..."

# Detect current architecture
ARCH=$(uname -m)
echo "🔍 Detected architecture: $ARCH"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install only required packages
echo "📦 Installing minimal dependencies..."
pip install --no-cache-dir pyinstaller PyQt6-Qt6 PyQt6-sip PyQt6

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build using optimized spec file
echo "🏗️  Building with optimized settings..."
pyinstaller --clean json_to_csv_multifile_pyqt.spec

# Check if build was successful
if [ -d "dist/JSON to CSV Converter.app" ]; then
    echo "✅ Build successful!"
    
    # Show app size
    APP_SIZE=$(du -sh "dist/JSON to CSV Converter.app" | cut -f1)
    echo "📊 App size: $APP_SIZE"
    
    echo "📍 App location: dist/JSON to CSV Converter.app"
    echo ""
    echo "🎉 Optimizations applied:"
    echo "• Excluded unused Qt modules"
    echo "• Stripped debug symbols"
    echo "• Optimized bytecode compilation"
    echo "• Removed unnecessary dependencies"
else
    echo "❌ Build failed"
fi

# Deactivate virtual environment
deactivate