from __future__ import annotations

import uuid
from datetime import datetime

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html


def _render(data: dict) -> str:
    f = data["fournisseur"]
    pieces = data["pieces"]
    commandes = data["commandes"]

    piece_rows = "".join(
        f"""<tr>
          <td>{p.reference_constructeur}</td>
          <td>{p.designation}</td>
          <td class="num">{p.quantite_stock}</td>
          <td class="num">{p.prix_achat:.3f} DT</td>
        </tr>"""
        for p in pieces
    )
    cmd_rows = "".join(
        f"""<tr>
          <td>{c.date_commande.strftime('%d/%m/%Y') if hasattr(c.date_commande, 'strftime') else '—'}</td>
          <td class="num">{len(c.lignes)}</td>
          <td>{c.statut.value}</td>
          <td>{c.notes[:40] if c.notes else '—'}</td>
        </tr>"""
        for c in commandes
    )

    body = f"""
<div class="section">
  <h2>Informations fournisseur</h2>
  <table>
    <tr><th>Raison sociale</th><td colspan="3">{f.raison_sociale}</td></tr>
    <tr><th>Contact</th><td>{f.contact_nom or '—'}</td><th>Téléphone</th><td>{f.telephone or '—'}</td></tr>
    <tr><th>Email</th><td>{f.email or '—'}</td><th>Délai livraison</th><td>{f.delai_livraison_jours} jours</td></tr>
    <tr><th>Adresse</th><td colspan="3">{f.adresse or '—'}</td></tr>
    <tr><th>Statut</th><td colspan="3">{"<span class='badge badge-ok'>Actif</span>" if f.est_actif else "<span class='badge badge-danger'>Inactif</span>"}</td></tr>
  </table>
</div>
<div class="section">
  <h2>Catalogue pièces ({len(pieces)} références)</h2>
  <table>
    <tr><th>Référence</th><th>Désignation</th><th class="num">Stock</th><th class="num">Prix achat</th></tr>
    {piece_rows or '<tr><td colspan="4" style="color:#6E6E73">Aucune pièce.</td></tr>'}
  </table>
</div>
<div class="section">
  <h2>Commandes ({len(commandes)})</h2>
  <table>
    <tr><th>Date</th><th class="num">Lignes</th><th>Statut</th><th>Notes</th></tr>
    {cmd_rows or '<tr><td colspan="4" style="color:#6E6E73">Aucune commande.</td></tr>'}
  </table>
</div>"""
    return build_html(
        f"Fiche Fournisseur — {f.raison_sociale}",
        f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        body,
    )


class FicheFournisseurWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession, fournisseur_id: uuid.UUID) -> None:
        data = ctx.analytics_service.fiche_fournisseur(session, fournisseur_id)
        html = _render(data)
        super().__init__(f"Fiche Fournisseur — {data['fournisseur'].raison_sociale}", html)
