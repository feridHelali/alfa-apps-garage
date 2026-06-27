from __future__ import annotations

import base64
import logging

from garage_app.bootstrap import AppContext
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.facture import Facture
from garage_app.gui.reports.report_viewer_window import ReportViewerWindow, build_html
from garage_app.tools.report_engine.html_template_manager import HtmlTemplateManager
from garage_app.tools.report_engine.html_template_renderer import HtmlTemplateRenderer

logger = logging.getLogger(__name__)

# Simple receipt/invoice SVG icon (white fill, works in Qt's HTML renderer)
_INVOICE_SVG = base64.b64encode(b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path fill="#1C1C1E" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3c1.93 0 3.5 1.57 3.5 3.5S13.93 13 12 13s-3.5-1.57-3.5-3.5S10.07 6 12 6zm7 13H5v-.23c0-.62.28-1.2.76-1.58C7.47 15.82 9.64 15 12 15s4.53.82 6.24 2.19c.48.38.76.97.76 1.58V19z"/>
</svg>""").decode()

# Wrench icon for "main d'oeuvre" sections
_WRENCH_SVG_HTML = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="14" height="14" '
    'style="vertical-align:middle; margin-right:4px;">'
    '<path fill="#0055a5" d="M13.1 2.9c-.9-.9-2.1-1.2-3.3-.9L11.5 4 10 5.5 8.3 3.8C8 5 8.3 6.2 9.2 7.1c.8.8 2 1.2 3.1 1L15 10.7c.4.4.4 1 0 1.4l-2.9 2.9c-.4.4-1 .4-1.4 0L8 12.3c-.8.1-1.7-.2-2.4-.9L2.1 14 1 12.9l2.6-2.5C2.9 9.7 2.7 8.8 3 8L1.3 6.3 2.8 4.8 4.5 6.5C5.4 5.6 6.7 5.3 7.9 5.5z"/>'
    '</svg>'
)

_PIECE_SVG_HTML = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="14" height="14" '
    'style="vertical-align:middle; margin-right:4px;">'
    '<path fill="#107C10" d="M8 2l-6 3v6l6 3 6-3V5L8 2zm0 2.2L12.3 6 8 7.8 3.7 6 8 4.2zM3 7.4l4 2V14l-4-2V7.4zm5 2l4-2v4.6l-4 2V9.4z"/>'
    '</svg>'
)


_STATUT_BADGE = {
    "brouillon":           "badge-warn",
    "emise":               "badge-warn",
    "partiellement_payee": "badge-warn",
    "payee":               "badge-ok",
    "annulee":             "badge-danger",
}

_STATUT_LABELS = {
    "brouillon":           "BROUILLON",
    "emise":               "ÉMISE",
    "partiellement_payee": "PART. PAYÉE",
    "payee":               "PAYÉE ✓",
    "annulee":             "ANNULÉE",
}


def _get_client_nom(facture: Facture, ctx: AppContext, session: UserSession, *, with_phone: bool = False) -> str:
    """Fetch the client display name; returns '—' on any failure."""
    try:
        clients = ctx.client_service.list_clients(session)
        client = next((c for c in clients if str(c.id) == str(facture.client_id)), None)
        if client:
            nom = f"{client.nom} {client.prenom}".strip()
            if with_phone and client.telephone:
                nom += f"<br><span style='color:#6E6E73; font-size:8pt'>{client.telephone}</span>"
            return nom
    except Exception:
        pass
    return "—"


def _render(facture: Facture, ctx: AppContext, session: UserSession) -> str:
    client_nom = _get_client_nom(facture, ctx, session, with_phone=True)

    emission_str = (
        facture.date_emission.strftime("%d/%m/%Y")
        if facture.date_emission else "—"
    )

    lignes_html = ""
    for i, ligne in enumerate(facture.lignes, 1):
        lignes_html += f"""<tr>
          <td style="text-align:center; color:#6E6E73">{i}</td>
          <td>{ligne.designation}</td>
          <td style="text-align:right">{ligne.quantite}</td>
          <td class="num">{ligne.prix_unitaire:.3f} DT</td>
          <td class="num"><b>{ligne.montant.format()}</b></td>
        </tr>"""

    if not lignes_html:
        lignes_html = '<tr><td colspan="5" style="color:#6E6E73; padding:12px; text-align:center;">Aucune ligne de facturation.</td></tr>'

    reste = facture.montant_ttc.amount - facture.montant_paye
    reste_color = "#A4262C" if reste > 0 else "#107C10"
    reste_label = "Reste à payer" if reste > 0 else "Solde"

    statut_cls = _STATUT_BADGE.get(facture.statut.value, "badge-warn")
    statut_label = _STATUT_LABELS.get(facture.statut.value, facture.statut.value.upper())

    body = f"""
<div style="display:table; width:100%; margin:14px 0 10px 0;">
  <div style="display:table-cell; vertical-align:top; width:50%;">
    <div style="font-size:8pt; color:#6E6E73; margin-bottom:2px;">FACTURÉ À</div>
    <div style="font-size:10pt; font-weight:700;">{client_nom}</div>
  </div>
  <div style="display:table-cell; vertical-align:top; text-align:right;">
    <table style="width:auto; float:right; border:none;">
      <tr><td style="color:#6E6E73; padding:2px 8px 2px 0; border:none;">N° Facture</td>
          <td style="font-weight:700; padding:2px 0; border:none;">{facture.numero}</td></tr>
      <tr><td style="color:#6E6E73; padding:2px 8px 2px 0; border:none;">Date</td>
          <td style="padding:2px 0; border:none;">{emission_str}</td></tr>
      <tr><td style="color:#6E6E73; padding:2px 8px 2px 0; border:none;">Statut</td>
          <td style="padding:2px 0; border:none;"><span class="badge {statut_cls}">{statut_label}</span></td></tr>
    </table>
  </div>
</div>
<div class="section">
  <h2>Détail des prestations</h2>
  <table>
    <tr>
      <th style="width:30px; text-align:center">#</th>
      <th>Désignation</th>
      <th style="text-align:right; width:50px">Qté</th>
      <th style="text-align:right; width:110px">P.U. HT</th>
      <th style="text-align:right; width:110px">Total HT</th>
    </tr>
    {lignes_html}
  </table>
</div>
<div style="display:table; width:100%; margin-top:12px;">
  <div style="display:table-cell; width:55%; vertical-align:top; color:#6E6E73; font-size:8pt; padding-top:8px;">
    Mode de paiement : {", ".join(p.mode for p in facture.paiements) if facture.paiements else "—"}<br>
    {f"Référence : {facture.paiements[0].reference}" if facture.paiements and facture.paiements[0].reference else ""}
  </div>
  <div style="display:table-cell; vertical-align:top;">
    <table style="border:1px solid #E5E5EA; border-radius:6px; overflow:hidden;">
      <tr>
        <td style="padding:5px 12px; color:#6E6E73; border-bottom:1px solid #F2F2F7;">Total HT</td>
        <td class="num" style="padding:5px 12px; border-bottom:1px solid #F2F2F7;">{facture.montant_ht.format()}</td>
      </tr>
      <tr>
        <td style="padding:5px 12px; color:#6E6E73; border-bottom:1px solid #F2F2F7;">TVA ({facture.taux_tva} %)</td>
        <td class="num" style="padding:5px 12px; border-bottom:1px solid #F2F2F7;">{facture.montant_tva.format()}</td>
      </tr>
      <tr>
        <td style="padding:7px 12px; font-weight:700; border-bottom:1px solid #D1D1D6; text-decoration:underline;">Total TTC</td>
        <td class="num" style="padding:7px 12px; font-weight:700; font-size:11pt; border-bottom:1px solid #D1D1D6; text-decoration:underline;">{facture.montant_ttc.format()}</td>
      </tr>
      <tr>
        <td style="padding:5px 12px;">Montant payé</td>
        <td class="num" style="padding:5px 12px; font-weight:700;">{facture.montant_paye:.3f} DT</td>
      </tr>
      <tr>
        <td style="padding:5px 12px; font-weight:700; font-style:italic;">{reste_label}</td>
        <td class="num" style="padding:5px 12px; font-weight:700; font-style:italic;">{reste:.3f} DT</td>
      </tr>
    </table>
  </div>
</div>"""

    return build_html(
        f"Facture N° {facture.numero}",
        f"Client : {client_nom.split('<')[0]}  |  Émise le {emission_str}",
        body,
        icon_svg_b64=_INVOICE_SVG,
    )


def _render_with_template(facture: Facture, ctx: AppContext, session: UserSession) -> str | None:
    """Try to render via the active HtmlReportTemplate; returns None to trigger fallback."""
    try:
        template = HtmlTemplateManager().get_default("facture")
        client_nom = _get_client_nom(facture, ctx, session)
        emission_str = facture.date_emission.strftime("%d/%m/%Y") if facture.date_emission else "—"
        statut_label = _STATUT_LABELS.get(facture.statut.value, facture.statut.value.upper())
        reste = float(facture.montant_ttc.amount) - float(facture.montant_paye)
        context = {
            "titre": f"Facture N° {facture.numero}",
            "sous_titre": f"Client : {client_nom}  |  Émise le {emission_str}",
            "entete_gauche": [("FACTURÉ À", ""), ("Client", client_nom)],
            "entete_droite": [
                ("N° Facture", facture.numero),
                ("Date", emission_str),
                ("Statut", statut_label),
            ],
            "lignes": [
                {
                    "index": i,
                    "designation": lg.designation,
                    "quantite": lg.quantite,
                    "prix_unitaire": float(lg.prix_unitaire),
                    "montant": float(lg.montant.amount),
                }
                for i, lg in enumerate(facture.lignes, 1)
            ],
            "totaux": {
                "montant_ht": float(facture.montant_ht.amount),
                "taux_tva": facture.taux_tva,
                "montant_tva": float(facture.montant_tva.amount),
                "montant_ttc": float(facture.montant_ttc.amount),
                "montant_paye": float(facture.montant_paye),
                "reste": reste,
            },
            "mode_paiement": ", ".join(p.mode for p in facture.paiements) if facture.paiements else "",
            "reference_paiement": (
                facture.paiements[0].reference
                if facture.paiements and facture.paiements[0].reference
                else ""
            ),
        }
        return HtmlTemplateRenderer().render(template, context)
    except Exception:
        logger.warning("Template render failed for facture %s; falling back to hardcoded renderer.", facture.numero, exc_info=True)
        return None


class FactureReportWindow(ReportViewerWindow):
    def __init__(self, ctx: AppContext, session: UserSession, facture: Facture) -> None:
        html = _render_with_template(facture, ctx, session) or _render(facture, ctx, session)
        super().__init__(f"Facture N° {facture.numero}", html)
