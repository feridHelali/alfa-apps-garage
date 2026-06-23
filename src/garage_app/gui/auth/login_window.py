from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal, Qt, QRectF
from PyQt6.QtGui import QPixmap, QFont, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel,
    QLineEdit, QMessageBox, QVBoxLayout, QWidget,
)

from garage_app.application.auth_service import AuthService, AuthError
from garage_app.domain.auth.user_session import UserSession

_LOGO = Path(__file__).parents[4] / "assets" / "brand" / "alfa_computers_logo.svg"


class LoginWindow(QDialog):
    logged_in = pyqtSignal(UserSession)

    def __init__(self, auth_service: AuthService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._auth = auth_service
        self.setWindowTitle("Connexion — Gestion Réparation Voiture")
        self.setFixedSize(380, 440)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        # Brand logo — render SVG at crisp 220×72 px
        logo_label = QLabel()
        if _LOGO.exists():
            renderer = QSvgRenderer(str(_LOGO))
            logo_w, logo_h = 220, 72
            pix = QPixmap(logo_w, logo_h)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            renderer.render(painter, QRectF(0, 0, logo_w, logo_h))
            painter.end()
            logo_label.setPixmap(pix)
        else:
            logo_label.setText("Alfa Computers Apps")
            logo_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        # App title
        title = QLabel("Gestion Réparation Voiture")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 11))
        layout.addWidget(title)

        # Form
        form = QFormLayout()
        self._username = QLineEdit()
        self._username.setPlaceholderText("Nom d'utilisateur")
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("Mot de passe")
        form.addRow("Utilisateur :", self._username)
        form.addRow("Mot de passe :", self._password)
        layout.addLayout(form)

        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: red;")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._error_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Se connecter")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self._try_login)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Enter key in password field triggers login
        self._password.returnPressed.connect(self._try_login)

    def _try_login(self) -> None:
        self._error_label.setText("")
        username = self._username.text().strip()
        password = self._password.text()
        if not username or not password:
            self._error_label.setText("Veuillez remplir tous les champs.")
            return
        try:
            session = self._auth.login(username, password)
            self.logged_in.emit(session)
            self.accept()
        except AuthError as e:
            self._error_label.setText(str(e))
            self._password.clear()
            self._password.setFocus()
