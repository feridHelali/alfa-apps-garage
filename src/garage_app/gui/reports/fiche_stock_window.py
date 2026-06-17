from __future__ import annotations

import uuid
from datetime import datetime

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html


def _render(data: dict) -> str:
    p = data["piece"]
    f = data["fournisseur"]
    commandes = data["commandes"]

    alerte = p.quantite_stock <= p.seuil_alerte
    badge = "<span class='badge badge-danger'>Alerte stock</span>" if alerte else "<span class='badge badge-ok'>Stock OK</span>"

    cmd_rows = "".join(
        f"""<tr>
          <td>{c.statut.value}</td>
          <td>{c.date_commande.strftime('%d/%m/%Y') if hasattr(c.date_commande, 'strftime') else '—'}</td>
          <td class="num">{sum(l.quantite_commandee for l in c.lignes if str(l.piece_id) == str(p.id))}</td>
        </tr>"""
        for c in commandes
        if any(str(l.piece_id) == str(p.id) for l in c.lignes)
    )

    body = f"""
<div class="section">
  <h2>Fiche pièce</h2>
  <table>
    <tr><th>Référence</th><td>{p.reference_constructeur}</td><th>Statut</th><td>{badge}</td></tr>
    <tr><th>Désignation</th><td colspan="3">{p.designation}</td></tr>
    <tr><th>Catégorie</th><td>{p.categorie}</td><th>Emplacement</th><td>{p.emplacement or '—'}</td></tr>
    <tr><th>Stock actuel</th><td class="num" style="font-weight:700;color:{'#A4262C' if alerte else '#107C10'}">{p.quantite_stock}</td>
        <th>Seuil alerte</th><td>{p.seuil_alerte}</td></tr>
    <tr><th>Prix achat</th><td class="num">{p.prix_achat:.3f} DT</td>
        <th>Prix vente</th><td class="num">{p.prix_vente:.3f} DT</td></tr>
    <tr><th>Valeur stock (achat)</th><td class="num">{(p.prix_achat * p.quantite_stock):.3f} DT</td>
        <th>Valeur stock (vente)</th><td class="num">{(p.prix_vente * p.quantite_stock):.3f} DT</td></tr>
    <tr><th>Fournisseur</th><td colspan="3">{f.raison_sociale if f else '—'}</td></tr>
  </table>
</div>
<div class="section">
  <h2>Commandes concernées</h2>
  <table>
    <tr><th>Statut</th><th>Date</th><th class="num">Qté commandée</th></tr>
    {cmd_rows or '<tr><td colspan="3" style="color:#6E6E73">Aucune commande.</td></tr>'}
  </table>
</div>"""
    return build_html(
        f"Fiche Stock — {p.designation}",
        f"Réf. {p.reference_constructeur} | Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        body,
    )


class FicheStockWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession, piece_id: uuid.UUID) -> None:
        data = ctx.analytics_service.fiche_piece(session, piece_id)
        html = _render(data)
        super().__init__(f"Fiche Stock — {data['piece'].designation}", html)
