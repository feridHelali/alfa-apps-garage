from __future__ import annotations

import uuid
from dataclasses import dataclass

from garage_app.domain.shared.domain_event import DomainEvent


@dataclass(frozen=True)
class DevisCreePourClient(DomainEvent):
    devis_id: uuid.UUID = uuid.uuid4()
    client_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class DevisEnvoyeAuClient(DomainEvent):
    devis_id: uuid.UUID = uuid.uuid4()
    client_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class DevisAccepteParClient(DomainEvent):
    devis_id: uuid.UUID = uuid.uuid4()
    client_id: uuid.UUID = uuid.uuid4()
    accepte_par: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class DevisRefuseParClient(DomainEvent):
    devis_id: uuid.UUID = uuid.uuid4()
    motif: str = ""


@dataclass(frozen=True)
class DevisTransformeEnDossier(DomainEvent):
    devis_id: uuid.UUID = uuid.uuid4()
    dossier_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class DevisTransformeEnProforma(DomainEvent):
    devis_id: uuid.UUID = uuid.uuid4()
    proforma_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class ProformaEmise(DomainEvent):
    proforma_id: uuid.UUID = uuid.uuid4()
    client_id: uuid.UUID = uuid.uuid4()


@dataclass(frozen=True)
class AcompteEnregistre(DomainEvent):
    proforma_id: uuid.UUID = uuid.uuid4()
    montant: float = 0.0
