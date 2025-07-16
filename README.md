# JSON to CSV Converter (Multi-File)

A powerful native macOS application for converting JSON files to CSV format with advanced schema analysis and field merging capabilities.

![Build Status](https://github.com/simplifi/json-converter/workflows/Build%20JSON%20to%20CSV%20Converter/badge.svg)

---

## 🚀 Quick Start

**Download for your Mac:**
- [📥 Intel Mac](https://github.com/simplifi/json-converter/releases/latest/download/JSON-to-CSV-Converter-intel.dmg) • [📥 Apple Silicon](https://github.com/simplifi/json-converter/releases/latest/download/JSON-to-CSV-Converter-apple-silicon.dmg)

**⚠️ First Launch:** Right-click the app and select "Open" to bypass the security warning (see [Installation](#installation) for details)

---

## Features

- 🚀 **Batch Processing**: Convert multiple JSON files at once
- 🧠 **Smart Schema Analysis**: Automatically analyzes and compares schemas across files
- 🔀 **Multiple Merge Strategies**:
  - Smart Auto: Fields present in 70%+ of files
  - All Available: Union of all fields across files
  - Common Only: Fields present in ALL files
  - Most Complete File: Use the file with most fields as template
  - Keep Separate: Individual CSV files with their own schemas
- 📊 **Nested Field Support**: Handles complex nested JSON structures
- 🖥️ **Native macOS Interface**: Built with PyQt6 for a smooth, native experience
- 📝 **Real-time Status Logging**: Track conversion progress with detailed logs

## 📥 Download

### Quick Download (Latest Release)

| Mac Type | Download Link |
|----------|--------------|
| **Intel Macs** | [📥 Download Intel DMG](https://github.com/simplifi/json-converter/releases/latest/download/JSON-to-CSV-Converter-intel.dmg) |
| **Apple Silicon** (M1/M2/M3) | [📥 Download Apple Silicon DMG](https://github.com/simplifi/json-converter/releases/latest/download/JSON-to-CSV-Converter-apple-silicon.dmg) |

> **📋 All Releases**: View all versions on the [Releases page](https://github.com/simplifi/json-converter/releases)

### How to check your Mac type
1. Click the Apple menu  > About This Mac
2. Look for "Chip" or "Processor"
   - Intel processor = Download Intel version
   - Apple M1/M2/M3 = Download Apple Silicon version

## Installation

1. Download the appropriate DMG file for your Mac
2. Double-click the DMG to mount it
3. Drag "JSON to CSV Converter" to your Applications folder
4. **First time running**: The app will show a security warning because it's not signed with an Apple Developer certificate

### 🔒 Security Warning Fix

When you first run the app, you'll see this warning:
> "JSON to CSV Converter.app" cannot be opened because Apple cannot verify that it is free from malware.

**To safely run the app:**

1. **Right-click** (or Control-click) on the app
2. Select **"Open"** from the context menu
3. Click **"Open"** in the dialog that appears
4. The app will now run normally

**Alternative method:**
1. Go to **System Preferences** > **Security & Privacy** > **General**
2. Click **"Open Anyway"** next to the blocked app message
3. Enter your password when prompted

**Why this happens:**
- The app is unsigned (requires a paid Apple Developer account)
- This is normal for open-source software distributed outside the Mac App Store
- The warning is Apple's way of ensuring you intentionally want to run the app

**Note:** After the first time, the app will open normally without any warnings.

## Usage

1. **Select JSON Files**: Click "Browse for JSON Files" to select one or more JSON files
2. **Schema Analysis**: The app automatically analyzes the structure of your files
3. **Choose Strategy**: Select how you want to handle different schemas across files
4. **Convert**: Click "Convert All Files" and choose an output directory

### Field Selection Strategies

- **Smart Auto**: Includes fields that appear in at least 70% of your files
- **All Available**: Includes every field found across all files (union)
- **Common Only**: Only includes fields that exist in every single file
- **Most Complete File**: Uses the schema from the file with the most fields
- **Keep Files Separate**: Creates individual CSV files, each with its own schema

## Building from Source

### Requirements

- macOS 10.13 or later
- Python 3.8 or later
- PyQt6

### Quick Build

```bash
# Clone the repository
git clone https://github.com/simplifi/json-converter.git
cd json-converter

# Run the build script
./build_app.sh
```

The built application will be in `dist/JSON to CSV Converter.app`

### Building for Different Architectures

See [README_BUILD.md](README_BUILD.md) for detailed instructions on building for both Intel and Apple Silicon Macs.

## Development

### Setting up the development environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python json_to_csv_multifile_pyqt.py
```

### Project Structure

```
json-converter/
├── json_to_csv_multifile_pyqt.py  # Main application
├── generate_sample_data.py         # Generate test data
├── build_app.sh                    # Build script
├── requirements.txt                # Python dependencies
└── samples/                        # Sample JSON files
```

## Sample Data

Generate sample data for testing:

```bash
python generate_sample_data.py
```

This creates various JSON files with different schemas and sizes in the `samples/` directory.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Packaged with [PyInstaller](https://www.pyinstaller.org/)

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/simplifi/json-converter).