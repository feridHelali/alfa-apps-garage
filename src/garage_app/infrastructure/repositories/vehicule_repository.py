from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from garage_app.domain.planification.vehicule import Vehicule
from garage_app.domain.planification.repositories import VehiculeRepository
from garage_app.infrastructure.db.models.client_model import VehiculeModel


class SqlAlchemyVehiculeRepository(VehiculeRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, entity_id: uuid.UUID) -> Vehicule | None:
        m = self._s.get(VehiculeModel, str(entity_id))
        return self._to_domain(m) if m else None

    def get_by_immatriculation(self, immat: str) -> Vehicule | None:
        m = self._s.query(VehiculeModel).filter_by(immatriculation=immat.upper()).first()
        return self._to_domain(m) if m else None

    def find_all(self) -> list[Vehicule]:
        return [self._to_domain(m) for m in self._s.query(VehiculeModel).all()]

    def find_by_client(self, client_id: uuid.UUID) -> list[Vehicule]:
        rows = self._s.query(VehiculeModel).filter_by(client_id=str(client_id)).all()
        return [self._to_domain(m) for m in rows]

    def save(self, v: Vehicule) -> None:
        m = self._s.get(VehiculeModel, str(v.id))
        if m:
            m.immatriculation = v.immatriculation
            m.vin = v.vin
            m.marque = v.marque
            m.modele = v.modele
            m.annee = v.annee
            m.couleur = v.couleur
        else:
            self._s.add(VehiculeModel(
                id=str(v.id), client_id=str(v.client_id),
                immatriculation=v.immatriculation, vin=v.vin,
                marque=v.marque, modele=v.modele, annee=v.annee, couleur=v.couleur,
            ))

    def delete(self, entity_id: uuid.UUID) -> None:
        m = self._s.get(VehiculeModel, str(entity_id))
        if m:
            self._s.delete(m)

    @staticmethod
    def _to_domain(m: VehiculeModel) -> Vehicule:
        v = Vehicule(id=uuid.UUID(m.id))
        v.client_id = uuid.UUID(m.client_id)
        v.immatriculation = m.immatriculation
        v.vin = m.vin
        v.marque = m.marque
        v.modele = m.modele
        v.annee = m.annee
        v.couleur = m.couleur
        return v
