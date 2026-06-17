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
    emplacement: str = ""
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

    def ajuster_stock(self, nouvelle_quantite: int) -> None:
        from garage_app.domain.stock.events import InventaireAjuste
        if nouvelle_quantite < 0:
            raise ValueError("Le stock ne peut pas être négatif.")
        ancienne = self.quantite_stock
        self.quantite_stock = nouvelle_quantite
        self._raise_event(InventaireAjuste(
            piece_id=self.id,
            ancienne_quantite=ancienne,
            nouvelle_quantite=nouvelle_quantite,
        ))
        if self.quantite_stock <= self.seuil_alerte:
            self._raise_event(StockAlerteDeclenchee(piece_id=self.id, quantite=self.quantite_stock))

    @property
    def est_disponible(self) -> bool:
        return self.quantite_stock > 0

    @property
    def en_alerte(self) -> bool:
        return self.quantite_stock <= self.seuil_alerte
