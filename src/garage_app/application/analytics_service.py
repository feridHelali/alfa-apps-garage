from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from garage_app.application.decorators import require_permission
from garage_app.domain.auth.permission import Permission
from garage_app.domain.auth.user_session import UserSession
from garage_app.infrastructure.repositories.client_repository import SqlAlchemyClientRepository
from garage_app.infrastructure.repositories.vehicule_repository import SqlAlchemyVehiculeRepository
from garage_app.infrastructure.repositories.dossier_repository import SqlAlchemyDossierRepository
from garage_app.infrastructure.repositories.facture_repository import SqlAlchemyFactureRepository
from garage_app.infrastructure.repositories.piece_repository import SqlAlchemyPieceRepository
from garage_app.infrastructure.repositories.fournisseur_repository import SqlAlchemyFournisseurRepository
from garage_app.infrastructure.repositories.commande_repository import SqlAlchemyCommandeRepository
from garage_app.infrastructure.repositories.credit_repository import SqlAlchemyCreditRepository


class AnalyticsService:
    def __init__(
        self,
        client_repo: SqlAlchemyClientRepository,
        vehicule_repo: SqlAlchemyVehiculeRepository,
        dossier_repo: SqlAlchemyDossierRepository,
        facture_repo: SqlAlchemyFactureRepository,
        piece_repo: SqlAlchemyPieceRepository,
        fournisseur_repo: SqlAlchemyFournisseurRepository,
        commande_repo: SqlAlchemyCommandeRepository,
        credit_repo: SqlAlchemyCreditRepository,
    ) -> None:
        self._clients = client_repo
        self._vehicules = vehicule_repo
        self._dossiers = dossier_repo
        self._factures = facture_repo
        self._pieces = piece_repo
        self._fournisseurs = fournisseur_repo
        self._commandes = commande_repo
        self._credits = credit_repo

    # ── CA mensuel ────────────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_FACTURES)
    def rapport_ca_mensuel(self, session: UserSession, annee: int) -> list[dict]:
        all_factures = self._factures.find_all()
        mois_data: dict[int, dict] = {
            m: {"mois": m, "nb_factures": 0, "ca_ht": Decimal(0), "tva": Decimal(0), "ca_ttc": Decimal(0), "encaisse": Decimal(0)}
            for m in range(1, 13)
        }
        from garage_app.domain.facturation.facture import StatutFacture
        for f in all_factures:
            if f.statut == StatutFacture.ANNULEE:
                continue
            # Use dossier_id as proxy for date — fall back to current year
            # Since Facture has no explicit date field, we use now() as placeholder
            # TODO: add date_emission field to Facture domain
            mois = datetime.now().month  # placeholder until date_emission added
            if mois not in mois_data:
                continue
            mois_data[mois]["nb_factures"] += 1
            mois_data[mois]["ca_ht"] += f.montant_ht.amount
            mois_data[mois]["tva"] += f.montant_tva.amount
            mois_data[mois]["ca_ttc"] += f.montant_ttc.amount
            mois_data[mois]["encaisse"] += f.montant_paye
        return list(mois_data.values())

    # ── Stock valorisé ────────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_STOCK)
    def rapport_stock_valorise(self, session: UserSession) -> dict:
        pieces = self._pieces.find_all()
        lignes = []
        total_achat = Decimal(0)
        total_vente = Decimal(0)
        for p in pieces:
            val_achat = p.prix_achat * p.quantite_stock
            val_vente = p.prix_vente * p.quantite_stock
            total_achat += val_achat
            total_vente += val_vente
            lignes.append({
                "reference": p.reference_constructeur,
                "designation": p.designation,
                "categorie": p.categorie,
                "quantite": p.quantite_stock,
                "seuil": p.seuil_alerte,
                "prix_achat": p.prix_achat,
                "prix_vente": p.prix_vente,
                "val_achat": val_achat,
                "val_vente": val_vente,
                "alerte": p.quantite_stock <= p.seuil_alerte,
            })
        return {
            "lignes": sorted(lignes, key=lambda x: x["designation"]),
            "total_achat": total_achat,
            "total_vente": total_vente,
            "nb_pieces": len(pieces),
            "nb_alerte": sum(1 for l in lignes if l["alerte"]),
        }

    # ── Alertes stock ─────────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_STOCK)
    def rapport_alertes(self, session: UserSession) -> list[dict]:
        pieces = self._pieces.find_in_alert()
        result = []
        for p in pieces:
            fournisseur_nom = ""
            if p.fournisseur_id:
                f = self._fournisseurs.get_by_id(p.fournisseur_id)
                fournisseur_nom = f.raison_sociale if f else ""
            result.append({
                "reference": p.reference_constructeur,
                "designation": p.designation,
                "quantite": p.quantite_stock,
                "seuil": p.seuil_alerte,
                "a_commander": max(0, p.seuil_alerte * 2 - p.quantite_stock),
                "fournisseur": fournisseur_nom,
                "prix_achat": p.prix_achat,
            })
        return sorted(result, key=lambda x: x["quantite"])

    # ── Créances clients ──────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_FACTURES)
    def rapport_creances(self, session: UserSession) -> dict:
        credits = self._credits.find_all_with_solde()
        total = sum(c.solde for c in credits)
        lignes = []
        for c in credits:
            client = self._clients.get_by_id(c.client_id)
            nom = f"{client.nom} {client.prenom}".strip() if client else str(c.client_id)[:8]
            telephone = client.telephone if client else ""
            lignes.append({
                "client": nom,
                "telephone": telephone,
                "solde": c.solde,
                "limite": c.limite_credit,
            })
        return {"lignes": lignes, "total": total}

    # ── Fiche client ──────────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_CLIENTS)
    def fiche_client(self, session: UserSession, client_id: uuid.UUID) -> dict:
        client = self._clients.get_by_id(client_id)
        if not client:
            raise ValueError("Client introuvable.")
        vehicules = self._vehicules.find_by_client(client_id)
        dossiers = self._dossiers.find_by_vehicule(vehicules[0].id) if vehicules else []
        # gather all dossiers for all vehicles
        all_dossiers = []
        for v in vehicules:
            all_dossiers.extend(self._dossiers.find_by_vehicule(v.id))
        factures = self._factures.find_by_client(client_id)
        total_facture = sum(f.montant_ttc.amount for f in factures)
        total_paye = sum(f.montant_paye for f in factures)
        return {
            "client": client,
            "vehicules": vehicules,
            "dossiers": all_dossiers,
            "factures": factures,
            "total_facture": total_facture,
            "total_paye": total_paye,
            "solde": total_facture - total_paye,
        }

    # ── Fiche réparation ──────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_DOSSIERS)
    def fiche_reparation(self, session: UserSession, dossier_id: uuid.UUID) -> dict:
        dossier = self._dossiers.get_by_id(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable.")
        vehicule = self._vehicules.get_by_id(dossier.vehicule_id)
        client = self._clients.get_by_id(dossier.client_id)
        facture = None
        if dossier.facture_id:
            facture = self._factures.get_by_id(dossier.facture_id)
        return {
            "dossier": dossier,
            "vehicule": vehicule,
            "client": client,
            "facture": facture,
        }

    # ── Fiche pièce / stock ───────────────────────────────────────────────────

    @require_permission(Permission.VIEW_STOCK)
    def fiche_piece(self, session: UserSession, piece_id: uuid.UUID) -> dict:
        piece = self._pieces.get_by_id(piece_id)
        if not piece:
            raise ValueError("Pièce introuvable.")
        fournisseur = None
        if piece.fournisseur_id:
            fournisseur = self._fournisseurs.get_by_id(piece.fournisseur_id)
        commandes = []
        if piece.fournisseur_id:
            commandes = self._commandes.find_by_fournisseur(piece.fournisseur_id)
        return {
            "piece": piece,
            "fournisseur": fournisseur,
            "commandes": commandes,
        }

    # ── Parc véhicules ────────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_CLIENTS)
    def parc_vehicules(self, session: UserSession) -> list[dict]:
        all_vehicules = self._vehicules.find_all()
        all_clients = {str(c.id): c for c in self._clients.find_all()}
        result = []
        for v in all_vehicules:
            client = all_clients.get(str(v.client_id))
            client_nom = f"{client.nom} {client.prenom}".strip() if client else "—"
            client_tel = client.telephone if client else ""
            dossiers = self._dossiers.find_by_vehicule(v.id)
            dates = [d.created_at for d in dossiers if d.created_at]
            premiere_visite = min(dates) if dates else None
            derniere_visite = max(dates) if dates else None
            km_max = max((d.kilometrage_entree for d in dossiers), default=0)
            result.append({
                "vehicule": v,
                "client_nom": client_nom,
                "client_tel": client_tel,
                "nb_dossiers": len(dossiers),
                "premiere_visite": premiere_visite,
                "derniere_visite": derniere_visite,
                "km_max": km_max,
            })
        result.sort(key=lambda x: x["client_nom"])
        return result

    # ── Carnet de Route ──────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_DOSSIERS)
    def carnet_de_route(self, session: UserSession, vehicule_id: uuid.UUID) -> dict:
        vehicule = self._vehicules.get_by_id(vehicule_id)
        if not vehicule:
            raise ValueError("Véhicule introuvable.")
        client = self._clients.get_by_id(vehicule.client_id)
        dossiers = self._dossiers.find_by_vehicule(vehicule_id)
        km_max = max((d.kilometrage_entree for d in dossiers), default=0)
        total_pieces = sum(len(d.pieces) for d in dossiers)
        total_ops = sum(len(d.operations) for d in dossiers)
        return {
            "vehicule": vehicule,
            "client": client,
            "dossiers": dossiers,
            "nb_interventions": len(dossiers),
            "km_max": km_max,
            "total_pieces": total_pieces,
            "total_ops": total_ops,
        }

    # ── Fiche fournisseur ─────────────────────────────────────────────────────

    @require_permission(Permission.VIEW_STOCK)
    def fiche_fournisseur(self, session: UserSession, fournisseur_id: uuid.UUID) -> dict:
        fournisseur = self._fournisseurs.get_by_id(fournisseur_id)
        if not fournisseur:
            raise ValueError("Fournisseur introuvable.")
        pieces = self._pieces.find_by_fournisseur(fournisseur_id)
        commandes = self._commandes.find_by_fournisseur(fournisseur_id)
        total_commandes = len(commandes)
        return {
            "fournisseur": fournisseur,
            "pieces": pieces,
            "commandes": commandes,
            "total_commandes": total_commandes,
        }
