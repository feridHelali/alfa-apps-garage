from __future__ import annotations

from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QVBoxLayout,
)

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html

_MOIS = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
         "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]


def _render(annee: int, data: list[dict]) -> str:
    total_ht = sum(d["ca_ht"] for d in data)
    total_tva = sum(d["tva"] for d in data)
    total_ttc = sum(d["ca_ttc"] for d in data)
    total_enc = sum(d["encaisse"] for d in data)
    rows = "".join(
        f"""<tr>
          <td>{_MOIS[d["mois"]]}</td>
          <td class="num">{d["nb_factures"]}</td>
          <td class="num">{d["ca_ht"]:.3f} DT</td>
          <td class="num">{d["tva"]:.3f} DT</td>
          <td class="num">{d["ca_ttc"]:.3f} DT</td>
          <td class="num">{d["encaisse"]:.3f} DT</td>
        </tr>"""
        for d in data
    )
    body = f"""
<div class="section">
  <h2>Chiffre d'affaires mensuel — {annee}</h2>
  <div class="kpi-grid">
    <div class="kpi"><div class="val">{total_ttc:.3f} DT</div><div class="lbl">CA TTC Total</div></div>
    <div class="kpi"><div class="val">{total_ht:.3f} DT</div><div class="lbl">CA HT Total</div></div>
    <div class="kpi"><div class="val">{total_tva:.3f} DT</div><div class="lbl">TVA Collectée</div></div>
    <div class="kpi"><div class="val">{total_enc:.3f} DT</div><div class="lbl">Encaissé</div></div>
  </div>
  <table>
    <tr><th>Mois</th><th class="num">Factures</th>
        <th class="num">CA HT</th><th class="num">TVA</th>
        <th class="num">CA TTC</th><th class="num">Encaissé</th></tr>
    {rows}
    <tr class="total-row">
      <td>TOTAL</td>
      <td class="num">{sum(d["nb_factures"] for d in data)}</td>
      <td class="num">{total_ht:.3f} DT</td>
      <td class="num">{total_tva:.3f} DT</td>
      <td class="num">{total_ttc:.3f} DT</td>
      <td class="num">{total_enc:.3f} DT</td>
    </tr>
  </table>
</div>"""
    return build_html(f"Rapport CA Mensuel {annee}",
                      f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", body)


class RapportMensuelWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession, annee: int) -> None:
        data = ctx.analytics_service.rapport_ca_mensuel(session, annee)
        html = _render(annee, data)
        super().__init__(f"Rapport CA Mensuel {annee}", html)


class AnneeDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Choisir l'année")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._spin = QSpinBox()
        self._spin.setRange(2020, 2099)
        self._spin.setValue(datetime.now().year)
        form.addRow("Année :", self._spin)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def annee(self) -> int:
        return self._spin.value()
