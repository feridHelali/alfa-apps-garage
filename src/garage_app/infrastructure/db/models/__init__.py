from garage_app.infrastructure.db.models.user_model import UserModel, RoleModel
from garage_app.infrastructure.db.models.societe_model import SocieteModel
from garage_app.infrastructure.db.models.client_model import ClientModel, VehiculeModel
from garage_app.infrastructure.db.models.dossier_model import (
    DossierReparationModel, LigneDiagnosticModel, OperationMecaniqueModel, PieceRequiseModel,
)
from garage_app.infrastructure.db.models.piece_model import (
    FournisseurModel, PieceModel,
    CommandeFournisseurModel, LigneCommandeModel, MouvementStockModel,
)
from garage_app.infrastructure.db.models.facture_model import (
    DevisModel, FactureModel, LigneFactureModel, PaiementModel,
    SessionCaisseModel, MouvementCaisseModel, CreditClientModel,
)
from garage_app.infrastructure.db.models.report_template_model import ReportTemplateModel
from garage_app.infrastructure.db.models.settings_model import AppSettingsModel
from garage_app.infrastructure.db.models.snapshot_model import SnapshotModel
from garage_app.infrastructure.db.models.audit_log_model import AuditLogModel

__all__ = [
    "UserModel", "RoleModel", "SocieteModel",
    "ClientModel", "VehiculeModel",
    "DossierReparationModel", "LigneDiagnosticModel", "OperationMecaniqueModel", "PieceRequiseModel",
    "FournisseurModel", "PieceModel",
    "CommandeFournisseurModel", "LigneCommandeModel", "MouvementStockModel",
    "DevisModel", "FactureModel", "LigneFactureModel", "PaiementModel",
    "SessionCaisseModel", "MouvementCaisseModel", "CreditClientModel",
    "ReportTemplateModel", "AppSettingsModel", "SnapshotModel", "AuditLogModel",
]
