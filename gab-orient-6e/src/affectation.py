"""
Moteur d'affectation multicritère — GAB-ORIENT 6è
Critères : moyenne académique, distance domicile-établissement, capacité résiduelle.
"""
from .distance import distance_eleve_etablissement


class MoteurAffectation:
    def __init__(self, eleves, etablissements, parametres):
        self.eleves = eleves
        self.etablissements = {e.id: e for e in etablissements}
        self.parametres = parametres

    def score(self, eleve, etablissement, distance_km):
        """
        Score composite = poids_moyenne * (moyenne/20) + poids_distance * (1 - distance/rayon_max)
        Plus le score est élevé, plus l'élève est prioritaire pour cet établissement.
        """
        crit = self.parametres["criteres"]
        rayon_max = self.parametres["distance"]["rayon_max_km"]
        echelle = self.parametres["moyenne"]["echelle"]

        score_moyenne = eleve.moyenne_generale / echelle
        score_distance = max(0.0, 1 - (distance_km / rayon_max)) if rayon_max > 0 else 0.0

        return (crit["poids_moyenne"] * score_moyenne) + (crit["poids_distance"] * score_distance)

    def eleves_eligibles(self):
        seuil = self.parametres["moyenne"]["minimale_requise"]
        return [e for e in self.eleves if e.moyenne_generale >= seuil]

    def affecter(self):
        """
        Algorithme :
        1. Filtrer les élèves éligibles (moyenne >= seuil)
        2. Pour chaque élève, calculer un score par vœu (dans le rayon max)
        3. Trier les candidatures par score décroissant (priorité mérite + proximité)
        4. Affecter en respectant la capacité résiduelle de chaque établissement
        5. Les élèves non casés sur liste d'attente / non affectés
        """
        rayon_max = self.parametres["distance"]["rayon_max_km"]
        candidatures = []  # (score, eleve, etablissement, distance)

        for eleve in self.eleves_eligibles():
            for voeu_id in eleve.voeux:
                etab = self.etablissements.get(voeu_id)
                if not etab:
                    continue
                dist = distance_eleve_etablissement(eleve, etab)
                if dist <= rayon_max:
                    s = self.score(eleve, etab, dist)
                    candidatures.append((s, eleve, etab, dist))

        # Tri par score décroissant : priorité au mérite + proximité
        candidatures.sort(key=lambda c: c[0], reverse=True)

        affectes_ids = set()
        for score, eleve, etab, dist in candidatures:
            if eleve.id in affectes_ids:
                continue  # déjà affecté à un vœu précédent mieux classé
            if etab.a_de_la_place():
                etab.occuper_place()
                eleve.etablissement_affecte = etab.id
                eleve.statut = "affecte"
                eleve.distance_affectation_km = dist
                affectes_ids.add(eleve.id)

        # Élèves éligibles mais non casés -> liste d'attente
        for eleve in self.eleves_eligibles():
            if eleve.id not in affectes_ids:
                eleve.statut = "liste_attente"

        # Élèves sous le seuil -> non affectés
        for eleve in self.eleves:
            if eleve.moyenne_generale < self.parametres["moyenne"]["minimale_requise"]:
                eleve.statut = "non_affecte"

        return self.eleves
