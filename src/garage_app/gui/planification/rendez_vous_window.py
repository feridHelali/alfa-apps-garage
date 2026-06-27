from __future__ import annotations

import uuid
from datetime import datetime

from PyQt6.QtCore import QDate, QDateTime, Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCalendarWidget, QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox,
    QFormLayout, QLabel, QLineEdit, QMdiSubWindow,
    QMessageBox, QPushButton, QSplitter, QTableView,
    QToolBar, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.planification.rendez_vous import RendezVous
from garage_app.domain.planification.client import Client
from garage_app.domain.planification.vehicule import Vehicule
from garage_app.gui.widgets.icon_helper import icon as _icon


_STATUT_LABELS = {
    "planifie": "Planifié",
    "confirme": "Confirmé",
    "termine": "Terminé",
    "annule": "Annulé",
}

_STATUT_COLORS: dict[str, tuple[str, str]] = {
    "planifie": ("#FFF3CD", "#856404"),
    "confirme": ("#D1ECF1", "#0C5460"),
    "termine": ("#D4EDDA", "#155724"),
    "annule": ("#F8D7DA", "#721C24"),
}


class _RdvTableModel(QAbstractTableModel):
    HEADERS = ["Heure", "Client", "Véhicule", "Motif", "Statut"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[RendezVous] = []
        self._clients: dict[uuid.UUID, Client] = {}
        self._vehicules: dict[uuid.UUID, Vehicule] = {}

    def reload(
        self,
        rows: list[RendezVous],
        clients: dict[uuid.UUID, Client],
        vehicules: dict[uuid.UUID, Vehicule],
    ) -> None:
        self.beginResetModel()
        self._rows = rows
        self._clients = clients
        self._vehicules = vehicules
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
        rdv = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return rdv.date_heure.strftime("%H:%M")
            if col == 1:
                c = self._clients.get(rdv.client_id)
                return f"{c.nom} {c.prenom}".strip() if c else str(rdv.client_id)[:8]
            if col == 2:
                v = self._vehicules.get(rdv.vehicule_id)
                return f"{v.marque} {v.modele} ({v.immatriculation})" if v else str(rdv.vehicule_id)[:8]
            if col == 3:
                return rdv.motif
            if col == 4:
                return _STATUT_LABELS.get(rdv.statut, rdv.statut)

        if role == Qt.ItemDataRole.BackgroundRole and col == 4:
            bg, _ = _STATUT_COLORS.get(rdv.statut, ("#FFFFFF", "#000000"))
            return QColor(bg)

        if role == Qt.ItemDataRole.ForegroundRole and col == 4:
            _, fg = _STATUT_COLORS.get(rdv.statut, ("#FFFFFF", "#000000"))
            return QColor(fg)

        if role == Qt.ItemDataRole.FontRole and col == 4:
            f = QFont()
            f.setBold(True)
            return f

        return None

    def get_rdv(self, row: int) -> RendezVous:
        return self._rows[row]


class _RendezVousFormDialog(QDialog):
    """Create or edit a rendez-vous."""

    def __init__(
        self,
        ctx: AppContext,
        session: UserSession,
        rdv: RendezVous | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nouveau rendez-vous" if rdv is None else "Modifier rendez-vous")
        self.setMinimumWidth(440)
        self._ctx = ctx
        self._session = session
        self._rdv = rdv
        self._clients: list[Client] = []
        self._vehicules: list[Vehicule] = []
        self._build_ui()
        self._load_clients()
        if rdv:
            self._populate(rdv)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)

        self._combo_client = QComboBox()
        self._combo_client.setMinimumWidth(280)
        self._combo_client.currentIndexChanged.connect(self._on_client_changed)
        form.addRow("Client :", self._combo_client)

        self._combo_vehicule = QComboBox()
        form.addRow("Véhicule :", self._combo_vehicule)

        self._dt_edit = QDateTimeEdit()
        self._dt_edit.setCalendarPopup(True)
        self._dt_edit.setDisplayFormat("dd/MM/yyyy HH:mm")
        _ref = (self._rdv.date_heure if self._rdv
                else datetime.now().replace(minute=0, second=0, microsecond=0))
        self._dt_edit.setDateTime(
            QDateTime(_ref.year, _ref.month, _ref.day, _ref.hour, _ref.minute, 0)
        )
        form.addRow("Date / Heure :", self._dt_edit)

        self._motif_edit = QLineEdit()
        self._motif_edit.setPlaceholderText("Raison de la visite…")
        form.addRow("Motif :", self._motif_edit)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _load_clients(self) -> None:
        try:
            self._clients = self._ctx.client_service.list_clients(self._session)
        except Exception:
            self._clients = []
        self._combo_client.clear()
        for c in self._clients:
            self._combo_client.addItem(f"{c.nom} {c.prenom}".strip(), c.id)

    def _on_client_changed(self, index: int) -> None:
        self._combo_vehicule.clear()
        if index < 0 or index >= len(self._clients):
            return
        client_id = self._clients[index].id
        try:
            self._vehicules = self._ctx.client_service.get_vehicules(self._session, client_id)
        except Exception:
            self._vehicules = []
        for v in self._vehicules:
            self._combo_vehicule.addItem(f"{v.marque} {v.modele} — {v.immatriculation}", v.id)

    def _populate(self, rdv: RendezVous) -> None:
        # Select client
        for i, c in enumerate(self._clients):
            if c.id == rdv.client_id:
                self._combo_client.setCurrentIndex(i)
                break
        # Select vehicule (after client triggered vehicle load)
        for i, v in enumerate(self._vehicules):
            if v.id == rdv.vehicule_id:
                self._combo_vehicule.setCurrentIndex(i)
                break
        self._motif_edit.setText(rdv.motif)

    def _on_accept(self) -> None:
        if self._combo_client.currentIndex() < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un client.")
            return
        if self._combo_vehicule.currentIndex() < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un véhicule.")
            return
        self.accept()

    @property
    def client_id(self) -> uuid.UUID:
        return self._combo_client.currentData()

    @property
    def vehicule_id(self) -> uuid.UUID:
        return self._combo_vehicule.currentData()

    @property
    def date_heure(self) -> datetime:
        qdt = self._dt_edit.dateTime()
        return datetime(
            qdt.date().year(), qdt.date().month(), qdt.date().day(),
            qdt.time().hour(), qdt.time().minute(),
        )

    @property
    def motif(self) -> str:
        return self._motif_edit.text().strip()


class RendezVousWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._can_manage = session.can(Permission.MANAGE_RENDEZ_VOUS)
        self._clients: dict[uuid.UUID, Client] = {}
        self._vehicules: dict[uuid.UUID, Vehicule] = {}
        self.setWindowTitle("Rendez-vous")
        self._build_ui()
        self._load_lookup_tables()
        self._load_for_date(QDate.currentDate())
        self.resize(960, 580)

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(4)

        # Toolbar
        tb = QToolBar()
        tb.setMovable(False)

        self._btn_new = QPushButton("+ Nouveau")
        self._btn_new.setIcon(_icon("new"))
        self._btn_new.setEnabled(self._can_manage)
        self._btn_new.clicked.connect(self._new_rdv)
        tb.addWidget(self._btn_new)

        self._btn_edit = QPushButton("Modifier")
        self._btn_edit.setIcon(_icon("edit"))
        self._btn_edit.setEnabled(False)
        self._btn_edit.clicked.connect(self._edit_rdv)
        tb.addWidget(self._btn_edit)

        tb.addSeparator()

        self._btn_confirm = QPushButton("Confirmer")
        self._btn_confirm.setIcon(_icon("ok"))
        self._btn_confirm.setEnabled(False)
        self._btn_confirm.clicked.connect(self._confirmer)
        tb.addWidget(self._btn_confirm)

        self._btn_termine = QPushButton("Terminer")
        self._btn_termine.setIcon(_icon("check"))
        self._btn_termine.setEnabled(False)
        self._btn_termine.clicked.connect(self._terminer)
        tb.addWidget(self._btn_termine)

        self._btn_cancel = QPushButton("Annuler")
        self._btn_cancel.setIcon(_icon("cancel"))
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.clicked.connect(self._annuler)
        tb.addWidget(self._btn_cancel)

        tb.addSeparator()

        self._btn_delete = QPushButton("Supprimer")
        self._btn_delete.setIcon(_icon("delete"))
        self._btn_delete.setEnabled(False)
        self._btn_delete.setStyleSheet("QPushButton { color: #C0392B; }")
        self._btn_delete.clicked.connect(self._supprimer)
        tb.addWidget(self._btn_delete)

        vbox.addWidget(tb)

        # Splitter: calendar | table
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: calendar + stats
        left = QWidget()
        left.setFixedWidth(260)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(2, 2, 2, 2)

        self._calendar = QCalendarWidget()
        self._calendar.setGridVisible(True)
        self._calendar.selectionChanged.connect(
            lambda: self._load_for_date(self._calendar.selectedDate())
        )
        lv.addWidget(self._calendar)

        self._stats_label = QLabel()
        self._stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stats_label.setStyleSheet("font-size: 11px; color: #555; padding: 4px;")
        lv.addWidget(self._stats_label)

        splitter.addWidget(left)

        # Right: table
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(2, 0, 2, 2)

        self._date_label = QLabel()
        self._date_label.setStyleSheet("font-weight: 700; font-size: 13px; padding: 4px 2px;")
        rv.addWidget(self._date_label)

        self._model = _RdvTableModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 70)
        self._table.setColumnWidth(1, 160)
        self._table.setColumnWidth(2, 200)
        self._table.setColumnWidth(4, 100)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.selectionModel().currentRowChanged.connect(self._on_selection_changed)
        self._table.doubleClicked.connect(lambda _: self._edit_rdv())
        rv.addWidget(self._table)

        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)
        vbox.addWidget(splitter)

        self.setWidget(root)

    # ── Data loading ─────────────────────────────────────────────────────────

    def _load_lookup_tables(self) -> None:
        try:
            clients = self._ctx.client_service.list_clients(self._session)
            self._clients = {c.id: c for c in clients}
            all_v: list[Vehicule] = []
            for c in clients:
                all_v += self._ctx.client_service.get_vehicules(self._session, c.id)
            self._vehicules = {v.id: v for v in all_v}
        except Exception:
            self._clients = {}
            self._vehicules = {}

    def _load_for_date(self, qdate: QDate) -> None:
        target_date = qdate.toPyDate()
        label = qdate.toString("dddd d MMMM yyyy")
        self._date_label.setText(label)
        try:
            rows = self._ctx.rendez_vous_service.list_by_date(self._session, target_date)
        except Exception as e:
            rows = []
        self._model.reload(rows, self._clients, self._vehicules)
        self._update_stats(qdate)
        self._on_selection_changed()

    def _update_stats(self, qdate: QDate) -> None:
        try:
            month_rows = self._ctx.rendez_vous_service.list_by_month(
                self._session, qdate.year(), qdate.month()
            )
        except Exception:
            month_rows = []
        planifie = sum(1 for r in month_rows if r.statut in ("planifie", "confirme"))
        total = len(month_rows)
        self._stats_label.setText(
            f"Ce mois : {total} rdv dont {planifie} à venir"
        )

    # ── Selection & button states ─────────────────────────────────────────────

    def _on_selection_changed(self, *_) -> None:
        idx = self._table.currentIndex()
        has_sel = idx.isValid()
        rdv = self._model.get_rdv(idx.row()) if has_sel else None

        self._btn_edit.setEnabled(has_sel and self._can_manage and rdv is not None and rdv.statut not in ("annule", "termine"))
        self._btn_confirm.setEnabled(has_sel and self._can_manage and rdv is not None and rdv.statut == "planifie")
        self._btn_termine.setEnabled(has_sel and self._can_manage and rdv is not None and rdv.statut == "confirme")
        self._btn_cancel.setEnabled(has_sel and self._can_manage and rdv is not None and rdv.statut in ("planifie", "confirme"))
        self._btn_delete.setEnabled(has_sel and self._can_manage)

    def _selected_rdv(self) -> RendezVous | None:
        idx = self._table.currentIndex()
        if not idx.isValid():
            return None
        return self._model.get_rdv(idx.row())

    # ── Actions ──────────────────────────────────────────────────────────────

    def _new_rdv(self) -> None:
        dlg = _RendezVousFormDialog(self._ctx, self._session, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.rendez_vous_service.planifier(
                    self._session,
                    client_id=dlg.client_id,
                    vehicule_id=dlg.vehicule_id,
                    date_heure=dlg.date_heure,
                    motif=dlg.motif,
                )
                self._refresh_with_vehicle_cache()
                self._load_for_date(self._calendar.selectedDate())
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _edit_rdv(self) -> None:
        rdv = self._selected_rdv()
        if not rdv:
            return
        dlg = _RendezVousFormDialog(self._ctx, self._session, rdv=rdv, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self._ctx.rendez_vous_service.modifier(
                    self._session,
                    rdv_id=rdv.id,
                    client_id=dlg.client_id,
                    vehicule_id=dlg.vehicule_id,
                    date_heure=dlg.date_heure,
                    motif=dlg.motif,
                )
                self._refresh_with_vehicle_cache()
                self._load_for_date(self._calendar.selectedDate())
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))

    def _confirmer(self) -> None:
        rdv = self._selected_rdv()
        if not rdv:
            return
        try:
            self._ctx.rendez_vous_service.confirmer(self._session, rdv.id)
            self._load_for_date(self._calendar.selectedDate())
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _terminer(self) -> None:
        rdv = self._selected_rdv()
        if not rdv:
            return
        try:
            self._ctx.rendez_vous_service.terminer(self._session, rdv.id)
            self._load_for_date(self._calendar.selectedDate())
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _annuler(self) -> None:
        rdv = self._selected_rdv()
        if not rdv:
            return
        if QMessageBox.question(
            self, "Annuler le rendez-vous",
            "Confirmer l'annulation de ce rendez-vous ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ctx.rendez_vous_service.annuler(self._session, rdv.id)
            self._load_for_date(self._calendar.selectedDate())
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _supprimer(self) -> None:
        rdv = self._selected_rdv()
        if not rdv:
            return
        if QMessageBox.question(
            self, "Supprimer",
            "Supprimer définitivement ce rendez-vous ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ctx.rendez_vous_service.supprimer(self._session, rdv.id)
            self._load_for_date(self._calendar.selectedDate())
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def _refresh_with_vehicle_cache(self) -> None:
        try:
            all_v: list[Vehicule] = []
            for c in self._clients.values():
                all_v += self._ctx.client_service.get_vehicules(self._session, c.id)
            self._vehicules = {v.id: v for v in all_v}
            clients = self._ctx.client_service.list_clients(self._session)
            self._clients = {c.id: c for c in clients}
        except Exception:
            pass
