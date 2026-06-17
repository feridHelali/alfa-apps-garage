from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from garage_app.domain.shared.domain_event import DomainEvent


@dataclass(frozen=True)
class DiagnosticLance(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class PanneIdentifiee(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()
    code_defaut: str = ""


@dataclass(frozen=True)
class DossierSoumisAuDevis(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class DevisApprouve(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()
    devis_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class DevisRefuse(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class DevisComplementaireCree(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class ReparationCommencee(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class ReparationTerminee(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class ControleQualiteValide(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class FactureGeneree(DomainEvent):
    dossier_id: uuid.UUID = uuid.uuid4()
    facture_id: uuid.UUID = uuid.uuid4()
    montant_ttc: Decimal = Decimal("0")
