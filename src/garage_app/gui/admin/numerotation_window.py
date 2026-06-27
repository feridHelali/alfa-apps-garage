from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMdiSubWindow, QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from garage_app.application.numerotation_service import TYPES_DOC, NumerotationConfig
from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.widgets.notification_bar import NotificationBar
from garage_app.gui.widgets.icon_helper import icon as _icon

_LABELS = {
    "facture":        "Facture client",
    "dossier":        "Dossier réparation",
    "bon_travail":    "Bon de travail",
    "facture_achat":  "Facture achat",
}


class _TypeTab(QWidget):
    def __init__(self, type_doc: str, config: NumerotationConfig) -> None:
        super().__init__()
        self._type_doc = type_doc
        form = QFormLayout(self)
        form.setSpacing(8)

        self._prefixe = QLineEdit(config.prefixe)
        self._prefixe.setPlaceholderText("ex. F{ANNEE}-")
        self._prochain = QSpinBox()
        self._prochain.setRange(1, 9999999)
        self._prochain.setValue(config.prochain)
        self._longueur = QSpinBox()
        self._longueur.setRange(1, 10)
        self._longueur.setValue(config.longueur)
        self._reset = QCheckBox("Remettre à 1 chaque 1er janvier")
        self._reset.setChecked(config.reset_annuel)

        self._preview = QLabel()
        self._preview.setStyleSheet("font-weight:700; color:#0055a5; font-size:12pt;")

        form.addRow("Préfixe :", self._prefixe)
        form.addRow("Macros :", QLabel("<span style='color:#6E6E73; font-size:9pt'>"
                                       "{ANNEE} → année courante &nbsp; {MOIS} → mois</span>"))
        form.addRow("Prochain N° :", self._prochain)
        form.addRow("Longueur séquence :", self._longueur)
        form.addRow("Réinitialisation :", self._reset)
        form.addRow("Aperçu :", self._preview)

        self._prefixe.textChanged.connect(self._refresh_preview)
        self._prochain.valueChanged.connect(self._refresh_preview)
        self._longueur.valueChanged.connect(self._refresh_preview)
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        from datetime import datetime
        year_now = datetime.now().year
        mois_now = f"{datetime.now().month:02d}"
        prefixe = self._prefixe.text().replace("{ANNEE}", str(year_now)).replace("{MOIS}", mois_now)
        longueur = self._longueur.value()
        prochain = self._prochain.value()
        self._preview.setText(f"{prefixe}{prochain:0{longueur}d}")

    def current_config(self) -> NumerotationConfig:
        return NumerotationConfig(
            type_doc=self._type_doc,
            prefixe=self._prefixe.text(),
            prochain=self._prochain.value(),
            longueur=self._longueur.value(),
            reset_annuel=self._reset.isChecked(),
        )


class NumerotationWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Numérotation des documents")
        self._build_ui()
        self.resize(520, 420)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(10, 10, 10, 10)

        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        grp = QGroupBox("Paramètres de numérotation par type de document")
        gv = QVBoxLayout(grp)
        self._tabs = QTabWidget()
        self._type_tabs: dict[str, _TypeTab] = {}

        svc = self._ctx.numerotation_service
        for type_doc in TYPES_DOC:
            cfg = svc.get_config(type_doc)
            tab = _TypeTab(type_doc, cfg)
            self._type_tabs[type_doc] = tab
            self._tabs.addTab(tab, _LABELS.get(type_doc, type_doc))

        gv.addWidget(self._tabs)
        vbox.addWidget(grp)

        foot = QHBoxLayout()
        btn_save = QPushButton(_icon("save"), "Enregistrer")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton(_icon("close"), "Fermer")
        btn_cancel.clicked.connect(self.close)
        foot.addStretch()
        foot.addWidget(btn_cancel)
        foot.addWidget(btn_save)
        vbox.addLayout(foot)

        self.setWidget(root)

    def _save(self) -> None:
        svc = self._ctx.numerotation_service
        errors: list[str] = []
        for type_doc, tab in self._type_tabs.items():
            try:
                svc.update_config(self._session, type_doc, tab.current_config())
            except Exception as e:
                errors.append(str(e))
        if errors:
            self._notif.show_message("\n".join(errors), "error")
        else:
            self._notif.show_message("Numérotation enregistrée.", "success")
