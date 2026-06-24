from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ── Column config ────────────────────────────────────────────────────────────

@dataclass
class ColonneConfig:
    champ: str
    titre: str
    largeur: int = -1       # -1 = stretch
    align: str = "left"     # left | center | right
    visible: bool = True


# ── Default columns per document type ────────────────────────────────────────

def _default_colonnes_facture() -> list[ColonneConfig]:
    return [
        ColonneConfig("index",         "#",           30,  "center"),
        ColonneConfig("designation",   "Désignation", -1,  "left"),
        ColonneConfig("quantite",      "Qté",         50,  "right"),
        ColonneConfig("prix_unitaire", "P.U. HT",     110, "right"),
        ColonneConfig("montant",       "Total HT",    110, "right"),
    ]

def _default_colonnes_dossier() -> list[ColonneConfig]:
    return [
        ColonneConfig("index",       "#",            30,  "center"),
        ColonneConfig("description", "Description", -1,  "left"),
        ColonneConfig("technicien",  "Technicien",  120, "left"),
        ColonneConfig("duree",       "Durée",        80,  "right"),
        ColonneConfig("montant",     "Montant",     100, "right"),
    ]

def _default_colonnes_facture_achat() -> list[ColonneConfig]:
    return [
        ColonneConfig("index",         "#",           30,  "center"),
        ColonneConfig("designation",   "Désignation", -1,  "left"),
        ColonneConfig("reference",     "Réf.",        90,  "left"),
        ColonneConfig("quantite",      "Qté",         50,  "right"),
        ColonneConfig("prix_unitaire", "Prix achat",  110, "right"),
        ColonneConfig("montant",       "Total HT",    110, "right"),
    ]


_DEFAULT_COLONNES: dict[str, list[ColonneConfig]] = {
    "facture":        _default_colonnes_facture(),
    "dossier":        _default_colonnes_dossier(),
    "bon_travail":    _default_colonnes_dossier(),
    "facture_achat":  _default_colonnes_facture_achat(),
}


# ── Main template ─────────────────────────────────────────────────────────────

@dataclass
class HtmlReportTemplate:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    nom: str = "Nouveau modèle"
    type_document: str = "facture"
    version: int = 1
    is_default: bool = False

    # Header band
    couleur_bande: str = "#007AFF"
    couleur_texte_bande: str = "#ffffff"
    show_logo: bool = True
    show_societe: bool = True
    show_slogan: bool = False

    # Lines table columns
    colonnes: list[ColonneConfig] = field(default_factory=list)

    # Totals block
    show_ht: bool = True
    show_tva: bool = True
    show_ttc: bool = True
    show_paye: bool = True
    show_reste: bool = True

    # Footer band
    texte_legal: str = "Merci de votre confiance."
    show_page_number: bool = False

    # Advanced
    css_custom: str = ""

    def __post_init__(self) -> None:
        if not self.colonnes:
            self.colonnes = [
                ColonneConfig(**c) if isinstance(c, dict) else c
                for c in _DEFAULT_COLONNES.get(self.type_document, _default_colonnes_facture())
            ]

    # ── Serialisation ────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HtmlReportTemplate:
        colonnes_raw = data.pop("colonnes", [])
        t = cls(**data)
        t.colonnes = [ColonneConfig(**c) for c in colonnes_raw]
        return t

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> HtmlReportTemplate:
        return cls.from_dict(json.loads(text))

    def save_to(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load_from(cls, path: Path) -> HtmlReportTemplate:
        return cls.from_json(path.read_text(encoding="utf-8"))
