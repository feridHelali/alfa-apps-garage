from __future__ import annotations

from dataclasses import dataclass, field

from garage_app.domain.shared.aggregate_root import AggregateRoot


@dataclass
class Client(AggregateRoot):
    nom: str = ""
    prenom: str = ""
    telephone: str = ""
    email: str = ""
    adresse: str = ""
    est_flotte: bool = False  # fleet/enterprise: 30-day payment allowed

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}".strip()
