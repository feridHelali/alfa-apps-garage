# 6. Rapports et Concepteur de Documents

---

## 6.1 Rapports disponibles

Tous les rapports sont accessibles via le menu **Rapports**.

### Rapports Réception

| Rapport | Accès | Description |
|---|---|---|
| **Fiche Client** | Rapports → Fiche Client… | Profil complet + historique du client |
| **Carnet de Route** | Rapports → Carnet de Route… | Historique d'entretien d'un véhicule |

### Rapports Atelier

| Rapport | Accès | Description |
|---|---|---|
| **Fiche Réparation** | Rapports → Fiche Réparation… | Rapport détaillé d'un dossier |
| **Bon de Travail** | Depuis le dossier | Document remis au technicien |
| **Dossiers en cours** | Rapports → Dossiers en cours | Tableau de bord des dossiers actifs |

### Rapports Stock

| Rapport | Accès | Description |
|---|---|---|
| **État du Stock** | Rapports → État du Stock | Inventaire complet avec alertes |
| **Mouvements de Stock** | Rapports → Mouvements… | Entrées/sorties par période |

### Rapports Facturation

| Rapport | Accès | Description |
|---|---|---|
| **Facture Client** | Depuis la facture | Document de facturation officiel |
| **Rapport de Ventes** | Rapports → Ventes… | CA par période et par type |
| **Créances** | Rapports → Créances | Liste des impayés |
| **Bilan Mensuel** | Rapports → Bilan… | CA vs Charges = Résultat net |

---

## 6.2 Imprimer un rapport

Pour tout rapport :

1. Ouvrez la fenêtre du rapport (aperçu HTML)
2. Vérifiez le contenu
3. Cliquez sur **Imprimer** dans la barre d'outils du rapport
4. La boîte de dialogue d'impression système s'ouvre
5. Choisissez l'imprimante et les options
6. Validez

> **Conseil** : Pour créer un PDF, choisissez **Microsoft Print to PDF** ou **PDF Creator** comme imprimante.

---

## 6.3 Concepteur de Documents

Menu **Rapports → Concepteur de documents…** (admin uniquement)

Le Concepteur de Documents vous permet de personnaliser l'apparence de tous vos documents imprimables sans aucune compétence en programmation.

### Interface du Concepteur

Le Concepteur est divisé en **3 panneaux** :

```
┌─────────────────┬──────────────────────────┬─────────────────────┐
│  Liste modèles  │     Éditeur (4 onglets)  │  Aperçu en direct  │
│                 │  ┌─────┬──────┬────┬───┐ │                     │
│  [+] Nouveau    │  │Entê.│Colon.│Tot.│Pie│ │  [rendu HTML]       │
│  Facture client │  └─────┴──────┴────┴───┘ │                     │
│  Fiche répar.   │                           │  Rafraîchi 500ms    │
│  Bon de travail │                           │  après chaque       │
│  Facture achat  │                           │  modification       │
└─────────────────┴──────────────────────────┴─────────────────────┘
```

### Onglet En-tête

Personnalisez la partie haute du document :

| Option | Description |
|---|---|
| **Couleur principale** | Couleur de fond de l'en-tête (bandeau) |
| **Afficher le logo** | Active/désactive le logo Alfa Computers |
| **Afficher le nom** | Affiche la raison sociale |
| **Afficher le slogan** | Affiche "Solutions de Gestion sur Mesure" |

> **Conseil** : Choisissez une couleur cohérente avec l'identité visuelle de votre garage (ex : bleu `#0055a5` pour un garage Renault, rouge pour Toyota...).

### Onglet Colonnes

Gérez les colonnes affichées dans le tableau de lignes :

- **Cocher/décocher** : affiche ou masque une colonne
- **Titre** : renommez l'en-tête de colonne (ex : "Désignation" → "Description de la pièce")
- **Largeur** : ajustez la largeur relative (en %)
- **Alignement** : Gauche, Centre, ou Droite

### Onglet Totaux

Activez ou désactivez les lignes de totaux en bas du tableau :

| Option | Description |
|---|---|
| **Afficher HT** | Total Hors Taxes |
| **Afficher TVA** | Montant de la TVA |
| **Afficher TTC** | Total Toutes Taxes Comprises |
| **Afficher Payé** | Montant déjà payé |
| **Afficher Reste** | Solde restant à payer |

### Onglet Pied de page

| Option | Description |
|---|---|
| **Texte légal** | Mentions légales (ex : matricule fiscal, conditions) |
| **Numéro de page** | Affiche "Page X / Y" en bas |
| **CSS personnalisé** | Pour les utilisateurs avancés — styles CSS additionnels |

### Créer un nouveau modèle

1. Cliquez sur **+ Nouveau modèle**
2. Sélectionnez le **type de document** (Facture, Fiche réparation, etc.)
3. Donnez-lui un **nom** (ex : "Facture Pro Bleu")
4. Personnalisez les 4 onglets
5. Cliquez sur **Enregistrer**

Pour définir ce modèle comme modèle **par défaut** pour ce type de document, cochez **Modèle par défaut**.

### Dupliquer un modèle

Sélectionnez un modèle existant et cliquez sur **Dupliquer** pour créer une variation rapidement.

---

## 6.4 Formats et compatibilité

Les rapports sont générés en **HTML** avec des styles inline, compatibles avec :

- **Impression directe** via Qt (sans navigateur)
- **Microsoft Print to PDF** (Windows)
- **Imprimantes A4** standard

> **Format recommandé** : A4, orientation Portrait pour les factures et fiches réparation. Paysage pour les rapports multi-colonnes (état du stock, rapport de ventes).
