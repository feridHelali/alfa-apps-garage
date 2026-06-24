# 4. Facturation — Factures, Caisse et Créances

---

## 4.1 Cycle de vie d'une facture

![Cycle de vie d'une facture](img/facture_lifecycle.svg)

| État | Description |
|---|---|
| **BROUILLON** | Facture en cours de saisie, modifiable |
| **ÉMISE** | Facture finalisée, remise au client |
| **PART. PAYÉE** | Acompte reçu, solde restant |
| **PAYÉE** | Facture intégralement encaissée |
| **ANNULÉE** | Facture annulée (ne peut pas être modifiée) |

---

## 4.2 Créer une facture

### Accéder aux factures

- Menu **Facturation → Factures** ou `Ctrl+F`
- Bouton **Facturation** dans la sidebar

### Création automatique depuis un dossier

Lorsqu'un dossier de réparation est clôturé, une facture est générée automatiquement avec :
- Toutes les opérations de main d'œuvre
- Toutes les pièces remplacées
- La numérotation automatique configurée

### Création manuelle

1. Cliquez sur **+ Nouvelle facture**
2. Sélectionnez le **client**
3. Ajoutez les lignes de facturation :
   - **Type** : Service, Pièce, ou Forfait
   - **Désignation** du prestation
   - **Quantité** et **Prix unitaire HT**
   - **TVA** applicable
4. Vérifiez les totaux (HT, TVA, TTC)
5. Cliquez sur **Émettre la facture** pour la finaliser

> **Attention** : Une facture émise ne peut plus être modifiée. Vérifiez bien avant d'émettre.

---

## 4.3 Imprimer une facture

1. Ouvrez la facture
2. Cliquez sur **Imprimer / Aperçu**
3. La facture s'affiche en aperçu HTML fidèle au modèle configuré
4. Utilisez **Ctrl+P** dans l'aperçu pour imprimer

> **Conseil** : Le modèle de facture est personnalisable via **Rapports → Concepteur de documents**. Ajustez les couleurs, le logo, les colonnes et les mentions légales selon vos préférences.

---

## 4.4 Encaisser un paiement

### Depuis la facture

1. Ouvrez la facture émise
2. Cliquez sur **Enregistrer un paiement**
3. Saisissez :
   - **Montant** encaissé
   - **Mode de paiement** : Espèces, Chèque, Virement, Carte
   - **Date** du paiement
   - **Référence** (numéro de chèque, etc.)
4. Cliquez sur **Valider**

Si le montant est inférieur au total, la facture passe en **PART. PAYÉE**.
Si le montant couvre le total, la facture passe en **PAYÉE**.

### Session de caisse

Menu **Facturation → Caisse**

La session de caisse enregistre tous les mouvements d'espèces :

1. Cliquez sur **Ouvrir la caisse** (entrez le fond de caisse)
2. Enregistrez les encaissements et décaissements au fil de la journée
3. En fin de journée, cliquez sur **Clôturer la caisse**
4. Saisissez le montant comptabilisé
5. L'écart est calculé automatiquement

---

## 4.5 Créances clients

Menu **Facturation → Créances clients**

La liste des créances affiche toutes les factures non intégralement payées :

| Colonne | Description |
|---|---|
| Client | Nom du client débiteur |
| N° Facture | Référence de la facture |
| Date | Date d'émission |
| Montant TTC | Montant total de la facture |
| Payé | Total des paiements reçus |
| Reste | Solde dû |
| Jours | Ancienneté de la créance |

> **Conseil** : Les créances de plus de 30 jours sont mises en évidence en orange, et celles de plus de 60 jours en rouge. Relancez régulièrement les clients en retard.

---

## 4.6 Charges du garage

Menu **Facturation → Charges**

Enregistrez les charges opérationnelles du garage (loyer, électricité, salaires, etc.) :

1. Cliquez sur **+ Nouvelle charge**
2. Saisissez :
   - **Catégorie** : Loyer, Électricité, Salaires, Assurance, Autres
   - **Désignation** détaillée
   - **Montant**
   - **Date**
3. Cliquez sur **Enregistrer**

---

## 4.7 Rapports Facturation

### Rapport de ventes

Menu **Rapports → Rapport de ventes…**

- Chiffre d'affaires par période (jour, semaine, mois, année)
- Répartition par type de prestation
- Top clients

### Bilan Charges vs CA

Menu **Rapports → Bilan mensuel…**

- Chiffre d'affaires du mois
- Total des charges du mois
- Résultat net estimé

### Export

Tous les rapports de facturation peuvent être :
- **Imprimés** directement
- **Exportés** en HTML pour archivage
