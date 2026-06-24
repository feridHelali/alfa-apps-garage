from __future__ import annotations

import base64

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QMdiSubWindow, QPushButton, QTextBrowser,
    QVBoxLayout, QWidget,
)

from garage_app.settings import resource_path

_LOGO_PATH = resource_path("assets", "brand", "alfa_computers_logo.svg")


def _logo_uri() -> str:
    try:
        data = base64.b64encode(_LOGO_PATH.read_bytes()).decode()
        return f"data:image/svg+xml;base64,{data}"
    except Exception:
        return ""


_BASE_CSS = """
body {
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    color: #1C1C1E;
    margin: 0;
    padding: 0;
}
.header {
    background: #007AFF;
    color: white;
    padding: 12px 16px;
    border-radius: 6px 6px 0 0;
}
.header h1 { margin: 0; font-size: 14pt; font-weight: 700; }
.header .subtitle { font-size: 9pt; opacity: 0.85; margin-top: 2px; }
.section {
    margin: 12px 0;
    padding: 0 4px;
}
.section h2 {
    font-size: 11pt;
    font-weight: 600;
    color: #007AFF;
    border-bottom: 1px solid #D1D1D6;
    padding-bottom: 4px;
    margin-bottom: 8px;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
}
th {
    background: #F2F2F7;
    color: #6E6E73;
    font-weight: 600;
    text-align: left;
    padding: 5px 8px;
    border-bottom: 1px solid #D1D1D6;
}
td {
    padding: 5px 8px;
    border-bottom: 1px solid #E5E5EA;
}
tr:last-child td { border-bottom: none; }
.num { text-align: right; }
.total-row td { font-weight: 700; background: #F9F9FB; }
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 8pt;
    font-weight: 600;
}
.badge-ok    { background: #D1FAE5; color: #065F46; }
.badge-warn  { background: #FEF3C7; color: #92400E; }
.badge-danger{ background: #FEE2E2; color: #991B1B; }
.kpi-grid {
    display: table;
    width: 100%;
    margin-bottom: 12px;
}
.kpi {
    display: table-cell;
    text-align: center;
    padding: 10px;
    border: 1px solid #E5E5EA;
    border-radius: 6px;
    width: 25%;
}
.kpi .val { font-size: 14pt; font-weight: 700; color: #007AFF; }
.kpi .lbl { font-size: 8pt; color: #6E6E73; margin-top: 2px; }
.footer {
    margin-top: 16px;
    font-size: 8pt;
    color: #AEAEB2;
    border-top: 1px solid #E5E5EA;
    padding-top: 6px;
    text-align: center;
}
"""


def build_html(title: str, subtitle: str, body: str, icon_svg_b64: str = "") -> str:
    logo_uri = _logo_uri()
    logo_html = (
        f'<img src="{logo_uri}" '
        'style="height:34px; float:right; margin-top:2px; margin-left:12px; opacity:0.92;">'
        if logo_uri else ""
    )
    icon_html = (
        f'<img src="data:image/svg+xml;base64,{icon_svg_b64}" '
        'style="width:42px; height:42px; float:right; margin-left:8px; margin-top:2px;">'
        if icon_svg_b64 else ""
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>{_BASE_CSS}</style>
</head><body>
<div class="header">
  {logo_html}{icon_html}
  <div class="subtitle">Alfa Computers Apps — Gestion Réparation Voiture</div>
  <h1>{title}</h1>
  <div class="subtitle">{subtitle}</div>
</div>
{body}
<div class="footer">Généré par Alfa Computers Apps — www.alfacomputers.tn</div>
</body></html>"""


class ReportViewerWindow(QMdiSubWindow):
    """Generic MDI window showing an HTML report with Print button."""

    def __init__(self, title: str, html: str) -> None:
        super().__init__()
        self.setWindowTitle(title)
        self._html = html

        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # toolbar
        bar = QWidget()
        bar.setStyleSheet("background: #F2F2F7; border-bottom: 1px solid #D1D1D6;")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(8, 4, 8, 4)
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: 600; font-size: 10pt;")
        btn_print = QPushButton("Imprimer…")
        btn_preview = QPushButton("Aperçu avant impression")
        btn_print.clicked.connect(self._print)
        btn_preview.clicked.connect(self._preview)
        bar_layout.addWidget(lbl)
        bar_layout.addStretch()
        bar_layout.addWidget(btn_preview)
        bar_layout.addWidget(btn_print)
        layout.addWidget(bar)

        self._browser = QTextBrowser()
        self._browser.setOpenLinks(False)
        self._browser.setHtml(html)
        layout.addWidget(self._browser)

        self.setWidget(main)
        self.resize(820, 640)

    def _get_doc(self) -> QTextDocument:
        doc = QTextDocument()
        doc.setHtml(self._html)
        return doc

    def _print(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            self._get_doc().print(printer)

    def _preview(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintPreviewDialog(printer, self)
        dlg.paintRequested.connect(lambda p: self._get_doc().print(p))
        dlg.exec()
