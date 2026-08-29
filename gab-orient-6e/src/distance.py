"""
Calcul de distance géographique — Formule de Haversine
GAB-ORIENT 6è
"""
from math import radians, sin, cos, sqrt, atan2

RAYON_TERRE_KM = 6371.0


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcule la distance en kilomètres entre deux points GPS
    en utilisant la formule de Haversine.
    """
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(RAYON_TERRE_KM * c, 2)


def distance_eleve_etablissement(eleve, etablissement):
    return haversine(
        eleve.latitude, eleve.longitude,
        etablissement.latitude, etablissement.longitude
    )
