# 5. Administration

> Toutes les fonctions d'administration sont regroupées dans le menu **Administration**. Les fonctions marquées 🔑 **Admin** sont accessibles aux administrateurs et superadministrateurs. Les fonctions marquées 🔐 **Superadmin** sont réservées au superadministrateur uniquement.

---

## Section Admin 🔑

*Accès : rôle `admin` ou `superadmin`*

---

### 5.1 Informations de la société

**Menu Administration → Société** — ou — **Administration → Paramètres**, onglet *Société*

Configurez les informations qui apparaissent sur tous vos documents (factures, bons de travail, fiches réparation) :

| Champ | Exemple |
|---|---|
| Raison sociale | Garage Ben Salah |
| SIRET / Matricule fiscal | 1234567/A/M/000 |
| Adresse | 12 Rue Ibn Khaldoun, Tunis 1001 |
| Téléphone | 71 123 456 |
| Email | contact@garage-bensalah.tn |
| Clé de licence | (fournie par Alfa Computers Apps) |
| Logo | Image PNG, JPG ou SVG — s'affiche sur les documents |

> **Important** : Le **matricule fiscal** est obligatoire sur les factures en Tunisie. Assurez-vous de le saisir correctement avant d'émettre la première facture.

> **Conseil** : Vous pouvez accéder rapidement à la fiche Société depuis **Administration → Paramètres** (onglet *Société*) sans ouvrir une fenêtre séparée.

---

### 5.2 Gestion des utilisateurs

**Menu Administration → Utilisateurs**

#### Créer un utilisateur

1. Cliquez sur **+ Nouvel utilisateur**
2. Remplissez :
   - **Identifiant** (login de connexion, ex : `ali.technicien`)
   - **Nom complet**
   - **Mot de passe** (minimum 8 caractères, 1 majuscule, 1 chiffre)
   - **Rôle** : Technicien, Admin, ou Superadmin
3. Cliquez sur **Créer**

#### Rôles et permissions

| Rôle | Modules accessibles |
|---|---|
| **Technicien** | Réception (lecture), Atelier, Stock (lecture), Devis (lecture), Rapports dossiers |
| **Admin** | Tous les modules — Facturation, Devis, Société, Utilisateurs, Numérotation, Paramètres |
| **Superadmin** | Admin + Gestion BDD, Journal d'audit, Snapshots, onglet Base de données dans Paramètres |

#### Modifier un utilisateur

1. Sélectionnez l'utilisateur dans la liste
2. Cliquez sur **Modifier**
3. Modifiez le nom complet ou le rôle
4. Cliquez sur **OK**

#### Changer le mot de passe

1. Sélectionnez l'utilisateur
2. Cliquez sur **Changer mot de passe**
3. Saisissez et confirmez le nouveau mot de passe

#### Désactiver un utilisateur

Sélectionnez l'utilisateur et cliquez sur **Désactiver**.

Un utilisateur désactivé ne peut plus se connecter, mais son historique est conservé dans tous les dossiers et factures.

> **Conseil** : Ne supprimez jamais un utilisateur (cela pourrait rompre l'historique des dossiers). Désactivez-le simplement quand il quitte le garage.

---

### 5.3 Numérotation des documents

**Menu Administration → Numérotation**

Configurez le format des numéros pour chaque type de document :

| Document | Format par défaut | Exemple |
|---|---|---|
| Dossier réparation | `REP-{YYYY}-{NNN}` | REP-2026-042 |
| Facture client | `FAC-{YYYY}-{NNN}` | FAC-2026-128 |
| Facture d'achat | `ACH-{YYYY}-{NNN}` | ACH-2026-015 |
| Bon de travail | `BT-{YYYY}-{NNN}` | BT-2026-003 |
| Devis | `DEV-{YYYY}-{NNNN}` | DEV-2026-0012 |
| Proforma | `PRO-{YYYY}-{NNNN}` | PRO-2026-0003 |

**Champs de format :**
- `{YYYY}` : Année sur 4 chiffres
- `{YY}` : Année sur 2 chiffres
- `{MM}` : Mois
- `{NNN}` / `{NNNN}` : Séquence numérique (nombre de zéros = largeur)

> **Important** : Ne modifiez pas la numérotation en cours d'exercice pour éviter les doublons. En cas de changement d'année, la séquence repart automatiquement à 1.

---

### 5.4 Paramètres de l'application

**Menu Administration → Paramètres**

La fenêtre Paramètres regroupe les réglages de l'application en plusieurs onglets :

#### Onglet Affichage

| Paramètre | Options |
|---|---|
| Langue | Français (défaut) / Arabe (à venir) |
| Thème | Clair (défaut) / Sombre (à venir) |

> Redémarrez l'application pour que le changement de thème prenne effet.

#### Onglet Numérotation

Raccourci vers la fenêtre de numérotation des documents (voir §5.3).

#### Onglet Société 🔑

Accès direct aux informations de la société (raison sociale, logo, adresse, etc.) sans ouvrir une fenêtre séparée. Équivalent à **Administration → Société**.

#### Onglet Base de données 🔐

*Visible uniquement pour le Superadmin.*

Regroupe les outils de maintenance de la base de données SQLite et la gestion des snapshots. Voir **Section Superadmin** ci-dessous pour le détail.

---

## Section Superadmin 🔐

*Accès : rôle `superadmin` uniquement*

> **Principe de sécurité** : Les fonctions Superadmin ont un impact direct sur l'intégrité des données. Elles ne doivent être utilisées que par une personne de confiance (gérant, responsable informatique, technicien Alfa Computers Apps). Ne communiquez jamais les identifiants Superadmin au personnel du garage.

---

### 5.5 Gestion de la base de données

**Menu Administration → Gestion de la base de données** — ou — **Administration → Paramètres**, onglet *Base de données*

#### Statistiques SQLite

La fenêtre affiche en temps réel :
- **Taille** du fichier de base de données
- **Nombre de pages** × taille de page
- **Fragmentation** (%) — plus elle est haute, plus un VACUUM est utile

#### Maintenance

| Action | Quand l'utiliser |
|---|---|
| **VACUUM** | Libère l'espace fragmenté. Recommandé 1 fois par mois. L'application peut ralentir quelques secondes. |
| **Checkpoint WAL** | Force l'écriture du journal WAL dans le fichier principal. Utile avant une sauvegarde externe. |
| **Vérifier l'intégrité** | Contrôle la cohérence de la base. À exécuter si l'application a planté ou après une coupure de courant. |

#### Snapshots / Sauvegardes

Un snapshot est une copie complète de la base de données à un instant donné.

**Créer un snapshot :**
1. Cliquez sur **Créer snapshot**
2. La copie est enregistrée dans `~/.garage_reparation/snapshots/` avec un horodatage automatique

**Restaurer un snapshot :**

> **ATTENTION** : La restauration **écrase toutes les données actuelles** sans possibilité d'annulation. Créez toujours un snapshot de la situation actuelle AVANT de restaurer.

1. Sélectionnez le snapshot dans la liste
2. Cliquez sur **Restaurer**
3. Confirmez dans la boîte de dialogue
4. **Redémarrez l'application** immédiatement après

**Supprimer un snapshot :**
1. Sélectionnez le snapshot
2. Cliquez sur **Supprimer**

> **Conseil** : Conservez au minimum les 5 derniers snapshots. Copiez-les régulièrement sur un disque externe ou un dossier réseau.

**Fréquence recommandée :**
- **Quotidien** : En fin de journée pour les garages à forte activité
- **Hebdomadaire** : Minimum pour tous les garages
- **Avant chaque mise à jour** de l'application

---

### 5.6 Journal d'audit

**Menu Administration → Journal d'audit**

Le journal d'audit enregistre **toutes les actions critiques** effectuées dans l'application, avec horodatage et identité de l'utilisateur. Il est **en lecture seule** — aucun utilisateur, même superadmin, ne peut le modifier.

| Colonne | Description |
|---|---|
| Date/Heure | Horodatage précis (secondes) |
| Utilisateur | Identifiant de l'utilisateur |
| Catégorie | AUTH, DOSSIER, FACTURE, STOCK, DB, USER… |
| Niveau | INFO, WARNING, ERROR |
| Description | Détail complet de l'action |

#### Filtrer le journal

- Par **période** (de → à)
- Par **catégorie** (AUTH, STOCK, FACTURE, DB, USER…)
- Par **utilisateur**
- Par **niveau** (erreurs uniquement, etc.)

> **Utilisation légale** : En cas de litige ou d'audit comptable, le journal d'audit fournit une traçabilité complète et infalsifiable de toutes les opérations.

---

## Récapitulatif des accès

| Fonctionnalité | Admin 🔑 | Superadmin 🔐 |
|---|---|---|
| Société (infos, logo) | ✓ | ✓ |
| Utilisateurs | ✓ | ✓ |
| Numérotation | ✓ | ✓ |
| Paramètres — Affichage | ✓ | ✓ |
| Paramètres — Société | ✓ | ✓ |
| Paramètres — Base de données | ✗ | ✓ |
| Gestion BDD (menu dédié) | ✗ | ✓ |
| Journal d'audit | ✗ | ✓ |
| Snapshots | ✗ | ✓ |
