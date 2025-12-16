# FileShift

A powerful native macOS application for converting, splitting, and merging JSON, JSONL, and CSV files.

[![Latest Release](https://img.shields.io/github/v/release/simplifi/FileShift)](https://github.com/simplifi/FileShift/releases/latest)

---

## Quick Start

**Download:** [FileShift for Apple Silicon](https://github.com/simplifi/FileShift/releases/latest/download/FileShift-apple-silicon.dmg) (M1/M2/M3/M4)

**First Launch:** Right-click the app and select "Open" to bypass the security warning (see [Installation](#installation) for details)

---

## Features

### Convert Tab
- **Batch Processing**: Convert multiple JSON files to CSV at once
- **Smart Schema Analysis**: Automatically analyzes and compares schemas across files
- **Multiple Merge Strategies**:
  - Smart Auto: Fields present in 70%+ of files
  - All Available: Union of all fields across files
  - Common Only: Fields present in ALL files
  - Most Complete File: Use the file with most fields as template
  - Keep Separate: Individual CSV files with their own schemas
- **Nested Field Support**: Handles complex nested JSON structures

### Split Tab
- **Split by Number of Files**: Divide a file into N equal parts
- **Split by Rows**: Create files with a specific number of records each
- **Split by Size**: Create files of approximately N kilobytes each
- **Format Flexibility**: Input can be JSON, JSONL, or CSV; output format is selectable

### Merge Tab
- **Combine Multiple Files**: Merge any number of files into one
- **Mixed Format Support**: Merge JSON, JSONL, and CSV files together
- **Schema Strategies**:
  - Union: Include all fields from all files
  - Intersection: Only include fields common to all files
  - First File: Use the schema from the first file
- **Output Format Selection**: Choose JSON, JSONL, or CSV output

### General
- **Native macOS Interface**: Built with PyQt6 for a smooth, native experience
- **Real-time Progress**: Track operations with progress bars and status logs
- **Memory Efficient**: Streaming processing for large files

## Download

| Mac Type | Download Link |
|----------|--------------|
| **Apple Silicon** (M1/M2/M3/M4) | [Download DMG](https://github.com/simplifi/FileShift/releases/latest/download/FileShift-apple-silicon.dmg) |

> **All Releases**: View all versions on the [Releases page](https://github.com/simplifi/FileShift/releases)

## Installation

1. Download the DMG file
2. Double-click the DMG to mount it
3. Drag "FileShift" to your Applications folder
4. **First time running**: The app will show a security warning because it's not signed with an Apple Developer certificate

### Security Warning Fix

Since the app isn't signed with an Apple Developer certificate, macOS will block it on first launch. Here's how to open it:

1. **Try to open the app** - You'll see a warning saying "FileShift.app cannot be opened because Apple cannot verify it is free of malware." Click **Done** (not "Move to Trash").

2. **Open System Settings** - Go to **Privacy & Security** and scroll down to the **Security** section. You'll see a message: *"FileShift.app" was blocked to protect your Mac.* Click **Open Anyway**.

3. **Confirm** - A final dialog will appear asking if you're sure. Click **Open Anyway** to launch the app.

After this one-time setup, the app will open normally without any warnings.

## Usage

### Converting Files

1. Go to the **Convert** tab
2. Click "Browse for JSON Files" to select one or more JSON files
3. The app automatically analyzes the structure of your files
4. Select a merge strategy for handling different schemas
5. Click "Convert All Files" and choose an output directory

### Splitting Files

1. Go to the **Split** tab
2. Select a single input file (JSON, JSONL, or CSV)
3. Choose a split mode:
   - **By number of files**: Split into N equal parts
   - **By rows per file**: Each output file has N records
   - **By file size**: Each output file is approximately N KB
4. Select output format and directory
5. Click "Split File"

### Merging Files

1. Go to the **Merge** tab
2. Select multiple input files (can be mixed formats)
3. Choose a schema strategy:
   - **Union**: All fields from all files
   - **Intersection**: Only common fields
   - **First file**: Use first file's schema
4. Select output format and file path
5. Click "Merge Files"

## Building from Source

### Requirements

- macOS 11 or later
- Python 3.9 or later
- PyQt6

### Quick Build

```bash
# Clone the repository
git clone https://github.com/simplifi/FileShift.git
cd FileShift

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install PyQt6 pyinstaller

# Build the app
pyinstaller --clean fileshift.spec
```

The built application will be in `dist/FileShift.app`

## Development

### Setting up the development environment

```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Run the application
python json_to_csv_multifile_pyqt.py

# Run tests
pytest
```

### Project Structure

```
FileShift/
├── json_to_csv_multifile_pyqt.py  # Main GUI application
├── src/
│   └── converters/                 # Core conversion library
│       ├── base.py                 # Base classes and types
│       ├── handlers.py             # Format handlers (JSON, JSONL, CSV)
│       └── operations.py           # Split and merge operations
├── tests/                          # Test suite
├── fileshift.spec                  # PyInstaller build spec
└── pyproject.toml                  # Project configuration
```

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

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/simplifi/FileShift).
