# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['PCYBI_WATCHDOG_SERVICE.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['win32serviceutil', 'win32service', 'win32event', 'win32ts', 'win32security', 'win32process', 'win32profile', 'win32con', 'servicemanager', 'win32timezone'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PCYBI_WATCHDOG_SERVICE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
