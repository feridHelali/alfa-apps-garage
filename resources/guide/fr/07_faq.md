# 7. Questions Fréquentes (FAQ)

---

## Connexion et accès

**Q : J'ai oublié mon mot de passe. Comment le réinitialiser ?**

Contactez votre administrateur (compte `admin`). L'administrateur peut modifier les mots de passe via **Administration → Utilisateurs → Modifier l'utilisateur**.

Si l'administrateur a également perdu son accès, contactez le support Alfa Computers Apps à l'adresse indiquée dans le contrat de licence.

---

**Q : L'application affiche "Accès refusé" quand j'essaie d'ouvrir un module.**

Votre rôle ne vous donne pas accès à ce module. Demandez à votre administrateur d'élever vos permissions ou d'attribuer le rôle approprié à votre compte.

---

**Q : Comment se déconnecter ?**

Menu **Fichier → Déconnexion** ou fermez directement la fenêtre principale (une confirmation sera demandée si des fenêtres sont ouvertes).

---

## Dossiers et réparations

**Q : Je ne peux plus modifier un dossier clôturé. Comment faire une correction ?**

Un dossier clôturé est en lecture seule pour garantir l'intégrité des données. Pour une correction :
- Si la facture n'est pas encore émise, annulez-la et recréez-en une.
- Si c'est une erreur grave, créez un **avoir** (voir module Facturation → Avoirs).

---

**Q : Un technicien a mal enregistré le kilométrage à l'entrée. Peut-on corriger ?**

Tant que le dossier est à l'état CRÉÉ ou DIAGNOSTIC, toutes les informations sont modifiables. À partir de EN_COURS, la modification nécessite un rôle Admin.

---

**Q : Comment annuler une transition d'état (ex : revenir de EN_COURS à DIAGNOSTIC) ?**

Les transitions d'état sont unidirectionnelles par conception (piste d'audit). Contactez un administrateur qui peut forcer un retour via l'interface d'administration avancée.

---

**Q : L'état "ATTENTE DEVIS" bloque-t-il le démarrage des travaux ?**

Oui, c'est intentionnel. Le garage ne peut pas démarrer les travaux sans l'accord explicite du client. Pour débloquer, cliquez sur **Accord client reçu** dans le dossier.

---

## Facturation

**Q : J'ai émis une facture avec le mauvais montant. Comment corriger ?**

Une facture émise ne peut plus être modifiée. Options :
1. **Annuler** la facture (si non payée) et en créer une nouvelle.
2. **Émettre un avoir** pour corriger la différence (si partiellement payée).

---

**Q : Le client veut payer en plusieurs fois. Comment enregistrer ?**

Enregistrez plusieurs paiements partiels sur la même facture :
1. Premier paiement : facture passe en **PARTIELLEMENT PAYÉE**
2. Deuxième paiement (solde) : facture passe en **PAYÉE**

---

**Q : Comment enregistrer un avoir / remboursement ?**

Menu **Facturation → Factures → Créer un avoir**. Sélectionnez la facture originale et le montant à rembourser.

---

## Stock

**Q : Une pièce apparaît en stock négatif. Comment corriger ?**

Utilisez **Ajuster le stock** sur la fiche pièce pour remettre à zéro ou corriger la quantité. Notez le motif "Correction inventaire" pour la traçabilité.

---

**Q : Peut-on importer un catalogue de pièces depuis Excel ?**

L'import Excel n'est pas disponible dans cette version. Saisissez les pièces manuellement ou contactez Alfa Computers Apps pour un import sur mesure.

---

## Sauvegardes et données

**Q : Où sont stockées les données de l'application ?**

La base de données SQLite est dans `C:\Users\[votre_nom]\AppData\Roaming\garage_reparation\garage.db` (ou le chemin configuré dans les paramètres).

---

**Q : À quelle fréquence dois-je créer des snapshots ?**

Recommandations :
- **Quotidien** : En fin de journée pour les garages à forte activité
- **Hebdomadaire** : Minimum pour tous les garages
- **Avant chaque mise à jour** de l'application

Conservez les snapshots sur un **disque externe ou réseau** en plus du disque local.

---

**Q : La base de données est endommagée. Que faire ?**

1. Ne pas paniquer — l'application utilise SQLite en mode WAL, très résistant aux corruptions.
2. Menu **Administration → Gestion de la base → Vérification intégrité**.
3. Si des erreurs sont détectées, restaurez le dernier snapshot valide.
4. Si nécessaire, contactez le support Alfa Computers Apps.

---

## Performance et technique

**Q : L'application est lente au démarrage.**

Causes possibles :
- Première ouverture après une longue période : SQLite WAL checkpoint en cours (normal, 5-10s)
- Base de données volumineuse : exécutez **VACUUM** depuis Administration → Gestion DB
- Disque dur fragmenTé : défragmentez le disque Windows

---

**Q : L'application plante avec "DLL not found".**

Réinstallez l'application avec le fichier `GarageReparationSetup_x64.exe`. Si le problème persiste, installez Visual C++ Redistributable 2022 depuis le site Microsoft.

---

**Q : Comment mettre à jour l'application ?**

Téléchargez le nouvel installeur depuis Alfa Computers Apps et exécutez-le. L'installeur Inno Setup met à jour les fichiers sans toucher à la base de données.

---

## Support

Pour toute question non couverte par ce guide, contactez :

**Alfa Computers Apps**
Support technique : Alfa Computers Apps — Solutions de Gestion sur Mesure

> Ce guide est distribué avec le logiciel sous licence propriétaire Alfa Computers Apps. Toute reproduction partielle ou totale est interdite sans autorisation écrite.
