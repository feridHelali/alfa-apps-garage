from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.stock.events import StockAlerteDeclenchee


@dataclass
class Piece(AggregateRoot):
    reference_constructeur: str = ""
    designation: str = ""
    categorie: str = ""
    prix_achat: Decimal = Decimal("0")
    prix_vente: Decimal = Decimal("0")
    quantite_stock: int = 0
    seuil_alerte: int = 5
    fournisseur_id: uuid.UUID | None = None

    def entrer_stock(self, quantite: int) -> None:
        if quantite <= 0:
            raise ValueError("La quantité doit être positive.")
        self.quantite_stock += quantite

    def sortir_stock(self, quantite: int) -> None:
        if quantite <= 0:
            raise ValueError("La quantité doit être positive.")
        if quantite > self.quantite_stock:
            raise ValueError(
                f"Stock insuffisant: {self.quantite_stock} disponible(s), {quantite} demandé(s)."
            )
        self.quantite_stock -= quantite
        if self.quantite_stock <= self.seuil_alerte:
            self._raise_event(StockAlerteDeclenchee(piece_id=self.id, quantite=self.quantite_stock))

    @property
    def est_disponible(self) -> bool:
        return self.quantite_stock > 0

    @property
    def en_alerte(self) -> bool:
        return self.quantite_stock <= self.seuil_alerte
