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

### Rapports Stock

| Rapport | Accès | Description |
|---|---|---|
| **Stock Valorisé** | Rapports → Stock Valorisé | Inventaire complet avec valeurs achat/vente |
| **Alertes Stock** | Rapports → Alertes Stock | Pièces sous le seuil minimum |
| **Fiche Stock (Pièce)** | Rapports → Fiche Stock (Pièce)… | Fiche détaillée d'une référence |
| **Fiche Fournisseur** | Rapports → Fiche Fournisseur… | Historique achats + créances fournisseur |

### Rapports Facturation

| Rapport | Accès | Description |
|---|---|---|
| **Facture Client** | Depuis la facture | Document de facturation officiel |
| **CA Mensuel** | Rapports → CA Mensuel… | Chiffre d'affaires mois par mois |
| **Créances Clients** | Rapports → Créances Clients | Liste des impayés par client |

---

## 6.2 Impression des rapports

### Impression directe

Pour tout rapport :

1. Ouvrez la fenêtre du rapport (aperçu HTML)
2. Vérifiez le contenu
3. Cliquez sur **Imprimer** dans la barre d'outils du rapport
4. La boîte de dialogue d'impression système s'ouvre
5. Choisissez l'imprimante et les options
6. Validez

### Aperçu avant impression

Cliquez sur **Aperçu avant impression** pour voir exactement ce qui sera imprimé avant d'envoyer à l'imprimante.

### Créer un PDF

Choisissez **Microsoft Print to PDF** comme imprimante pour créer un fichier PDF.

---

## 6.3 Format d'impression — Économie d'encre

Tous les rapports et documents (factures, fiches, états de stock…) sont générés avec un style **sans fond coloré** :

| Élément | Style |
|---|---|
| En-tête du document | Ligne de séparation seulement — pas de fond coloré |
| Titre de section | **Gras** + Souligné |
| En-têtes de colonnes | **Gras** + bordure basse épaisse |
| Ligne Total TTC | **Gras** + Souligné |
| Reste à payer | ***Gras Italique*** |
| Badges de statut | Encadrés en noir — pas de fond coloré |

> **Avantage** : Cette conception économise significativement l'encre d'impression. Une cartouche dure 3 à 4 fois plus longtemps qu'avec des fonds colorés. Idéal pour les garages qui impriment de nombreuses factures quotidiennement.

> **Compatibilité** : Les rapports sont générés en HTML compatible avec toutes les imprimantes A4 standard. Format recommandé : A4 Portrait pour les factures et fiches individuelles, A4 Paysage pour les états multi-colonnes.

---

## 6.4 Concepteur de Documents

**Menu Rapports → Concepteur de documents…** (admin uniquement)

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
| **Afficher le logo** | Active/désactive le logo société |
| **Afficher le nom** | Affiche la raison sociale |
| **Afficher le slogan** | Affiche "Solutions de Gestion sur Mesure" |

> **Note** : La couleur de bande n'est plus appliquée en fond (impression économique). Elle peut être utilisée pour le CSS personnalisé.

### Onglet Colonnes

Gérez les colonnes affichées dans le tableau de lignes :

- **Cocher/décocher** : affiche ou masque une colonne
- **Titre** : renommez l'en-tête de colonne
- **Largeur** : ajustez la largeur en pixels (-1 = étirable)
- **Alignement** : Gauche, Centre, ou Droite

### Onglet Totaux

Activez ou désactivez les lignes de totaux en bas du tableau :

| Option | Description |
|---|---|
| **Afficher HT** | Total Hors Taxes |
| **Afficher TVA** | Montant de la TVA |
| **Afficher TTC** | Total Toutes Taxes Comprises (gras + souligné) |
| **Afficher Payé** | Montant déjà payé |
| **Afficher Reste** | Solde restant à payer (gras italique) |

### Onglet Pied de page

| Option | Description |
|---|---|
| **Texte légal** | Mentions légales (ex : matricule fiscal, conditions) |
| **Numéro de page** | Affiche "Page 1" en bas |
| **CSS personnalisé** | Pour les utilisateurs avancés — styles CSS additionnels |

### Créer un nouveau modèle

1. Cliquez sur **+ Nouveau modèle**
2. Sélectionnez le **type de document** (Facture, Fiche réparation, etc.)
3. Donnez-lui un **nom** (ex : "Facture Garage Ben Salah")
4. Personnalisez les 4 onglets
5. Cliquez sur **Enregistrer**

Pour définir ce modèle comme modèle **par défaut** pour ce type de document, cochez **Modèle par défaut**.

### Dupliquer un modèle

Sélectionnez un modèle existant et cliquez sur **Dupliquer** pour créer une variation rapidement.
