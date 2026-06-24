from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from garage_app.domain.devis.devis import Devis, FactureProforma, LigneDevis, LigneProforma
from garage_app.domain.devis.repositories import DevisRepository, ProformaRepository
from garage_app.domain.devis.statut_devis import StatutDevis, StatutProforma, TypeLigne
from garage_app.domain.shared.value_objects import Money
from garage_app.infrastructure.db.models.facture_model import DevisModel
from garage_app.infrastructure.db.models.devis_model import (
    LigneDevisModel, FactureProformaModel, LigneProformaModel,
)
from garage_app.infrastructure.db.session import SessionFactory


class SqlAlchemyDevisRepository(DevisRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    # ── Repository[Devis] ───────────────────────────────────────────────────

    def get_by_id(self, entity_id: uuid.UUID) -> Devis | None:
        with self._sf.get_session() as s:
            m = s.get(DevisModel, str(entity_id))
            if not m:
                return None
            lignes = s.query(LigneDevisModel).filter_by(
                devis_id=str(entity_id)
            ).order_by(LigneDevisModel.ordre).all()
            return self._to_domain(m, lignes)

    def find_all(self) -> list[Devis]:
        with self._sf.get_session() as s:
            rows = s.query(DevisModel).order_by(DevisModel.date_creation.desc()).all()
            return [self._to_domain(m, self._lignes(s, m.id)) for m in rows]

    def find_by_client(self, client_id: uuid.UUID) -> list[Devis]:
        with self._sf.get_session() as s:
            rows = s.query(DevisModel).filter(
                DevisModel.client_id == str(client_id)
            ).order_by(DevisModel.date_creation.desc()).all()
            return [self._to_domain(m, self._lignes(s, m.id)) for m in rows]

    def find_by_statut(self, statut: StatutDevis) -> list[Devis]:
        with self._sf.get_session() as s:
            rows = s.query(DevisModel).filter(
                DevisModel.statut == statut.value
            ).order_by(DevisModel.date_creation.desc()).all()
            return [self._to_domain(m, self._lignes(s, m.id)) for m in rows]

    def find_actifs(self) -> list[Devis]:
        with self._sf.get_session() as s:
            rows = s.query(DevisModel).filter(
                DevisModel.statut.in_(["brouillon", "envoye", "accepte"])
            ).order_by(DevisModel.date_creation.desc()).all()
            return [self._to_domain(m, self._lignes(s, m.id)) for m in rows]

    def save(self, d: Devis) -> None:
        with self._sf.get_session() as s:
            m = s.get(DevisModel, str(d.id))
            now_str = datetime.now().isoformat(timespec="seconds")
            if m:
                m.statut = d.statut.value
                m.client_id = str(d.client_id)
                m.vehicule_id = str(d.vehicule_id) if d.vehicule_id else None
                m.notes = d.notes_client
                m.notes_client = d.notes_client
                m.notes_internes = d.notes_internes
                m.date_expiration = d.date_expiration.isoformat() if d.date_expiration else None
                m.dossier_id = str(d.dossier_id) if d.dossier_id else None
                m.proforma_id = str(d.proforma_id) if d.proforma_id else None
                m.montant_ht = float(d.total_ht.amount)
                m.montant_ttc = float(d.total_ttc.amount)
                m.updated_at = now_str
                # replace lines
                s.query(LigneDevisModel).filter_by(devis_id=str(d.id)).delete()
                for l in d.lignes:
                    s.add(self._ligne_to_model(l, str(d.id)))
            else:
                m = DevisModel(
                    id=str(d.id),
                    numero=d.numero,
                    statut=d.statut.value,
                    client_id=str(d.client_id),
                    vehicule_id=str(d.vehicule_id) if d.vehicule_id else None,
                    date_creation=datetime.combine(d.date_creation, datetime.min.time()),
                    notes=d.notes_client,
                    notes_client=d.notes_client,
                    notes_internes=d.notes_internes,
                    date_expiration=d.date_expiration.isoformat() if d.date_expiration else None,
                    dossier_id=str(d.dossier_id) if d.dossier_id else None,
                    proforma_id=str(d.proforma_id) if d.proforma_id else None,
                    created_by=str(d.created_by) if d.created_by else "",
                    updated_at=now_str,
                    montant_ht=float(d.total_ht.amount),
                    montant_ttc=float(d.total_ttc.amount),
                )
                s.add(m)
                for l in d.lignes:
                    s.add(self._ligne_to_model(l, str(d.id)))

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            s.query(LigneDevisModel).filter_by(devis_id=str(entity_id)).delete()
            m = s.get(DevisModel, str(entity_id))
            if m:
                s.delete(m)

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _lignes(s, devis_id: str) -> list[LigneDevisModel]:
        return s.query(LigneDevisModel).filter_by(
            devis_id=devis_id
        ).order_by(LigneDevisModel.ordre).all()

    @staticmethod
    def _ligne_to_model(l: LigneDevis, devis_id: str) -> LigneDevisModel:
        return LigneDevisModel(
            id=str(l.id),
            devis_id=devis_id,
            type_ligne=l.type_ligne.value,
            designation=l.designation,
            quantite=str(l.quantite),
            prix_unitaire_ht=str(l.prix_unitaire_ht.amount),
            taux_tva=str(l.taux_tva),
            remise_pct=str(l.remise_pct),
            ordre=l.ordre,
            piece_id=str(l.piece_id) if l.piece_id else None,
        )

    @staticmethod
    def _to_domain(m: DevisModel, lignes: list[LigneDevisModel]) -> Devis:
        d = Devis(id=uuid.UUID(m.id))
        d.numero = m.numero or ""
        d.client_id = uuid.UUID(m.client_id) if (getattr(m, "client_id", None) or "").strip() else d.client_id
        d.vehicule_id = uuid.UUID(m.vehicule_id) if getattr(m, "vehicule_id", None) else None
        d.notes_client = getattr(m, "notes_client", None) or m.notes or ""
        d.notes_internes = getattr(m, "notes_internes", None) or ""
        try:
            d.statut = StatutDevis(m.statut)
        except ValueError:
            d.statut = StatutDevis.BROUILLON
        if m.date_creation:
            d.date_creation = m.date_creation.date() if hasattr(m.date_creation, "date") else date.today()
        exp = getattr(m, "date_expiration", None)
        d.date_expiration = date.fromisoformat(exp) if exp else None
        d.dossier_id = uuid.UUID(m.dossier_id) if m.dossier_id else None
        pf = getattr(m, "proforma_id", None)
        d.proforma_id = uuid.UUID(pf) if pf else None
        cb = getattr(m, "created_by", None)
        d.created_by = uuid.UUID(cb) if (cb or "").strip() else None
        for lm in lignes:
            ligne = LigneDevis(id=uuid.UUID(lm.id), devis_id=uuid.UUID(lm.devis_id))
            try:
                ligne.type_ligne = TypeLigne(lm.type_ligne)
            except ValueError:
                ligne.type_ligne = TypeLigne.SERVICE
            ligne.designation = lm.designation
            ligne.quantite = Decimal(str(lm.quantite or "1"))
            ligne.prix_unitaire_ht = Money(Decimal(str(lm.prix_unitaire_ht or "0")))
            ligne.taux_tva = Decimal(str(lm.taux_tva or "0.19"))
            ligne.remise_pct = Decimal(str(lm.remise_pct or "0"))
            ligne.ordre = lm.ordre or 0
            ligne.piece_id = uuid.UUID(lm.piece_id) if lm.piece_id else None
            d.lignes.append(ligne)
        return d


class SqlAlchemyProformaRepository(ProformaRepository):
    def __init__(self, sf: SessionFactory) -> None:
        self._sf = sf

    def get_by_id(self, entity_id: uuid.UUID) -> FactureProforma | None:
        with self._sf.get_session() as s:
            m = s.get(FactureProformaModel, str(entity_id))
            return self._to_domain(m) if m else None

    def find_all(self) -> list[FactureProforma]:
        with self._sf.get_session() as s:
            rows = s.query(FactureProformaModel).order_by(
                FactureProformaModel.date_emission.desc()
            ).all()
            return [self._to_domain(m) for m in rows]

    def find_by_client(self, client_id: uuid.UUID) -> list[FactureProforma]:
        with self._sf.get_session() as s:
            rows = s.query(FactureProformaModel).filter_by(
                client_id=str(client_id)
            ).order_by(FactureProformaModel.date_emission.desc()).all()
            return [self._to_domain(m) for m in rows]

    def find_by_devis(self, devis_id: uuid.UUID) -> FactureProforma | None:
        with self._sf.get_session() as s:
            m = s.query(FactureProformaModel).filter_by(
                devis_id=str(devis_id)
            ).first()
            return self._to_domain(m) if m else None

    def find_by_statut(self, statut: StatutProforma) -> list[FactureProforma]:
        with self._sf.get_session() as s:
            rows = s.query(FactureProformaModel).filter_by(
                statut=statut.value
            ).order_by(FactureProformaModel.date_emission.desc()).all()
            return [self._to_domain(m) for m in rows]

    def save(self, pf: FactureProforma) -> None:
        with self._sf.get_session() as s:
            m = s.get(FactureProformaModel, str(pf.id))
            if m:
                m.statut = pf.statut.value
                m.acompte_recu = str(pf.acompte_recu.amount)
                m.facture_finale_id = str(pf.facture_finale_id) if pf.facture_finale_id else None
                m.notes = pf.notes
                # replace lines
                s.query(LigneProformaModel).filter_by(proforma_id=str(pf.id)).delete()
                for l in pf.lignes:
                    m.lignes.append(self._ligne_to_model(l, str(pf.id)))
            else:
                m = FactureProformaModel(
                    id=str(pf.id),
                    numero=pf.numero,
                    client_id=str(pf.client_id),
                    devis_id=str(pf.devis_id) if pf.devis_id else None,
                    statut=pf.statut.value,
                    date_emission=pf.date_emission.isoformat(),
                    acompte_recu=str(pf.acompte_recu.amount),
                    facture_finale_id=str(pf.facture_finale_id) if pf.facture_finale_id else None,
                    notes=pf.notes,
                )
                s.add(m)
                for l in pf.lignes:
                    m.lignes.append(self._ligne_to_model(l, str(pf.id)))

    def delete(self, entity_id: uuid.UUID) -> None:
        with self._sf.get_session() as s:
            m = s.get(FactureProformaModel, str(entity_id))
            if m:
                s.delete(m)

    @staticmethod
    def _ligne_to_model(l: LigneProforma, proforma_id: str) -> LigneProformaModel:
        return LigneProformaModel(
            id=str(l.id),
            proforma_id=proforma_id,
            type_ligne=l.type_ligne.value,
            designation=l.designation,
            quantite=str(l.quantite),
            prix_unitaire_ht=str(l.prix_unitaire_ht.amount),
            taux_tva=str(l.taux_tva),
            remise_pct=str(l.remise_pct),
            ordre=l.ordre,
        )

    @staticmethod
    def _to_domain(m: FactureProformaModel) -> FactureProforma:
        pf = FactureProforma(id=uuid.UUID(m.id))
        pf.numero = m.numero
        pf.client_id = uuid.UUID(m.client_id)
        pf.devis_id = uuid.UUID(m.devis_id) if m.devis_id else None
        try:
            pf.statut = StatutProforma(m.statut)
        except ValueError:
            pf.statut = StatutProforma.EMISE
        pf.date_emission = date.fromisoformat(m.date_emission) if m.date_emission else date.today()
        pf.acompte_recu = Money(Decimal(str(m.acompte_recu or "0")))
        pf.facture_finale_id = uuid.UUID(m.facture_finale_id) if m.facture_finale_id else None
        pf.notes = m.notes or ""
        for lm in (m.lignes or []):
            l = LigneProforma(id=uuid.UUID(lm.id), proforma_id=uuid.UUID(lm.proforma_id))
            try:
                l.type_ligne = TypeLigne(lm.type_ligne)
            except ValueError:
                l.type_ligne = TypeLigne.SERVICE
            l.designation = lm.designation
            l.quantite = Decimal(str(lm.quantite or "1"))
            l.prix_unitaire_ht = Money(Decimal(str(lm.prix_unitaire_ht or "0")))
            l.taux_tva = Decimal(str(lm.taux_tva or "0.19"))
            l.remise_pct = Decimal(str(lm.remise_pct or "0"))
            l.ordre = lm.ordre or 0
            pf.lignes.append(l)
        return pf
