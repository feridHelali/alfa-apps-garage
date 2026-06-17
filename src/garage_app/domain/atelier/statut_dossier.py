from enum import StrEnum


class StatutDossier(StrEnum):
    CREE = "cree"
    DIAGNOSTIC = "diagnostic"
    EN_ATTENTE_DEVIS = "en_attente_devis"
    EN_COURS = "en_cours"
    QUALITE = "qualite"
    PRET = "pret"
    CLOTURE = "cloture"

    def label_fr(self) -> str:
        return {
            self.CREE: "Créé",
            self.DIAGNOSTIC: "Diagnostic",
            self.EN_ATTENTE_DEVIS: "Attente devis",
            self.EN_COURS: "En cours",
            self.QUALITE: "Contrôle qualité",
            self.PRET: "Prêt",
            self.CLOTURE: "Clôturé",
        }[self]

    def color(self) -> str:
        return {
            self.CREE: "#6c757d",
            self.DIAGNOSTIC: "#0d6efd",
            self.EN_ATTENTE_DEVIS: "#ffc107",
            self.EN_COURS: "#fd7e14",
            self.QUALITE: "#0dcaf0",
            self.PRET: "#198754",
            self.CLOTURE: "#343a40",
        }[self]


class StatutTache(StrEnum):
    A_FAIRE = "a_faire"
    EN_COURS = "en_cours"
    TERMINEE = "terminee"


class StatutDispo(StrEnum):
    EN_STOCK = "en_stock"
    COMMANDE = "commande"
    RECU = "recu"


class GravitePanne(StrEnum):
    BLOQUANT = "bloquant"
    A_SURVEILLER = "a_surveiller"
    INFO = "info"
