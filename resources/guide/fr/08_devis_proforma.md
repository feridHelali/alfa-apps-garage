# 8. Devis Commerciaux et Factures Proforma

---

## 8.1 Vue d'ensemble

Le module **Devis / Proforma** couvre le cycle commercial **avant-vente** :

```
Devis (brouillon) ──► Envoyé ──► Accepté ──► Dossier de Réparation
                                    └──────► Facture Proforma ──► Facture Client
                              Refusé (dupliquer pour révision)
```

Ce module est accessible aux techniciens (lecture) et aux administrateurs (gestion complète).

---

## 8.2 Devis commerciaux

### Accéder aux devis

- Menu **Atelier → Devis commerciaux…** ou `Ctrl+W`

### Créer un devis

1. Cliquez sur **+ Nouveau devis**
2. Sélectionnez le **client** dans la liste
3. Sélectionnez le **véhicule** du client (obligatoire pour la conversion en dossier)
4. Définissez une **date d'expiration** (30 jours par défaut)
5. Saisissez les **notes client** (description des travaux demandés)
6. Ajoutez les **lignes** :

| Champ | Description |
|---|---|
| Type | Service / Pièce / Forfait |
| Désignation | Description de la prestation |
| Quantité | Nombre d'unités |
| Prix unitaire HT | Prix sans TVA |
| TVA | Taux applicable (19% par défaut) |
| Remise | Réduction en % (facultatif) |

7. Vérifiez les totaux (HT, TVA, TTC) en bas du formulaire
8. Cliquez sur **Enregistrer**

Le devis est créé à l'état **BROUILLON** avec un numéro automatique (ex : `DEV-2026-0001`).

> **Conseil** : Les notes internes ne sont pas imprimées sur le devis remis au client — utilisez-les pour les détails techniques ou les négociations.

---

## 8.3 Cycle de vie d'un devis

| État | Couleur | Signification |
|---|---|---|
| **BROUILLON** | Gris | En cours de préparation — modifiable |
| **ENVOYÉ** | Bleu | Remis au client pour approbation |
| **ACCEPTÉ** | Vert | Accord du client obtenu |
| **REFUSÉ** | Rouge | Client a refusé le devis |
| **TRANSFORMÉ** | Cyan | Converti en dossier ou proforma |
| **EXPIRÉ** | Jaune | Date d'expiration dépassée sans réponse |
| **ANNULÉ** | Sombre | Annulé manuellement |

### Transitions disponibles

| Depuis | Action | Vers |
|---|---|---|
| BROUILLON | **Envoyer au client** | ENVOYÉ |
| ENVOYÉ | **Accepter** | ACCEPTÉ |
| ENVOYÉ | **Refuser** (avec motif) | REFUSÉ |
| ACCEPTÉ | **→ Dossier** | TRANSFORMÉ + Dossier créé |
| ACCEPTÉ | **→ Proforma** | TRANSFORMÉ + Proforma créée |
| BROUILLON / ENVOYÉ | **Annuler** | ANNULÉ |
| Tout état | **Dupliquer** | Nouveau BROUILLON (révision) |

---

## 8.4 Convertir un devis en dossier de réparation

Lorsque le client accepte le devis :

1. Sélectionnez le devis dans la liste
2. Cliquez sur **Accepter** (si pas encore fait)
3. Cliquez sur **→ Dossier**
4. Confirmez dans la boîte de dialogue

Un **Dossier de Réparation** est créé automatiquement avec :
- Le client et le véhicule du devis
- Les notes client comme description initiale
- L'état **CRÉÉ** (prêt pour le diagnostic)

> **Note** : Le devis passe à l'état **TRANSFORMÉ** et reste consultable. Retrouvez le dossier dans **Atelier → Dossiers de réparation**.

---

## 8.5 Convertir un devis en facture proforma

Pour les clients professionnels qui ont besoin d'un engagement écrit avant paiement :

1. Sélectionnez le devis **ACCEPTÉ**
2. Cliquez sur **→ Proforma**
3. La facture proforma s'ouvre automatiquement

La proforma reprend toutes les lignes du devis avec les mêmes montants.

> **Rappel** : Une facture proforma n'a **pas de valeur comptable**. Elle sert uniquement d'engagement ou de demande d'acompte. La facture définitive est émise après clôture du dossier.

---

## 8.6 Factures Proforma

### Accéder aux proformas

- Menu **Facturation → Factures proforma…**

### Vue d'ensemble d'une proforma

La fenêtre d'aperçu proforma affiche :
- Le numéro (ex : `PRO-2026-0001`)
- Le tableau de lignes avec montants HT et TTC
- Le total TTC
- L'acompte reçu et le solde restant
- Le statut (Émise / Acompte reçu / Liée à facture / Annulée)

### Enregistrer un acompte

1. Ouvrez la facture proforma
2. Cliquez sur **Enregistrer un acompte…**
3. Saisissez le montant reçu
4. Cliquez sur **OK**

Le statut passe à **ACOMPTE REÇU** et le solde restant est mis à jour.

### Numérotation

Les devis et proformas ont leur propre numérotation configurable :

| Document | Séquence par défaut |
|---|---|
| Devis | `DEV-{ANNEE}-0001` |
| Proforma | `PRO-{ANNEE}-0001` |

Configurez le préfixe et le prochain numéro via **Administration → Numérotation**.

---

## 8.7 Imprimer un devis ou une proforma

### Devis

1. Sélectionnez le devis dans la liste
2. Cliquez sur **Imprimer**
3. La boîte de dialogue d'impression système s'ouvre

### Proforma

1. Ouvrez la proforma (double-clic dans la liste)
2. Cliquez sur **Imprimer…** dans la fenêtre d'aperçu

> **Format** : Les documents sont générés en HTML avec styles inline — imprimables en A4 Portrait directement depuis l'application.

---

## 8.8 Cas pratique — Devis carrosserie

**Scénario** : Un client amène sa voiture pour une réparation de carrosserie après un accident.

1. **Réception** : Créer un **rendez-vous** ou accueillir directement le client
2. **Devis** : Créer un devis avec :
   - Ligne 1 : Débosselage aile avant — 120,000 DT HT
   - Ligne 2 : Peinture aile avant (pièce + pose) — 350,000 DT HT
   - Ligne 3 : Remplacement phare — 180,000 DT HT
3. **Envoi** : Cliquer sur **Envoyer au client** et remettre le document
4. **Acceptation** : Le client accepte — cliquer sur **Accepter**
5. **Dossier** : Cliquer sur **→ Dossier** pour démarrer les travaux
6. **Facturation** : En fin de réparation, le dossier génère automatiquement la facture

**Pour les flottes professionnelles** :
- À l'étape 4, cliquer sur **→ Proforma** au lieu de Dossier
- Envoyer la proforma au service comptabilité du client pour paiement d'acompte
- Une fois l'acompte reçu, enregistrer l'acompte sur la proforma
- Créer ensuite le dossier de réparation manuellement
