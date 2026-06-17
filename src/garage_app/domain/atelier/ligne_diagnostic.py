from __future__ import annotations

from dataclasses import dataclass, field

from garage_app.domain.shared.entity import Entity
from garage_app.domain.atelier.statut_dossier import GravitePanne


@dataclass
class LigneDiagnostic(Entity):
    code_defaut: str = ""        # OBD2 code, e.g. P0300
    description: str = ""
    gravite: GravitePanne = GravitePanne.BLOQUANT
