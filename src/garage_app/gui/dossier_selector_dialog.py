from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from garage_app.dossier_manager import DossierInfo, DossierManager
from garage_app.settings import APP_DATA_DIR
from garage_app.gui.widgets.notification_bar import NotificationBar


class DossierSelectorDialog(QDialog):
    """Shown at startup when multiple DB dossiers exist.
    Sets self.selected_db_path on acceptance."""

    def __init__(self, manager: DossierManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self.selected_db_path: str | None = None
        self.setWindowTitle("Alfa Computers — Sélection du dossier")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint)
        self.setModal(True)
        self._build_ui()
        self._load()
        self.resize(640, 440)

    def _build_ui(self) -> None:
        vbox = QVBoxLayout(self)
        vbox.setSpacing(10)

        title = QLabel("Sélectionnez un dossier ou créez-en un nouveau")
        title.setStyleSheet("font-size:13pt; font-weight:700; color:#0055a5; padding-bottom:4px;")
        vbox.addWidget(title)

        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.itemDoubleClicked.connect(self._open_selected)
        vbox.addWidget(self._list, stretch=1)

        bar = QHBoxLayout()
        btn_new = QPushButton("+ Nouveau dossier")
        btn_new.clicked.connect(self._new_dossier)
        btn_remove = QPushButton("Retirer de la liste")
        btn_remove.clicked.connect(self._remove_selected)
        btn_open = QPushButton("Ouvrir")
        btn_open.setDefault(True)
        btn_open.setStyleSheet("background:#0055a5; color:white; font-weight:700; padding:6px 18px;")
        btn_open.clicked.connect(self._open_selected)
        btn_quit = QPushButton("Quitter")
        btn_quit.clicked.connect(self.reject)
        bar.addWidget(btn_new)
        bar.addWidget(btn_remove)
        bar.addStretch()
        bar.addWidget(btn_quit)
        bar.addWidget(btn_open)
        vbox.addLayout(bar)

        self._dossiers: list[DossierInfo] = []

    def _load(self) -> None:
        self._dossiers = self._manager.list_dossiers()
        self._list.clear()
        for d in self._dossiers:
            try:
                acces = datetime.fromisoformat(d.dernier_acces).strftime("%d/%m/%Y %H:%M")
            except Exception:
                acces = "—"
            nom_societe = f"  ({d.societe})" if d.societe else ""
            item = QListWidgetItem(
                f"{d.nom}{nom_societe}\n    Dernier accès : {acces}   —   {d.chemin}"
            )
            self._list.addItem(item)

    def _open_selected(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= len(self._dossiers):
            self._notif.show_message("Sélectionnez un dossier.", "warning")
            return
        d = self._dossiers[row]
        db_path = d.db_path()
        if not db_path.exists():
            self._notif.show_message(
                f"Fichier introuvable : {db_path}", "error"
            )
            return
        self._manager.touch_acces(d.id)
        self.selected_db_path = str(db_path)
        self.accept()

    def _remove_selected(self) -> None:
        row = self._list.currentRow()
        if row < 0:
            return
        d = self._dossiers[row]
        rep = QMessageBox.question(
            self, "Retirer",
            f"Retirer '{d.nom}' de la liste ?\n"
            "Le fichier .db ne sera pas supprimé.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if rep == QMessageBox.StandardButton.Yes:
            self._manager.retirer_dossier(d.id)
            self._load()

    def _new_dossier(self) -> None:
        dlg = NouveauDossierDialog(self._manager, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.created_path:
            self._load()
            # Auto-select the newly created dossier
            self.selected_db_path = dlg.created_path
            self.accept()


class NouveauDossierDialog(QDialog):
    """Create a brand-new database with full seed."""

    def __init__(self, manager: DossierManager, parent=None) -> None:
        super().__init__(parent)
        self._manager = manager
        self.created_path: str | None = None
        self.setWindowTitle("Nouveau dossier")
        self.setModal(True)
        self._build_ui()
        self.resize(480, 280)

    def _build_ui(self) -> None:
        vbox = QVBoxLayout(self)
        self._notif = NotificationBar()
        vbox.addWidget(self._notif)

        form = QFormLayout()
        form.setSpacing(8)
        self._nom = QLineEdit()
        self._nom.setPlaceholderText("ex. Exercice 2027")
        self._societe = QLineEdit()
        self._societe.setPlaceholderText("ex. Garage Central Tunis")
        self._chemin = QLineEdit()
        default_name = f"garage_{datetime.now().year}.db"
        self._chemin.setText(str(APP_DATA_DIR / default_name))

        browse = QPushButton("Parcourir…")
        browse.setFixedWidth(90)
        browse.clicked.connect(self._browse)
        chemin_row = QWidget()
        hl = QHBoxLayout(chemin_row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self._chemin)
        hl.addWidget(browse)

        form.addRow("Nom du dossier *", self._nom)
        form.addRow("Société", self._societe)
        form.addRow("Fichier DB *", chemin_row)
        vbox.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Créer")
        buttons.accepted.connect(self._create)
        buttons.rejected.connect(self.reject)
        vbox.addWidget(buttons)

    def _browse(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Choisir l'emplacement du fichier DB",
            str(APP_DATA_DIR),
            "SQLite Database (*.db)",
        )
        if path:
            self._chemin.setText(path)

    def _create(self) -> None:
        nom = self._nom.text().strip()
        if not nom:
            self._notif.show_message("Le nom du dossier est obligatoire.", "error")
            return
        chemin = self._chemin.text().strip()
        if not chemin:
            self._notif.show_message("Choisissez un emplacement pour le fichier DB.", "error")
            return
        try:
            dossier = self._manager.creer_dossier(
                nom=nom,
                societe=self._societe.text().strip(),
                chemin=chemin,
            )
            self.created_path = str(dossier.db_path())
            self.accept()
        except FileExistsError as e:
            self._notif.show_message(str(e), "error")
        except Exception as e:
            self._notif.show_message(f"Erreur : {e}", "error")
