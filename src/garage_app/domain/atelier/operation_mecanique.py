from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from garage_app.domain.shared.entity import Entity
from garage_app.domain.atelier.statut_dossier import StatutTache
from garage_app.domain.shared.value_objects import Money


@dataclass
class OperationMecanique(Entity):
    technicien_id: uuid.UUID | None = None
    code_main_oeuvre: str = ""
    description: str = ""
    temps_estime: Decimal = Decimal("0")   # heures
    temps_passe: Decimal = Decimal("0")    # heures
    taux_horaire: Decimal = Decimal("0")   # € / heure
    statut: StatutTache = StatutTache.A_FAIRE

    @property
    def montant(self) -> Money:
        return Money.of(self.taux_horaire * self.temps_passe)

    @property
    def est_terminee(self) -> bool:
        return self.statut == StatutTache.TERMINEE

    def demarrer(self) -> None:
        self.statut = StatutTache.EN_COURS

    def terminer(self, temps_passe: Decimal) -> None:
        if temps_passe < Decimal("0"):
            raise ValueError("Le temps passé ne peut pas être négatif.")
        self.temps_passe = temps_passe
        self.statut = StatutTache.TERMINEE
