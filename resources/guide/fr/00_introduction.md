# Guide Utilisateur — Gestion Réparation Voiture

**Alfa Computers Apps** — Solutions de Gestion sur Mesure

---

## Bienvenue

**Gestion Réparation Voiture** est un logiciel de gestion intégré conçu pour les garages automobiles tunisiens. Il couvre l'ensemble du cycle de vie d'une réparation, de la prise en charge du véhicule jusqu'à la facturation et l'encaissement.

![Vue d'ensemble des modules](img/module_overview.svg)

---

## Les modules de l'application

| Module | Accès | Description |
|---|---|---|
| **Réception** | Menu Réception | Clients, véhicules, rendez-vous |
| **Atelier** | Menu Atelier | Dossiers de réparation, bons de travail |
| **Stock** | Menu Stock | Catalogue pièces, fournisseurs, achats |
| **Facturation** | Menu Facturation | Factures, caisse, créances, charges |
| **Rapports** | Menu Rapports | Tous les rapports et analyses |
| **Administration** | Menu Administration | Société, utilisateurs, paramètres |

---

## Rôles et accès

L'application distingue trois profils d'utilisateurs :

| Rôle | Accès |
|---|---|
| **Technicien** | Dossiers, stock (lecture), bons de travail |
| **Admin** | Tous les modules sauf gestion DB |
| **Superadmin** | Accès total — gestion DB, audit, snapshots |

> **Conseil** : Créez un compte `admin` pour chaque gérant de garage. Le `superadmin` est réservé aux interventions techniques et à la gestion des sauvegardes.

---

## Connexion

Au démarrage, l'écran de connexion apparaît :

1. Saisissez votre **identifiant** (ex : `admin`)
2. Saisissez votre **mot de passe**
3. Cliquez sur **Se connecter** ou appuyez sur `Entrée`

**Identifiants par défaut à la première installation :**

| Utilisateur | Mot de passe | Rôle |
|---|---|---|
| `admin` | `Admin@2025!` | admin |
| `superadmin` | `SuperAdmin@2025!` | superadmin |

> **Attention** : Changez les mots de passe par défaut dès la première utilisation via **Administration → Utilisateurs**.

---

## Navigation

### La barre latérale (sidebar)

La sidebar à gauche donne accès direct aux modules principaux :

- Cliquez sur un bouton pour ouvrir la fenêtre correspondante
- Le bouton **◀/▶** en haut réduit ou agrandit la sidebar
- Sur écran 15" (1366×768), le mode compact s'active automatiquement

### Les fenêtres MDI

L'application utilise une interface MDI (*Multiple Document Interface*) : plusieurs fenêtres peuvent être ouvertes simultanément dans l'espace de travail central.

- **Menu Fenêtres → Cascade** : réorganise les fenêtres en cascade
- **Menu Fenêtres → Mosaïque** : dispose les fenêtres côte à côte
- **Menu Fenêtres → Fermer tout** : ferme toutes les fenêtres ouvertes

### La barre de menus

Chaque menu regroupe les fonctions d'un module :

- **Réception** — Clients, Véhicules, Rendez-vous
- **Atelier** — Dossiers, Bons de travail
- **Stock** — Catalogue, Fournisseurs, Commandes, Achats
- **Facturation** — Factures, Caisse, Créances, Charges
- **Rapports** — Tous les rapports disponibles
- **Administration** — Société, Utilisateurs, Paramètres, Numérotation
- **Aide** — Ce guide, à propos

---

## Raccourcis clavier

| Raccourci | Action |
|---|---|
| `Ctrl+K` | Ouvrir la liste des clients |
| `Ctrl+V` | Ouvrir la liste des véhicules |
| `Ctrl+D` | Ouvrir les dossiers de réparation |
| `Ctrl+R` | Bon de travail rapide |
| `Ctrl+P` | Catalogue pièces |
| `Ctrl+F` | Liste des factures |
| `Alt+F4` | Quitter l'application |

---

## Monnaie

L'application utilise le **Dinar Tunisien (DT)** avec 3 décimales (millimes).

Format : `1 234,567 DT`

Les devises EUR, USD et CAD sont également supportées pour les imports.

---

## Premier démarrage — liste de contrôle

- [ ] Changer les mots de passe par défaut (Administration → Utilisateurs)
- [ ] Saisir les informations de la société (Administration → Société)
- [ ] Configurer la numérotation des documents (Administration → Numérotation)
- [ ] Créer les utilisateurs du garage (techniciens, réceptionnistes)
- [ ] Saisir le catalogue de pièces initial (Stock → Catalogue)
- [ ] Enregistrer les fournisseurs habituels (Stock → Fournisseurs)
