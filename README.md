# GAB-ORIENT 6è

Plateforme d'affectation scolaire automatisée et géolocalisée pour l'entrée en classe de 6ème au Gabon (Grand Libreville).

Ce projet propose une réponse concrète aux difficultés rencontrées chaque année lors de l'orientation des élèves de CM2 : longs temps de transport quotidiens, saturation de certains lycées historiques et manque de lisibilité dans les critères d'affectation.

---

## L'idée du projet

À Libreville et dans les communes voisines (Owendo, Akanda, Ntoum), de nombreux enfants sont encore scolarisés très loin de chez eux. Cela pèse lourdement sur les familles (frais de transport, fatigue, retards).

GAB-ORIENT 6è a été conçu pour automatiser et fiabiliser ce processus à l'aide de données cartographiques et scolaires claires, en s'appuyant sur deux piliers :
1. **Le mérite académique** : la moyenne obtenue au CM2 / examen d'entrée.
2. **La proximité géographique** : la distance réelle entre le domicile de l'élève et l'établissement demandé, calculée par coordonnées GPS.

L'objectif est d'assurer une répartition équitable tout en respectant scrupuleusement les places disponibles dans chaque établissement.

---

## Ce que propose l'application

- **Simulation et affectation automatique** : calcul du classement des candidatures selon un score mixte (notes + proximité) avec gestion des capacités résiduelles et des listes d'attente.
- **Carte interactive du Grand Libreville** :
  - Visualisation des collèges et lycées partenaires.
  - Recherche d'établissements par quartier avec suggestions instantanées (*Louis, Akébé, Nzeng-Ayong, Okala, Mikolongo, Bikélé, etc.*) et réglage du rayon de recherche (1.5 km à 10 km).
  - Après chaque session d'affectation, les élèves sont visualisés sur la carte avec leur statut (affecté, liste d'attente, non affecté) et le tracé du trajet validé jusqu'à leur établissement.
- **Tableau de bord et statistiques** : suivi des taux de remplissage, satisfaction des vœux (vœu 1, 2 ou 3) et répartition des effectifs.
- **Rapports officiels prêts à imprimer** : fiches récapitulatives et procès-verbaux de session pour les commissions d'orientation.
- **Gestion ouverte des données** : import/export CSV et stockage lisible en fichiers YAML modifiables.

---

## Comment fonctionne l'algorithme ?

Pour chaque élève admissible (moyenne générale $\ge$ 10/20 par défaut) :

1. L'élève formule jusqu'à 3 vœux d'établissements.
2. Pour chaque vœu, la distance réelle entre son domicile et l'école est calculée (formule de Haversine).
3. Un score d'affectation est attribué en combinant le niveau scolaire et la proximité :
   $$\text{Score} = (\text{Poids Note} \times \text{Moyenne}) + (\text{Poids Proximité} \times \text{Score Distance})$$
4. Les candidatures sont traitées par ordre de score décroissant :
   - Si l'établissement a encore des places en 6ème, l'élève y est affecté.
   - Si l'établissement est plein, l'algorithme examine le vœu suivant.
   - Si tous les vœux sont saturés, l'élève est placé sur liste d'attente priorisée par le mérite.

Tous les paramètres (seuil d'admission, coefficients de pondération, rayon maximum) sont ajustables dans le fichier `data/regles.yaml`.

---

## Structure du répertoire

```text
├── data/                    # Données métier modifiables (YAML)
│   ├── carte_scolaire.yaml  # Établissements, coordonnées GPS et capacités
│   ├── eleves.yaml          # Candidats, adresses, moyennes et vœux
│   └── regles.yaml          # Paramètres de calcul de l'orientation
├── views/                   # Pages et composants de l'interface (EJS)
├── public/                  # Feuilles de style et scripts clients
├── server.ts                # Serveur applicatif principal (Node.js / Express / TypeScript)
├── gab-orient-6e/           # Moteur algorithmique initial en Python / Flask
└── README.md
```

---

## Démarrage rapide

### Prérequis
- [Node.js](https://nodejs.org/) (version 18 ou supérieure)
- Un navigateur web récent

### Installation et lancement

1. Récupérer le projet :
   ```bash
   git clone https://github.com/votre-utilisateur/gab-orient-6e.git
   cd gab-orient-6e
   ```

2. Installer les dépendances :
   ```bash
   npm install
   ```

3. Démarrer le serveur en local :
   ```bash
   npm run dev
   ```

4. Ouvrir l'application dans votre navigateur :
   - Rendez-vous sur `http://localhost:3000`
   - Mot de passe d'accès pour les sessions d'affectation : `gaborient2025`

*(Note : le sous-dossier `gab-orient-6e/` contient également une implémentation alternative autonome en Python avec Flask si vous préférez exécuter le moteur via `python app.py`)*.

---

## Modifier ou enrichir les données

Vous pouvez tester le système avec vos propres données :
- Ajouter des écoles dans `data/carte_scolaire.yaml` en indiquant nom, coordonnées GPS et capacité d'accueil.
- Ajouter des élèves soit manuellement dans `data/eleves.yaml`, soit via la page **Importer des élèves** depuis un fichier CSV.

---

## Licence et utilisation

Projet conçu dans le cadre des réflexions sur la modernisation et la numérisation de la carte scolaire gabonaise. Le code est partagé dans un esprit de transparence pour servir de base d'expérimentation et d'amélioration continue.
