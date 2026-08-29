"""
Modèles de données — GAB-ORIENT 6è
"""


class Etablissement:
    def __init__(self, id, nom, type, commune, quartier, latitude, longitude,
                 capacite_6eme, places_occupees=0):
        self.id = id
        self.nom = nom
        self.type = type
        self.commune = commune
        self.quartier = quartier
        self.latitude = latitude
        self.longitude = longitude
        self.capacite_6eme = capacite_6eme
        self.places_occupees = places_occupees

    @property
    def places_restantes(self):
        return max(0, self.capacite_6eme - self.places_occupees)

    @property
    def taux_remplissage(self):
        if self.capacite_6eme == 0:
            return 0.0
        return round((self.places_occupees / self.capacite_6eme) * 100, 1)

    def a_de_la_place(self):
        return self.places_restantes > 0

    def occuper_place(self):
        if self.a_de_la_place():
            self.places_occupees += 1
            return True
        return False

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            nom=data["nom"],
            type=data["type"],
            commune=data["commune"],
            quartier=data["quartier"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            capacite_6eme=data["capacite_6eme"],
            places_occupees=data.get("places_occupees", 0),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "type": self.type,
            "commune": self.commune,
            "quartier": self.quartier,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "capacite_6eme": self.capacite_6eme,
            "places_occupees": self.places_occupees,
            "places_restantes": self.places_restantes,
            "taux_remplissage": self.taux_remplissage,
        }


class Eleve:
    def __init__(self, id, nom, prenom, moyenne_generale, adresse,
                 latitude, longitude, voeux=None):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.moyenne_generale = moyenne_generale
        self.adresse = adresse
        self.latitude = latitude
        self.longitude = longitude
        self.voeux = voeux or []
        # Rempli par le moteur d'affectation
        self.etablissement_affecte = None
        self.statut = "en_attente"  # en_attente | affecte | liste_attente | non_affecte
        self.distance_affectation_km = None

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            nom=data["nom"],
            prenom=data["prenom"],
            moyenne_generale=data["moyenne_generale"],
            adresse=data["adresse"],
            latitude=data["latitude"],
            longitude=data["longitude"],
            voeux=data.get("voeux", []),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "moyenne_generale": self.moyenne_generale,
            "adresse": self.adresse,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "voeux": self.voeux,
            "etablissement_affecte": self.etablissement_affecte,
            "statut": self.statut,
            "distance_affectation_km": self.distance_affectation_km,
        }
