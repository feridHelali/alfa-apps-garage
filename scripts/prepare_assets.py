"""
Prepare build assets from SVG sources.

Outputs:
  assets/icons/app_icon.ico          — multi-size ICO (16→256) for EXE and installer
  installer/wizard_image.bmp         — 164×314 wizard side-panel (Inno Setup modern)
  installer/wizard_small_image.bmp   — 55×55 wizard small image (Inno Setup modern)

Requires PyQt6 + PyQt6-Qt6 (already in project deps). Run from project root:
  python scripts/prepare_assets.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Qt helpers
# ---------------------------------------------------------------------------

_qapp = None  # kept alive for the process lifetime


def _ensure_qapp() -> None:
    global _qapp
    from PyQt6.QtWidgets import QApplication
    if QApplication.instance() is None:
        _qapp = QApplication(sys.argv[:1])
    else:
        _qapp = QApplication.instance()


def _render_svg_to_png_bytes(svg_path: Path, size: int) -> bytes:
    from PyQt6.QtCore import QBuffer, QIODeviceBase
    from PyQt6.QtGui import QImage, QPainter
    from PyQt6.QtSvg import QSvgRenderer

    renderer = QSvgRenderer(str(svg_path))
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(0x00000000)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()

    buf = QBuffer()
    buf.open(QIODeviceBase.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def _render_svg_wizard_bmp(
    svg_path: Path,
    canvas_w: int,
    canvas_h: int,
    bg_top: str,
    bg_bottom: str,
    out_path: Path,
) -> None:
    """Render logo SVG on a gradient background to produce a wizard BMP."""
    from PyQt6.QtCore import QPointF, QRectF
    from PyQt6.QtGui import (
        QColor,
        QImage,
        QLinearGradient,
        QPainter,
        QPainterPath,
    )
    from PyQt6.QtSvg import QSvgRenderer

    img = QImage(canvas_w, canvas_h, QImage.Format.Format_RGB32)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Gradient background
    grad = QLinearGradient(QPointF(0, 0), QPointF(0, canvas_h))
    grad.setColorAt(0.0, QColor(bg_top))
    grad.setColorAt(1.0, QColor(bg_bottom))
    painter.fillRect(img.rect(), grad)

    # Render SVG centred in upper 60% of canvas with padding
    logo_h = int(canvas_h * 0.55)
    logo_w = canvas_w - 20
    logo_x = 10
    logo_y = int(canvas_h * 0.08)

    renderer = QSvgRenderer(str(svg_path))
    # Preserve aspect ratio
    svg_size = renderer.defaultSize()
    if svg_size.width() > 0 and svg_size.height() > 0:
        ratio = min(logo_w / svg_size.width(), logo_h / svg_size.height())
        rw = int(svg_size.width() * ratio)
        rh = int(svg_size.height() * ratio)
        rx = logo_x + (logo_w - rw) // 2
        ry = logo_y + (logo_h - rh) // 2
    else:
        rx, ry, rw, rh = logo_x, logo_y, logo_w, logo_h

    renderer.render(painter, QRectF(rx, ry, rw, rh))

    # Bottom text strip
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont

    font = QFont("Segoe UI", 8)
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))
    text_rect = QRectF(0, canvas_h * 0.82, canvas_w, canvas_h * 0.18)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                     "Alfa Computers Apps\nSolutions de Gestion sur Mesure")

    painter.end()
    img.save(str(out_path), "BMP")
    print(f"  ok {out_path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# ICO writer (Vista+ PNG-in-ICO format)
# ---------------------------------------------------------------------------

def _write_ico(png_list: list[bytes], out_path: Path) -> None:
    """Write ICO file with embedded PNGs (Windows Vista+ format)."""
    n = len(png_list)
    # ICONDIR: reserved=0, type=1 (icon), count=n
    header = struct.pack("<HHH", 0, 1, n)

    # First image data starts after header (6) + n*ICONDIRENTRY (16 each)
    offset = 6 + n * 16
    entries = bytearray()

    for png in png_list:
        # Read width/height from PNG IHDR (bytes 16-20 = width, 20-24 = height)
        w = struct.unpack(">I", png[16:20])[0]
        h = struct.unpack(">I", png[20:24])[0]
        # ICO stores 0 to mean 256
        bw = 0 if w >= 256 else w
        bh = 0 if h >= 256 else h
        entries += struct.pack("<BBBBHHII", bw, bh, 0, 0, 1, 32, len(png), offset)
        offset += len(png)

    with out_path.open("wb") as f:
        f.write(header)
        f.write(entries)
        for png in png_list:
            f.write(png)

    print(f"  ok {out_path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _ensure_qapp()

    icon_svg = ROOT / "assets" / "icons" / "app_icon.svg"
    logo_svg = ROOT / "assets" / "brand" / "alfa_computers_logo.svg"
    icons_dir = ROOT / "assets" / "icons"
    inst_dir = ROOT / "installer"

    if not icon_svg.exists():
        sys.exit(f"Missing: {icon_svg}")
    if not logo_svg.exists():
        sys.exit(f"Missing: {logo_svg}")

    print(">> Generating app_icon.ico ...")
    sizes = [16, 24, 32, 48, 64, 128, 256]
    pngs = [_render_svg_to_png_bytes(icon_svg, s) for s in sizes]
    _write_ico(pngs, icons_dir / "app_icon.ico")

    print(">> Generating installer wizard images ...")
    # Tall side-panel: 164×314
    _render_svg_wizard_bmp(
        logo_svg, 164, 314,
        bg_top="#0055a5", bg_bottom="#003d7a",
        out_path=inst_dir / "wizard_image.bmp",
    )
    # Small top-right image: 55×55
    _render_svg_wizard_bmp(
        logo_svg, 55, 55,
        bg_top="#0055a5", bg_bottom="#0055a5",
        out_path=inst_dir / "wizard_small_image.bmp",
    )

    print("OK All assets ready.")


if __name__ == "__main__":
    main()
