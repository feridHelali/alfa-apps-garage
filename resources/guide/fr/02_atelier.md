# 2. Atelier — Dossiers de Réparation

---

## 2.1 Cycle de vie d'un dossier

Un dossier de réparation suit un cycle d'états défini. Chaque étape représente l'avancement réel du travail dans le garage.

![Cycle de vie d'un dossier](img/dossier_state_machine.svg)

| État | Couleur | Description |
|---|---|---|
| **CRÉÉ** | Vert | Dossier ouvert à la réception du véhicule |
| **DIAGNOSTIC** | Bleu | Technicien en cours de diagnostic |
| **ATTENTE DEVIS** | Orange | En attente d'accord du client sur le devis |
| **EN COURS** | Orange vif | Travaux en cours |
| **QUALITÉ** | Cyan | Contrôle qualité avant restitution |
| **PRÊT** | Vert foncé | Véhicule prêt, client prévenu |
| **CLÔTURÉ** | Gris | Réparation terminée et facturée |

---

## 2.2 Créer un dossier de réparation

### Accéder aux dossiers

- Menu **Atelier → Dossiers de réparation** ou `Ctrl+D`
- Bouton **Dossiers** dans la sidebar

### Étapes de création

1. Cliquez sur **+ Nouveau dossier**
2. Sélectionnez le **client** (ou créez-en un nouveau via le bouton +)
3. Sélectionnez le **véhicule** du client
4. Saisissez le **kilométrage à l'entrée**
5. Ajoutez une description des **plaintes du client** dans le champ notes
6. Cliquez sur **Enregistrer**

Le dossier est créé à l'état **CRÉÉ** et un numéro lui est attribué automatiquement (ex : `REP-0042`).

> **Conseil** : Notez toujours le kilométrage à l'entrée — il sera affiché dans la fiche réparation et le carnet de route.

---

## 2.3 Avancement des travaux

### Passer au Diagnostic

1. Ouvrez le dossier
2. Cliquez sur **Démarrer le diagnostic**
3. Dans l'onglet **Diagnostic**, ajoutez les lignes de diagnostic :
   - Description du problème constaté
   - Gravité : `BLOQUANT`, `À SURVEILLER`, `INFO`

### Passer en Attente de Devis

1. Depuis l'état DIAGNOSTIC, cliquez sur **Attente devis**
2. Le client est notifié pour accord

### Démarrer les travaux

1. Une fois l'accord du client obtenu, cliquez sur **Démarrer les travaux**
2. Le dossier passe à l'état **EN COURS**
3. Dans l'onglet **Opérations**, ajoutez les travaux effectués :
   - Désignation de l'opération
   - Durée estimée
   - Montant de la main d'œuvre

### Ajouter des pièces

Dans l'onglet **Pièces** :

1. Cliquez sur **+ Ajouter une pièce**
2. Recherchez la pièce dans le catalogue
3. Indiquez la quantité
4. Le stock est automatiquement réservé

> **Conseil** : Si une pièce n'est pas en stock, vous pouvez créer une **commande fournisseur** directement depuis le dossier.

### Contrôle qualité

1. Cliquez sur **Terminer les travaux**
2. Le dossier passe en **QUALITÉ**
3. Effectuez la vérification finale
4. Cliquez sur **Valider la qualité** → état **PRÊT**
5. Prévenez le client que son véhicule est prêt

### Clôturer et facturer

1. Depuis l'état **PRÊT**, cliquez sur **Générer la facture**
2. Le dossier passe en **CLÔTURÉ**
3. La facture est créée automatiquement avec toutes les opérations et pièces

---

## 2.4 Bon de travail rapide

Pour les interventions simples et rapides (vidange, gonflage, etc.) :

- Menu **Atelier → Bon de travail rapide** ou `Ctrl+R`
- Bouton **Rapide** dans la sidebar

Le bon de travail rapide permet de créer et facturer une intervention en une seule étape, sans passer par les étapes du dossier complet.

**Champs :**
- Client et véhicule
- Description de l'intervention
- Pièces utilisées
- Main d'œuvre
- **Bouton « Facturer directement »** : génère une facture immédiatement

---

## 2.5 Rapport — Fiche Réparation

Menu **Rapports → Fiche Réparation…**

Sélectionnez un dossier pour générer un rapport PDF complet :
- Informations client et véhicule
- Kilométrage entrée/sortie
- Détail des diagnostics
- Opérations effectuées avec technicien et durée
- Pièces remplacées avec références
- Montant total

> **Conseil** : Remettez la fiche réparation au client avec son véhicule — c'est un gage de professionnalisme et un document de traçabilité.
