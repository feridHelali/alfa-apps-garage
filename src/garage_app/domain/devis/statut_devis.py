from enum import StrEnum


class StatutDevis(StrEnum):
    BROUILLON = "brouillon"
    ENVOYE = "envoye"
    ACCEPTE = "accepte"
    REFUSE = "refuse"
    TRANSFORME = "transforme"
    EXPIRE = "expire"
    ANNULE = "annule"

    def label_fr(self) -> str:
        return {
            self.BROUILLON: "Brouillon",
            self.ENVOYE: "Envoyé",
            self.ACCEPTE: "Accepté",
            self.REFUSE: "Refusé",
            self.TRANSFORME: "Transformé",
            self.EXPIRE: "Expiré",
            self.ANNULE: "Annulé",
        }[self]

    def color(self) -> str:
        return {
            self.BROUILLON: "#6c757d",
            self.ENVOYE: "#0d6efd",
            self.ACCEPTE: "#198754",
            self.REFUSE: "#dc3545",
            self.TRANSFORME: "#0dcaf0",
            self.EXPIRE: "#ffc107",
            self.ANNULE: "#343a40",
        }[self]

    def peut_modifier(self) -> bool:
        return self == self.BROUILLON

    def peut_envoyer(self) -> bool:
        return self == self.BROUILLON

    def peut_accepter(self) -> bool:
        return self == self.ENVOYE

    def peut_refuser(self) -> bool:
        return self == self.ENVOYE

    def peut_convertir(self) -> bool:
        return self == self.ACCEPTE

    def peut_annuler(self) -> bool:
        return self in (self.BROUILLON, self.ENVOYE)


class TypeLigne(StrEnum):
    SERVICE = "service"
    PIECE = "piece"
    FORFAIT = "forfait"

    def label_fr(self) -> str:
        return {self.SERVICE: "Service", self.PIECE: "Pièce", self.FORFAIT: "Forfait"}[self]


class StatutProforma(StrEnum):
    EMISE = "emise"
    ACOMPTE_RECU = "acompte_recu"
    LIEE_FACTURE = "liee_facture"
    ANNULEE = "annulee"

    def label_fr(self) -> str:
        return {
            self.EMISE: "Émise",
            self.ACOMPTE_RECU: "Acompte reçu",
            self.LIEE_FACTURE: "Liée à facture",
            self.ANNULEE: "Annulée",
        }[self]

    def color(self) -> str:
        return {
            self.EMISE: "#0d6efd",
            self.ACOMPTE_RECU: "#ffc107",
            self.LIEE_FACTURE: "#198754",
            self.ANNULEE: "#dc3545",
        }[self]
