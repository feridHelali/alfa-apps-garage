from __future__ import annotations

from dataclasses import dataclass, field

from garage_app.domain.shared.aggregate_root import AggregateRoot


@dataclass
class Societe(AggregateRoot):
    """Singleton aggregate — one record per installation (acts as licence anchor)."""
    raison_sociale: str = ""
    siret: str = ""
    adresse: str = ""
    telephone: str = ""
    email: str = ""
    logo_path: str = ""
    licence_key: str = ""
    taux_tva_defaut: float = 20.0
