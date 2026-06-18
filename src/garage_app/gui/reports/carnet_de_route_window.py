from __future__ import annotations

import base64
import uuid
from datetime import datetime

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html

# Car SVG illustration for the carnet de route header
_CAR_SVG = base64.b64encode(b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path fill="white" d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"/>
</svg>""").decode()


def _render(data: dict) -> str:
    v = data["vehicule"]
    client = data["client"]
    dossiers = data["dossiers"]

    client_nom = f"{client.nom} {client.prenom}".strip() if client else "—"
    veh_label = f"{v.marque} {v.modele} {v.annee}"

    dos_rows = ""
    for d in sorted(dossiers, key=lambda x: x.kilometrage_entree):
        ops_list = ", ".join(op.description for op in d.operations) or "—"
        pieces_list = ", ".join(
            f"{p.designation} ×{p.quantite}" for p in d.pieces
        ) or "—"
        statut_cls = "badge-ok" if d.statut.value in ("pret", "cloture") else "badge-warn"
        dos_rows += f"""<tr>
          <td>{d.kilometrage_entree:,} km</td>
          <td><span class="badge {statut_cls}">{d.statut.value.upper()}</span></td>
          <td>{ops_list}</td>
          <td>{pieces_list}</td>
          <td>{d.notes[:60] if d.notes else '—'}</td>
        </tr>"""

    body = f"""
<div class="section">
  <h2>Véhicule</h2>
  <table>
    <tr>
      <th>Marque / Modèle</th><td>{veh_label}</td>
      <th>Immatriculation</th><td>{v.immatriculation}</td>
    </tr>
    <tr>
      <th>VIN</th><td>{v.vin or '—'}</td>
      <th>Couleur</th><td>{v.couleur or '—'}</td>
    </tr>
    <tr>
      <th>Propriétaire</th><td colspan="3">{client_nom}</td>
    </tr>
  </table>
</div>
<div class="section">
  <h2>Résumé</h2>
  <div class="kpi-grid">
    <div class="kpi">
      <div class="val">{data["nb_interventions"]}</div>
      <div class="lbl">Interventions</div>
    </div>
    <div class="kpi">
      <div class="val">{data["km_max"]:,}</div>
      <div class="lbl">Km max enregistré</div>
    </div>
    <div class="kpi">
      <div class="val">{data["total_ops"]}</div>
      <div class="lbl">Opérations</div>
    </div>
    <div class="kpi">
      <div class="val">{data["total_pieces"]}</div>
      <div class="lbl">Pièces utilisées</div>
    </div>
  </div>
</div>
<div class="section">
  <h2>Historique des interventions ({len(dossiers)})</h2>
  <table>
    <tr>
      <th>Kilométrage</th>
      <th>Statut</th>
      <th>Opérations effectuées</th>
      <th>Pièces posées</th>
      <th>Notes</th>
    </tr>
    {dos_rows or '<tr><td colspan="5" style="color:#6E6E73">Aucune intervention enregistrée.</td></tr>'}
  </table>
</div>"""

    return build_html(
        f"Carnet de Route — {v.immatriculation}",
        f"{veh_label}  |  Propriétaire : {client_nom}  |  Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        body,
        icon_svg_b64=_CAR_SVG,
    )


class CarnetDeRouteWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession, vehicule_id: uuid.UUID) -> None:
        data = ctx.analytics_service.carnet_de_route(session, vehicule_id)
        v = data["vehicule"]
        html = _render(data)
        super().__init__(f"Carnet de Route — {v.immatriculation}", html)
