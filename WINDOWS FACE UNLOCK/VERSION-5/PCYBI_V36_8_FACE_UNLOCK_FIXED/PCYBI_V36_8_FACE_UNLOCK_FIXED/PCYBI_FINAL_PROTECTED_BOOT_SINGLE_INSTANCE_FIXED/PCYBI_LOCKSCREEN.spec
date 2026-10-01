# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['cv2.face']
hiddenimports += collect_submodules('cv2')
hiddenimports += collect_submodules('pywinauto')
hiddenimports += collect_submodules('comtypes')


a = Analysis(
    ['PCYBI_LOCKSCREEN.py'],
    pathex=[],
    binaries=[],
    datas=[('data/haarcascade_frontalface_default.xml', 'data'), ('data/haarcascade_eye.xml', 'data'), ('common.py', '.')],
    hiddenimports=hiddenimports,
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
    name='PCYBI_LOCKSCREEN',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
