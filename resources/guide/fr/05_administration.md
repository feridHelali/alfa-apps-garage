# 5. Administration

---

## 5.1 Informations de la société

Menu **Administration → Société**

Configurez les informations qui apparaissent sur tous vos documents (factures, bons de travail, fiches réparation) :

| Champ | Exemple |
|---|---|
| Raison sociale | Garage Ben Salah |
| Forme juridique | SARL |
| Capital | 20 000,000 DT |
| Matricule fiscal | 1234567/A/M/000 |
| Adresse | 12 Rue Ibn Khaldoun, Tunis 1001 |
| Téléphone | 71 123 456 |
| Email | contact@garage-bensalah.tn |
| Site web | www.garage-bensalah.tn |
| RIB / IBAN | TN59 1234 5678 9012 3456 7890 |
| Banque | STB — Agence Bab Bhar |
| Mentions légales | Toute facture non réglée... |

> **Important** : Le **matricule fiscal** est obligatoire sur les factures en Tunisie. Assurez-vous de le saisir correctement.

---

## 5.2 Gestion des utilisateurs

Menu **Administration → Utilisateurs** (admin uniquement)

### Créer un utilisateur

1. Cliquez sur **+ Nouvel utilisateur**
2. Remplissez :
   - **Nom d'utilisateur** (identifiant de connexion)
   - **Nom complet** et **Prénom**
   - **Mot de passe** (minimum 8 caractères, 1 majuscule, 1 chiffre)
   - **Rôle** : Technicien, Admin, ou Superadmin
3. Cliquez sur **Créer**

### Rôles et permissions

| Rôle | Modules accessibles |
|---|---|
| **Technicien** | Réception (lecture), Atelier, Stock (lecture), Rapports dossiers |
| **Admin** | Tous les modules — Facturation, Utilisateurs, Société, Numérotation |
| **Superadmin** | Admin + Gestion DB, Journal d'audit, Snapshots |

### Désactiver un utilisateur

Sélectionnez l'utilisateur et cliquez sur **Désactiver**. Un utilisateur désactivé ne peut plus se connecter, mais son historique est conservé.

> **Conseil** : Ne supprimez jamais un utilisateur (cela pourrait rompre l'historique des dossiers). Désactivez-le simplement quand il quitte le garage.

---

## 5.3 Numérotation des documents

Menu **Administration → Numérotation**

Configurez le format des numéros pour chaque type de document :

| Document | Format par défaut | Exemple |
|---|---|---|
| Dossier réparation | `REP-{YYYY}-{NNN}` | REP-2026-042 |
| Facture client | `FAC-{YYYY}-{NNN}` | FAC-2026-128 |
| Facture d'achat | `ACH-{YYYY}-{NNN}` | ACH-2026-015 |
| Bon de travail | `BT-{YYYY}-{NNN}` | BT-2026-003 |

**Champs de format :**
- `{YYYY}` : Année sur 4 chiffres
- `{YY}` : Année sur 2 chiffres
- `{MM}` : Mois
- `{NNN}` : Séquence numérique (nombre de zéros = largeur)

> **Important** : Ne modifiez pas la numérotation en cours d'exercice pour éviter les doublons.

---

## 5.4 Gestion des sauvegardes

Menu **Administration → Gestion de la base de données** (superadmin uniquement)

### Créer un snapshot

1. Cliquez sur **Créer un snapshot**
2. Saisissez un **commentaire** descriptif (ex : "Avant migration v2.0")
3. Cliquez sur **Créer**

Le snapshot est enregistré dans `~/.garage_reparation/snapshots/` avec un horodatage.

### Restaurer un snapshot

> **Attention** : La restauration écrase toutes les données actuelles.

1. Sélectionnez le snapshot dans la liste
2. Cliquez sur **Restaurer**
3. Confirmez l'action dans la boîte de dialogue

### Maintenance de la base

| Action | Description |
|---|---|
| **VACUUM** | Compacte la base (libère l'espace disque) |
| **WAL Checkpoint** | Force l'écriture du journal WAL |
| **Vérification intégrité** | Contrôle la cohérence de la base |

> **Conseil** : Exécutez VACUUM une fois par mois et créez toujours un snapshot avant toute intervention technique importante.

---

## 5.5 Journal d'audit

Menu **Administration → Journal d'audit** (superadmin uniquement)

Le journal d'audit enregistre **toutes les actions critiques** effectuées dans l'application :

| Colonne | Description |
|---|---|
| Date/Heure | Horodatage précis de l'action |
| Utilisateur | Qui a fait l'action |
| Catégorie | AUTH, DOSSIER, FACTURE, STOCK, DB, USER… |
| Niveau | INFO, WARNING, ERROR |
| Description | Détail de l'action |

### Filtrer le journal

- Par **période** (de → à)
- Par **catégorie**
- Par **utilisateur**
- Par **niveau** (erreurs uniquement, etc.)

> **Note légale** : Le journal d'audit est en lecture seule — il ne peut pas être modifié ni supprimé par aucun utilisateur.

---

## 5.6 Paramètres

Menu **Administration → Paramètres**

| Paramètre | Description |
|---|---|
| Thème | Clair (défaut) — sombre (à venir) |
| Langue | Français (défaut) — Arabe (à venir) |
| Devise par défaut | TND (défaut), EUR, USD, CAD |
| Taux TVA standard | 19% (Tunisie) |
| Imprimante par défaut | Sélectionner l'imprimante locale |
