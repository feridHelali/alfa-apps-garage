"""DevisListWindow — list of commercial quotes with status badges and actions."""
from __future__ import annotations

import uuid

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QMdiSubWindow, QMessageBox, QPushButton,
    QSplitter, QTableView, QVBoxLayout, QWidget, QHeaderView,
    QInputDialog, QLineEdit,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.devis.devis import Devis
from garage_app.domain.devis.statut_devis import StatutDevis
from garage_app.domain.shared.exceptions import BusinessRuleError
from garage_app.gui.widgets.icon_helper import icon as _icon


class _DevisTableModel(QAbstractTableModel):
    HEADERS = ["Numéro", "Date", "Client", "Véhicule", "Total TTC", "Statut", "Expiration"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[Devis] = []
        self._clients: dict[str, str] = {}
        self._vehicules: dict[str, str] = {}

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        d = self._rows[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            client_nom = self._clients.get(str(d.client_id), str(d.client_id)[:8])
            veh = self._vehicules.get(str(d.vehicule_id), "") if d.vehicule_id else "—"
            exp = d.date_expiration.isoformat() if d.date_expiration else "—"
            return [
                d.numero or str(d.id)[:8],
                d.date_creation.isoformat() if d.date_creation else "—",
                client_nom,
                veh,
                d.total_ttc.format(),
                d.statut.label_fr(),
                exp,
            ][col]

        if role == Qt.ItemDataRole.ForegroundRole and col == 5:
            return QBrush(QColor(d.statut.color()))

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (4,):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    def get_devis(self, row: int) -> Devis:
        return self._rows[row]

    def reload(
        self,
        rows: list[Devis],
        clients: dict[str, str] | None = None,
        vehicules: dict[str, str] | None = None,
    ) -> None:
        self.beginResetModel()
        self._rows = rows
        self._clients = clients or {}
        self._vehicules = vehicules or {}
        self.endResetModel()


class DevisListWindow(QMdiSubWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self.setWindowTitle("Devis commerciaux")
        self.setMinimumSize(900, 540)
        self.resize(1020, 600)

        widget = QWidget()
        self.setWidget(widget)
        root = QVBoxLayout(widget)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # toolbar
        toolbar = QHBoxLayout()
        btn_new = QPushButton(_icon("new"), "+ Nouveau devis")
        btn_new.setEnabled(session.can(Permission.MANAGE_DEVIS))
        btn_new.clicked.connect(self._new_devis)

        self._filter_combo = QComboBox()
        self._filter_combo.addItem("Tous", None)
        for s in StatutDevis:
            self._filter_combo.addItem(s.label_fr(), s)
        self._filter_combo.currentIndexChanged.connect(self._reload)

        toolbar.addWidget(btn_new)
        toolbar.addStretch()
        toolbar.addWidget(QLabel("Statut :"))
        toolbar.addWidget(self._filter_combo)
        root.addLayout(toolbar)

        # table
        self._model = _DevisTableModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.doubleClicked.connect(self._open_selected)
        root.addWidget(self._table)

        # action buttons
        actions = QHBoxLayout()
        self._btn_open = QPushButton(_icon("edit"), "Ouvrir / Modifier")
        self._btn_send = QPushButton(_icon("forward"), "Envoyer au client")
        self._btn_accept = QPushButton(_icon("ok"), "Accepter")
        self._btn_refuse = QPushButton(_icon("cancel"), "Refuser")
        self._btn_convert_dossier = QPushButton(_icon("forward"), "→ Dossier")
        self._btn_convert_proforma = QPushButton(_icon("forward"), "→ Proforma")
        self._btn_duplicate = QPushButton(_icon("new"), "Dupliquer")
        self._btn_cancel = QPushButton(_icon("cancel"), "Annuler")
        self._btn_print = QPushButton(_icon("print"), "Imprimer")

        for btn in (
            self._btn_open, self._btn_send, self._btn_accept, self._btn_refuse,
            self._btn_convert_dossier, self._btn_convert_proforma,
            self._btn_duplicate, self._btn_cancel, self._btn_print,
        ):
            actions.addWidget(btn)

        self._btn_open.clicked.connect(self._open_selected)
        self._btn_send.clicked.connect(self._envoyer)
        self._btn_accept.clicked.connect(self._accepter)
        self._btn_refuse.clicked.connect(self._refuser)
        self._btn_convert_dossier.clicked.connect(self._convertir_dossier)
        self._btn_convert_proforma.clicked.connect(self._convertir_proforma)
        self._btn_duplicate.clicked.connect(self._dupliquer)
        self._btn_cancel.clicked.connect(self._annuler)
        self._btn_print.clicked.connect(self._imprimer)
        root.addLayout(actions)

        self._table.selectionModel().selectionChanged.connect(self._update_buttons)
        self._update_buttons()
        self._reload()

    # ── Data ────────────────────────────────────────────────────────────────

    def _reload(self) -> None:
        statut = self._filter_combo.currentData()
        try:
            if statut is None:
                rows = self._ctx.devis_service.list_devis(self._session)
            else:
                rows = self._ctx.devis_service.list_devis(self._session)
                rows = [r for r in rows if r.statut == statut]
        except Exception:
            rows = []

        clients: dict[str, str] = {}
        vehicules: dict[str, str] = {}
        try:
            all_clients = self._ctx.client_service.list_clients(self._session)
            for c in all_clients:
                clients[str(c.id)] = f"{c.nom} {c.prenom}"
                try:
                    for v in self._ctx.client_service.get_vehicules(self._session, c.id):
                        vehicules[str(v.id)] = v.immatriculation
                except Exception:
                    pass
        except Exception:
            pass

        self._model.reload(rows, clients, vehicules)
        self._update_buttons()

    def _selected(self) -> Devis | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        return self._model.get_devis(rows[0].row())

    def _update_buttons(self) -> None:
        d = self._selected()
        has = d is not None
        can_manage = self._session.can(Permission.MANAGE_DEVIS)
        can_convert = self._session.can(Permission.CONVERT_DEVIS)

        self._btn_open.setEnabled(has)
        self._btn_send.setEnabled(has and can_manage and (d.statut.peut_envoyer() if d else False))
        self._btn_accept.setEnabled(has and can_manage and (d.statut.peut_accepter() if d else False))
        self._btn_refuse.setEnabled(has and can_manage and (d.statut.peut_refuser() if d else False))
        self._btn_convert_dossier.setEnabled(has and can_convert and (d.statut.peut_convertir() if d else False))
        self._btn_convert_proforma.setEnabled(has and can_convert and (d.statut.peut_convertir() if d else False))
        self._btn_duplicate.setEnabled(has and can_manage)
        self._btn_cancel.setEnabled(has and can_manage and (d.statut.peut_annuler() if d else False))
        self._btn_print.setEnabled(has)

    # ── Actions ─────────────────────────────────────────────────────────────

    def _new_devis(self) -> None:
        from garage_app.gui.devis.devis_form_window import DevisFormWindow
        dlg = DevisFormWindow(self._ctx, self._session, parent=self.parentWidget())
        if dlg.exec():
            self._reload()

    def _open_selected(self) -> None:
        d = self._selected()
        if not d:
            return
        from garage_app.gui.devis.devis_form_window import DevisFormWindow
        dlg = DevisFormWindow(self._ctx, self._session, devis=d, parent=self.parentWidget())
        if dlg.exec():
            self._reload()

    def _envoyer(self) -> None:
        d = self._selected()
        if not d:
            return
        try:
            self._ctx.devis_service.envoyer(self._session, d.id)
            self._reload()
        except BusinessRuleError as e:
            QMessageBox.warning(self, "Impossible", str(e))

    def _accepter(self) -> None:
        d = self._selected()
        if not d:
            return
        try:
            self._ctx.devis_service.accepter(self._session, d.id)
            self._reload()
        except BusinessRuleError as e:
            QMessageBox.warning(self, "Impossible", str(e))

    def _refuser(self) -> None:
        d = self._selected()
        if not d:
            return
        motif, ok = QInputDialog.getText(
            self, "Motif de refus", "Motif (facultatif) :", QLineEdit.EchoMode.Normal
        )
        if not ok:
            return
        try:
            self._ctx.devis_service.refuser(self._session, d.id, motif=motif)
            self._reload()
        except BusinessRuleError as e:
            QMessageBox.warning(self, "Impossible", str(e))

    def _convertir_dossier(self) -> None:
        d = self._selected()
        if not d:
            return
        reply = QMessageBox.question(
            self, "Convertir en dossier",
            f"Convertir le devis {d.numero} en dossier de réparation ?\n\n"
            f"Un dossier sera créé pour le client et le véhicule sélectionnés.",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            vehicule_id = d.vehicule_id
            if not vehicule_id:
                QMessageBox.warning(
                    self, "Véhicule requis",
                    "Ce devis n'a pas de véhicule associé.\n"
                    "Modifiez le devis pour ajouter un véhicule avant la conversion."
                )
                return
            dossier = self._ctx.dossier_service.ouvrir_dossier(
                self._session,
                vehicule_id=vehicule_id,
                client_id=d.client_id,
                kilometrage=0,
            )
            self._ctx.devis_service.marquer_transforme_en_dossier(
                self._session, d.id, dossier.id
            )
            QMessageBox.information(
                self, "Dossier créé",
                f"Dossier de réparation créé avec succès.\n"
                f"Retrouvez-le dans le menu Atelier → Dossiers de réparation."
            )
            self._reload()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def _convertir_proforma(self) -> None:
        d = self._selected()
        if not d:
            return
        try:
            pf = self._ctx.devis_service.convertir_en_proforma(self._session, d.id)
            from garage_app.gui.devis.proforma_viewer_window import ProformaViewerWindow
            dlg = ProformaViewerWindow(self._ctx, self._session, pf, parent=self.parentWidget())
            dlg.exec()
            self._reload()
        except BusinessRuleError as e:
            QMessageBox.warning(self, "Impossible", str(e))

    def _dupliquer(self) -> None:
        d = self._selected()
        if not d:
            return
        try:
            copie = self._ctx.devis_service.dupliquer(self._session, d.id)
            QMessageBox.information(self, "Devis dupliqué", f"Nouveau devis créé : {copie.numero}")
            self._reload()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def _annuler(self) -> None:
        d = self._selected()
        if not d:
            return
        reply = QMessageBox.question(self, "Annuler le devis", f"Annuler le devis {d.numero} ?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self._ctx.devis_service.annuler(self._session, d.id)
            self._reload()
        except BusinessRuleError as e:
            QMessageBox.warning(self, "Impossible", str(e))

    def _imprimer(self) -> None:
        d = self._selected()
        if not d:
            return
        from garage_app.gui.devis.proforma_viewer_window import _render_devis_html
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt6.QtWidgets import QTextBrowser
        html = _render_devis_html(d, self._ctx, self._session)
        browser = QTextBrowser()
        browser.setHtml(html)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            browser.print(printer)
