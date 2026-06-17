# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Gestion Réparation Voiture — Alfa Computers Apps
Usage: pyinstaller garage_app.spec
"""

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        (str(ROOT / "assets"),             "assets"),
        (str(ROOT / "resources"),          "resources"),
    ],
    hiddenimports=[
        "sqlalchemy.dialects.sqlite",
        "bcrypt",
        "PyQt6.QtPrintSupport",
        "PyQt6.QtSvg",
        "PyQt6.QtSvgWidgets",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GarageReparation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ROOT / "assets" / "icons" / "app_icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="garage_reparation",
)
