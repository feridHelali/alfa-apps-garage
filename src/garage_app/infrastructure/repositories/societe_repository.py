from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from garage_app.domain.societe.societe import Societe
from garage_app.domain.societe.repositories import SocieteRepository
from garage_app.infrastructure.db.models.societe_model import SocieteModel


class SqlAlchemySocieteRepository(SocieteRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_singleton(self) -> Societe | None:
        m = self._s.get(SocieteModel, 1)
        return self._to_domain(m) if m else None

    def get_by_id(self, entity_id: uuid.UUID) -> Societe | None:
        return self.get_singleton()

    def find_all(self) -> list[Societe]:
        s = self.get_singleton()
        return [s] if s else []

    def save(self, societe: Societe) -> None:
        m = self._s.get(SocieteModel, 1)
        if m:
            m.raison_sociale = societe.raison_sociale
            m.siret = societe.siret
            m.adresse = societe.adresse
            m.telephone = societe.telephone
            m.email = societe.email
            m.logo_path = societe.logo_path
            m.licence_key = societe.licence_key
            m.taux_tva_defaut = societe.taux_tva_defaut
        else:
            self._s.add(SocieteModel(
                id=1,
                raison_sociale=societe.raison_sociale,
                siret=societe.siret,
                adresse=societe.adresse,
                telephone=societe.telephone,
                email=societe.email,
                logo_path=societe.logo_path,
                licence_key=societe.licence_key,
                taux_tva_defaut=societe.taux_tva_defaut,
            ))

    def delete(self, entity_id: uuid.UUID) -> None:
        pass  # singleton — never deleted

    @staticmethod
    def _to_domain(m: SocieteModel) -> Societe:
        s = Societe()
        s.raison_sociale = m.raison_sociale
        s.siret = m.siret
        s.adresse = m.adresse
        s.telephone = m.telephone
        s.email = m.email
        s.logo_path = m.logo_path
        s.licence_key = m.licence_key
        s.taux_tva_defaut = m.taux_tva_defaut
        return s
