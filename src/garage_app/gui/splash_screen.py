from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication, QSplashScreen

_LOGO_SVG = Path(__file__).parents[3] / "assets" / "brand" / "alfa_computers_logo.svg"

_W, _H = 520, 300


def _build_pixmap() -> QPixmap:
    px = QPixmap(_W, _H)
    px.fill(QColor("#ffffff"))

    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    # ── Logo (SVG) centred in upper half ────────────────────────────────────
    if _LOGO_SVG.exists():
        renderer = QSvgRenderer(str(_LOGO_SVG))
        logo_w, logo_h = 360, 120
        logo_x = (_W - logo_w) // 2
        logo_y = 50
        from PyQt6.QtCore import QRectF
        renderer.render(painter, QRectF(logo_x, logo_y, logo_w, logo_h))
    else:
        painter.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        painter.setPen(QColor("#0055a5"))
        painter.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "Alfa Computers Apps")

    # ── App name ─────────────────────────────────────────────────────────────
    painter.setFont(QFont("Segoe UI", 13))
    painter.setPen(QColor("#1a1a1a"))
    painter.drawText(0, 185, _W, 30, Qt.AlignmentFlag.AlignHCenter, "Gestion Réparation Voiture")

    # ── Thin separator ────────────────────────────────────────────────────────
    painter.setPen(QColor("#d4d0c8"))
    painter.drawLine(60, 225, _W - 60, 225)

    # ── Loading message ───────────────────────────────────────────────────────
    painter.setFont(QFont("Segoe UI", 9))
    painter.setPen(QColor("#808080"))
    painter.drawText(0, 235, _W, 20, Qt.AlignmentFlag.AlignHCenter, "Chargement…")

    # ── Version ───────────────────────────────────────────────────────────────
    painter.setFont(QFont("Segoe UI", 8))
    painter.setPen(QColor("#b0b0b0"))
    painter.drawText(0, _H - 20, _W, 18, Qt.AlignmentFlag.AlignHCenter, "v0.1.0 — Alfa Computers Apps")

    # ── Border ────────────────────────────────────────────────────────────────
    painter.setPen(QColor("#d4d0c8"))
    painter.drawRect(0, 0, _W - 1, _H - 1)

    painter.end()
    return px


class SplashScreen(QSplashScreen):
    def __init__(self) -> None:
        super().__init__(_build_pixmap(), Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

    def update_message(self, msg: str) -> None:
        self.showMessage(
            msg,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            QColor("#0055a5"),
        )
        QApplication.processEvents()
