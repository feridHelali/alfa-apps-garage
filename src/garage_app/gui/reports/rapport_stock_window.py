from __future__ import annotations

from datetime import datetime

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html


def _render(data: dict) -> str:
    rows = "".join(
        f"""<tr>
          <td>{l["reference"]}</td>
          <td>{l["designation"]}</td>
          <td>{l["categorie"]}</td>
          <td class="num">{l["quantite"]}</td>
          <td class="num">{l["seuil"]}</td>
          <td class="num">{l["prix_achat"]:.3f} DT</td>
          <td class="num">{l["val_achat"]:.3f} DT</td>
          <td class="num">{l["val_vente"]:.3f} DT</td>
          <td>{"<span class='badge badge-danger'>Alerte</span>" if l["alerte"] else "<span class='badge badge-ok'>OK</span>"}</td>
        </tr>"""
        for l in data["lignes"]
    )
    body = f"""
<div class="section">
  <h2>Valorisation du stock</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="val">{data["nb_pieces"]}</div><div class="lbl">Références</div></div>
    <div class="kpi"><div class="val">{data["total_achat"]:.3f} DT</div><div class="lbl">Valeur Stock (Achat)</div></div>
    <div class="kpi"><div class="val">{data["total_vente"]:.3f} DT</div><div class="lbl">Valeur Stock (Vente)</div></div>
    <div class="kpi"><div class="val">{data["nb_alerte"]}</div><div class="lbl">En Alerte</div></div>
  </div>
  <table>
    <tr>
      <th>Réf.</th><th>Désignation</th><th>Catégorie</th>
      <th class="num">Qté</th><th class="num">Seuil</th>
      <th class="num">P. Achat</th><th class="num">Val. Achat</th>
      <th class="num">Val. Vente</th><th>Statut</th>
    </tr>
    {rows}
    <tr class="total-row">
      <td colspan="6">TOTAL</td>
      <td class="num">{data["total_achat"]:.3f} DT</td>
      <td class="num">{data["total_vente"]:.3f} DT</td>
      <td></td>
    </tr>
  </table>
</div>"""
    return build_html("Rapport Stock Valorisé",
                      f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", body)


class RapportStockWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession) -> None:
        data = ctx.analytics_service.rapport_stock_valorise(session)
        html = _render(data)
        super().__init__("Rapport Stock Valorisé", html)
