from __future__ import annotations

from datetime import datetime

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html


def _render(data: dict) -> str:
    lignes = data["lignes"]
    if not lignes:
        rows = "<tr><td colspan='3' style='text-align:center;color:#6E6E73;'>Aucune créance.</td></tr>"
    else:
        rows = "".join(
            f"""<tr>
              <td>{l["client"]}</td>
              <td>{l["telephone"]}</td>
              <td class="num" style="font-weight:700;">{l["solde"]:.3f} DT</td>
            </tr>"""
            for l in lignes
        )
    body = f"""
<div class="section">
  <h2>Créances clients</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="val">{len(lignes)}</div><div class="lbl">Clients débiteurs</div></div>
    <div class="kpi"><div class="val">{data["total"]:.3f} DT</div><div class="lbl">Total créances</div></div>
  </div>
  <table>
    <tr><th>Client</th><th>Téléphone</th><th class="num">Solde dû</th></tr>
    {rows}
    <tr class="total-row">
      <td colspan="2">TOTAL</td>
      <td class="num">{data["total"]:.3f} DT</td>
    </tr>
  </table>
</div>"""
    return build_html("Rapport Créances Clients",
                      f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", body)


class RapportCreancesWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        data = ctx.analytics_service.rapport_creances(session)
        html = _render(data)
        super().__init__("Rapport Créances Clients", html)
