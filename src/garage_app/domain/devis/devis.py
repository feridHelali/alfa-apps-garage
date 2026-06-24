from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.shared.entity import Entity
from garage_app.domain.shared.exceptions import BusinessRuleError
from garage_app.domain.shared.value_objects import Money
from garage_app.domain.devis.statut_devis import StatutDevis, StatutProforma, TypeLigne
from garage_app.domain.devis import events


@dataclass
class LigneDevis(Entity):
    devis_id: uuid.UUID = field(default_factory=uuid.uuid4)
    type_ligne: TypeLigne = TypeLigne.SERVICE
    designation: str = ""
    quantite: Decimal = Decimal("1")
    prix_unitaire_ht: Money = field(default_factory=Money.zero)
    taux_tva: Decimal = Decimal("0.19")
    remise_pct: Decimal = Decimal("0")
    ordre: int = 0
    piece_id: uuid.UUID | None = None

    @property
    def montant_ht(self) -> Money:
        brut = self.prix_unitaire_ht * self.quantite
        remise = brut * self.remise_pct
        return Money(brut.amount - remise.amount, brut.currency)

    @property
    def montant_tva(self) -> Money:
        return self.montant_ht * self.taux_tva

    @property
    def montant_ttc(self) -> Money:
        return Money(
            self.montant_ht.amount + self.montant_tva.amount,
            self.montant_ht.currency,
        )


@dataclass
class Devis(AggregateRoot):
    """Commercial quote aggregate.

    State machine: BROUILLON → ENVOYE → ACCEPTE/REFUSE → TRANSFORME
                                           → EXPIRE (after N days)
                            → ANNULE (from BROUILLON or ENVOYE)
    """
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    vehicule_id: uuid.UUID | None = None
    numero: str = ""
    statut: StatutDevis = StatutDevis.BROUILLON
    date_creation: date = field(default_factory=date.today)
    date_expiration: date | None = None
    lignes: list[LigneDevis] = field(default_factory=list)
    notes_client: str = ""
    notes_internes: str = ""
    dossier_id: uuid.UUID | None = None
    proforma_id: uuid.UUID | None = None
    created_by: uuid.UUID | None = None
    updated_at: datetime = field(default_factory=datetime.now)

    # ── Guards ──────────────────────────────────────────────────────────────

    def _assert(self, condition: bool, msg: str) -> None:
        if not condition:
            raise BusinessRuleError(msg)

    # ── Computed totals ──────────────────────────────────────────────────────

    @property
    def total_ht(self) -> Money:
        total = Money.zero()
        for l in self.lignes:
            total = total + l.montant_ht
        return total

    @property
    def total_tva(self) -> Money:
        total = Money.zero()
        for l in self.lignes:
            total = total + l.montant_tva
        return total

    @property
    def total_ttc(self) -> Money:
        return Money(self.total_ht.amount + self.total_tva.amount, "TND")

    # ── State machine ────────────────────────────────────────────────────────

    def envoyer(self) -> None:
        self._assert(
            self.statut.peut_envoyer(),
            f"Impossible d'envoyer depuis l'état '{self.statut.label_fr()}'.",
        )
        self._assert(len(self.lignes) > 0, "Un devis doit contenir au moins une ligne.")
        self.statut = StatutDevis.ENVOYE
        self.updated_at = datetime.now()
        self._raise_event(events.DevisEnvoyeAuClient(
            devis_id=self.id, client_id=self.client_id
        ))

    def accepter(self, par: uuid.UUID) -> None:
        self._assert(
            self.statut.peut_accepter(),
            f"Impossible d'accepter depuis l'état '{self.statut.label_fr()}'.",
        )
        self.statut = StatutDevis.ACCEPTE
        self.updated_at = datetime.now()
        self._raise_event(events.DevisAccepteParClient(
            devis_id=self.id, client_id=self.client_id, accepte_par=par
        ))

    def refuser(self, motif: str = "") -> None:
        self._assert(
            self.statut.peut_refuser(),
            f"Impossible de refuser depuis l'état '{self.statut.label_fr()}'.",
        )
        self.statut = StatutDevis.REFUSE
        self.updated_at = datetime.now()
        self._raise_event(events.DevisRefuseParClient(devis_id=self.id, motif=motif))

    def annuler(self) -> None:
        self._assert(
            self.statut.peut_annuler(),
            f"Impossible d'annuler depuis l'état '{self.statut.label_fr()}'.",
        )
        self.statut = StatutDevis.ANNULE
        self.updated_at = datetime.now()

    def expirer(self) -> None:
        self._assert(
            self.statut == StatutDevis.ENVOYE,
            "Seul un devis envoyé peut expirer.",
        )
        self.statut = StatutDevis.EXPIRE
        self.updated_at = datetime.now()

    def marquer_transforme(
        self,
        dossier_id: uuid.UUID | None = None,
        proforma_id: uuid.UUID | None = None,
    ) -> None:
        self._assert(
            self.statut.peut_convertir(),
            f"Seul un devis accepté peut être transformé (état actuel : '{self.statut.label_fr()}').",
        )
        self._assert(
            dossier_id is not None or proforma_id is not None,
            "Précisez le dossier ou la proforma cible.",
        )
        if dossier_id:
            self.dossier_id = dossier_id
            self._raise_event(events.DevisTransformeEnDossier(
                devis_id=self.id, dossier_id=dossier_id
            ))
        if proforma_id:
            self.proforma_id = proforma_id
            self._raise_event(events.DevisTransformeEnProforma(
                devis_id=self.id, proforma_id=proforma_id
            ))
        self.statut = StatutDevis.TRANSFORME
        self.updated_at = datetime.now()

    def dupliquer(self) -> "Devis":
        """Return a new BROUILLON Devis with the same lines."""
        copy = Devis(
            client_id=self.client_id,
            vehicule_id=self.vehicule_id,
            notes_client=self.notes_client,
            notes_internes=self.notes_internes,
        )
        for l in self.lignes:
            copy.lignes.append(LigneDevis(
                devis_id=copy.id,
                type_ligne=l.type_ligne,
                designation=l.designation,
                quantite=l.quantite,
                prix_unitaire_ht=l.prix_unitaire_ht,
                taux_tva=l.taux_tva,
                remise_pct=l.remise_pct,
                ordre=l.ordre,
                piece_id=l.piece_id,
            ))
        return copy


@dataclass
class LigneProforma(Entity):
    proforma_id: uuid.UUID = field(default_factory=uuid.uuid4)
    type_ligne: TypeLigne = TypeLigne.SERVICE
    designation: str = ""
    quantite: Decimal = Decimal("1")
    prix_unitaire_ht: Money = field(default_factory=Money.zero)
    taux_tva: Decimal = Decimal("0.19")
    remise_pct: Decimal = Decimal("0")
    ordre: int = 0

    @property
    def montant_ht(self) -> Money:
        brut = self.prix_unitaire_ht * self.quantite
        remise = brut * self.remise_pct
        return Money(brut.amount - remise.amount, brut.currency)

    @property
    def montant_ttc(self) -> Money:
        tva = self.montant_ht * self.taux_tva
        return Money(self.montant_ht.amount + tva.amount, "TND")


@dataclass
class FactureProforma(AggregateRoot):
    """Proforma invoice — commercial engagement, not a legal accounting document."""
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    devis_id: uuid.UUID | None = None
    numero: str = ""
    statut: StatutProforma = StatutProforma.EMISE
    date_emission: date = field(default_factory=date.today)
    lignes: list[LigneProforma] = field(default_factory=list)
    acompte_recu: Money = field(default_factory=Money.zero)
    facture_finale_id: uuid.UUID | None = None
    notes: str = ""

    @property
    def total_ht(self) -> Money:
        total = Money.zero()
        for l in self.lignes:
            total = total + l.montant_ht
        return total

    @property
    def total_ttc(self) -> Money:
        total = Money.zero()
        for l in self.lignes:
            total = total + l.montant_ttc
        return total

    @property
    def solde_restant(self) -> Money:
        return Money(
            max(Decimal("0"), self.total_ttc.amount - self.acompte_recu.amount),
            "TND",
        )

    def enregistrer_acompte(self, montant: Money) -> None:
        from garage_app.domain.shared.exceptions import BusinessRuleError
        if montant.amount <= Decimal("0"):
            raise BusinessRuleError("L'acompte doit être positif.")
        if montant.amount > self.total_ttc.amount:
            raise BusinessRuleError("L'acompte ne peut pas dépasser le total TTC.")
        self.acompte_recu = Money(self.acompte_recu.amount + montant.amount, "TND")
        if self.statut == StatutProforma.EMISE:
            self.statut = StatutProforma.ACOMPTE_RECU
        self._raise_event(events.AcompteEnregistre(
            proforma_id=self.id, montant=float(montant.amount)
        ))

    def lier_facture(self, facture_id: uuid.UUID) -> None:
        self.facture_finale_id = facture_id
        self.statut = StatutProforma.LIEE_FACTURE

    def annuler(self) -> None:
        from garage_app.domain.shared.exceptions import BusinessRuleError
        if self.statut == StatutProforma.LIEE_FACTURE:
            raise BusinessRuleError("Impossible d'annuler une proforma liée à une facture.")
        self.statut = StatutProforma.ANNULEE
