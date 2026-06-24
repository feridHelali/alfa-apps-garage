# 3. Stock — Pièces et Fournisseurs

---

## 3.1 Catalogue de pièces

### Accéder au catalogue

- Menu **Stock → Catalogue de pièces** ou `Ctrl+P`
- Bouton **Stock** dans la sidebar

### Ajouter une pièce

1. Cliquez sur **+ Nouvelle pièce**
2. Remplissez la fiche :

| Champ | Obligatoire | Exemple |
|---|---|---|
| Référence | Oui | FILH-GOLF6-1.6 |
| Désignation | Oui | Filtre à huile Golf VI 1.6 TDI |
| Catégorie | Non | Filtration |
| Fournisseur principal | Non | Auto Pièces Tunis |
| Prix d'achat | Oui | 8,500 DT |
| Prix de vente HT | Oui | 14,000 DT |
| TVA | Non | 19% |
| Quantité en stock | Non | 5 |
| Stock minimum | Non | 2 |
| Emplacement | Non | Rayon A3 |

3. Cliquez sur **Enregistrer**

> **Conseil** : Définissez un **stock minimum** pour chaque pièce courante. Une alerte visuelle (ligne rouge) apparaît dans la liste quand le stock tombe sous ce seuil.

### Rechercher et filtrer

- Barre de recherche : cherche sur référence et désignation
- Filtre **Catégorie** : affiche uniquement les pièces d'une famille
- Filtre **Stock faible** : affiche les pièces sous le seuil minimum

### Ajuster le stock manuellement

Pour corriger un inventaire :

1. Sélectionnez la pièce
2. Cliquez sur **Ajuster le stock**
3. Entrez la nouvelle quantité et le motif (ex : inventaire physique)
4. L'ajustement est enregistré dans le journal de stock

---

## 3.2 Fournisseurs

### Ajouter un fournisseur

- Menu **Stock → Fournisseurs**

1. Cliquez sur **+ Nouveau fournisseur**
2. Remplissez :

| Champ | Exemple |
|---|---|
| Nom | Auto Pièces Tunis |
| Contact | Mohamed Trabelsi |
| Téléphone | 71 234 567 |
| Email | contact@aptunis.tn |
| Adresse | Zone Industrielle, Tunis |
| Conditions de paiement | 30 jours net |

3. Cliquez sur **Enregistrer**

### Fiche fournisseur

La fiche d'un fournisseur affiche :
- Ses coordonnées complètes
- Toutes ses commandes (historique)
- Le montant total des achats
- Les créances éventuelles

---

## 3.3 Commandes fournisseurs

### Créer une commande

- Menu **Stock → Commandes fournisseurs**

1. Cliquez sur **+ Nouvelle commande**
2. Sélectionnez le **fournisseur**
3. Ajoutez les lignes :
   - Sélectionnez la pièce dans le catalogue (ou saisissez manuellement)
   - Indiquez la quantité commandée
   - Saisissez le prix unitaire négocié
4. Cliquez sur **Confirmer la commande**

### Réceptionner une commande

Lorsque les pièces arrivent :

1. Ouvrez la commande
2. Cliquez sur **Réceptionner**
3. Vérifiez les quantités reçues (modifiables en cas de livraison partielle)
4. Cliquez sur **Valider la réception**

Le stock est automatiquement mis à jour avec les quantités réceptionnées.

---

## 3.4 Factures d'achat

Menu **Stock → Factures d'achat**

Les factures d'achat enregistrent les achats de pièces et consommables auprès des fournisseurs.

### Créer une facture d'achat

1. Cliquez sur **+ Nouvelle facture d'achat**
2. Sélectionnez le **fournisseur** et la **date**
3. Saisissez le **numéro de facture fournisseur**
4. Ajoutez les lignes d'achat
5. Cliquez sur **Enregistrer**

> **Conseil** : Associez toujours une facture d'achat à la commande correspondante pour un suivi complet (commande → réception → facture).

---

## 3.5 Rapport — État du stock

Menu **Rapports → État du stock**

Génère un rapport complet :
- Liste de toutes les pièces avec quantité actuelle
- Valeur totale du stock (au prix d'achat)
- Pièces sous le seuil minimum (alerte rouge)
- Pièces en rupture de stock

> **Conseil** : Éditez ce rapport lors de chaque inventaire mensuel. Le rapport peut être imprimé ou exporté.
