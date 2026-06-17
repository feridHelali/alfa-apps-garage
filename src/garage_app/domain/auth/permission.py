from enum import StrEnum, auto


class Permission(StrEnum):
    # Planification
    VIEW_CLIENTS = auto()
    MANAGE_CLIENTS = auto()
    VIEW_RENDEZ_VOUS = auto()
    MANAGE_RENDEZ_VOUS = auto()
    # Atelier
    VIEW_DOSSIERS = auto()
    CREATE_DOSSIER = auto()
    MANAGE_DOSSIER = auto()
    APPROVE_DEVIS = auto()
    VALIDATE_QUALITY = auto()
    # Stock
    VIEW_STOCK = auto()
    MANAGE_STOCK = auto()
    # Facturation
    VIEW_FACTURES = auto()
    MANAGE_FACTURES = auto()
    RECORD_PAYMENT = auto()
    MANAGE_CAISSE = auto()
    # Administration
    MANAGE_USERS = auto()
    MANAGE_SOCIETE = auto()
    MANAGE_REPORTS = auto()
    MANAGE_SNAPSHOTS = auto()
    MANAGE_SETTINGS = auto()


ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "superadmin": frozenset(Permission),
    "admin": frozenset({
        Permission.VIEW_CLIENTS, Permission.MANAGE_CLIENTS,
        Permission.VIEW_RENDEZ_VOUS, Permission.MANAGE_RENDEZ_VOUS,
        Permission.VIEW_DOSSIERS, Permission.CREATE_DOSSIER, Permission.MANAGE_DOSSIER,
        Permission.APPROVE_DEVIS, Permission.VALIDATE_QUALITY,
        Permission.VIEW_STOCK, Permission.MANAGE_STOCK,
        Permission.VIEW_FACTURES, Permission.MANAGE_FACTURES, Permission.RECORD_PAYMENT,
        Permission.MANAGE_CAISSE,
        Permission.MANAGE_REPORTS, Permission.MANAGE_SETTINGS,
    }),
    "technicien": frozenset({
        Permission.VIEW_CLIENTS,
        Permission.VIEW_RENDEZ_VOUS,
        Permission.VIEW_DOSSIERS, Permission.MANAGE_DOSSIER,
        Permission.VALIDATE_QUALITY,
        Permission.VIEW_STOCK,
        Permission.VIEW_FACTURES,
    }),
}
