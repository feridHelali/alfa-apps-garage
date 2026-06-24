"""GuideWindow — MDI sub-window displaying the user guide.

Layout: QSplitter with a chapter list on the left and a QTextBrowser on the right.
Chapters are loaded from Markdown files in resources/guide/fr/.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMdiSubWindow,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from garage_app.tools.guide_generator.md_renderer import render as md_render
from garage_app.settings import resource_path


_CHAPTERS: list[tuple[str, str]] = [
    ("00_introduction.md", "Introduction"),
    ("01_reception.md", "1. Réception"),
    ("02_atelier.md", "2. Atelier"),
    ("03_stock.md", "3. Stock"),
    ("04_facturation.md", "4. Facturation"),
    ("05_administration.md", "5. Administration"),
    ("06_rapports.md", "6. Rapports"),
    ("07_faq.md", "7. FAQ"),
    ("08_devis_proforma.md", "8. Devis & Proforma"),
]


class GuideWindow(QMdiSubWindow):
    """User guide MDI sub-window."""

    def __init__(self, ctx=None, session=None) -> None:
        super().__init__()
        self.setWindowTitle("Guide utilisateur")
        self.setMinimumSize(900, 640)
        self.resize(1000, 680)

        self._guide_dir = resource_path("resources/guide/fr")
        self._img_dir = resource_path("resources/guide/img")

        widget = QWidget()
        self.setWidget(widget)
        root = QVBoxLayout(widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { border: none; background: #f0f0f0; }")
        lbl = QLabel("  Guide utilisateur — Gestion Réparation Voiture  ")
        lbl.setStyleSheet("font-weight:bold; color:#0055a5;")
        toolbar.addWidget(lbl)
        toolbar.addSeparator()
        btn_print = QPushButton("Imprimer…")
        btn_print.setFixedHeight(24)
        btn_print.clicked.connect(self._print)
        toolbar.addWidget(btn_print)
        root.addWidget(toolbar)

        # splitter: chapter list | content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        # left: chapter list
        self._chapter_list = QListWidget()
        self._chapter_list.setFixedWidth(200)
        self._chapter_list.setStyleSheet(
            "QListWidget { border: none; border-right: 1px solid #ccc; }"
            "QListWidget::item { padding: 6px 10px; }"
            "QListWidget::item:selected { background: #0055a5; color: white; }"
        )
        for _filename, title in _CHAPTERS:
            self._chapter_list.addItem(QListWidgetItem(title))
        self._chapter_list.currentRowChanged.connect(self._load_chapter)
        splitter.addWidget(self._chapter_list)

        # right: content browser
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setStyleSheet("QTextBrowser { border: none; padding: 8px; }")
        splitter.addWidget(self._browser)

        splitter.setSizes([200, 800])

        # load first chapter
        self._chapter_list.setCurrentRow(0)

    # ------------------------------------------------------------------

    def _load_chapter(self, row: int) -> None:
        if row < 0 or row >= len(_CHAPTERS):
            return
        filename, _ = _CHAPTERS[row]
        md_path = Path(self._guide_dir) / filename
        if not md_path.exists():
            self._browser.setHtml(
                f"<p style='color:red;'>Fichier non trouvé : {md_path}</p>"
            )
            return
        markdown = md_path.read_text(encoding="utf-8")
        html = md_render(markdown, image_dir=Path(self._img_dir))
        self._browser.setHtml(f"<html><body>{html}</body></html>")
        self._browser.scrollToAnchor("")
        self._browser.verticalScrollBar().setValue(0)

    def _print(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            self._browser.print(printer)
