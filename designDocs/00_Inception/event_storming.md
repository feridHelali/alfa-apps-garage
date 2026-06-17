Voici un modèle complet d'Event Storming pour un système de Garage de Réparation Auto et Diagnostic.
L'Event Storming consiste à identifier tous les événements métier (au passé) qui jalonnent la vie du système, ainsi que les commandes (actions) et les concepts clés.📅 Les Événements Métier (Domain Events)

Voici la chronologie des événements clés, regroupés par cycle de vie du véhicule.

1. Prise en charge & DiagnosticRendezVousPlanifié : Le client a validé son créneau.VéhiculeDéposé : La voiture est arrivée au garage.FicheRéceptionCréée : Le kilométrage et l'état visuel sont notés.DiagnosticLancé : Le mécanicien commence à chercher la panne.PanneIdentifiée : Le rapport de diagnostic électronique ou mécanique est prêt.
2. Devis & ApprobationDevisGénéré : Le coût des pièces et de la main-d'œuvre est calculé.DevisEnvoyéAuClient : Le client reçoit la proposition par SMS/Email.DevisApprouvé : Le client donne son accord pour les travaux.DevisRefusé : Le client refuse (le véhicule sera restitué en l'état).
3. Réparation & StockPiècesCommandées : Les pièces nécessaires ne sont pas en stock.
PiècesReçues : Les pièces sont livrées par le fournisseur.RéparationCommencée : Un technicien est affecté et travaille sur l'auto.RéparationTerminée : Les travaux mécaniques sont finis.ContrôleQualitéValidé : Essai routier ou contre-diagnostic réussi.4. Facturation & RestitutionFactureGénérée : Le système clôture le dossier de réparation.ClientNotifié : Le client sait que son véhicule est prêt.PaiementEncaissé : Le règlement (carte, espèces, chèque) est validé.VéhiculeRestitué : Le client récupère ses clés et repart.🛠️ Commandes, Agrégats et ActeursPour faire le lien, voici comment les actions (Commandes) transforment nos concepts clés (Agrégats).Acteur / RôleCommande (Action)Agrégat (Concept)Événement GénéréClientRéserver un créneauRendezVousRendezVousPlanifiéRéceptionnisteOuvrir l'ordre de réparationDossierVéhiculeVéhiculeDéposéMécanicienSaisir le résultat du scanDiagnosticPanneIdentifiéeChef d'atelierChiffrer les réparationsDevisDevisGénéréClientValider le devis en ligneDevisDevisApprouvéMagasinierSortir/Commander les piècesStockPiècesCommandéesMécanicienDéclarer la fin des travauxDossierVéhiculeRéparationTerminéeSecrétaireÉmettre le document finalFactureFactureGénérée
🧱 Contextes Bornés (Bounded Contexts) ProposésSi vous devez concevoir une architecture logicielle (comme des microservices), vous pouvez découper le garage en 4 grands modules autonomes :Context de Planification & Réception : Gère l'agenda, les clients et l'accueil des véhicules.Context de Diagnostic & Atelier : Gère les fiches techniques, l'affectation des mécaniciens et le suivi des tâches.Context d'Approvisionnement (Stock) : Gère le catalogue de pièces, les alertes de stock et les commandes fournisseurs.Context de Facturation & Comptabilité : Gère les devis, les taxes, les factures et les terminaux de paiement.

Ces règles automatisent les transitions entre les événements ou bloquent les actions non autorisées.1. Sécurité et Consentement (Devis & Travaux)Règle Strict-Accord : Impossible de générer un OrdreDeRéparation si le statut du devis n'est pas DevisApprouvé.Règle Avenant-Obligatoire : Si une nouvelle panne est découverte en cours de route, la réparation est stoppée. Un devis complémentaire doit être généré (DevisComplémentaireCréé) et validé.2. Logistique et Atelier (Pièces & Main d'œuvre)Règle Flux-Tendu : L'événement DevisApprouvé déclenche automatiquement la vérification du stock. Si une pièce manque, la commande fournisseur est émise instantanément (PiècesCommandées).Règle Planification-Atelier : Un mécanicien ne peut être affecté à une Réparation que s'il est déclaré disponible dans le module de planning et possède la qualification requise (ex: certification Véhicule Électrique pour un diagnostic de batterie).3. Clôture et Restitution (Finance)Règle Anti-Vol : L'action Restituer les clés est bloquée par le système tant que l'événement PaiementEncaissé n'a pas été reçu (sauf pour les clients "Flotte/Entreprise" avec option de paiement à 30 jours).Règle Garantie-Qualité : La FactureGénérée ne peut l'être que si le ContrôleQualitéValidé a été enregistré par le chef d'atelier.📦 Structure de l'Agrégat : DossierRéparation (RepairOrder)C'est le cœur du système (la "State Machine"). Il maintient la cohérence des données du dépôt du véhicule jusqu'à sa sortie.DossierRéparation (Racine d'Agrégat / Aggregate Root)
│
├── Identifiants & Clés
│   ├── DossierId (UUID)
│   ├── VéhiculeId (Immatriculation / VIN)
│   └── ClientId (Réf Client)
│
├── États (Status)
│   ├── StatutDossier (Créé ➔ Diagnostic ➔ EnAttenteDevis ➔ EnCours ➔ Qualité ➔ Prêt ➔ Clôturé)
│   └── KilométrageEntrée (Int)
│
├── 🛠️ Entités Internes (Données locales à l'agrégat)
│   │
│   ├── LignesDiagnostic (Liste)
│   │   ├── CodeDéfaut (OBD2)
│   │   ├── DescriptionPanne
│   │   └── Gravité (Bloquant / À surveiller)
│   │
│   ├── OpérationsMécaniques (Liste)
│   │   ├── TechnicienId
│   │   ├── CodeMainD'Oeuvre
│   │   ├── TempsEstimé vs TempsPassé
│   │   └── StatutTâche (ÀFaire / EnCours / Terminé)
│   │
│   └── PiècesRequises (Liste)
│       ├── PièceId (Réf Constructeur)
│       ├── Quantité
│       └── StatutDispo (EnStock / Commandé / Reçu)
│
└── 🔒 Invariants (Ce qui doit TOUJOURS être vrai dans l'agrégat)
    * Le montant total du dossier doit être égal à la somme des lignes de pièces + main d'œuvre.
    * Le temps passé total ne peut pas être enregistré comme négatif.
    * Impossible de passer le statut à "Prêt" si une seule tâche de la liste est
