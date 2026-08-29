from src.models import Eleve, Etablissement
from src.affectation import MoteurAffectation


def test_affectation_prioritizes_moyenne():
    etab = Etablissement('GAB001', 'E1', 'public', 'Commune', 'Q', 0.0, 0.0, capacite_6eme=1)
    eleve1 = Eleve('ELV001', 'Nom', 'A', 16.0, 'Addr', 0.0, 0.0, voeux=['GAB001'])
    eleve2 = Eleve('ELV002', 'Nom', 'B', 12.0, 'Addr', 0.0, 0.0, voeux=['GAB001'])

    moteur = MoteurAffectation([eleve1, eleve2], [etab], {'criteres': {'poids_moyenne': 1.0, 'poids_distance': 0.0}, 'distance': {'rayon_max_km': 10}, 'moyenne': {'echelle': 20.0, 'minimale_requise': 0.0}})
    resultat = moteur.affecter()

    # Only one place: eleve1 should be affecte
    assert eleve1.statut == 'affecte'
    assert eleve2.statut == 'liste_attente'


def test_distance_threshold_excludes_far():
    etab = Etablissement('GAB002', 'E2', 'public', 'Commune', 'Q', 0.0, 0.0, capacite_6eme=10)
    # student far away (> rayon_max)
    eleve = Eleve('ELV003', 'Nom', 'C', 15.0, 'Addr', 10.0, 10.0, voeux=['GAB002'])

    moteur = MoteurAffectation([eleve], [etab], {'criteres': {'poids_moyenne': 1.0, 'poids_distance': 0.0}, 'distance': {'rayon_max_km': 1}, 'moyenne': {'echelle': 20.0, 'minimale_requise': 0.0}})
    resultat = moteur.affecter()

    assert eleve.statut == 'liste_attente' or eleve.statut == 'non_affecte'

