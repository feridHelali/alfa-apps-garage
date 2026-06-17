from __future__ import annotations

import uuid

from garage_app.domain.planification.client import Client
from garage_app.domain.planification.repositories import ClientRepository
from garage_app.infrastructure.db.models.client_model import ClientModel
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyClientRepository(ClientRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> Client | None:
        with self._sf.get_session() as s:
            m = s.get(ClientModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_all(self) -> list[Client]:
        with self._sf.get_session() as s:
            return [self._to_domain(m) for m in s.query(ClientModel).all()]

    def search(self, query: str) -> list[Client]:
        q = f"%{query}%"
        with self._sf.get_session() as s:
            rows = s.query(ClientModel).filter(
                ClientModel.nom.ilike(q) | ClientModel.prenom.ilike(q) | ClientModel.telephone.ilike(q)
            ).all()
            return [self._to_domain(m) for m in rows]

    def save(self, client: Client) -> None:
        with self._sf.get_session() as s:
            m = s.get(ClientModel, str(client.id))
            if m:
                m.nom = client.nom
                m.prenom = client.prenom
                m.telephone = client.telephone
                m.email = client.email
                m.adresse = client.adresse
                m.est_flotte = client.est_flotte
            else:
                s.add(ClientModel(
                    id=str(client.id), nom=client.nom, prenom=client.prenom,
                    telephone=client.telephone, email=client.email,
                    adresse=client.adresse, est_flotte=client.est_flotte,
                ))

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(ClientModel, str(entity_id))
            if m:
                s.delete(m)

    @staticmethod
    def _to_domain(m: ClientModel) -> Client:
        c = Client(id=uuid.UUID(m.id))
        c.nom = m.nom
        c.prenom = m.prenom
        c.telephone = m.telephone
        c.email = m.email
        c.adresse = m.adresse
        c.est_flotte = m.est_flotte
        return c
