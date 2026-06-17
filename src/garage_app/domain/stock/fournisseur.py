from __future__ import annotations

from dataclasses import dataclass

from garage_app.domain.shared.aggregate_root import AggregateRoot


@dataclass
class Fournisseur(AggregateRoot):
    raison_sociale: str = ""
    contact_nom: str = ""
    telephone: str = ""
    email: str = ""
    adresse: str = ""
    delai_livraison_jours: int = 7
    est_actif: bool = True

    def desactiver(self) -> None:
        if not self.est_actif:
            raise ValueError("Fournisseur déjà inactif.")
        self.est_actif = False

    def activer(self) -> None:
        if self.est_actif:
            raise ValueError("Fournisseur déjà actif.")
        self.est_actif = True
