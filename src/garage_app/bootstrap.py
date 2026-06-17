from __future__ import annotations

from dataclasses import dataclass

from garage_app.settings import AppSettings
from garage_app.infrastructure.db.engine import create_db_engine
from garage_app.infrastructure.db.session import SessionFactory
from garage_app.infrastructure.db.initializer import DatabaseInitializer
from garage_app.infrastructure.events.in_memory_event_bus import InMemoryEventBus
from garage_app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository
from garage_app.infrastructure.repositories.client_repository import SqlAlchemyClientRepository
from garage_app.infrastructure.repositories.vehicule_repository import SqlAlchemyVehiculeRepository
from garage_app.infrastructure.repositories.dossier_repository import SqlAlchemyDossierRepository
from garage_app.infrastructure.repositories.piece_repository import SqlAlchemyPieceRepository
from garage_app.infrastructure.repositories.fournisseur_repository import SqlAlchemyFournisseurRepository
from garage_app.infrastructure.repositories.commande_repository import SqlAlchemyCommandeRepository
from garage_app.infrastructure.repositories.facture_repository import SqlAlchemyFactureRepository
from garage_app.infrastructure.repositories.caisse_repository import SqlAlchemyCaisseRepository
from garage_app.infrastructure.repositories.credit_repository import SqlAlchemyCreditRepository
from garage_app.infrastructure.repositories.societe_repository import SqlAlchemySocieteRepository
from garage_app.infrastructure.repositories.report_template_repository import SqlAlchemyReportTemplateRepository
from garage_app.infrastructure.repositories.audit_log_repository import AuditLogRepository
from garage_app.application.auth_service import AuthService
from garage_app.application.client_service import ClientService
from garage_app.application.dossier_service import DossierService
from garage_app.application.stock_service import StockService
from garage_app.application.fournisseur_service import FournisseurService
from garage_app.application.commande_service import CommandeService
from garage_app.application.facture_service import FactureService
from garage_app.application.caisse_service import CaisseService
from garage_app.application.credit_service import CreditService
from garage_app.application.societe_service import SocieteService
from garage_app.application.report_service import ReportService
from garage_app.application.snapshot_service import SnapshotService
from garage_app.application.settings_service import SettingsService
from garage_app.application.audit_service import AuditService
from garage_app.application.db_management_service import DbManagementService


@dataclass
class AppContext:
    settings: AppSettings
    session_factory: SessionFactory
    event_bus: InMemoryEventBus
    auth_service: AuthService
    client_service: ClientService
    dossier_service: DossierService
    stock_service: StockService
    fournisseur_service: FournisseurService
    commande_service: CommandeService
    facture_service: FactureService
    caisse_service: CaisseService
    credit_service: CreditService
    societe_service: SocieteService
    report_service: ReportService
    snapshot_service: SnapshotService
    settings_service: SettingsService
    audit_service: AuditService
    db_management_service: DbManagementService


def bootstrap() -> AppContext:
    settings = AppSettings()
    AppSettings.ensure_dirs()

    engine = create_db_engine(settings.db_path)
    sf = SessionFactory(engine)
    DatabaseInitializer(engine, sf).initialize()

    event_bus = InMemoryEventBus()

    audit_repo = AuditLogRepository(sf)
    audit_svc = AuditService(audit_repo)
    audit_svc.log_system("Application démarrée")

    user_repo = SqlAlchemyUserRepository(sf)
    client_repo = SqlAlchemyClientRepository(sf)
    vehicule_repo = SqlAlchemyVehiculeRepository(sf)
    dossier_repo = SqlAlchemyDossierRepository(sf)
    piece_repo = SqlAlchemyPieceRepository(sf)
    fournisseur_repo = SqlAlchemyFournisseurRepository(sf)
    commande_repo = SqlAlchemyCommandeRepository(sf)
    facture_repo = SqlAlchemyFactureRepository(sf)
    caisse_repo = SqlAlchemyCaisseRepository(sf)
    credit_repo = SqlAlchemyCreditRepository(sf)
    societe_repo = SqlAlchemySocieteRepository(sf)
    template_repo = SqlAlchemyReportTemplateRepository(sf)

    return AppContext(
        settings=settings,
        session_factory=sf,
        event_bus=event_bus,
        auth_service=AuthService(sf, user_repo),
        client_service=ClientService(sf, client_repo, vehicule_repo),
        dossier_service=DossierService(sf, dossier_repo, event_bus),
        stock_service=StockService(sf, piece_repo, event_bus),
        fournisseur_service=FournisseurService(sf, fournisseur_repo),
        commande_service=CommandeService(sf, commande_repo, piece_repo, event_bus),
        facture_service=FactureService(sf, facture_repo, dossier_repo, event_bus),
        caisse_service=CaisseService(sf, caisse_repo, event_bus, audit_svc),
        credit_service=CreditService(sf, credit_repo),
        societe_service=SocieteService(sf, societe_repo),
        report_service=ReportService(template_repo),
        snapshot_service=SnapshotService(settings),
        settings_service=SettingsService(settings),
        audit_service=audit_svc,
        db_management_service=DbManagementService(sf, settings, audit_svc),
    )
