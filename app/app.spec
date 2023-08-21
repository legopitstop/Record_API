# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['C:\\Users\\1589l\\Documents\\GitHub\\Minecraft\\Record_API\\app/src/app.pyw'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\1589l\\AppData\\Local\\Packages\\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\\LocalCache\\local-packages\\Python311\\site-packages\\customtkinter', 'customtkinter/'), ('C:\\Users\\1589l\\Documents\\GitHub\\Minecraft\\Record_API\\app/src/resources/icon.ico', '.'), ('C:\\Users\\1589l\\Documents\\GitHub\\Minecraft\\Record_API\\app/src/resources', 'resources/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\1589l\\Documents\\GitHub\\Minecraft\\Record_API\\app\\src\\resources\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)
