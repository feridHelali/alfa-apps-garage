from __future__ import annotations

import base64
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from garage_app.settings import resource_path
from garage_app.tools.report_engine.html_template import ColonneConfig, HtmlReportTemplate

logger = logging.getLogger(__name__)

_LOGO_PATH = resource_path("assets", "brand", "alfa_computers_logo.svg")


def _logo_b64() -> str:
    try:
        return base64.b64encode(_LOGO_PATH.read_bytes()).decode()
    except Exception:
        return ""


# Encode once at import time — the logo never changes during a session.
_CACHED_LOGO_B64: str = _logo_b64()


_BASE_CSS = """
body { font-family: "Helvetica Neue", Arial, sans-serif; font-size:10pt; color:#1C1C1E; margin:0; padding:0; }
table { width:100%; border-collapse:collapse; font-size:9pt; }
th { background:#F2F2F7; color:#6E6E73; font-weight:600; text-align:left; padding:5px 8px; border-bottom:1px solid #D1D1D6; }
td { padding:5px 8px; border-bottom:1px solid #E5E5EA; }
tr:last-child td { border-bottom:none; }
.num { text-align:right; }
.center { text-align:center; }
.section { margin:12px 0; padding:0 4px; }
.section h2 { font-size:11pt; font-weight:600; border-bottom:1px solid #D1D1D6; padding-bottom:4px; margin-bottom:8px; }
.totaux-table { width:auto; float:right; border:1px solid #E5E5EA; border-radius:6px; overflow:hidden; }
.totaux-table td { padding:5px 12px; border-bottom:1px solid #F2F2F7; }
.totaux-table tr:last-child td { border-bottom:none; }
.footer-band { margin-top:16px; font-size:8pt; color:#AEAEB2; border-top:1px solid #E5E5EA; padding-top:6px; text-align:center; }
.badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:8pt; font-weight:600; }
.badge-ok { background:#D1FAE5; color:#065F46; }
.badge-warn { background:#FEF3C7; color:#92400E; }
.badge-danger { background:#FEE2E2; color:#991B1B; }
"""

# Context dict keys used by the renderer
# context = {
#   "titre": str, "sous_titre": str,
#   "entete_gauche": list[tuple[str, str]],  # [(label, value), ...]
#   "entete_droite": list[tuple[str, str]],
#   "lignes": list[dict],    # keys match ColonneConfig.champ
#   "totaux": dict,          # montant_ht, taux_tva, montant_tva, montant_ttc, montant_paye, reste
#   "mode_paiement": str,
#   "reference_paiement": str,
# }


def _fmt(val: Any) -> str:
    if val is None:
        return "—"
    if isinstance(val, (float, Decimal)):
        # CPython's `:,` always uses ASCII comma/dot (C locale) — system LC_ALL is ignored.
        # "1,234.567" → "1 234,567 DT" (TND: space=thousands, comma=decimal, 3 millimes)
        return f"{float(val):,.3f}".replace(",", " ").replace(".", ",") + " DT"
    return str(val)


def _col_style(col: ColonneConfig) -> str:
    parts = []
    if col.align == "right":
        parts.append("text-align:right")
    elif col.align == "center":
        parts.append("text-align:center")
    if col.largeur > 0:
        parts.append(f"width:{col.largeur}px")
    return "; ".join(parts)


class HtmlTemplateRenderer:
    """Renders HtmlReportTemplate + a context dict → full HTML string."""

    def render(self, template: HtmlReportTemplate, context: dict[str, Any]) -> str:
        css = _BASE_CSS
        if template.css_custom:
            css += "\n" + template.css_custom
        # Color override for header
        css += f"\n.header-band {{ background:{template.couleur_bande}; color:{template.couleur_texte_bande}; padding:12px 16px; border-radius:6px 6px 0 0; }}"
        css += f"\n.section h2 {{ color:{template.couleur_bande}; }}"

        titre = context.get("titre", "Document")
        sous_titre = context.get("sous_titre", "")

        header_html = self._header(template, titre, sous_titre)
        entete_html = self._entete_block(
            context.get("entete_gauche", []),
            context.get("entete_droite", []),
        )
        lines_html = self._lines_table(template, context.get("lignes", []))
        totaux_html = self._totaux_block(
            template,
            context.get("totaux", {}),
            context.get("mode_paiement", ""),
            context.get("reference_paiement", ""),
        )
        footer_html = f'<div class="footer-band">{template.texte_legal}</div>'
        if template.show_page_number:
            footer_html += '<div class="footer-band" style="font-size:7pt;">Page 1</div>'

        return (
            f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f"<style>{css}</style></head><body>"
            f"{header_html}"
            f"{entete_html}"
            f"{lines_html}"
            f"{totaux_html}"
            f"{footer_html}"
            f"</body></html>"
        )

    # ── Header band ───────────────────────────────────────────────────────────

    def _header(self, template: HtmlReportTemplate, titre: str, sous_titre: str) -> str:
        logo_html = ""
        if template.show_logo:
            b64 = _CACHED_LOGO_B64
            if b64:
                logo_html = (
                    f'<img src="data:image/svg+xml;base64,{b64}" '
                    'style="height:34px; float:right; margin-top:2px; margin-left:12px; opacity:0.92;">'
                )
        societe_html = ""
        if template.show_societe:
            societe_html = (
                '<div style="font-size:8.5pt; opacity:0.85; margin-top:2px;">'
                "Alfa Computers Apps — Gestion Réparation Voiture"
                "</div>"
            )
        slogan_html = ""
        if template.show_slogan:
            slogan_html = (
                '<div style="font-size:8pt; opacity:0.75; margin-top:1px; font-style:italic;">'
                "Solutions de Gestion sur Mesure"
                "</div>"
            )
        sous_titre_html = f'<div style="font-size:9pt; opacity:0.85; margin-top:2px;">{sous_titre}</div>' if sous_titre else ""
        return (
            f'<div class="header-band">'
            f"{logo_html}"
            f"{societe_html}{slogan_html}"
            f'<h1 style="margin:4px 0 0 0; font-size:14pt; font-weight:700;">{titre}</h1>'
            f"{sous_titre_html}"
            f"</div>"
        )

    # ── Entête two-column block ────────────────────────────────────────────────

    def _entete_block(
        self, left: list[tuple[str, str]], right: list[tuple[str, str]]
    ) -> str:
        if not left and not right:
            return ""

        def _rows(items: list[tuple[str, str]]) -> str:
            rows = ""
            for lbl, val in items:
                rows += (
                    f'<tr><td style="color:#6E6E73;border:none;padding:2px 8px 2px 0;">{lbl}</td>'
                    f'<td style="font-weight:600;border:none;padding:2px 0;">{val}</td></tr>'
                )
            return rows

        left_html = (
            f'<div style="display:table-cell;vertical-align:top;width:50%;">'
            f'<table style="border:none;">{_rows(left)}</table></div>'
            if left else '<div style="display:table-cell;width:50%;"></div>'
        )
        right_html = (
            f'<div style="display:table-cell;vertical-align:top;text-align:right;">'
            f'<table style="border:none;float:right;">{_rows(right)}</table></div>'
            if right else '<div style="display:table-cell;"></div>'
        )
        return (
            f'<div style="display:table;width:100%;margin:12px 0 8px 0;">'
            f"{left_html}{right_html}</div>"
        )

    # ── Lines table ───────────────────────────────────────────────────────────

    def _lines_table(self, template: HtmlReportTemplate, lignes: list[dict]) -> str:
        visible_cols = [c for c in template.colonnes if c.visible]
        if not visible_cols:
            return ""

        header_cells = ""
        for col in visible_cols:
            style = _col_style(col)
            header_cells += f'<th style="{style}">{col.titre}</th>'

        rows_html = ""
        for row in lignes:
            cells = ""
            for col in visible_cols:
                val = row.get(col.champ, "")
                style = _col_style(col)
                if col.champ in ("montant", "prix_unitaire", "prix_achat"):
                    display = _fmt(val)
                    cells += f'<td style="{style}"><b>{display}</b></td>'
                elif col.champ in ("quantite",):
                    cells += f'<td style="{style}">{val}</td>'
                else:
                    cells += f'<td style="{style}">{val}</td>'
            rows_html += f"<tr>{cells}</tr>"

        if not rows_html:
            colspan = len(visible_cols)
            rows_html = (
                f'<tr><td colspan="{colspan}" '
                'style="color:#6E6E73;padding:12px;text-align:center;">Aucune ligne.</td></tr>'
            )

        return (
            f'<div class="section">'
            f'<h2>Détail des prestations</h2>'
            f'<table><tr>{header_cells}</tr>{rows_html}</table>'
            f"</div>"
        )

    # ── Totaux block ──────────────────────────────────────────────────────────

    def _totaux_block(
        self,
        template: HtmlReportTemplate,
        totaux: dict,
        mode_paiement: str,
        reference_paiement: str,
    ) -> str:
        rows = ""
        ht = totaux.get("montant_ht", 0.0)
        tva = totaux.get("montant_tva", 0.0)
        ttc = totaux.get("montant_ttc", 0.0)
        paye = totaux.get("montant_paye", 0.0)
        reste = totaux.get("reste", 0.0)
        taux_tva = totaux.get("taux_tva", 19)

        if template.show_ht:
            rows += (
                f'<tr><td style="color:#6E6E73;padding:5px 12px;border-bottom:1px solid #F2F2F7;">Total HT</td>'
                f'<td class="num" style="padding:5px 12px;border-bottom:1px solid #F2F2F7;">{_fmt(ht)}</td></tr>'
            )
        if template.show_tva:
            rows += (
                f'<tr><td style="color:#6E6E73;padding:5px 12px;border-bottom:1px solid #F2F2F7;">TVA ({taux_tva} %)</td>'
                f'<td class="num" style="padding:5px 12px;border-bottom:1px solid #F2F2F7;">{_fmt(tva)}</td></tr>'
            )
        if template.show_ttc:
            rows += (
                f'<tr style="background:#F9F9FB;">'
                f'<td style="padding:7px 12px;font-weight:700;border-bottom:1px solid #E5E5EA;">Total TTC</td>'
                f'<td class="num" style="padding:7px 12px;font-weight:700;font-size:11pt;border-bottom:1px solid #E5E5EA;">{_fmt(ttc)}</td></tr>'
            )
        if template.show_paye:
            rows += (
                f'<tr><td style="color:#6E6E73;padding:5px 12px;">Montant payé</td>'
                f'<td class="num" style="padding:5px 12px;color:#107C10;">{_fmt(paye)}</td></tr>'
            )
        if template.show_reste:
            reste_color = "#A4262C" if float(reste) > 0 else "#107C10"
            reste_lbl = "Reste à payer" if float(reste) > 0 else "Soldé ✓"
            rows += (
                f'<tr><td style="font-weight:700;padding:5px 12px;color:{reste_color};">{reste_lbl}</td>'
                f'<td class="num" style="font-weight:700;padding:5px 12px;color:{reste_color};">{_fmt(reste)}</td></tr>'
            )

        if not rows:
            return ""

        mode_html = ""
        if mode_paiement:
            mode_html = f'<div style="font-size:8pt;color:#6E6E73;padding-top:6px;">Mode : {mode_paiement}'
            if reference_paiement:
                mode_html += f" · Réf. {reference_paiement}"
            mode_html += "</div>"

        return (
            f'<div style="display:table;width:100%;margin-top:12px;">'
            f'<div style="display:table-cell;width:55%;vertical-align:top;">{mode_html}</div>'
            f'<div style="display:table-cell;vertical-align:top;">'
            f'<table class="totaux-table"><tbody>{rows}</tbody></table>'
            f"</div></div>"
        )


# ── Sample context (used by the designer for live preview) ────────────────────

SAMPLE_CONTEXTS: dict[str, dict] = {
    "facture": {
        "titre": "Facture N° FAC-2025-001",
        "sous_titre": "Client : Mahmoud Baklouti  |  Émise le 24/06/2025",
        "entete_gauche": [("FACTURÉ À", ""), ("Client", "Mahmoud Baklouti"), ("Téléphone", "+216 XX XXX XXX")],
        "entete_droite": [("N° Facture", "FAC-2025-001"), ("Date", "24/06/2025"), ("Statut", "ÉMISE")],
        "lignes": [
            {"index": 1, "designation": "Vidange huile moteur 5W40", "quantite": 1, "prix_unitaire": 45.0, "montant": 45.0},
            {"index": 2, "designation": "Filtre à huile BOSCH F026407229", "quantite": 1, "prix_unitaire": 18.5, "montant": 18.5},
            {"index": 3, "designation": "Main d'œuvre — Vidange", "quantite": 1, "prix_unitaire": 25.0, "montant": 25.0},
        ],
        "totaux": {"montant_ht": 88.5, "taux_tva": 19, "montant_tva": 16.815, "montant_ttc": 105.315, "montant_paye": 0.0, "reste": 105.315},
        "mode_paiement": "", "reference_paiement": "",
    },
    "dossier": {
        "titre": "Fiche Réparation N° DOS-2025-001",
        "sous_titre": "Véhicule : Renault Clio IV — AA-123-TU  |  Ouvert le 20/06/2025",
        "entete_gauche": [("Client", "Mahmoud Baklouti"), ("Véhicule", "Renault Clio IV"), ("Immatriculation", "AA-123-TU")],
        "entete_droite": [("N° Dossier", "DOS-2025-001"), ("Statut", "CLOTURÉ"), ("Kilométrage", "85 000 km")],
        "lignes": [
            {"index": 1, "description": "Remplacement plaquettes frein AV", "technicien": "Ali Ben Salem", "duree": "1h00", "montant": 120.0},
            {"index": 2, "description": "Vérification freinage — contrôle qualité", "technicien": "Ali Ben Salem", "duree": "0h30", "montant": 0.0},
        ],
        "totaux": {"montant_ht": 120.0, "taux_tva": 19, "montant_tva": 22.8, "montant_ttc": 142.8, "montant_paye": 142.8, "reste": 0.0},
        "mode_paiement": "Espèces", "reference_paiement": "",
    },
    "bon_travail": {
        "titre": "Bon de Travail N° BT-2025-001",
        "sous_titre": "Technicien : Ali Ben Salem  |  Date : 24/06/2025",
        "entete_gauche": [("Client", "Karim Trabelsi"), ("Véhicule", "Peugeot 208"), ("Immatriculation", "BB-456-TU")],
        "entete_droite": [("N° BT", "BT-2025-001"), ("Priorité", "NORMALE"), ("Estimation", "2h00")],
        "lignes": [
            {"index": 1, "description": "Diagnostic électronique OBD2", "technicien": "Ali Ben Salem", "duree": "0h30", "montant": 35.0},
            {"index": 2, "description": "Remplacement capteur MAP", "technicien": "Ali Ben Salem", "duree": "1h30", "montant": 85.0},
        ],
        "totaux": {"montant_ht": 120.0, "taux_tva": 19, "montant_tva": 22.8, "montant_ttc": 142.8, "montant_paye": 0.0, "reste": 142.8},
        "mode_paiement": "", "reference_paiement": "",
    },
    "facture_achat": {
        "titre": "Facture Achat N° FA-2025-001",
        "sous_titre": "Fournisseur : Pièces Auto Tunis  |  Date : 24/06/2025",
        "entete_gauche": [("Fournisseur", "Pièces Auto Tunis"), ("MF", "1234567/A/M/000"), ("Téléphone", "+216 71 XXX XXX")],
        "entete_droite": [("Notre N°", "FA-2025-001"), ("N° Fournisseur", "PA-2025-0987"), ("Date", "24/06/2025")],
        "lignes": [
            {"index": 1, "designation": "Plaquettes frein FERODO FDB4398", "reference": "FDB4398", "quantite": 4, "prix_unitaire": 28.0, "montant": 112.0},
            {"index": 2, "designation": "Disques frein BREMBO 09.8892.11", "reference": "09.8892.11", "quantite": 2, "prix_unitaire": 65.0, "montant": 130.0},
        ],
        "totaux": {"montant_ht": 242.0, "taux_tva": 19, "montant_tva": 45.98, "montant_ttc": 287.98, "montant_paye": 0.0, "reste": 287.98},
        "mode_paiement": "", "reference_paiement": "",
    },
}
