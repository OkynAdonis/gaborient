# ORIENT 6E

Solution logicielle d'orientation scolaire géolocalisée pour les élèves
de CM2 en classe de 6ème.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer l'application

```bash
python app.py
```

Puis ouvrir http://127.0.0.1:5000 dans le navigateur.

## Structure du projet

```
gab-orient-6e/
├── data/                    # Fichiers YAML (élèves, carte scolaire, paramètres)
├── src/                     # Moteur métier Python
│   ├── models.py            # Classes Eleve, Etablissement
│   ├── distance.py          # Formule de Haversine
│   ├── affectation.py       # Algorithme de classement multicritère
│   └── rapport.py           # Génération des rapports YAML/JSON
├── app/
│   ├── templates/           # Pages HTML (Jinja2)
│   └── static/css/style.css # Thème visuel
├── output/                  # Rapports générés
└── app.py                   # Application Flask
```

## Fonctionnement de l'algorithme

1. Filtrage des élèves éligibles (moyenne ≥ seuil ministériel, `data/parametres.yaml`)
2. Calcul d'un score par vœu = poids_moyenne × (moyenne/20) + poids_distance × (1 − distance/rayon_max)
3. Classement de toutes les candidatures par score décroissant
4. Affectation en respectant la capacité résiduelle de chaque établissement
5. Élèves non casés → liste d'attente (classée par mérite) ; sous le seuil → non affectés

## Modifier les données

Les fichiers `data/eleves.yaml` et `data/carte_scolaire.yaml` sont éditables
directement pour ajouter des candidats ou des établissements.
