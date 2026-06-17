from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html


def _render(data: dict) -> str:
    d = data["dossier"]
    v = data["vehicule"]
    c = data["client"]
    f = data["facture"]

    client_nom = f"{c.nom} {c.prenom}".strip() if c else "—"
    veh_info = f"{v.marque} {v.modele} ({v.immatriculation})" if v else "—"

    op_rows = "".join(
        f"""<tr>
          <td>{op.code_main_oeuvre}</td>
          <td>{op.description}</td>
          <td class="num">{op.temps_passe:.2f} h</td>
          <td class="num">{op.taux_horaire:.3f} DT/h</td>
          <td class="num">{(op.temps_passe * op.taux_horaire):.3f} DT</td>
          <td>{op.statut.value}</td>
        </tr>"""
        for op in d.operations
    )
    piece_rows = "".join(
        f"""<tr>
          <td>{p.reference}</td>
          <td>{p.designation}</td>
          <td class="num">{p.quantite}</td>
          <td class="num">{p.prix_unitaire:.3f} DT</td>
          <td class="num">{(p.quantite * p.prix_unitaire):.3f} DT</td>
        </tr>"""
        for p in d.pieces
    )

    total_mo = sum(op.temps_passe * op.taux_horaire for op in d.operations)
    total_pieces = sum(p.quantite * p.prix_unitaire for p in d.pieces)
    total_ht = total_mo + total_pieces

    fac_section = ""
    if f:
        fac_section = f"""
<div class="section">
  <h2>Facture — {f.numero}</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="val">{f.montant_ht.amount:.3f} DT</div><div class="lbl">HT</div></div>
    <div class="kpi"><div class="val">{f.montant_tva.amount:.3f} DT</div><div class="lbl">TVA ({f.taux_tva}%)</div></div>
    <div class="kpi"><div class="val">{f.montant_ttc.amount:.3f} DT</div><div class="lbl">TTC</div></div>
    <div class="kpi"><div class="val">{f.solde_restant:.3f} DT</div><div class="lbl">Solde dû</div></div>
  </div>
</div>"""

    body = f"""
<div class="section">
  <h2>Informations dossier</h2>
  <table>
    <tr><th>Client</th><td>{client_nom}</td><th>Véhicule</th><td>{veh_info}</td></tr>
    <tr><th>Kilométrage entrée</th><td>{d.kilometrage_entree} km</td><th>Statut</th><td>{d.statut.value}</td></tr>
    <tr><th>Notes</th><td colspan="3">{d.notes or '—'}</td></tr>
  </table>
</div>
<div class="section">
  <h2>Opérations main d'œuvre ({len(d.operations)})</h2>
  <table>
    <tr><th>Code</th><th>Description</th><th class="num">Temps passé</th>
        <th class="num">Taux horaire</th><th class="num">Montant</th><th>Statut</th></tr>
    {op_rows or '<tr><td colspan="6" style="color:#6E6E73">Aucune opération.</td></tr>'}
    {"<tr class='total-row'><td colspan='4'>Total main d'œuvre</td><td class='num'>" + f"{total_mo:.3f} DT</td><td></td></tr>" if d.operations else ""}
  </table>
</div>
<div class="section">
  <h2>Pièces requises ({len(d.pieces)})</h2>
  <table>
    <tr><th>Référence</th><th>Désignation</th>
        <th class="num">Quantité</th><th class="num">Prix unitaire</th><th class="num">Total</th></tr>
    {piece_rows or '<tr><td colspan="5" style="color:#6E6E73">Aucune pièce.</td></tr>'}
    {"<tr class='total-row'><td colspan='4'>Total pièces</td><td class='num'>" + f"{total_pieces:.3f} DT</td></tr>" if d.pieces else ""}
  </table>
</div>
{fac_section}"""
    return build_html(
        f"Fiche Réparation",
        f"Client : {client_nom} | Véhicule : {veh_info} | Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        body,
    )


class FicheReparationWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession, dossier_id: uuid.UUID) -> None:
        data = ctx.analytics_service.fiche_reparation(session, dossier_id)
        c = data["client"]
        client_nom = f"{c.nom} {c.prenom}".strip() if c else "Dossier"
        html = _render(data)
        super().__init__(f"Fiche Réparation — {client_nom}", html)
