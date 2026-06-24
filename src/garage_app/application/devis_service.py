"""DevisService — commercial quotes lifecycle + conversion to DossierReparation / FactureProforma."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from garage_app.application.decorators import require_permission
from garage_app.application.numerotation_service import NumerotationService
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.domain.devis.devis import Devis, FactureProforma, LigneDevis, LigneProforma
from garage_app.domain.devis.repositories import DevisRepository, ProformaRepository
from garage_app.domain.devis.statut_devis import StatutDevis, TypeLigne
from garage_app.domain.shared.exceptions import BusinessRuleError
from garage_app.domain.shared.value_objects import Money
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus


class DevisService:
    def __init__(
        self,
        sf: SessionFactory,
        devis_repo: DevisRepository,
        proforma_repo: ProformaRepository,
        bus: InMemoryEventBus,
        numerotation: NumerotationService | None = None,
    ) -> None:
        self._sf = sf
        self._devis = devis_repo
        self._proformas = proforma_repo
        self._bus = bus
        self._numerotation = numerotation

    def _next_numero_devis(self) -> str:
        if self._numerotation:
            return self._numerotation.generer_numero("devis")
        year = date.today().year
        return f"DEV-{year}-0001"

    def _next_numero_proforma(self) -> str:
        if self._numerotation:
            return self._numerotation.generer_numero("proforma")
        year = date.today().year
        return f"PRO-{year}-0001"

    # ── Queries ─────────────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_DEVIS)
    def list_devis(self, session: UserSession) -> list[Devis]:
        with self._sf.get_session():
            return self._devis.find_all()

    @require_permission(Permission.VIEW_DEVIS)
    def list_actifs(self, session: UserSession) -> list[Devis]:
        with self._sf.get_session():
            return self._devis.find_actifs()

    @require_permission(Permission.VIEW_DEVIS)
    def get_devis(self, session: UserSession, devis_id: uuid.UUID) -> Devis | None:
        with self._sf.get_session():
            return self._devis.get_by_id(devis_id)

    @require_permission(Permission.VIEW_PROFORMA)
    def list_proformas(self, session: UserSession) -> list[FactureProforma]:
        with self._sf.get_session():
            return self._proformas.find_all()

    @require_permission(Permission.VIEW_PROFORMA)
    def get_proforma(self, session: UserSession, proforma_id: uuid.UUID) -> FactureProforma | None:
        with self._sf.get_session():
            return self._proformas.get_by_id(proforma_id)

    # ── Devis CRUD ──────────────────────────────────────────────────────────

    @require_permission(Permission.MANAGE_DEVIS)
    def creer_devis(
        self,
        session: UserSession,
        client_id: uuid.UUID,
        vehicule_id: uuid.UUID | None = None,
        notes_client: str = "",
        notes_internes: str = "",
        date_expiration: date | None = None,
    ) -> Devis:
        with self._sf.get_session():
            devis = Devis(
                client_id=client_id,
                vehicule_id=vehicule_id,
                notes_client=notes_client,
                notes_internes=notes_internes,
                date_expiration=date_expiration,
                created_by=session.user_id,
                numero=self._next_numero_devis(),
            )
            self._devis.save(devis)
            for evt in devis.pull_events():
                self._bus.publish(evt)
            return devis

    @require_permission(Permission.MANAGE_DEVIS)
    def ajouter_ligne(
        self,
        session: UserSession,
        devis_id: uuid.UUID,
        type_ligne: TypeLigne,
        designation: str,
        quantite: Decimal,
        prix_unitaire_ht: Decimal,
        taux_tva: Decimal = Decimal("0.19"),
        remise_pct: Decimal = Decimal("0"),
        piece_id: uuid.UUID | None = None,
    ) -> Devis:
        with self._sf.get_session():
            devis = self._devis.get_by_id(devis_id)
            if not devis:
                raise ValueError(f"Devis {devis_id} introuvable.")
            if not devis.statut.peut_modifier():
                raise BusinessRuleError(
                    f"Impossible de modifier un devis '{devis.statut.label_fr()}'."
                )
            ligne = LigneDevis(
                devis_id=devis_id,
                type_ligne=type_ligne,
                designation=designation,
                quantite=quantite,
                prix_unitaire_ht=Money(prix_unitaire_ht),
                taux_tva=taux_tva,
                remise_pct=remise_pct,
                ordre=len(devis.lignes),
                piece_id=piece_id,
            )
            devis.lignes.append(ligne)
            self._devis.save(devis)
            return devis

    @require_permission(Permission.MANAGE_DEVIS)
    def sauvegarder_devis(
        self,
        session: UserSession,
        devis: Devis,
    ) -> Devis:
        """Persist a fully-built Devis object (used by the form dialog)."""
        with self._sf.get_session():
            if not devis.statut.peut_modifier():
                raise BusinessRuleError(
                    f"Impossible de modifier un devis '{devis.statut.label_fr()}'."
                )
            self._devis.save(devis)
            return devis

    # ── State transitions ────────────────────────────────────────────────────

    @require_permission(Permission.MANAGE_DEVIS)
    def envoyer(self, session: UserSession, devis_id: uuid.UUID) -> Devis:
        with self._sf.get_session():
            devis = self._devis.get_by_id(devis_id)
            if not devis:
                raise ValueError(f"Devis {devis_id} introuvable.")
            devis.envoyer()
            self._devis.save(devis)
            for evt in devis.pull_events():
                self._bus.publish(evt)
            return devis

    @require_permission(Permission.MANAGE_DEVIS)
    def accepter(self, session: UserSession, devis_id: uuid.UUID) -> Devis:
        with self._sf.get_session():
            devis = self._devis.get_by_id(devis_id)
            if not devis:
                raise ValueError(f"Devis {devis_id} introuvable.")
            devis.accepter(par=session.user_id)
            self._devis.save(devis)
            for evt in devis.pull_events():
                self._bus.publish(evt)
            return devis

    @require_permission(Permission.MANAGE_DEVIS)
    def refuser(self, session: UserSession, devis_id: uuid.UUID, motif: str = "") -> Devis:
        with self._sf.get_session():
            devis = self._devis.get_by_id(devis_id)
            if not devis:
                raise ValueError(f"Devis {devis_id} introuvable.")
            devis.refuser(motif=motif)
            self._devis.save(devis)
            for evt in devis.pull_events():
                self._bus.publish(evt)
            return devis

    @require_permission(Permission.MANAGE_DEVIS)
    def annuler(self, session: UserSession, devis_id: uuid.UUID) -> Devis:
        with self._sf.get_session():
            devis = self._devis.get_by_id(devis_id)
            if not devis:
                raise ValueError(f"Devis {devis_id} introuvable.")
            devis.annuler()
            self._devis.save(devis)
            return devis

    # ── Conversion ───────────────────────────────────────────────────────────

    @require_permission(Permission.CONVERT_DEVIS)
    def convertir_en_proforma(
        self, session: UserSession, devis_id: uuid.UUID
    ) -> FactureProforma:
        """Convert an ACCEPTE Devis into a FactureProforma."""
        with self._sf.get_session():
            devis = self._devis.get_by_id(devis_id)
            if not devis:
                raise ValueError(f"Devis {devis_id} introuvable.")
            if not devis.statut.peut_convertir():
                raise BusinessRuleError(
                    f"Seul un devis accepté peut être converti "
                    f"(état actuel : '{devis.statut.label_fr()}')."
                )
            proforma = FactureProforma(
                client_id=devis.client_id,
                devis_id=devis.id,
                numero=self._next_numero_proforma(),
            )
            for l in devis.lignes:
                proforma.lignes.append(LigneProforma(
                    proforma_id=proforma.id,
                    type_ligne=l.type_ligne,
                    designation=l.designation,
                    quantite=l.quantite,
                    prix_unitaire_ht=l.prix_unitaire_ht,
                    taux_tva=l.taux_tva,
                    remise_pct=l.remise_pct,
                    ordre=l.ordre,
                ))
            self._proformas.save(proforma)
            devis.marquer_transforme(proforma_id=proforma.id)
            self._devis.save(devis)
            for evt in devis.pull_events():
                self._bus.publish(evt)
            for evt in proforma.pull_events():
                self._bus.publish(evt)
            return proforma

    @require_permission(Permission.MANAGE_PROFORMA)
    def enregistrer_acompte_proforma(
        self, session: UserSession, proforma_id: uuid.UUID, montant: Decimal
    ) -> FactureProforma:
        with self._sf.get_session():
            pf = self._proformas.get_by_id(proforma_id)
            if not pf:
                raise ValueError(f"Proforma {proforma_id} introuvable.")
            pf.enregistrer_acompte(Money(montant))
            self._proformas.save(pf)
            for evt in pf.pull_events():
                self._bus.publish(evt)
            return pf

    @require_permission(Permission.CONVERT_DEVIS)
    def marquer_transforme_en_dossier(
        self, session: UserSession, devis_id: uuid.UUID, dossier_id: uuid.UUID
    ) -> Devis:
        """Mark a Devis as TRANSFORME after a DossierReparation has been created externally."""
        with self._sf.get_session():
            devis = self._devis.get_by_id(devis_id)
            if not devis:
                raise ValueError(f"Devis {devis_id} introuvable.")
            devis.marquer_transforme(dossier_id=dossier_id)
            self._devis.save(devis)
            for evt in devis.pull_events():
                self._bus.publish(evt)
            return devis

    @require_permission(Permission.MANAGE_DEVIS)
    def dupliquer(self, session: UserSession, devis_id: uuid.UUID) -> Devis:
        with self._sf.get_session():
            devis = self._devis.get_by_id(devis_id)
            if not devis:
                raise ValueError(f"Devis {devis_id} introuvable.")
            copie = devis.dupliquer()
            copie.numero = self._next_numero_devis()
            copie.created_by = session.user_id
            self._devis.save(copie)
            return copie
