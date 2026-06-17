from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from garage_app.domain.shared.aggregate_root import AggregateRoot
from garage_app.domain.shared.exceptions import BusinessRuleError, InvariantViolationError
from garage_app.domain.shared.value_objects import Money
from garage_app.domain.atelier.statut_dossier import StatutDossier
from garage_app.domain.atelier.ligne_diagnostic import LigneDiagnostic
from garage_app.domain.atelier.operation_mecanique import OperationMecanique
from garage_app.domain.atelier.piece_requise import PieceRequise
from garage_app.domain.atelier import events


@dataclass
class DossierReparation(AggregateRoot):
    """
    Core aggregate — state machine governing the full repair lifecycle.

    Créé → Diagnostic → EnAttenteDevis → EnCours → Qualité → Prêt → Clôturé
    """
    vehicule_id: uuid.UUID = field(default_factory=uuid.uuid4)
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    kilometrage_entree: int = 0
    statut: StatutDossier = StatutDossier.CREE
    lignes_diagnostic: list[LigneDiagnostic] = field(default_factory=list)
    operations: list[OperationMecanique] = field(default_factory=list)
    pieces: list[PieceRequise] = field(default_factory=list)
    devis_id: uuid.UUID | None = None
    facture_id: uuid.UUID | None = None
    notes: str = ""

    # ── Invariants ──────────────────────────────────────────────────────────

    def _assert_statut(self, *allowed: StatutDossier, action: str) -> None:
        if self.statut not in allowed:
            raise BusinessRuleError(
                f"Action '{action}' impossible depuis l'état '{self.statut.label_fr()}'."
            )

    @property
    def montant_pieces(self) -> Money:
        total = Money.zero()
        for p in self.pieces:
            total = total + p.montant
        return total

    @property
    def montant_main_oeuvre(self) -> Money:
        total = Money.zero()
        for op in self.operations:
            total = total + op.montant
        return total

    @property
    def montant_total_ht(self) -> Money:
        return self.montant_pieces + self.montant_main_oeuvre

    # ── State machine transitions ────────────────────────────────────────────

    def lancer_diagnostic(self) -> None:
        self._assert_statut(StatutDossier.CREE, action="lancer_diagnostic")
        self.statut = StatutDossier.DIAGNOSTIC
        self._raise_event(events.DiagnosticLance(dossier_id=self.id))

    def enregistrer_panne(self, ligne: LigneDiagnostic) -> None:
        self._assert_statut(StatutDossier.DIAGNOSTIC, action="enregistrer_panne")
        self.lignes_diagnostic.append(ligne)
        self._raise_event(events.PanneIdentifiee(dossier_id=self.id, code_defaut=ligne.code_defaut))

    def soumettre_au_devis(self) -> None:
        self._assert_statut(StatutDossier.DIAGNOSTIC, action="soumettre_au_devis")
        if not self.lignes_diagnostic:
            raise InvariantViolationError(
                "Au moins une panne doit être identifiée avant d'établir un devis."
            )
        self.statut = StatutDossier.EN_ATTENTE_DEVIS
        self._raise_event(events.DossierSoumisAuDevis(dossier_id=self.id))

    def approuver_devis(self, devis_id: uuid.UUID) -> None:
        """Règle Strict-Accord: cannot start repair without approved devis."""
        self._assert_statut(StatutDossier.EN_ATTENTE_DEVIS, action="approuver_devis")
        self.devis_id = devis_id
        self.statut = StatutDossier.EN_COURS
        self._raise_event(events.DevisApprouve(dossier_id=self.id, devis_id=devis_id))

    def refuser_devis(self) -> None:
        self._assert_statut(StatutDossier.EN_ATTENTE_DEVIS, action="refuser_devis")
        self.statut = StatutDossier.CLOTURE
        self._raise_event(events.DevisRefuse(dossier_id=self.id))

    def ajouter_operation(self, operation: OperationMecanique) -> None:
        self._assert_statut(StatutDossier.EN_COURS, action="ajouter_operation")
        self.operations.append(operation)

    def ajouter_piece(self, piece: PieceRequise) -> None:
        self._assert_statut(StatutDossier.EN_COURS, action="ajouter_piece")
        self.pieces.append(piece)

    def signaler_nouvelle_panne(self, ligne: LigneDiagnostic) -> None:
        """Règle Avenant-Obligatoire: mid-repair new issue requires a new devis."""
        self._assert_statut(StatutDossier.EN_COURS, action="signaler_nouvelle_panne")
        self.lignes_diagnostic.append(ligne)
        self.statut = StatutDossier.EN_ATTENTE_DEVIS
        self._raise_event(events.DevisComplementaireCree(dossier_id=self.id))

    def terminer_reparation(self) -> None:
        self._assert_statut(StatutDossier.EN_COURS, action="terminer_reparation")
        taches_incompletes = [op for op in self.operations if not op.est_terminee]
        if taches_incompletes:
            raise InvariantViolationError(
                f"{len(taches_incompletes)} tâche(s) non terminée(s). "
                "Impossible de passer en contrôle qualité."
            )
        self.statut = StatutDossier.QUALITE
        self._raise_event(events.ReparationTerminee(dossier_id=self.id))

    def valider_controle_qualite(self) -> None:
        """Règle Garantie-Qualité: must be validated before invoice can be generated."""
        self._assert_statut(StatutDossier.QUALITE, action="valider_controle_qualite")
        self.statut = StatutDossier.PRET
        self._raise_event(events.ControleQualiteValide(dossier_id=self.id))

    def generer_facture(self, facture_id: uuid.UUID, montant_ttc: Decimal) -> None:
        """Règle Garantie-Qualité: requires ContrôleQualitéValidé (statut PRET)."""
        self._assert_statut(StatutDossier.PRET, action="generer_facture")
        self.facture_id = facture_id
        self.statut = StatutDossier.CLOTURE
        self._raise_event(events.FactureGeneree(
            dossier_id=self.id, facture_id=facture_id, montant_ttc=montant_ttc
        ))
