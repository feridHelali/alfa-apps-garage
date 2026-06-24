from __future__ import annotations

import json
import logging
from pathlib import Path

from garage_app.settings import APP_DATA_DIR
from garage_app.tools.report_engine.html_template import HtmlReportTemplate

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = APP_DATA_DIR / "report_templates"

# Built-in default templates embedded in the package
_BUILTIN_DEFAULTS: dict[str, dict] = {
    "facture": {
        "nom": "Facture Standard",
        "type_document": "facture",
        "couleur_bande": "#007AFF",
        "is_default": True,
        "texte_legal": "Merci de votre confiance. Règlement à réception de facture.",
    },
    "dossier": {
        "nom": "Fiche Réparation Standard",
        "type_document": "dossier",
        "couleur_bande": "#107C10",
        "is_default": True,
        "texte_legal": "Document interne — Gestion Réparation Voiture.",
    },
    "bon_travail": {
        "nom": "Bon de Travail Standard",
        "type_document": "bon_travail",
        "couleur_bande": "#1D7340",
        "is_default": True,
        "texte_legal": "Bon de travail à conserver.",
    },
    "facture_achat": {
        "nom": "Facture Achat Standard",
        "type_document": "facture_achat",
        "couleur_bande": "#8B4513",
        "is_default": True,
        "texte_legal": "Document comptable — Entrée stock.",
    },
}


class HtmlTemplateManager:
    """File-based CRUD for HtmlReportTemplate JSON files."""

    def _dir(self, type_doc: str) -> Path:
        d = _TEMPLATES_DIR / type_doc
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _path(self, type_doc: str, template_id: str) -> Path:
        return self._dir(type_doc) / f"{template_id}.json"

    # ── Seed defaults on first use ────────────────────────────────────────────

    def _ensure_defaults(self, type_doc: str) -> None:
        if any(self._dir(type_doc).glob("*.json")):
            return
        defaults = _BUILTIN_DEFAULTS.get(type_doc)
        if defaults:
            t = HtmlReportTemplate(**defaults)
            t.save_to(self._path(type_doc, t.id))

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def list_templates(self, type_doc: str) -> list[HtmlReportTemplate]:
        self._ensure_defaults(type_doc)
        templates = []
        for p in sorted(self._dir(type_doc).glob("*.json")):
            try:
                templates.append(HtmlReportTemplate.load_from(p))
            except json.JSONDecodeError as exc:
                logger.error("Corrupted template JSON %s: %s", p.name, exc)
            except Exception as exc:
                logger.error("Failed to load template %s: %s", p.name, exc)
        return templates

    def get(self, type_doc: str, template_id: str) -> HtmlReportTemplate | None:
        p = self._path(type_doc, template_id)
        if not p.exists():
            return None
        try:
            return HtmlReportTemplate.load_from(p)
        except json.JSONDecodeError as exc:
            logger.error("Corrupted template JSON %s: %s", p.name, exc)
            return None
        except Exception as exc:
            logger.error("Failed to load template %s: %s", p.name, exc)
            return None

    def get_default(self, type_doc: str) -> HtmlReportTemplate:
        self._ensure_defaults(type_doc)
        templates = self.list_templates(type_doc)
        default = next((t for t in templates if t.is_default), None)
        if default:
            return default
        if templates:
            return templates[0]
        t = HtmlReportTemplate(**_BUILTIN_DEFAULTS.get(type_doc, {"nom": "Défaut", "type_document": type_doc}))
        self.save(t)
        return t

    def save(self, template: HtmlReportTemplate) -> None:
        template.save_to(self._path(template.type_document, template.id))

    def set_default(self, type_doc: str, template_id: str) -> None:
        for t in self.list_templates(type_doc):
            t.is_default = (t.id == template_id)
            self.save(t)

    def delete(self, type_doc: str, template_id: str) -> None:
        p = self._path(type_doc, template_id)
        if p.exists():
            p.unlink()

    def duplicate(self, type_doc: str, template_id: str, new_nom: str) -> HtmlReportTemplate:
        original = self.get(type_doc, template_id)
        if not original:
            raise ValueError(f"Template {template_id} introuvable.")
        import uuid as _uuid
        copy = HtmlReportTemplate.from_dict(original.to_dict())
        copy.id = str(_uuid.uuid4())
        copy.nom = new_nom
        copy.is_default = False
        self.save(copy)
        return copy

    def export_to(self, type_doc: str, template_id: str, dest: Path) -> None:
        p = self._path(type_doc, template_id)
        if p.exists():
            dest.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")

    def import_from(self, src: Path) -> HtmlReportTemplate:
        t = HtmlReportTemplate.load_from(src)
        self.save(t)
        return t
