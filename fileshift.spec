# -*- mode: python ; coding: utf-8 -*-
# FileShift PyInstaller spec file

block_cipher = None

excluded_modules = [
    'PyQt6.QtBluetooth', 'PyQt6.QtDesigner', 'PyQt6.QtHelp',
    'PyQt6.QtLocation', 'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtNetwork', 'PyQt6.QtNfc', 'PyQt6.QtOpenGL',
    'PyQt6.QtOpenGLWidgets', 'PyQt6.QtPdf', 'PyQt6.QtPdfWidgets',
    'PyQt6.QtPositioning', 'PyQt6.QtPrintSupport', 'PyQt6.QtQml',
    'PyQt6.QtQuick', 'PyQt6.QtQuick3D', 'PyQt6.QtQuickWidgets',
    'PyQt6.QtRemoteObjects', 'PyQt6.QtSensors', 'PyQt6.QtSerialPort',
    'PyQt6.QtSpatialAudio', 'PyQt6.QtSql', 'PyQt6.QtSvg',
    'PyQt6.QtSvgWidgets', 'PyQt6.QtTest', 'PyQt6.QtWebChannel',
    'PyQt6.QtWebEngine', 'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineWidgets',
    'PyQt6.QtWebSockets', 'PyQt6.QtXml',
    'test', 'unittest', 'xml', 'email', 'html', 'http', 'urllib',
    'ssl', '_ssl', 'cryptography', 'certifi', 'PIL', 'numpy', 'matplotlib',
]

a = Analysis(
    ['json_to_csv_multifile_pyqt.py'],
    pathex=['.'],
    datas=[('src', 'src')],
    hiddenimports=['src.converters', 'src.converters.base', 'src.converters.handlers', 'src.converters.operations'],
    excludes=excluded_modules,
    optimize=2,
)

excluded_binaries = [
    'QtNetwork', 'QtPdf', 'QtSvg', 'QtWebEngine', 'QtMultimedia',
    'QtQml', 'QtQuick', 'QtBluetooth', 'QtPositioning', 'QtSensors',
    'QtSerialPort', 'QtSql', 'QtTest', 'QtXml',
]

a.binaries = [x for x in a.binaries if not any(excl in x[0] for excl in excluded_binaries)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='FileShift',
    debug=False,
    strip=True,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=True,
    upx=False,
    name='FileShift',
)

app = BUNDLE(
    coll,
    name='FileShift.app',
    bundle_identifier='com.simplifi.fileshift',
)
