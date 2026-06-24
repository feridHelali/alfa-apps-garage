from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QMdiArea

from garage_app.settings import resource_path

_LOGO_SVG = resource_path("assets", "brand", "alfa_computers_logo.svg")


class BrandedMdiArea(QMdiArea):
    """MDI area that paints the Alfa Computers logo + tagline as a watermark."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._renderer: QSvgRenderer | None = None
        if _LOGO_SVG.exists():
            self._renderer = QSvgRenderer(str(_LOGO_SVG))

    def paintEvent(self, event) -> None:  # type: ignore[override]
        super().paintEvent(event)

        if not self.subWindowList():
            # Only paint watermark when no sub-windows are open
            self._paint_watermark()

    def _paint_watermark(self) -> None:
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.viewport().width()
        h = self.viewport().height()
        cx = w / 2
        cy = h / 2

        painter.setOpacity(0.18)

        if self._renderer:
            logo_w = min(400, int(w * 0.55))
            logo_h = int(logo_w * 100 / 300)   # keep SVG aspect ratio (300×100)
            logo_x = cx - logo_w / 2
            logo_y = cy - logo_h / 2 - 30
            self._renderer.render(painter, QRectF(logo_x, logo_y, logo_w, logo_h))
        else:
            painter.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
            painter.setPen(QColor("#0055a5"))
            painter.drawText(
                0, int(cy - 40), w, 50,
                Qt.AlignmentFlag.AlignHCenter, "Alfa Computers Apps"
            )

        painter.setOpacity(0.12)
        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QColor("#0055a5"))
        painter.drawText(
            0, int(cy + 55), w, 24,
            Qt.AlignmentFlag.AlignHCenter,
            "Gestion Réparation Voiture — Solutions de Gestion sur Mesure",
        )

        painter.end()
