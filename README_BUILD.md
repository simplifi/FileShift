# Building FileShift

## Quick Build

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

## Build Configuration

The build uses `fileshift.spec` which:
- Excludes unnecessary PyQt6 modules to reduce app size
- Includes the `src/converters` package for split/merge functionality
- Creates a proper macOS app bundle

## GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/build.yml`) that automatically builds the app for Apple Silicon Macs on every push to `main`.

To create a release with downloadable DMG:
```bash
git tag v0.2.0
git push --tags
```

This triggers the release workflow which:
1. Builds the app
2. Creates a DMG installer
3. Publishes it as a GitHub Release

## Architecture Notes

- **Apple Silicon (M1/M2/M3/M4)**: Supported via GitHub Actions (`macos-15` runner)
- **Intel Macs**: Not currently built (GitHub retired `macos-13` runners)

If you need an Intel build, you can build locally on an Intel Mac using the same `fileshift.spec` file.

## Checking Your Architecture

```bash
uname -m
```
- `arm64` = Apple Silicon Mac
- `x86_64` = Intel Mac
