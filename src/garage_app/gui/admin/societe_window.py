from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMdiSubWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.societe.societe import Societe
from garage_app.gui.widgets.notification_bar import NotificationBar
from garage_app.gui.widgets.icon_helper import icon as _icon


class SocieteWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Ma Société")
        self.setWindowIcon(QIcon.fromTheme("emblem-default"))
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._notif = NotificationBar()
        layout.addWidget(self._notif)

        # Logo section
        logo_box = QGroupBox("Logo")
        logo_layout = QHBoxLayout(logo_box)
        self._logo_label = QLabel()
        self._logo_label.setFixedSize(120, 80)
        self._logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_label.setStyleSheet("border: 1px solid #c0c0c0; background: #f8f8f8;")
        btn_logo = QPushButton(_icon("logo"), "Choisir…")
        btn_logo.clicked.connect(self._pick_logo)
        logo_layout.addWidget(self._logo_label)
        logo_layout.addWidget(btn_logo)
        logo_layout.addStretch()
        layout.addWidget(logo_box)

        # Form
        form = QFormLayout()
        self._raison = QLineEdit()
        self._siret = QLineEdit()
        self._adresse = QLineEdit()
        self._tel = QLineEdit()
        self._email = QLineEdit()
        self._licence = QLineEdit()
        self._licence.setReadOnly(True)
        form.addRow("Raison sociale :", self._raison)
        form.addRow("SIRET :", self._siret)
        form.addRow("Adresse :", self._adresse)
        form.addRow("Téléphone :", self._tel)
        form.addRow("Email :", self._email)
        form.addRow("Clé de licence :", self._licence)
        layout.addLayout(form)

        btn_save = QPushButton(_icon("save"), "Enregistrer")
        btn_save.clicked.connect(self._save)
        layout.addWidget(btn_save)

        self.setWidget(widget)
        self.resize(500, 500)

    def _load(self) -> None:
        s = self._ctx.societe_service.get()
        if s:
            self._societe = s
            self._raison.setText(s.raison_sociale)
            self._siret.setText(s.siret)
            self._adresse.setText(s.adresse)
            self._tel.setText(s.telephone)
            self._email.setText(s.email)
            self._licence.setText(s.licence_key)
            if s.logo_path and Path(s.logo_path).exists():
                pix = QPixmap(s.logo_path).scaled(
                    120, 80, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._logo_label.setPixmap(pix)
        else:
            self._societe = Societe()

    def _pick_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "", "Images (*.png *.jpg *.svg *.ico)"
        )
        if path:
            self._societe.logo_path = path
            pix = QPixmap(path).scaled(
                120, 80, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._logo_label.setPixmap(pix)

    def _save(self) -> None:
        self._societe.raison_sociale = self._raison.text().strip()
        self._societe.siret = self._siret.text().strip()
        self._societe.adresse = self._adresse.text().strip()
        self._societe.telephone = self._tel.text().strip()
        self._societe.email = self._email.text().strip()
        try:
            self._ctx.societe_service.update(self._session, self._societe)
            self._notif.show_message("Société enregistrée.", "success")
        except Exception as e:
            self._notif.show_message(str(e), "error")
