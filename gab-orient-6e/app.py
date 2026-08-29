"""
GAB-ORIENT 6è — Application Flask
Solution logicielle pour l'affectation automatisée et géolocalisée
des élèves de CM2 en classe de 6ème au Gabon.
"""
import os
import io
import csv
import shutil
import urllib.parse
import urllib.request
from datetime import datetime
try:
    import yaml
except Exception:
    yaml = None
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response

from src.models import Eleve, Etablissement
from src.affectation import MoteurAffectation
from src.rapport import generer_rapport, exporter_yaml, exporter_json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
ARCHIVE_DIR = os.path.join(OUTPUT_DIR, "archives")
ETAT_PATH = os.path.join(OUTPUT_DIR, "etat_campagne.yaml")
ANNEE_PATH = os.path.join(DATA_DIR, "annee_courante.yaml")

# ⚠️ À changer avant toute mise en ligne réelle : ceci est un mot de passe
# de démonstration pour le projet académique, pas une sécurité de production.
MOT_DE_PASSE_ADMIN = "gabon2026"

app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.secret_key = os.environ.get("SECRET_KEY", "cle-secrete-projet-gab-orient-6e")


@app.before_request
def verifier_connexion():
    routes_publiques = {"connexion", "static"}
    if request.endpoint in routes_publiques or request.endpoint is None:
        return
    if not session.get("connecte"):
        return redirect(url_for("connexion"))


@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    erreur = None
    if request.method == "POST":
        if request.form.get("mot_de_passe") == MOT_DE_PASSE_ADMIN:
            session["connecte"] = True
            return redirect(url_for("index"))
        erreur = "Mot de passe incorrect."
    return render_template("connexion.html", erreur=erreur)


@app.route("/deconnexion", methods=["POST"])
def deconnexion():
    session.pop("connecte", None)
    return redirect(url_for("connexion"))


def charger_yaml(nom_fichier):
    # Prefer a JSON sidecar if present (avoid dependency on PyYAML for quick local tests)
    chemin_yaml = os.path.join(DATA_DIR, nom_fichier)
    chemin_json = os.path.splitext(chemin_yaml)[0] + ".json"

    # Prefer YAML file when present; fall back to JSON sidecar only if YAML missing.
    if os.path.exists(chemin_yaml):
        if yaml is None:
            raise RuntimeError(
                "PyYAML non disponible alors que le fichier YAML existe. Installez PyYAML ou supprimez le fichier YAML pour utiliser JSON."
            )
        with open(chemin_yaml, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    if os.path.exists(chemin_json):
        with open(chemin_json, "r", encoding="utf-8") as f:
            return json.load(f)

    # Neither YAML nor JSON found
    return {}


def rechercher_adresses(adresse, limite=5):
    """Retourne plusieurs suggestions de lieux correspondants à une adresse."""
    adresse = (adresse or "").strip()
    if not adresse:
        return []

    params = urllib.parse.urlencode({"q": adresse, "format": "jsonv2", "limit": limite})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    requete = urllib.request.Request(
        url,
        headers={
            "User-Agent": "GabOrient6e/1.0 (gestionnaire-ecole@local)",
            "Accept-Language": "fr",
        },
    )

    with urllib.request.urlopen(requete, timeout=10) as reponse:
        donnees = json.loads(reponse.read().decode("utf-8"))

    suggestions = []
    for item in donnees:
        try:
            suggestions.append({
                "label": item.get("display_name", adresse),
                "latitude": float(item["lat"]),
                "longitude": float(item["lon"]),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return suggestions


def geocoder_adresse(adresse):
    """Retourne les coordonnées GPS d'une adresse via l'API OpenStreetMap Nominatim."""
    suggestions = rechercher_adresses(adresse, limite=1)
    if not suggestions:
        return None, "Aucune coordonnée trouvée pour cette adresse."

    resultat = suggestions[0]
    return {
        "latitude": resultat["latitude"],
        "longitude": resultat["longitude"],
        "label": resultat["label"],
    }, None


def charger_donnees():
    """Charge les données SOURCES (élèves, établissements, paramètres),
    inchangées quel que soit le nombre de campagnes déjà lancées."""
    eleves_data = charger_yaml("eleves.yaml")["eleves"]
    etabs_data = charger_yaml("carte_scolaire.yaml")["etablissements"]
    parametres = charger_yaml("parametres.yaml")

    eleves = [Eleve.from_dict(d) for d in eleves_data]
    etablissements = [Etablissement.from_dict(d) for d in etabs_data]
    return eleves, etablissements, parametres


def sauvegarder_etat_campagne(eleves, etablissements):
    """Persiste le résultat de la dernière campagne d'affectation,
    séparément des données sources, pour que toutes les pages restent
    synchronisées après un lancement."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    etat = {
        "eleves": {
            e.id: {
                "statut": e.statut,
                "etablissement_affecte": e.etablissement_affecte,
                "distance_affectation_km": e.distance_affectation_km,
            }
            for e in eleves
        },
        "etablissements": {
            etab.id: {"places_occupees": etab.places_occupees}
            for etab in etablissements
        },
    }
    with open(ETAT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(etat, f, allow_unicode=True, sort_keys=False)


def appliquer_etat_campagne(eleves, etablissements):
    """Recharge la dernière campagne persistée (s'il y en a une) et
    l'applique aux objets fraîchement chargés depuis les données sources."""
    if not os.path.exists(ETAT_PATH):
        return
    with open(ETAT_PATH, "r", encoding="utf-8") as f:
        etat = yaml.safe_load(f) or {}

    etat_eleves = etat.get("eleves", {})
    for e in eleves:
        info = etat_eleves.get(e.id)
        if info:
            e.statut = info["statut"]
            e.etablissement_affecte = info["etablissement_affecte"]
            e.distance_affectation_km = info["distance_affectation_km"]

    etat_etabs = etat.get("etablissements", {})
    for etab in etablissements:
        info = etat_etabs.get(etab.id)
        if info:
            etab.places_occupees = info["places_occupees"]


def sauvegarder_etablissements(etabs_data):
    """Réécrit le fichier source carte_scolaire.yaml avec la liste
    d'établissements fournie (utilisé pour l'ajout d'une nouvelle école)."""
    chemin = os.path.join(DATA_DIR, "carte_scolaire.yaml")
    with open(chemin, "w", encoding="utf-8") as f:
        yaml.dump({"etablissements": etabs_data}, f, allow_unicode=True, sort_keys=False)


def prochain_id_etablissement(etabs_data):
    import re
    numeros = []
    prefixes = {}
    for e in etabs_data:
        m = re.search(r"^(?P<prefix>[^0-9]+)(?P<num>[0-9]+)$", e.get("id", ""))
        if m:
            prefix = m.group("prefix")
            num = int(m.group("num"))
            numeros.append(num)
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
    if prefixes:
        # choose the most common prefix among existing ids
        chosen_prefix = max(prefixes.items(), key=lambda kv: kv[1])[0]
    else:
        chosen_prefix = "GAB"
    next_num = (max(numeros) + 1) if numeros else 1
    return f"{chosen_prefix}{next_num:03d}"


def sauvegarder_eleves(eleves_data):
    """Réécrit le fichier source eleves.yaml avec la liste de candidats
    fournie (utilisé pour l'ajout d'un élève et la remise à zéro annuelle)."""
    chemin = os.path.join(DATA_DIR, "eleves.yaml")
    with open(chemin, "w", encoding="utf-8") as f:
        yaml.dump({"eleves": eleves_data}, f, allow_unicode=True, sort_keys=False)


def prochain_id_eleve(eleves_data):
    numeros = [int(e["id"][3:]) for e in eleves_data if e["id"].startswith("ELV")]
    return f"ELV{(max(numeros) + 1) if numeros else 1:03d}"


def charger_annee_courante():
    if os.path.exists(ANNEE_PATH):
        with open(ANNEE_PATH, "r", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("annee", "Année non définie")
    # Valeur par défaut raisonnable si jamais configurée : année scolaire
    # en cours selon la date du jour (rentrée en septembre).
    aujourdhui = datetime.now()
    debut = aujourdhui.year if aujourdhui.month >= 9 else aujourdhui.year - 1
    return f"{debut}-{debut + 1}"


def sauvegarder_annee_courante(annee):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ANNEE_PATH, "w", encoding="utf-8") as f:
        yaml.dump({"annee": annee}, f, allow_unicode=True)


def demarrer_nouvelle_annee(nouvelle_annee_label):
    """Archive la campagne et la liste de candidats de l'année écoulée
    (avec métadonnées : libellé d'année, date, résumé), puis vide la liste
    des élèves pour permettre la saisie des nouveaux candidats. Les
    établissements (carte scolaire) sont conservés tels quels d'une année
    sur l'autre."""
    annee_archivee = charger_annee_courante()
    horodatage = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = f"{annee_archivee.replace(' ', '_')}__{horodatage}"
    dossier_archive = os.path.join(ARCHIVE_DIR, slug)
    os.makedirs(dossier_archive, exist_ok=True)

    resume = None
    chemin_rapport = os.path.join(OUTPUT_DIR, "rapport_affectation.yaml")
    if os.path.exists(chemin_rapport):
        with open(chemin_rapport, "r", encoding="utf-8") as f:
            resume = (yaml.safe_load(f) or {}).get("resume")

    for nom_fichier in ["etat_campagne.yaml", "rapport_affectation.yaml", "rapport_affectation.json"]:
        chemin = os.path.join(OUTPUT_DIR, nom_fichier)
        if os.path.exists(chemin):
            shutil.move(chemin, os.path.join(dossier_archive, nom_fichier))

    chemin_eleves = os.path.join(DATA_DIR, "eleves.yaml")
    if os.path.exists(chemin_eleves):
        shutil.copy(chemin_eleves, os.path.join(dossier_archive, "eleves.yaml"))

    meta = {
        "annee": annee_archivee,
        "archive_le": datetime.now().strftime("%d/%m/%Y à %H:%M"),
        "resume": resume,
    }
    with open(os.path.join(dossier_archive, "meta.yaml"), "w", encoding="utf-8") as f:
        yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

    sauvegarder_eleves([])
    sauvegarder_annee_courante(nouvelle_annee_label)
    return slug


@app.route("/")
def index():
    eleves, etablissements, parametres = charger_donnees()
    appliquer_etat_campagne(eleves, etablissements)
    return render_template(
        "index.html",
        nb_eleves=len(eleves),
        nb_etablissements=len(etablissements),
        capacite_totale=sum(e.capacite_6eme for e in etablissements),
        annee_courante=charger_annee_courante(),
    )


@app.route("/dashboard")
def dashboard():
    eleves, etablissements, parametres = charger_donnees()
    appliquer_etat_campagne(eleves, etablissements)

    total = len(eleves)
    affectes = len([e for e in eleves if e.statut == 'affecte'])
    liste_attente = len([e for e in eleves if e.statut == 'liste_attente'])
    non_affectes = len([e for e in eleves if e.statut == 'non_affecte'])

    # capacities
    capacite_totale = sum(e.capacite_6eme for e in etablissements)
    places_occupees = sum(e.places_occupees for e in etablissements)
    taux_remplissage_global = round((places_occupees / capacite_totale * 100), 1) if capacite_totale else 0.0

    # top establishments by taux_remplissage desc
    etabs_sorted = sorted(etablissements, key=lambda x: x.taux_remplissage, reverse=True)

    # reports available
    rapport_yaml = os.path.join(OUTPUT_DIR, 'rapport_affectation.yaml')
    rapport_json = os.path.join(OUTPUT_DIR, 'rapport_affectation.json')
    has_yaml = os.path.exists(rapport_yaml)
    has_json = os.path.exists(rapport_json)

    return render_template(
        "dashboard.html",
        nb_eleves=total,
        nb_etablissements=len(etablissements),
        capacite_totale=capacite_totale,
        annee_courante=charger_annee_courante(),
        nb_affectes=affectes,
        nb_liste_attente=liste_attente,
        nb_non_affectes=non_affectes,
        taux_remplissage_global=taux_remplissage_global,
        top_etablissements=etabs_sorted[:6],
        has_yaml=has_yaml,
        has_json=has_json,
    )


@app.route('/output/<path:filename>')
def download_output(filename):
    # Serve generated report files from output/ for local preview
    from flask import send_from_directory
    if not os.path.exists(os.path.join(OUTPUT_DIR, filename)):
        return redirect(url_for('dashboard'))
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


@app.route("/eleves")
def liste_eleves():
    eleves, etablissements, parametres = charger_donnees()
    appliquer_etat_campagne(eleves, etablissements)
    return render_template("eleves.html", eleves=eleves, annee_courante=charger_annee_courante())


@app.route("/carte")
def carte():
    eleves, etablissements, parametres = charger_donnees()
    appliquer_etat_campagne(eleves, etablissements)
    return render_template(
        "carte.html",
        eleves=[e.to_dict() for e in eleves],
        etablissements=[e.to_dict() for e in etablissements],
        annee_courante=charger_annee_courante(),
    )


@app.route("/affectation", methods=["GET", "POST"])
def affectation():
    eleves, etablissements, parametres = charger_donnees()
    annee_courante = charger_annee_courante()

    if request.method == "POST":
        moteur = MoteurAffectation(eleves, etablissements, parametres)
        moteur.affecter()
        rapport = generer_rapport(eleves, etablissements)
        rapport["annee"] = annee_courante

        sauvegarder_etat_campagne(eleves, etablissements)
        exporter_yaml(rapport, os.path.join(OUTPUT_DIR, "rapport_affectation.yaml"))
        exporter_json(rapport, os.path.join(OUTPUT_DIR, "rapport_affectation.json"))

        return render_template("resultats.html", rapport=rapport)

    appliquer_etat_campagne(eleves, etablissements)
    campagne_deja_lancee = os.path.exists(ETAT_PATH)
    return render_template(
        "affectation.html",
        nb_eleves=len(eleves),
        campagne_deja_lancee=campagne_deja_lancee,
        annee_courante=annee_courante,
    )


@app.route("/affectation/reinitialiser", methods=["POST"])
def reinitialiser_campagne():
    if os.path.exists(ETAT_PATH):
        os.remove(ETAT_PATH)
    return redirect(url_for("affectation"))


@app.route("/eleves/importer", methods=["GET", "POST"])
def importer_eleves():
    erreurs = []
    nb_importes = 0

    if request.method == "POST":
        fichier = request.files.get("fichier_csv")
        if not fichier or fichier.filename == "":
            erreurs.append("Aucun fichier sélectionné.")
        else:
            try:
                contenu = fichier.read().decode("utf-8-sig")
                lecteur = csv.DictReader(io.StringIO(contenu), delimiter=";")

                colonnes_requises = {"nom", "prenom", "moyenne_generale", "adresse", "latitude", "longitude"}
                if not colonnes_requises.issubset(set(lecteur.fieldnames or [])):
                    erreurs.append(
                        "Colonnes attendues : nom;prenom;moyenne_generale;adresse;latitude;longitude;voeux "
                        f"— colonnes trouvées : {', '.join(lecteur.fieldnames or [])}"
                    )
                else:
                    eleves_data = charger_yaml("eleves.yaml")["eleves"]
                    lignes = list(lecteur)

                    for i, ligne in enumerate(lignes, start=2):
                        try:
                            voeux_bruts = ligne.get("voeux", "") or ""
                            nouvel_eleve_data = {
                                "id": prochain_id_eleve(eleves_data),
                                "nom": ligne["nom"].strip(),
                                "prenom": ligne["prenom"].strip(),
                                "moyenne_generale": float(ligne["moyenne_generale"].replace(",", ".")),
                                "adresse": ligne["adresse"].strip(),
                                "latitude": float(ligne["latitude"].replace(",", ".")),
                                "longitude": float(ligne["longitude"].replace(",", ".")),
                                "voeux": [v.strip() for v in voeux_bruts.replace(",", "|").split("|") if v.strip()],
                            }
                            eleves_data.append(nouvel_eleve_data)
                            nb_importes += 1
                        except (ValueError, KeyError) as e:
                            erreurs.append(f"Ligne {i} ignorée ({ligne.get('nom', '?')} {ligne.get('prenom', '?')}) : {e}")

                    if nb_importes > 0:
                        sauvegarder_eleves(eleves_data)
            except UnicodeDecodeError:
                erreurs.append("Le fichier doit être encodé en UTF-8 (enregistre-le en \"CSV UTF-8\" depuis Excel).")

    return render_template("importer_eleves.html", erreurs=erreurs, nb_importes=nb_importes)


@app.route("/eleves/modele-csv")
def modele_csv():
    contenu = (
        "nom;prenom;moyenne_generale;adresse;latitude;longitude;voeux\n"
        "Nguema;Sarah;15.8;Quartier Glass, Libreville;0.3895;9.4530;GAB001,GAB009\n"
        "Obame;Junior;12.4;Quartier Akébé, Libreville;0.4200;9.4640;GAB003\n"
    )
    return Response(
        contenu,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=modele_eleves.csv"},
    )


@app.route("/eleves/nouveau", methods=["GET", "POST"])
def nouvel_eleve():
    if request.method == "POST":
        eleves_data = charger_yaml("eleves.yaml")["eleves"]
        voeux_bruts = request.form.get("voeux", "")
        nouvel_eleve_data = {
            "id": prochain_id_eleve(eleves_data),
            "nom": request.form["nom"].strip(),
            "prenom": request.form["prenom"].strip(),
            "moyenne_generale": float(request.form["moyenne_generale"]),
            "adresse": request.form["adresse"].strip(),
            "latitude": float(request.form["latitude"]),
            "longitude": float(request.form["longitude"]),
            "voeux": [v.strip() for v in voeux_bruts.split(",") if v.strip()],
        }
        eleves_data.append(nouvel_eleve_data)
        sauvegarder_eleves(eleves_data)
        return redirect(url_for("liste_eleves"))

    _, etablissements, _ = charger_donnees()
    return render_template("nouvel_eleve.html", etablissements=etablissements)


@app.route("/annee-scolaire")
def annee_scolaire():
    eleves, etablissements, parametres = charger_donnees()
    campagne_en_cours = os.path.exists(ETAT_PATH)

    archives = []
    if os.path.exists(ARCHIVE_DIR):
        for nom in sorted(os.listdir(ARCHIVE_DIR), reverse=True):
            chemin_meta = os.path.join(ARCHIVE_DIR, nom, "meta.yaml")
            if os.path.exists(chemin_meta):
                with open(chemin_meta, "r", encoding="utf-8") as f:
                    meta = yaml.safe_load(f) or {}
                archives.append({"slug": nom, **meta})
            else:
                archives.append({"slug": nom, "annee": nom, "archive_le": "", "resume": None})

    return render_template(
        "annee_scolaire.html",
        nb_eleves=len(eleves),
        campagne_en_cours=campagne_en_cours,
        annee_courante=charger_annee_courante(),
        archives=archives,
    )


@app.route("/annee-scolaire/nouvelle", methods=["POST"])
def nouvelle_annee_scolaire():
    nouvelle_annee = request.form.get("nouvelle_annee", "").strip()
    if not nouvelle_annee:
        aujourdhui = datetime.now()
        debut = aujourdhui.year if aujourdhui.month >= 9 else aujourdhui.year - 1
        nouvelle_annee = f"{debut}-{debut + 1}"
    demarrer_nouvelle_annee(nouvelle_annee)
    return redirect(url_for("annee_scolaire"))


@app.route("/annee-scolaire/archives/<slug>")
def voir_archive(slug):
    dossier = os.path.join(ARCHIVE_DIR, slug)
    chemin_rapport = os.path.join(dossier, "rapport_affectation.yaml")
    if not os.path.exists(chemin_rapport):
        return redirect(url_for("annee_scolaire"))
    with open(chemin_rapport, "r", encoding="utf-8") as f:
        rapport = yaml.safe_load(f)
    return render_template("resultats.html", rapport=rapport, archive=True)


@app.route("/etablissements")
def liste_etablissements():
    eleves, etablissements, parametres = charger_donnees()
    appliquer_etat_campagne(eleves, etablissements)
    return render_template(
        "etablissements.html",
        etablissements=etablissements,
        annee_courante=charger_annee_courante(),
    )


@app.route("/etablissements/nouveau", methods=["GET", "POST"])
def nouvel_etablissement():
    if request.method == "POST":
        etabs_data = charger_yaml("carte_scolaire.yaml")["etablissements"]
        nouvel_etab = {
            "id": prochain_id_etablissement(etabs_data),
            "nom": request.form["nom"].strip(),
            "type": request.form["type"],
            "commune": request.form["commune"].strip(),
            "quartier": request.form["quartier"].strip(),
            "latitude": float(request.form["latitude"]),
            "longitude": float(request.form["longitude"]),
            "capacite_6eme": int(request.form["capacite_6eme"]),
            "places_occupees": 0,
        }
        etabs_data.append(nouvel_etab)
        sauvegarder_etablissements(etabs_data)
        return redirect(url_for("liste_etablissements"))

    return render_template("nouvel_etablissement.html")


@app.route("/api/geocode")
def api_geocode():
    adresse = request.args.get("adresse", "").strip()
    if not adresse:
        return jsonify({"error": "Adresse manquante."}), 400

    try:
        suggestions = rechercher_adresses(adresse, limite=5)
    except Exception:
        return jsonify({"error": "Impossible de récupérer les coordonnées pour cette adresse."}), 502

    if not suggestions:
        return jsonify({"error": "Aucune adresse trouvée."}), 404

    if request.args.get("mode") == "suggestions":
        return jsonify({"suggestions": suggestions})

    resultat = suggestions[0]
    return jsonify({
        "latitude": resultat["latitude"],
        "longitude": resultat["longitude"],
        "label": resultat["label"],
    })


@app.route("/api/etablissements")
def api_etablissements():
    _, etablissements, _ = charger_donnees()
    appliquer_etat_campagne([], etablissements)
    return jsonify([e.to_dict() for e in etablissements])


if __name__ == "__main__":
    app.run(debug=True, port=5000)

