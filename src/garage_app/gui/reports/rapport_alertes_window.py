from __future__ import annotations

from datetime import datetime

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html


def _render(lignes: list[dict]) -> str:
    if not lignes:
        rows = "<tr><td colspan='6' style='text-align:center;color:#6E6E73;'>Aucune alerte stock.</td></tr>"
    else:
        rows = "".join(
            f"""<tr>
              <td>{l["reference"]}</td>
              <td>{l["designation"]}</td>
              <td class="num" style="color:#A4262C;font-weight:700;">{l["quantite"]}</td>
              <td class="num">{l["seuil"]}</td>
              <td class="num">{l["a_commander"]}</td>
              <td>{l["fournisseur"]}</td>
            </tr>"""
            for l in lignes
        )
    body = f"""
<div class="section">
  <h2>Alertes stock — {len(lignes)} référence(s)</h2>
  <p style="color:#A4262C;font-weight:600;">
    {"⚠ " + str(len(lignes)) + " référence(s) en rupture ou sous le seuil d'alerte." if lignes else "✓ Aucune alerte stock."}
  </p>
  <table>
    <tr>
      <th>Réf.</th><th>Désignation</th>
      <th class="num">Qté actuelle</th><th class="num">Seuil alerte</th>
      <th class="num">Qté à commander</th><th>Fournisseur</th>
    </tr>
    {rows}
  </table>
</div>"""
    return build_html("Rapport Alertes Stock",
                      f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", body)


class RapportAlertesWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        lignes = ctx.analytics_service.rapport_alertes(session)
        html = _render(lignes)
        super().__init__("Rapport Alertes Stock", html)
