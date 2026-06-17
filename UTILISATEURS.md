# Comptes utilisateurs — Gestion Réparation Voiture

> **Alfa Computers Apps** — Ces identifiants sont insérés automatiquement au premier lancement.
> Changer les mots de passe immédiatement après la mise en production.

---

## Comptes par défaut (seed)

| Utilisateur | Mot de passe | Rôle | Accès |
|---|---|---|---|
| `admin` | `Admin@2025!` | Super Administrateur | Toutes les fonctions |
| `superadmin` | `SuperAdmin@2025!` | Super Administrateur | Toutes les fonctions + gestion BDD |

> **Note :** Le seed crée uniquement le compte `admin`. Le compte `superadmin` doit être créé manuellement
> via **Administration → Utilisateurs** avec le rôle `superadmin`.

---

## Rôles et permissions

### Super Administrateur (`superadmin`)

Accès complet sans restriction.

| Catégorie | Permissions |
|---|---|
| Clients & Rendez-vous | Voir, créer, modifier |
| Atelier | Voir, créer dossier, gérer, approuver devis, valider qualité |
| Stock | Voir, gérer |
| Facturation | Voir, gérer, enregistrer paiements |
| Administration | **Gérer utilisateurs**, **gérer société**, **gérer snapshots BDD**, gérer rapports, paramètres |
| Audit | Lire le journal d'audit complet |

---

### Administrateur (`admin`)

Accès opérationnel complet, sans accès à la gestion des utilisateurs ni aux snapshots BDD.

| Catégorie | Permissions |
|---|---|
| Clients & Rendez-vous | Voir, créer, modifier |
| Atelier | Voir, créer dossier, gérer, approuver devis, valider qualité |
| Stock | Voir, gérer |
| Facturation | Voir, gérer, enregistrer paiements |
| Administration | Gérer rapports, paramètres |
| Audit | ✗ Pas d'accès au journal |
| Utilisateurs | ✗ Pas d'accès |
| Snapshots BDD | ✗ Pas d'accès |

---

### Technicien (`technicien`)

Accès lecture seule sur la plupart des modules, peut gérer les dossiers qui lui sont assignés.

| Catégorie | Permissions |
|---|---|
| Clients | Voir uniquement |
| Rendez-vous | Voir uniquement |
| Atelier | Voir dossiers, gérer dossier (tâches/opérations), valider qualité |
| Stock | Voir uniquement |
| Facturation | Voir uniquement |
| Administration | ✗ Aucun accès |

---

## Politique de mots de passe recommandée

| Règle | Recommandation |
|---|---|
| Longueur minimale | 10 caractères |
| Complexité | Majuscule + minuscule + chiffre + caractère spécial |
| Rotation | Tous les 90 jours |
| Réutilisation | 5 derniers mots de passe interdits |

Exemple de mot de passe fort : `Garage@2025!`

---

## Créer un nouvel utilisateur

1. Se connecter avec un compte `superadmin`
2. Menu **Administration → Utilisateurs**
3. Cliquer **Nouveau**
4. Renseigner : nom d'utilisateur, nom complet, rôle, mot de passe
5. **Enregistrer**

---

## Réinitialiser un mot de passe (superadmin)

1. Menu **Administration → Utilisateurs**
2. Sélectionner l'utilisateur
3. Champ **Nouveau mot de passe** → saisir → **Enregistrer**

> Les mots de passe sont stockés avec **bcrypt** (coût 12) — jamais en clair.

---

## Désactiver un compte

Dans **Administration → Utilisateurs**, décocher **Compte actif** puis **Enregistrer**.
L'utilisateur ne pourra plus se connecter mais ses données sont conservées.

---

## Fichier seed

Source : `resources/seed/seed_data.json`

Pour modifier les données initiales (nom de la société, paramètres défaut, templates rapports),
éditer ce fichier **avant** le premier lancement.
Après le premier lancement, utiliser l'interface **Administration → Société** et **Administration → Paramètres**.
