from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.infrastructure.db.models.settings_model import AppSettingsModel
from garage_app.infrastructure.db.session import SessionFactory

TYPES_DOC = ["facture", "dossier", "bon_travail", "facture_achat", "devis", "proforma"]


@dataclass
class NumerotationConfig:
    type_doc: str
    prefixe: str = ""
    prochain: int = 1
    longueur: int = 4
    reset_annuel: bool = False


class NumerotationService:
    """Atomic document-number generator backed by app_settings."""

    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    # ── Read ────────────────────────────────────────────────────────────────

    def get_config(self, type_doc: str) -> NumerotationConfig:
        p = f"numerotation.{type_doc}."
        with self._sf.get_session() as s:
            def _g(k: str, d: str = "") -> str:
                m = s.get(AppSettingsModel, p + k)
                return m.value if m else d
            return NumerotationConfig(
                type_doc=type_doc,
                prefixe=_g("prefixe"),
                prochain=int(_g("prochain", "1") or "1"),
                longueur=int(_g("longueur", "4") or "4"),
                reset_annuel=_g("reset_annuel", "false") == "true",
            )

    # ── Write (guarded) ─────────────────────────────────────────────────────

    @require_permission(Permission.MANAGE_SETTINGS)
    def update_config(
        self, session: UserSession, type_doc: str, config: NumerotationConfig
    ) -> None:
        p = f"numerotation.{type_doc}."
        with self._sf.get_session() as s:
            def _w(k: str, v: str) -> None:
                m = s.get(AppSettingsModel, p + k)
                if m:
                    m.value = v
                else:
                    s.add(AppSettingsModel(key=p + k, value=v))
            _w("prefixe", config.prefixe)
            _w("prochain", str(config.prochain))
            _w("longueur", str(config.longueur))
            _w("reset_annuel", "true" if config.reset_annuel else "false")

    # ── Generate (called from other services) ───────────────────────────────

    def generer_numero(self, type_doc: str) -> str:
        """Atomic read-increment-write in a single session/transaction."""
        p = f"numerotation.{type_doc}."
        with self._sf.get_session() as s:
            def _g(k: str, d: str = "") -> str:
                m = s.get(AppSettingsModel, p + k)
                return m.value if m else d

            def _w(k: str, v: str) -> None:
                m = s.get(AppSettingsModel, p + k)
                if m:
                    m.value = v
                else:
                    s.add(AppSettingsModel(key=p + k, value=v))

            prefixe_raw = _g("prefixe")
            prochain = int(_g("prochain", "1") or "1")
            longueur = int(_g("longueur", "4") or "4")
            reset_annuel = _g("reset_annuel", "false") == "true"
            dernier_annee = int(_g("dernier_annee", "0") or "0")

            year_now = datetime.now().year
            if reset_annuel and 0 < dernier_annee < year_now:
                prochain = 1

            _w("dernier_annee", str(year_now))

            prefixe = prefixe_raw.replace("{ANNEE}", str(year_now)).replace(
                "{MOIS}", f"{datetime.now().month:02d}"
            )
            numero = f"{prefixe}{prochain:0{longueur}d}"
            _w("prochain", str(prochain + 1))

        return numero

    def apercu(self, type_doc: str) -> str:
        """Next-number preview — does not increment."""
        cfg = self.get_config(type_doc)
        year_now = datetime.now().year
        prefixe = cfg.prefixe.replace("{ANNEE}", str(year_now)).replace(
            "{MOIS}", f"{datetime.now().month:02d}"
        )
        return f"{prefixe}{cfg.prochain:0{cfg.longueur}d}"
