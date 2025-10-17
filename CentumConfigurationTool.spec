# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Kushal\\PycharmProjects\\Image_font_to C Converter\\dummy_final_app.py'],
    pathex=[],
    binaries=[],
    datas=[('icons\\FontConverterToC.jpg', 'icons'), ('icons\\ImageConverterToC.jpg', 'icons')],
    hiddenimports=[],
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
    name='CentumConfigurationTool',
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
    icon=['C:\\Users\\Kushal\\PycharmProjects\\Image_font_to C Converter\\icons\\CentumTool.ico'],
)
