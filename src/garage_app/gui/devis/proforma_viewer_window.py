"""ProformaViewerWindow — HTML preview + acompte + print for FactureProforma.

Also exports _render_devis_html() used by DevisListWindow for print.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextBrowser,
    QToolBar, QVBoxLayout, QWidget,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.devis.devis import Devis, FactureProforma
from garage_app.domain.shared.value_objects import Money


# ── HTML rendering helpers ───────────────────────────────────────────────────

def _fmt(amount: Decimal) -> str:
    return f"{amount:,.3f}".replace(",", " ").replace(".", ",") + " DT"


def _get_client_nom(client_id: uuid.UUID, ctx: AppContext, session: UserSession) -> str:
    try:
        clients = ctx.client_service.list_clients(session)
        for c in clients:
            if c.id == client_id:
                return f"{c.nom} {c.prenom}"
    except Exception:
        pass
    return str(client_id)[:8]


def _render_devis_html(d: Devis, ctx: AppContext, session: UserSession) -> str:
    client_nom = _get_client_nom(d.client_id, ctx, session)
    rows_html = ""
    for i, l in enumerate(d.lignes):
        bg = "#f4f2ee" if i % 2 == 0 else "#ffffff"
        rows_html += (
            f'<tr style="background:{bg};">'
            f'<td>{l.type_ligne.label_fr()}</td>'
            f'<td>{l.designation}</td>'
            f'<td style="text-align:right;">{l.quantite}</td>'
            f'<td style="text-align:right;">{_fmt(l.prix_unitaire_ht.amount)}</td>'
            f'<td style="text-align:right;">{int(float(l.taux_tva) * 100)}%</td>'
            f'<td style="text-align:right;">{_fmt(l.montant_ht.amount)}</td>'
            f'<td style="text-align:right;">{_fmt(l.montant_ttc.amount)}</td>'
            f'</tr>'
        )

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;font-size:10pt;margin:20px;color:#333;}}
.header{{background:#0055a5;color:white;padding:12px 16px;border-radius:4px;margin-bottom:12px;}}
.header h2{{margin:0;font-size:14pt;}} .header p{{margin:2px 0;font-size:9pt;opacity:.85;}}
table{{width:100%;border-collapse:collapse;margin:10px 0;}}
th{{background:#0055a5;color:white;padding:5px 8px;text-align:left;font-size:9pt;}}
td{{padding:4px 8px;border-bottom:1px solid #e0e0e0;font-size:9pt;}}
.totals{{margin-top:8px;text-align:right;}}
.totals td{{border:none;padding:2px 8px;}}
.grand-total{{font-weight:bold;font-size:12pt;color:#0055a5;}}
</style></head><body>
<div class="header">
<h2>Devis N° {d.numero}</h2>
<p>Date : {d.date_creation.isoformat() if d.date_creation else '—'}
{'&nbsp;&nbsp;|&nbsp;&nbsp;Expiration : ' + d.date_expiration.isoformat() if d.date_expiration else ''}</p>
<p>Client : {client_nom}</p>
</div>
<p><b>Objet :</b> {d.notes_client or '—'}</p>
<table>
<thead><tr>
<th>Type</th><th>Désignation</th><th>Qté</th><th>PU HT</th><th>TVA</th><th>Total HT</th><th>Total TTC</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
<table class="totals">
<tr><td>Total HT :</td><td>{_fmt(d.total_ht.amount)}</td></tr>
<tr><td>TVA :</td><td>{_fmt(d.total_tva.amount)}</td></tr>
<tr class="grand-total"><td>Total TTC :</td><td>{_fmt(d.total_ttc.amount)}</td></tr>
</table>
{'<p><i>' + d.notes_internes + '</i></p>' if d.notes_internes else ''}
<p style="margin-top:20px;font-size:8.5pt;color:#888;">
Devis établi par Alfa Computers Apps — Solutions de Gestion sur Mesure<br/>
Ce devis est valable jusqu'au {d.date_expiration.isoformat() if d.date_expiration else 'la date de votre accord'}.
</p>
</body></html>"""


def _render_proforma_html(pf: FactureProforma, ctx: AppContext, session: UserSession) -> str:
    client_nom = _get_client_nom(pf.client_id, ctx, session)
    rows_html = ""
    for i, l in enumerate(pf.lignes):
        bg = "#f4f2ee" if i % 2 == 0 else "#ffffff"
        rows_html += (
            f'<tr style="background:{bg};">'
            f'<td>{l.type_ligne.label_fr()}</td>'
            f'<td>{l.designation}</td>'
            f'<td style="text-align:right;">{l.quantite}</td>'
            f'<td style="text-align:right;">{_fmt(l.prix_unitaire_ht.amount)}</td>'
            f'<td style="text-align:right;">{int(float(l.taux_tva) * 100)}%</td>'
            f'<td style="text-align:right;">{_fmt(l.montant_ht.amount)}</td>'
            f'<td style="text-align:right;">{_fmt(l.montant_ttc.amount)}</td>'
            f'</tr>'
        )

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;font-size:10pt;margin:20px;color:#333;}}
.header{{background:#0067C0;color:white;padding:12px 16px;border-radius:4px;margin-bottom:12px;}}
.header h2{{margin:0;font-size:14pt;}} .header p{{margin:2px 0;font-size:9pt;opacity:.85;}}
.badge{{display:inline-block;background:#ffc107;color:#333;padding:2px 8px;border-radius:3px;
        font-size:9pt;font-weight:bold;margin-bottom:4px;}}
table{{width:100%;border-collapse:collapse;margin:10px 0;}}
th{{background:#0067C0;color:white;padding:5px 8px;text-align:left;font-size:9pt;}}
td{{padding:4px 8px;border-bottom:1px solid #e0e0e0;font-size:9pt;}}
.totals{{margin-top:8px;text-align:right;}}
.totals td{{border:none;padding:2px 8px;}}
.grand-total{{font-weight:bold;font-size:12pt;color:#0067C0;}}
.acompte{{color:#198754;font-weight:bold;}}
.solde{{color:#dc3545;font-weight:bold;font-size:12pt;}}
</style></head><body>
<div class="header">
<span class="badge">PROFORMA</span>
<h2>Facture Proforma N° {pf.numero}</h2>
<p>Date d'émission : {pf.date_emission.isoformat() if pf.date_emission else '—'}</p>
<p>Client : {client_nom}</p>
</div>
<table>
<thead><tr>
<th>Type</th><th>Désignation</th><th>Qté</th><th>PU HT</th><th>TVA</th><th>Total HT</th><th>Total TTC</th>
</tr></thead>
<tbody>{rows_html}</tbody>
</table>
<table class="totals">
<tr><td>Total HT :</td><td>{_fmt(pf.total_ht.amount)}</td></tr>
<tr class="grand-total"><td>Total TTC :</td><td>{_fmt(pf.total_ttc.amount)}</td></tr>
{'<tr class="acompte"><td>Acompte reçu :</td><td>- ' + _fmt(pf.acompte_recu.amount) + '</td></tr>' if pf.acompte_recu.amount > Decimal("0") else ''}
{'<tr class="solde"><td>Solde restant :</td><td>' + _fmt(pf.solde_restant.amount) + '</td></tr>' if pf.acompte_recu.amount > Decimal("0") else ''}
</table>
<p style="margin-top:20px;font-size:8.5pt;color:#888;">
<b>Ce document est une facture proforma et n'a pas de valeur comptable.</b><br/>
Alfa Computers Apps — Solutions de Gestion sur Mesure
</p>
</body></html>"""


# ── Window ───────────────────────────────────────────────────────────────────

class ProformaViewerWindow(QDialog):
    """View a FactureProforma, record acompte, print."""

    def __init__(
        self,
        ctx: AppContext,
        session: UserSession,
        proforma: FactureProforma,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._ctx = ctx
        self._session = session
        self._proforma = proforma

        self.setWindowTitle(f"Facture Proforma — {proforma.numero}")
        self.setMinimumSize(780, 580)

        root = QVBoxLayout(self)

        # toolbar
        toolbar = QHBoxLayout()
        btn_print = QPushButton("Imprimer…")
        btn_print.clicked.connect(self._print)

        can_acompte = session.can(Permission.MANAGE_PROFORMA)
        btn_acompte = QPushButton("Enregistrer un acompte…")
        btn_acompte.setEnabled(can_acompte and proforma.statut.value in ("emise", "acompte_recu"))
        btn_acompte.clicked.connect(self._acompte)

        lbl_statut = QLabel(f"Statut : {proforma.statut.label_fr()}")
        lbl_statut.setStyleSheet(f"color:{proforma.statut.color()};font-weight:bold;")

        toolbar.addWidget(lbl_statut)
        toolbar.addStretch()
        toolbar.addWidget(btn_acompte)
        toolbar.addWidget(btn_print)
        root.addLayout(toolbar)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        root.addWidget(self._browser)

        root.addWidget(
            QDialogButtonBox(QDialogButtonBox.StandardButton.Close,
                             accepted=self.accept, rejected=self.reject)
        )

        self._refresh()

    def _refresh(self) -> None:
        html = _render_proforma_html(self._proforma, self._ctx, self._session)
        self._browser.setHtml(html)

    def _print(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            self._browser.print(printer)

    def _acompte(self) -> None:
        dlg = _AcompteDialog(float(self._proforma.solde_restant.amount), parent=self)
        if dlg.exec():
            montant = dlg.montant()
            try:
                self._proforma = self._ctx.devis_service.enregistrer_acompte_proforma(
                    self._session, self._proforma.id, Decimal(str(montant))
                )
                self._refresh()
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))


class _AcompteDialog(QDialog):
    def __init__(self, max_montant: float, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Enregistrer un acompte")
        form = QFormLayout(self)
        self._spin = QDoubleSpinBox()
        self._spin.setDecimals(3)
        self._spin.setRange(0.001, max_montant)
        self._spin.setValue(max_montant)
        self._spin.setSuffix(" DT")
        form.addRow("Montant de l'acompte :", self._spin)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def montant(self) -> float:
        return self._spin.value()
