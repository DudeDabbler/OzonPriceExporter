# -*- mode: python ; coding: utf-8 -*-
"""Portable one-folder build for Ozon Customer Price Exporter."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata


HERE = Path(SPECPATH).resolve()
ROOT = HERE.parents[1]

playwright_datas, playwright_binaries, playwright_hidden = collect_all("playwright")
openpyxl_datas, openpyxl_binaries, openpyxl_hidden = collect_all("openpyxl")

datas = [
    (str(HERE / "static"), "tools/ozon_price_exporter/static"),
]
datas += playwright_datas
datas += openpyxl_datas
datas += copy_metadata("playwright")
datas += copy_metadata("openpyxl")

hiddenimports = sorted(
    set(
        playwright_hidden
        + openpyxl_hidden
        + [
            "greenlet",
            "playwright.sync_api",
            "playwright._impl._driver",
            "tools.ozon_price_exporter",
        ]
    )
)

a = Analysis(
    [str(HERE / "portable_entry.py")],
    pathex=[str(ROOT)],
    binaries=playwright_binaries + openpyxl_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "PyInstaller",
        "pandas",
        "numpy",
        "pyarrow",
        "matplotlib",
        "IPython",
        "jupyter",
        "notebook",
        "tkinter",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OzonPriceExporter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

bundle = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="OzonPriceExporter",
)
