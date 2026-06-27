from __future__ import annotations

import base64
from decimal import Decimal

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMdiSubWindow,
    QMessageBox, QPushButton, QSpinBox, QTableView, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.shared.value_objects import Money
from garage_app.gui.widgets.icon_helper import icon as _icon

_QUICK_SVG = base64.b64encode(b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path fill="white" d="M7 2v11h3v9l7-12h-4l4-8z"/>
</svg>""").decode()


class _LignesModel(QAbstractTableModel):
    HEADERS = ["Type", "Désignation", "Qté", "Prix unit. (DT)", "Total (DT)"]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[dict] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        r = self._rows[index.row()]
        total = Decimal(str(r["quantite"])) * Decimal(str(r["prix_unitaire"]))
        return [
            r["type"],
            r["designation"],
            str(r["quantite"]),
            f"{r['prix_unitaire']:.3f}",
            f"{total:.3f}",
        ][index.column()]

    def add_ligne(self, ligne: dict) -> None:
        pos = len(self._rows)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self._rows.append(ligne)
        self.endInsertRows()

    def remove_ligne(self, row: int) -> None:
        if 0 <= row < len(self._rows):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._rows.pop(row)
            self.endRemoveRows()

    def get_lignes(self) -> list[dict]:
        return [
            {
                "designation": r["designation"],
                "quantite": r["quantite"],
                "prix_unitaire": r["prix_unitaire"],
            }
            for r in self._rows
        ]

    def total_ht(self) -> Decimal:
        return sum(
            (Decimal(str(r["quantite"])) * Decimal(str(r["prix_unitaire"])) for r in self._rows),
            Decimal("0"),
        )


class _AddLigneDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ajouter une ligne")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._type = QComboBox()
        self._type.addItems(["Service / Main d'œuvre", "Pièce"])
        form.addRow("Type *", self._type)

        self._designation = QLineEdit()
        self._designation.setPlaceholderText("Description de la prestation ou pièce")
        form.addRow("Désignation *", self._designation)

        self._qty = QSpinBox()
        self._qty.setRange(1, 9999)
        self._qty.setValue(1)
        form.addRow("Quantité *", self._qty)

        self._prix = QDoubleSpinBox()
        self._prix.setRange(0.001, 999_999.999)
        self._prix.setDecimals(3)
        self._prix.setSuffix(" DT")
        form.addRow("Prix unitaire *", self._prix)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validate)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.resize(360, 200)

    def _validate(self) -> None:
        if not self._designation.text().strip():
            QMessageBox.warning(self, "Saisie", "La désignation est obligatoire.")
            return
        if self._prix.value() <= 0:
            QMessageBox.warning(self, "Saisie", "Le prix doit être supérieur à zéro.")
            return
        self.accept()

    @property
    def ligne(self) -> dict:
        return {
            "type": self._type.currentText(),
            "designation": self._designation.text().strip(),
            "quantite": self._qty.value(),
            "prix_unitaire": Decimal(str(self._prix.value())),
        }


class BonTravailRapideWindow(QMdiSubWindow):
    """Quick direct invoice: client + vehicle + lines → facture in one step."""

    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        super().__init__()
        self._ctx = ctx
        self._session = session
        self._clients: list = []
        self.setWindowTitle("Bon de Travail Rapide")
        self._build_ui()
        self._load_clients()

    def _build_ui(self) -> None:
        main = QWidget()
        layout = QVBoxLayout(main)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Bon de Travail Rapide")
        title.setStyleSheet("font-size: 13pt; font-weight: 700; color: #0067C0;")
        layout.addWidget(title)

        # ── Identification ───────────────────────────────────────────────────
        grp_id = QGroupBox("Identification du client / véhicule")
        form = QFormLayout(grp_id)

        self._client_cb = QComboBox()
        self._client_cb.setMinimumWidth(240)
        self._client_cb.currentIndexChanged.connect(self._on_client_changed)
        form.addRow("Client *", self._client_cb)

        self._vehicule_cb = QComboBox()
        self._vehicule_cb.setMinimumWidth(240)
        form.addRow("Véhicule *", self._vehicule_cb)

        self._km = QSpinBox()
        self._km.setRange(0, 9_999_999)
        self._km.setSuffix(" km")
        form.addRow("Kilométrage", self._km)

        self._notes = QLineEdit()
        self._notes.setPlaceholderText("Notes optionnelles sur la réparation")
        form.addRow("Notes", self._notes)

        layout.addWidget(grp_id)

        # ── Lines table ──────────────────────────────────────────────────────
        grp_lignes = QGroupBox("Prestations / Pièces")
        gv = QVBoxLayout(grp_lignes)

        self._model = _LignesModel()
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        gv.addWidget(self._table)

        ligne_btns = QHBoxLayout()
        btn_add = QPushButton(_icon("new"), "+ Ajouter ligne")
        btn_add.clicked.connect(self._add_ligne)
        btn_rm = QPushButton(_icon("delete"), "Supprimer ligne sélectionnée")
        btn_rm.clicked.connect(self._remove_ligne)
        ligne_btns.addWidget(btn_add)
        ligne_btns.addWidget(btn_rm)
        ligne_btns.addStretch()
        gv.addLayout(ligne_btns)

        layout.addWidget(grp_lignes, stretch=1)

        # ── Totals + TVA ─────────────────────────────────────────────────────
        tot_row = QHBoxLayout()

        form_tva = QFormLayout()
        self._tva_spin = QDoubleSpinBox()
        self._tva_spin.setRange(0, 100)
        self._tva_spin.setDecimals(1)
        self._tva_spin.setValue(19.0)
        self._tva_spin.setSuffix(" %")
        self._tva_spin.valueChanged.connect(self._refresh_totals)
        form_tva.addRow("TVA :", self._tva_spin)
        tot_row.addLayout(form_tva)
        tot_row.addStretch()

        form_tot = QFormLayout()
        self._lbl_ht = QLabel("0,000 DT")
        self._lbl_tva_amt = QLabel("0,000 DT")
        self._lbl_ttc = QLabel("0,000 DT")
        self._lbl_ttc.setStyleSheet("font-weight: 700; font-size: 11pt;")
        form_tot.addRow("Total HT :", self._lbl_ht)
        form_tot.addRow("TVA :", self._lbl_tva_amt)
        form_tot.addRow("Total TTC :", self._lbl_ttc)
        tot_row.addLayout(form_tot)

        layout.addLayout(tot_row)

        # ── Generate button ──────────────────────────────────────────────────
        btn_gen = QPushButton("  Générer Facture  ")
        btn_gen.setDefault(True)
        btn_gen.setStyleSheet(
            "background:#107C10; color:white; font-weight:bold;"
            "padding:6px 20px; border-radius:4px; font-size:10pt;"
        )
        btn_gen.clicked.connect(self._generate)
        layout.addWidget(btn_gen, alignment=Qt.AlignmentFlag.AlignRight)

        self.setWidget(main)
        self.resize(780, 640)

    def _load_clients(self) -> None:
        self._clients = self._ctx.client_service.list_clients(self._session)
        self._client_cb.blockSignals(True)
        self._client_cb.clear()
        self._client_cb.addItem("— Choisir un client —", None)
        for c in self._clients:
            self._client_cb.addItem(f"{c.nom} {c.prenom}".strip(), c.id)
        self._client_cb.blockSignals(False)
        self._on_client_changed()

    def _on_client_changed(self) -> None:
        client_id = self._client_cb.currentData()
        self._vehicule_cb.clear()
        if client_id is None:
            self._vehicule_cb.addItem("— Choisir d'abord un client —", None)
            return
        vehicules = self._ctx.client_service.get_vehicules(self._session, client_id)
        if not vehicules:
            self._vehicule_cb.addItem("Aucun véhicule enregistré", None)
        else:
            for v in vehicules:
                self._vehicule_cb.addItem(
                    f"{v.marque} {v.modele} ({v.immatriculation})", v.id
                )

    def _add_ligne(self) -> None:
        dlg = _AddLigneDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._model.add_ligne(dlg.ligne)
            self._refresh_totals()

    def _remove_ligne(self) -> None:
        row = self._table.currentIndex().row()
        if row >= 0:
            self._model.remove_ligne(row)
            self._refresh_totals()

    def _refresh_totals(self) -> None:
        ht = self._model.total_ht()
        tva_rate = Decimal(str(self._tva_spin.value())) / Decimal("100")
        tva_amt = ht * tva_rate
        self._lbl_ht.setText(Money.of(ht).format())
        self._lbl_tva_amt.setText(Money.of(tva_amt).format())
        self._lbl_ttc.setText(Money.of(ht + tva_amt).format())

    def _generate(self) -> None:
        client_id = self._client_cb.currentData()
        vehicule_id = self._vehicule_cb.currentData()
        if client_id is None or vehicule_id is None:
            QMessageBox.warning(
                self, "Saisie incomplète",
                "Veuillez sélectionner un client et un véhicule.",
            )
            return
        lignes = self._model.get_lignes()
        if not lignes:
            QMessageBox.warning(
                self, "Saisie incomplète",
                "Ajoutez au moins une prestation ou pièce avant de générer la facture.",
            )
            return
        try:
            facture = self._ctx.facture_service.generer_facture_directe(
                self._session,
                client_id=client_id,
                vehicule_id=vehicule_id,
                lignes=lignes,
                taux_tva=Decimal(str(self._tva_spin.value())),
                notes=self._notes.text().strip(),
                kilometrage=self._km.value(),
            )
            from garage_app.gui.reports.facture_report_window import FactureReportWindow
            from garage_app.gui.window_registry import open_sub
            mdi = self.mdiArea()
            if mdi:
                open_sub(mdi, FactureReportWindow(self._ctx, self._session, facture))
            QMessageBox.information(
                self, "Facture créée",
                f"Facture {facture.numero} générée avec succès.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))
