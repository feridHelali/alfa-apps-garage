from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow, QMessageBox,
    QPushButton, QTableView, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import ROLE_PERMISSIONS
from garage_app.domain.auth.user import User
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.widgets.icon_helper import icon as _icon

_ROLE_LABELS = {
    "superadmin": "Super Admin",
    "admin": "Administrateur",
    "technicien": "Technicien",
}

_AVAILABLE_ROLES = ["technicien", "admin", "superadmin"]


class _UserTableModel(QAbstractTableModel):
    HEADERS = ["Identifiant", "Nom complet", "Rôle", "Statut"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[User] = []

    def reload(self, rows: list[User]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        u = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return u.username
            if col == 1:
                return u.full_name
            if col == 2:
                return _ROLE_LABELS.get(u.role, u.role)
            if col == 3:
                return "Actif" if u.is_active else "Désactivé"

        if role == Qt.ItemDataRole.ForegroundRole and col == 3:
            return QColor("#155724") if u.is_active else QColor("#721C24")

        if role == Qt.ItemDataRole.FontRole and col == 3:
            f = QFont()
            f.setBold(True)
            return f

        if role == Qt.ItemDataRole.BackgroundRole and not u.is_active:
            return QColor("#FFF5F5")

        return None

    def get_user(self, row: int) -> User:
        return self._rows[row]


class _UserFormDialog(QDialog):
    def __init__(self, user: User | None = None, parent=None) -> None:
        super().__init__(parent)
        self._editing = user is not None
        self.setWindowTitle("Modifier l'utilisateur" if self._editing else "Nouvel utilisateur")
        self.setMinimumWidth(380)

        form = QFormLayout(self)

        self._username = QLineEdit()
        self._username.setPlaceholderText("login…")
        if self._editing:
            self._username.setText(user.username)
            self._username.setEnabled(False)
        form.addRow("Identifiant :", self._username)

        self._full_name = QLineEdit()
        self._full_name.setPlaceholderText("Prénom Nom…")
        if self._editing:
            self._full_name.setText(user.full_name)
        form.addRow("Nom complet :", self._full_name)

        self._role = QComboBox()
        for r in _AVAILABLE_ROLES:
            self._role.addItem(_ROLE_LABELS.get(r, r), r)
        if self._editing:
            idx = _AVAILABLE_ROLES.index(user.role) if user.role in _AVAILABLE_ROLES else 0
            self._role.setCurrentIndex(idx)
        form.addRow("Rôle :", self._role)

        if not self._editing:
            self._pwd = QLineEdit()
            self._pwd.setEchoMode(QLineEdit.EchoMode.Password)
            self._pwd.setPlaceholderText("Mot de passe…")
            form.addRow("Mot de passe :", self._pwd)

            self._pwd2 = QLineEdit()
            self._pwd2.setEchoMode(QLineEdit.EchoMode.Password)
            self._pwd2.setPlaceholderText("Confirmer…")
            form.addRow("Confirmer :", self._pwd2)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _on_ok(self) -> None:
        if not self._username.text().strip():
            QMessageBox.warning(self, "Erreur", "L'identifiant est obligatoire.")
            return
        if not self._full_name.text().strip():
            QMessageBox.warning(self, "Erreur", "Le nom complet est obligatoire.")
            return
        if not self._editing:
            if not self._pwd.text():
                QMessageBox.warning(self, "Erreur", "Le mot de passe est obligatoire.")
                return
            if self._pwd.text() != self._pwd2.text():
                QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
                return
        self.accept()

    @property
    def username(self) -> str:
        return self._username.text().strip()

    @property
    def full_name(self) -> str:
        return self._full_name.text().strip()

    @property
    def role(self) -> str:
        return self._role.currentData()

    @property
    def password(self) -> str:
        return self._pwd.text() if not self._editing else ""


class _ChangePasswordDialog(QDialog):
    def __init__(self, username: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Changer le mot de passe — {username}")
        self.setMinimumWidth(320)
        form = QFormLayout(self)

        self._pwd = QLineEdit()
        self._pwd.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Nouveau mot de passe :", self._pwd)

        self._pwd2 = QLineEdit()
        self._pwd2.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirmer :", self._pwd2)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _on_ok(self) -> None:
        if not self._pwd.text():
            QMessageBox.warning(self, "Erreur", "Mot de passe vide.")
            return
        if self._pwd.text() != self._pwd2.text():
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return
        self.accept()

    @property
    def new_password(self) -> str:
        return self._pwd.text()


class UserManagementWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Gestion des utilisateurs")
        self._build_ui()
        self._load()
        self.resize(780, 480)

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(6, 6, 6, 6)

        # Toolbar buttons
        btn_row = QHBoxLayout()
        self._btn_new = QPushButton(_icon("new"), "+ Nouvel utilisateur")
        self._btn_new.clicked.connect(self._new_user)
        btn_row.addWidget(self._btn_new)

        self._btn_edit = QPushButton(_icon("edit"), "Modifier")
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._edit_user)
        btn_row.addWidget(self._btn_edit)

        self._btn_pwd = QPushButton(_icon("password"), "Changer mot de passe")
        self._btn_pwd.setEnabled(False)
        self._btn_pwd.clicked.connect(self._change_password)
        btn_row.addWidget(self._btn_pwd)

        btn_row.addStretch()

        self._btn_toggle = QPushButton(_icon("user"), "Désactiver")
        self._btn_toggle.setEnabled(False)
        self._btn_toggle.clicked.connect(self._toggle_active)
        btn_row.addWidget(self._btn_toggle)

        vbox.addLayout(btn_row)

        # Table
        self._model = _UserTableModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 140)
        self._table.setColumnWidth(1, 200)
        self._table.setColumnWidth(2, 140)
        self._table.setColumnWidth(3, 100)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.selectionModel().currentRowChanged.connect(self._on_select)
        self._table.doubleClicked.connect(lambda _: self._edit_user())
        vbox.addWidget(self._table)

        # Info bar
        self._info_label = QLabel()
        self._info_label.setStyleSheet("color: #555; font-size: 10px; padding: 2px;")
        vbox.addWidget(self._info_label)

        self.setWidget(root)

    def _load(self) -> None:
        try:
            users = self._ctx.auth_service.list_users(self._session)
            self._model.reload(users)
            self._info_label.setText(
                f"{len(users)} utilisateur(s) — "
                f"{sum(1 for u in users if u.is_active)} actif(s)"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _on_select(self, *_) -> None:
        idx = self._table.currentIndex()
        has_sel = idx.isValid()
        self._btn_edit.setEnabled(has_sel)
        self._btn_pwd.setEnabled(has_sel)
        self._btn_toggle.setEnabled(has_sel)
        if has_sel:
            user = self._model.get_user(idx.row())
            self._btn_toggle.setText("Réactiver" if not user.is_active else "Désactiver")

    def _selected_user(self) -> User | None:
        idx = self._table.currentIndex()
        return self._model.get_user(idx.row()) if idx.isValid() else None

    def _new_user(self) -> None:
        dlg = _UserFormDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.auth_service.create_user(
                    self._session,
                    username=dlg.username,
                    full_name=dlg.full_name,
                    role=dlg.role,
                    password=dlg.password,
                )
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _edit_user(self) -> None:
        user = self._selected_user()
        if not user:
            return
        dlg = _UserFormDialog(user=user, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.auth_service.update_user(
                    self._session,
                    user_id=user.id,
                    full_name=dlg.full_name,
                    role=dlg.role,
                )
                self._load()
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _change_password(self) -> None:
        user = self._selected_user()
        if not user:
            return
        dlg = _ChangePasswordDialog(user.username, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.auth_service.change_password(
                    self._session, user.id, dlg.new_password
                )
                QMessageBox.information(self, "Succès", "Mot de passe modifié.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _toggle_active(self) -> None:
        user = self._selected_user()
        if not user:
            return
        action = "réactiver" if not user.is_active else "désactiver"
        if QMessageBox.question(
            self, "Confirmation",
            f"Voulez-vous {action} l'utilisateur « {user.username} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            if user.is_active:
                self._ctx.auth_service.deactivate_user(self._session, user.id)
            else:
                self._ctx.auth_service.reactivate_user(self._session, user.id)
            self._load()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
