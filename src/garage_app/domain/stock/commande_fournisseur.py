from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum, auto

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.shared.entity import Entity
from garage_app.domain.stock.events import CommandeEnvoyee, PiecesRecues


class StatutCommande(StrEnum):
    BROUILLON = auto()
    ENVOYEE = auto()
    PARTIELLEMENT_RECUE = auto()
    RECUE = auto()
    ANNULEE = auto()


@dataclass
class LigneCommande(Entity):
    piece_id: uuid.UUID = field(default_factory=uuid.uuid4)
    designation: str = ""
    quantite_commandee: int = 0
    quantite_recue: int = 0
    prix_unitaire: float = 0.0

    @property
    def est_recue(self) -> bool:
        return self.quantite_recue >= self.quantite_commandee

    @property
    def reste_a_recevoir(self) -> int:
        return max(0, self.quantite_commandee - self.quantite_recue)


@dataclass
class CommandeFournisseur(AggregateRoot):
    fournisseur_id: uuid.UUID = field(default_factory=uuid.uuid4)
    statut: StatutCommande = StatutCommande.BROUILLON
    date_commande: datetime = field(default_factory=datetime.now)
    date_livraison_prevue: datetime | None = None
    notes: str = ""
    lignes: list[LigneCommande] = field(default_factory=list)

    def ajouter_ligne(
        self,
        piece_id: uuid.UUID,
        quantite: int,
        prix_unitaire: float = 0.0,
        designation: str = "",
    ) -> LigneCommande:
        if self.statut != StatutCommande.BROUILLON:
            raise ValueError("Impossible de modifier une commande non-brouillon.")
        if quantite <= 0:
            raise ValueError("La quantité doit être positive.")
        ligne = LigneCommande(
            piece_id=piece_id,
            designation=designation,
            quantite_commandee=quantite,
            prix_unitaire=prix_unitaire,
        )
        self.lignes.append(ligne)
        return ligne

    def supprimer_ligne(self, ligne_id: uuid.UUID) -> None:
        if self.statut != StatutCommande.BROUILLON:
            raise ValueError("Impossible de modifier une commande non-brouillon.")
        self.lignes = [l for l in self.lignes if l.id != ligne_id]

    def envoyer(self) -> None:
        if self.statut != StatutCommande.BROUILLON:
            raise ValueError(f"Impossible d'envoyer en statut '{self.statut}'.")
        if not self.lignes:
            raise ValueError("La commande doit contenir au moins une ligne.")
        self.statut = StatutCommande.ENVOYEE
        self._raise_event(CommandeEnvoyee(commande_id=self.id))

    def recevoir_partiel(self, receptions: dict[uuid.UUID, int]) -> list[PiecesRecues]:
        """receptions: {ligne_id: quantite_recue}. Returns list of PiecesRecues events."""
        if self.statut not in (StatutCommande.ENVOYEE, StatutCommande.PARTIELLEMENT_RECUE):
            raise ValueError(f"Impossible de réceptionner en statut '{self.statut}'.")
        events: list[PiecesRecues] = []
        for ligne in self.lignes:
            qte = receptions.get(ligne.id, 0)
            if qte <= 0:
                continue
            if qte < 0:
                raise ValueError("Quantité reçue ne peut pas être négative.")
            qte_effective = min(qte, ligne.reste_a_recevoir)
            if qte_effective > 0:
                ligne.quantite_recue += qte_effective
                ev = PiecesRecues(
                    commande_id=self.id,
                    piece_id=ligne.piece_id,
                    quantite=qte_effective,
                )
                self._raise_event(ev)
                events.append(ev)
        if all(l.est_recue for l in self.lignes):
            self.statut = StatutCommande.RECUE
        elif any(l.quantite_recue > 0 for l in self.lignes):
            self.statut = StatutCommande.PARTIELLEMENT_RECUE
        return events

    def recevoir_tout(self) -> list[PiecesRecues]:
        receptions = {l.id: l.reste_a_recevoir for l in self.lignes}
        return self.recevoir_partiel(receptions)

    def annuler(self) -> None:
        if self.statut not in (StatutCommande.BROUILLON, StatutCommande.ENVOYEE):
            raise ValueError(f"Impossible d'annuler en statut '{self.statut}'.")
        self.statut = StatutCommande.ANNULEE
