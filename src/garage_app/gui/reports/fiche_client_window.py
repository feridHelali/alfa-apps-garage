from __future__ import annotations

import uuid
from datetime import datetime

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html


def _render(data: dict) -> str:
    c = data["client"]
    nom = f"{c.nom} {c.prenom}".strip()
    vehicules = data["vehicules"]
    dossiers = data["dossiers"]
    factures = data["factures"]

    veh_rows = "".join(
        f"<tr><td>{v.marque} {v.modele}</td><td>{v.immatriculation}</td><td>{v.annee}</td><td>{v.vin or '—'}</td></tr>"
        for v in vehicules
    )
    dos_rows = "".join(
        f"<tr><td>{d.statut.value}</td><td>{d.notes[:50] if d.notes else '—'}</td></tr>"
        for d in dossiers
    )
    fac_rows = "".join(
        f"""<tr>
          <td>{f.numero}</td>
          <td class="num">{f.montant_ttc.amount:.3f} DT</td>
          <td class="num">{f.montant_paye:.3f} DT</td>
          <td class="num">{f.solde_restant:.3f} DT</td>
          <td>{f.statut.value}</td>
        </tr>"""
        for f in factures
    )

    body = f"""
<div class="section">
  <h2>Informations client</h2>
  <table>
    <tr><th>Nom</th><td>{nom}</td><th>Téléphone</th><td>{c.telephone}</td></tr>
    <tr><th>Email</th><td>{c.email or '—'}</td><th>Type</th><td>{"Flotte" if c.est_flotte else "Particulier"}</td></tr>
    <tr><th>Adresse</th><td colspan="3">{c.adresse or '—'}</td></tr>
  </table>
</div>
<div class="section">
  <h2>Véhicules ({len(vehicules)})</h2>
  <table>
    <tr><th>Marque/Modèle</th><th>Immatriculation</th><th>Année</th><th>VIN</th></tr>
    {veh_rows or '<tr><td colspan="4" style="color:#6E6E73">Aucun véhicule.</td></tr>'}
  </table>
</div>
<div class="section">
  <h2>Dossiers de réparation ({len(dossiers)})</h2>
  <table>
    <tr><th>Statut</th><th>Notes</th></tr>
    {dos_rows or '<tr><td colspan="2" style="color:#6E6E73">Aucun dossier.</td></tr>'}
  </table>
</div>
<div class="section">
  <h2>Facturation</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="val">{len(factures)}</div><div class="lbl">Factures</div></div>
    <div class="kpi"><div class="val">{data["total_facture"]:.3f} DT</div><div class="lbl">Total Facturé</div></div>
    <div class="kpi"><div class="val">{data["total_paye"]:.3f} DT</div><div class="lbl">Payé</div></div>
    <div class="kpi"><div class="val">{data["solde"]:.3f} DT</div><div class="lbl">Solde dû</div></div>
  </div>
  <table>
    <tr><th>N° Facture</th><th class="num">Montant TTC</th><th class="num">Payé</th><th class="num">Solde</th><th>Statut</th></tr>
    {fac_rows or '<tr><td colspan="5" style="color:#6E6E73">Aucune facture.</td></tr>'}
  </table>
</div>"""
    return build_html(
        f"Fiche Client — {nom}",
        f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        body,
    )


class FicheClientWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession, client_id: uuid.UUID) -> None:
        data = ctx.analytics_service.fiche_client(session, client_id)
        nom = f"{data['client'].nom} {data['client'].prenom}".strip()
        html = _render(data)
        super().__init__(f"Fiche Client — {nom}", html)
