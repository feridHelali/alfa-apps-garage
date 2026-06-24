from __future__ import annotations

import uuid
from decimal import Decimal

from garage_app.application.decorators import require_permission
from garage_app.application.numerotation_service import NumerotationService
from garage_app.domain.atelier.dossier_reparation import DossierReparation
from garage_app.domain.atelier.statut_dossier import StatutDossier
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.facturation.facture import Facture, LigneFacture, StatutFacture
from garage_app.domain.facturation.repositories import FactureRepository
from garage_app.domain.atelier.repositories import DossierReparationRepository
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus


class FactureService:
    def __init__(
        self,
        sf: SessionFactory,
        facture_repo: FactureRepository,
        dossier_repo: DossierReparationRepository,
        bus: InMemoryEventBus,
        numerotation_service: NumerotationService | None = None,
    ) -> None:
        self._sf = sf
        self._factures = facture_repo
        self._dossiers = dossier_repo
        self._bus = bus
        self._numerotation = numerotation_service

    def _next_numero_facture(self) -> str:
        if self._numerotation:
            return self._numerotation.generer_numero("facture")
        return self._factures.next_numero()

    @require_permission(Permission.VIEW_FACTURES)
    def list_factures(self, session: UserSession) -> list[Facture]:
        with self._sf.get_session():
            return self._factures.find_all()

    @require_permission(Permission.VIEW_FACTURES)
    def list_impayees(self, session: UserSession) -> list[Facture]:
        with self._sf.get_session():
            return self._factures.find_impayees()

    @require_permission(Permission.VIEW_FACTURES)
    def get_facture(self, session: UserSession, facture_id: uuid.UUID) -> Facture | None:
        with self._sf.get_session():
            return self._factures.get_by_id(facture_id)

    @require_permission(Permission.MANAGE_FACTURES)
    def generer_facture(
        self,
        session: UserSession,
        dossier_id: uuid.UUID,
        taux_tva: Decimal = Decimal("19"),
    ) -> Facture:
        with self._sf.get_session():
            dossier = self._dossiers.get_by_id(dossier_id)
            if not dossier:
                raise ValueError(f"Dossier {dossier_id} introuvable.")
            numero = self._next_numero_facture()
            facture = Facture(
                dossier_id=dossier_id,
                client_id=dossier.client_id,
                numero=numero,
                taux_tva=taux_tva,
            )
            for op in dossier.operations:
                if op.montant.amount > 0:
                    facture.lignes.append(LigneFacture(
                        designation=op.description or op.code_main_oeuvre or "Intervention technique",
                        quantite=1,
                        prix_unitaire=op.montant.amount,
                    ))
            for p in dossier.pieces:
                facture.lignes.append(LigneFacture(
                    designation=p.designation or p.reference or "Pièce",
                    quantite=p.quantite,
                    prix_unitaire=p.prix_unitaire,
                ))
            facture.emettre()
            dossier.generer_facture(facture.id, facture.montant_ttc.amount)
            self._factures.save(facture)
            self._dossiers.save(dossier)
        self._bus.publish_all(facture.pull_events())
        self._bus.publish_all(dossier.pull_events())
        return facture

    @require_permission(Permission.RECORD_PAYMENT)
    def enregistrer_paiement(
        self,
        session: UserSession,
        facture_id: uuid.UUID,
        montant: Decimal,
        mode: str,
        reference: str = "",
    ) -> Facture:
        with self._sf.get_session():
            facture = self._factures.get_by_id(facture_id)
            if not facture:
                raise ValueError(f"Facture {facture_id} introuvable.")
            facture.enregistrer_paiement(montant, mode, reference)
            self._factures.save(facture)
        self._bus.publish_all(facture.pull_events())
        return facture

    @require_permission(Permission.MANAGE_FACTURES)
    def generer_facture_directe(
        self,
        session: UserSession,
        client_id: uuid.UUID,
        vehicule_id: uuid.UUID,
        lignes: list[dict],
        taux_tva: Decimal = Decimal("19"),
        notes: str = "",
        kilometrage: int = 0,
    ) -> Facture:
        """Quick invoice: creates a CLOTURE dossier + invoice in one step (no state machine)."""
        with self._sf.get_session():
            dossier = DossierReparation(
                vehicule_id=vehicule_id,
                client_id=client_id,
                kilometrage_entree=kilometrage,
                statut=StatutDossier.CLOTURE,
                notes=notes,
            )
            numero = self._next_numero_facture()
            facture = Facture(
                dossier_id=dossier.id,
                client_id=client_id,
                numero=numero,
                taux_tva=taux_tva,
            )
            for l in lignes:
                facture.lignes.append(LigneFacture(
                    designation=l["designation"],
                    quantite=l["quantite"],
                    prix_unitaire=Decimal(str(l["prix_unitaire"])),
                ))
            facture.emettre()
            dossier.facture_id = facture.id
            self._dossiers.save(dossier)
            self._factures.save(facture)
        self._bus.publish_all(facture.pull_events())
        return facture

    @require_permission(Permission.MANAGE_FACTURES)
    def annuler_facture(self, session: UserSession, facture_id: uuid.UUID) -> Facture:
        with self._sf.get_session():
            facture = self._factures.get_by_id(facture_id)
            if not facture:
                raise ValueError(f"Facture {facture_id} introuvable.")
            facture.annuler()
            self._factures.save(facture)
        self._bus.publish_all(facture.pull_events())
        return facture
