from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMdiSubWindow,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy,
    QSplitter, QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.tools.report_engine.html_template import ColonneConfig, HtmlReportTemplate
from garage_app.tools.report_engine.html_template_manager import HtmlTemplateManager
from garage_app.tools.report_engine.html_template_renderer import SAMPLE_CONTEXTS, HtmlTemplateRenderer
from garage_app.gui.widgets.icon_helper import icon as _icon

_DOC_TYPES = [
    ("facture", "Facture client"),
    ("dossier", "Fiche réparation"),
    ("bon_travail", "Bon de travail"),
    ("facture_achat", "Facture d'achat"),
]

_DOC_TYPE_KEYS = [k for k, _ in _DOC_TYPES]
_DOC_TYPE_LABELS = {k: v for k, v in _DOC_TYPES}


def _color_swatch(hex_color: str) -> QIcon:
    px = QPixmap(16, 16)
    px.fill(QColor(hex_color))
    return QIcon(px)


class _ColumnRow(QWidget):
    """Single row in the columns editor table."""

    def __init__(self, col: ColonneConfig, on_change) -> None:
        super().__init__()
        self._col = col
        self._on_change = on_change
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(4)

        self._chk_visible = QCheckBox()
        self._chk_visible.setChecked(col.visible)
        self._chk_visible.setFixedWidth(20)
        self._chk_visible.toggled.connect(self._save)

        self._lbl_champ = QLabel(col.champ)
        self._lbl_champ.setFixedWidth(100)
        self._lbl_champ.setStyleSheet("color:#6E6E73; font-size:9pt;")

        self._edit_titre = QLineEdit(col.titre)
        self._edit_titre.setPlaceholderText("Titre colonne")
        self._edit_titre.textChanged.connect(self._save)

        self._combo_align = QComboBox()
        self._combo_align.addItems(["left", "center", "right"])
        self._combo_align.setCurrentText(col.align)
        self._combo_align.setFixedWidth(72)
        self._combo_align.currentTextChanged.connect(self._save)

        layout.addWidget(self._chk_visible)
        layout.addWidget(self._lbl_champ)
        layout.addWidget(self._edit_titre, 1)
        layout.addWidget(self._combo_align)

    def _save(self) -> None:
        self._col.visible = self._chk_visible.isChecked()
        self._col.titre = self._edit_titre.text().strip() or self._col.champ
        self._col.align = self._combo_align.currentText()
        self._on_change()


class _BandeTab(QWidget):
    def __init__(self, template: HtmlReportTemplate, on_change) -> None:
        super().__init__()
        self._template = template
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        form_grp = QGroupBox("Bande d'en-tête")
        form = QFormLayout(form_grp)

        self._color_btn = QPushButton()
        self._color_btn.setFixedWidth(80)
        self._color_btn.setIcon(_color_swatch(template.couleur_bande))
        self._color_btn.setText(template.couleur_bande)
        self._color_btn.clicked.connect(self._pick_color)
        form.addRow("Couleur bande :", self._color_btn)

        self._chk_logo = QCheckBox("Afficher le logo")
        self._chk_logo.setChecked(template.show_logo)
        self._chk_logo.toggled.connect(self._save)
        form.addRow(self._chk_logo)

        self._chk_societe = QCheckBox("Afficher le nom société")
        self._chk_societe.setChecked(template.show_societe)
        self._chk_societe.toggled.connect(self._save)
        form.addRow(self._chk_societe)

        self._chk_slogan = QCheckBox("Afficher le slogan")
        self._chk_slogan.setChecked(template.show_slogan)
        self._chk_slogan.toggled.connect(self._save)
        form.addRow(self._chk_slogan)

        layout.addWidget(form_grp)
        layout.addStretch()

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._template.couleur_bande), self)
        if color.isValid():
            self._template.couleur_bande = color.name()
            self._color_btn.setIcon(_color_swatch(color.name()))
            self._color_btn.setText(color.name())
            self._on_change()

    def _save(self) -> None:
        self._template.show_logo = self._chk_logo.isChecked()
        self._template.show_societe = self._chk_societe.isChecked()
        self._template.show_slogan = self._chk_slogan.isChecked()
        self._on_change()


class _ColonnesTab(QWidget):
    def __init__(self, template: HtmlReportTemplate, on_change) -> None:
        super().__init__()
        self._template = template
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        hdr = QWidget()
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(6, 0, 6, 0)
        for lbl, w in [("Vis.", 20), ("Champ", 100), ("Titre", -1), ("Align", 72)]:
            l = QLabel(lbl)
            l.setStyleSheet("font-weight:600; color:#6E6E73; font-size:9pt;")
            if w > 0:
                l.setFixedWidth(w)
            hdr_layout.addWidget(l, 0 if w > 0 else 1)
        layout.addWidget(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        self._cols_layout = QVBoxLayout(scroll_content)
        self._cols_layout.setContentsMargins(0, 0, 0, 0)
        self._cols_layout.setSpacing(1)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        self._refresh_rows()

    def _refresh_rows(self) -> None:
        while self._cols_layout.count():
            item = self._cols_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for col in self._template.colonnes:
            row = _ColumnRow(col, self._on_change)
            self._cols_layout.addWidget(row)
        self._cols_layout.addStretch()


class _TotauxTab(QWidget):
    def __init__(self, template: HtmlReportTemplate, on_change) -> None:
        super().__init__()
        self._template = template
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        grp = QGroupBox("Lignes du bloc totaux")
        form = QVBoxLayout(grp)

        self._chk_ht = QCheckBox("Afficher Total HT")
        self._chk_tva = QCheckBox("Afficher TVA")
        self._chk_ttc = QCheckBox("Afficher Total TTC")
        self._chk_paye = QCheckBox("Afficher Montant payé")
        self._chk_reste = QCheckBox("Afficher Reste à payer / Soldé")

        for chk, attr in [
            (self._chk_ht, "show_ht"),
            (self._chk_tva, "show_tva"),
            (self._chk_ttc, "show_ttc"),
            (self._chk_paye, "show_paye"),
            (self._chk_reste, "show_reste"),
        ]:
            chk.setChecked(getattr(template, attr))
            chk.toggled.connect(self._save)
            form.addWidget(chk)

        layout.addWidget(grp)
        layout.addStretch()

    def _save(self) -> None:
        self._template.show_ht = self._chk_ht.isChecked()
        self._template.show_tva = self._chk_tva.isChecked()
        self._template.show_ttc = self._chk_ttc.isChecked()
        self._template.show_paye = self._chk_paye.isChecked()
        self._template.show_reste = self._chk_reste.isChecked()
        self._on_change()


class _PiedTab(QWidget):
    def __init__(self, template: HtmlReportTemplate, on_change) -> None:
        super().__init__()
        self._template = template
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        grp = QGroupBox("Pied de page")
        form = QFormLayout(grp)

        self._edit_texte = QLineEdit(template.texte_legal)
        self._edit_texte.textChanged.connect(self._save)
        form.addRow("Texte légal :", self._edit_texte)

        self._chk_page = QCheckBox("Numéro de page")
        self._chk_page.setChecked(template.show_page_number)
        self._chk_page.toggled.connect(self._save)
        form.addRow(self._chk_page)

        layout.addWidget(grp)

        css_grp = QGroupBox("CSS personnalisé (avancé)")
        css_layout = QVBoxLayout(css_grp)
        from PyQt6.QtWidgets import QPlainTextEdit
        self._css_edit = QPlainTextEdit(template.css_custom)
        self._css_edit.setPlaceholderText("/* ex: td { font-size: 8pt; } */")
        self._css_edit.setMaximumHeight(90)
        self._css_edit.textChanged.connect(self._save)
        css_layout.addWidget(self._css_edit)
        layout.addWidget(css_grp)

        layout.addStretch()

    def _save(self) -> None:
        self._template.texte_legal = self._edit_texte.text()
        self._template.show_page_number = self._chk_page.isChecked()
        self._template.css_custom = self._css_edit.toPlainText()
        self._on_change()


class _EditorPanel(QWidget):
    """Center panel: name field + tab editors for each template section."""

    def __init__(self, template: HtmlReportTemplate, on_change) -> None:
        super().__init__()
        self._template = template
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Nom du modèle :"))
        self._nom_edit = QLineEdit(template.nom)
        self._nom_edit.textChanged.connect(self._on_name_change)
        name_row.addWidget(self._nom_edit, 1)
        layout.addLayout(name_row)

        tabs = QTabWidget()
        tabs.addTab(_BandeTab(template, on_change), "En-tête")
        tabs.addTab(_ColonnesTab(template, on_change), "Colonnes")
        tabs.addTab(_TotauxTab(template, on_change), "Totaux")
        tabs.addTab(_PiedTab(template, on_change), "Pied")
        layout.addWidget(tabs, 1)

    def _on_name_change(self, text: str) -> None:
        self._template.nom = text.strip() or "Modèle"
        self._on_change()

    def get_nom(self) -> str:
        return self._nom_edit.text().strip()


class ReportDesignerWindow(QMdiSubWindow):
    """3-pane self-service Report Designer (Crystal Reports style)."""

    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._manager = HtmlTemplateManager()
        self._renderer = HtmlTemplateRenderer()
        self._current_type: str = _DOC_TYPE_KEYS[0]
        self._current_template: HtmlReportTemplate | None = None
        self._dirty = False

        self.setWindowTitle("Concepteur de documents")
        self._build_ui()
        self.resize(1200, 720)
        self._load_type(_DOC_TYPE_KEYS[0])

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setStyleSheet("background:#F2F2F7; border-bottom:1px solid #D1D1D6;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(8)

        tb_layout.addWidget(QLabel("Type de document :"))
        self._type_combo = QComboBox()
        for key, label in _DOC_TYPES:
            self._type_combo.addItem(label, key)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        tb_layout.addWidget(self._type_combo)

        tb_layout.addStretch()

        self._btn_new = QPushButton(_icon("new"), "+ Nouveau")
        self._btn_new.clicked.connect(self._new_template)
        self._btn_dup = QPushButton(_icon("new"), "Dupliquer")
        self._btn_dup.clicked.connect(self._duplicate_template)
        self._btn_save = QPushButton(_icon("save"), "Enregistrer")
        self._btn_save.setStyleSheet("font-weight:600; color:#0055a5;")
        self._btn_save.clicked.connect(self._save_template)
        self._btn_del = QPushButton(_icon("delete"), "Supprimer")
        self._btn_del.setStyleSheet("color:#A4262C;")
        self._btn_del.clicked.connect(self._delete_template)
        self._btn_default = QPushButton(_icon("check"), "Définir par défaut")
        self._btn_default.clicked.connect(self._set_default)

        for btn in [self._btn_new, self._btn_dup, self._btn_save,
                    self._btn_del, self._btn_default]:
            tb_layout.addWidget(btn)

        root_layout.addWidget(toolbar)

        # ── Main splitter ─────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left pane: template list
        left = QWidget()
        left.setMinimumWidth(170)
        left.setMaximumWidth(260)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.addWidget(QLabel("Modèles disponibles :"))
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_list_row_changed)
        left_layout.addWidget(self._list, 1)
        splitter.addWidget(left)

        # Center pane: editor (replaced on template load)
        self._editor_container = QWidget()
        self._editor_layout = QVBoxLayout(self._editor_container)
        self._editor_layout.setContentsMargins(0, 0, 0, 0)
        self._editor_panel: _EditorPanel | None = None
        splitter.addWidget(self._editor_container)

        # Right pane: live preview
        right = QWidget()
        right.setMinimumWidth(350)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        preview_lbl = QLabel("Aperçu en direct")
        preview_lbl.setStyleSheet(
            "font-weight:600; padding:4px 8px; background:#F9F9FB; border-bottom:1px solid #E5E5EA;"
        )
        right_layout.addWidget(preview_lbl)
        self._preview = QTextBrowser()
        self._preview.setOpenLinks(False)
        right_layout.addWidget(self._preview, 1)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        splitter.setSizes([200, 450, 550])

        root_layout.addWidget(splitter, 1)

        # Debounce timer
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(500)
        self._preview_timer.timeout.connect(self._refresh_preview)

        self.setWidget(root)

    # ── Type / list management ────────────────────────────────────────────────

    def _on_type_changed(self, _index: int) -> None:
        self._current_type = self._type_combo.currentData()
        self._load_type(self._current_type)

    def _load_type(self, type_doc: str) -> None:
        self._current_type = type_doc
        templates = self._manager.list_templates(type_doc)
        self._list.blockSignals(True)
        self._list.clear()
        for t in templates:
            item = QListWidgetItem(("★ " if t.is_default else "  ") + t.nom)
            item.setData(Qt.ItemDataRole.UserRole, t.id)
            self._list.addItem(item)
        self._list.blockSignals(False)
        if templates:
            self._list.setCurrentRow(0)
        else:
            self._load_template(None)

    def _on_list_row_changed(self, row: int) -> None:
        if row < 0:
            self._load_template(None)
            return
        item = self._list.item(row)
        if not item:
            return
        template_id = item.data(Qt.ItemDataRole.UserRole)
        template = self._manager.get(self._current_type, template_id)
        self._load_template(template)

    def _load_template(self, template: HtmlReportTemplate | None) -> None:
        if self._dirty and self._current_template:
            self._ask_save()
        self._current_template = template
        self._dirty = False

        # Clear editor pane
        while self._editor_layout.count():
            item = self._editor_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if template is None:
            placeholder = QLabel("Aucun modèle sélectionné.\nCliquez sur « + Nouveau » pour en créer un.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color:#6E6E73;")
            self._editor_layout.addWidget(placeholder)
            self._preview.setHtml("")
            self._editor_panel = None
            return

        self._editor_panel = _EditorPanel(template, self._on_template_changed)
        self._editor_layout.addWidget(self._editor_panel)
        self._refresh_preview()

    # ── Editor change callback ────────────────────────────────────────────────

    def _on_template_changed(self) -> None:
        self._dirty = True
        self._preview_timer.start()

    def _refresh_preview(self) -> None:
        if not self._current_template:
            return
        context = SAMPLE_CONTEXTS.get(self._current_type, SAMPLE_CONTEXTS["facture"])
        try:
            html = self._renderer.render(self._current_template, context)
            self._preview.setHtml(html)
        except Exception as exc:
            self._preview.setPlainText(f"Erreur de rendu :\n{exc}")

    # ── CRUD actions ──────────────────────────────────────────────────────────

    def _new_template(self) -> None:
        name, ok = QInputDialog.getText(self, "Nouveau modèle", "Nom du modèle :")
        if not ok or not name.strip():
            return
        t = HtmlReportTemplate(nom=name.strip(), type_document=self._current_type)
        self._manager.save(t)
        self._load_type(self._current_type)
        # Select the new one
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == t.id:
                self._list.setCurrentRow(i)
                break

    def _duplicate_template(self) -> None:
        if not self._current_template:
            return
        name, ok = QInputDialog.getText(
            self, "Dupliquer", "Nom du nouveau modèle :",
            text=self._current_template.nom + " (copie)",
        )
        if not ok or not name.strip():
            return
        copy = self._manager.duplicate(self._current_type, self._current_template.id, name.strip())
        self._load_type(self._current_type)
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == copy.id:
                self._list.setCurrentRow(i)
                break

    def _save_template(self) -> None:
        if not self._current_template:
            return
        if self._editor_panel:
            self._current_template.nom = self._editor_panel.get_nom()
        self._manager.save(self._current_template)
        self._dirty = False
        self._load_type(self._current_type)
        # Reselect saved template
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == self._current_template.id:
                self._list.setCurrentRow(i)
                break

    def _delete_template(self) -> None:
        if not self._current_template:
            return
        reply = QMessageBox.question(
            self, "Supprimer",
            f"Supprimer le modèle « {self._current_template.nom} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._manager.delete(self._current_type, self._current_template.id)
        self._current_template = None
        self._dirty = False
        self._load_type(self._current_type)

    def _set_default(self) -> None:
        if not self._current_template:
            return
        self._manager.set_default(self._current_type, self._current_template.id)
        self._load_type(self._current_type)
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == self._current_template.id:
                self._list.setCurrentRow(i)
                break

    def _ask_save(self) -> None:
        if not self._current_template:
            return
        reply = QMessageBox.question(
            self, "Modifications non sauvegardées",
            f"Sauvegarder les modifications sur « {self._current_template.nom} » ?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Save:
            self._manager.save(self._current_template)
        self._dirty = False

    def closeEvent(self, event) -> None:
        if self._dirty and self._current_template:
            self._ask_save()
        super().closeEvent(event)
