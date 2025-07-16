# Building JSON to CSV Converter for Different Architectures

## Current Situation

The app is built using PyInstaller, which creates architecture-specific binaries based on the Python installation used during the build process.

## Architecture Compatibility

- **Apple Silicon (M1/M2/M3) Macs**: Need an arm64 build
- **Intel Macs**: Need an x86_64 build
- **Universal Binary**: Requires special setup (see below)

## Build Scripts Available

### 1. `build_app.sh` (Default)
Builds for the current machine's architecture.
```bash
./build_app.sh
```

### 2. `build_app_intel.sh` (Intel-specific)
Attempts to build for Intel Macs. Works best when run on an Intel Mac.
```bash
./build_app_intel.sh
```

### 3. `build_app_cross_platform.sh` (Current architecture)
Builds for the current architecture with clear labeling.
```bash
./build_app_cross_platform.sh
```

## Solutions for Cross-Architecture Compatibility

### Option 1: Build on Target Architecture
The most reliable method is to build the app on the target architecture:
- For Intel Macs: Build on an Intel Mac
- For Apple Silicon: Build on an Apple Silicon Mac

### Option 2: GitHub Actions (Recommended)
Use GitHub Actions to automatically build for both architectures:

1. Create `.github/workflows/build.yml`:
```yaml
name: Build App

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-macos:
    strategy:
      matrix:
        os: [macos-latest, macos-13]  # macos-latest is ARM, macos-13 is Intel
    runs-on: ${{ matrix.os }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyinstaller PyQt6
    
    - name: Build application
      run: |
        pyinstaller --name "JSON to CSV Converter" \
          --windowed \
          --onedir \
          --noconfirm \
          --clean \
          --osx-bundle-identifier "com.jsontocsv.converter" \
          json_to_csv_multifile_pyqt.py
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: JSON-to-CSV-Converter-${{ matrix.os }}
        path: dist/
```

### Option 3: Manual Universal Binary Creation
If you have access to both architectures:

1. Build on Intel Mac: `./build_app.sh`
2. Build on Apple Silicon Mac: `./build_app.sh`
3. Combine using `lipo`:
```bash
# Extract the executables
cp "dist_intel/JSON to CSV Converter.app/Contents/MacOS/JSON to CSV Converter" converter_intel
cp "dist_arm/JSON to CSV Converter.app/Contents/MacOS/JSON to CSV Converter" converter_arm

# Create universal binary
lipo -create -output "JSON to CSV Converter" converter_intel converter_arm

# Replace in app bundle
cp "JSON to CSV Converter" "dist/JSON to CSV Converter.app/Contents/MacOS/"
```

### Option 4: Use Universal Python
Install a universal Python distribution that includes both architectures, then build normally. This is complex and not recommended for most users.

## Current Limitation

Due to the Homebrew Python installation being architecture-specific (ARM64 on Apple Silicon), creating a universal binary directly on this machine results in the error:
```
IncompatibleBinaryArchError: [binary] is not a fat binary!
```

## Recommendation

For distributing to users with different Mac architectures:
1. Use GitHub Actions to build for both architectures automatically
2. Provide separate downloads for Intel and Apple Silicon Macs
3. Let users know which version to download based on their Mac type

Users can check their architecture by running:
```bash
uname -m
```
- `x86_64` = Intel Mac
- `arm64` = Apple Silicon Mac