"""
Génération de rapports d'affectation — GAB-ORIENT 6è
"""
import json
try:
    import yaml
except Exception:
    yaml = None


def generer_rapport(eleves, etablissements):
    affectes = [e for e in eleves if e.statut == "affecte"]
    liste_attente = [e for e in eleves if e.statut == "liste_attente"]
    non_affectes = [e for e in eleves if e.statut == "non_affecte"]

    rapport = {
        "resume": {
            "total_eleves": len(eleves),
            "total_affectes": len(affectes),
            "total_liste_attente": len(liste_attente),
            "total_non_affectes": len(non_affectes),
        },
        "affectations": [e.to_dict() for e in affectes],
        "liste_attente": [e.to_dict() for e in liste_attente],
        "non_affectes": [e.to_dict() for e in non_affectes],
        "etablissements": [etab.to_dict() for etab in etablissements],
    }
    return rapport


def exporter_yaml(rapport, chemin):
    if yaml is None:
        # PyYAML absent — fallback: write JSON content but keep .yaml filename
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("# PyYAML absent — contenu sérialisé au format JSON pour compatibilité\n")
            json.dump(rapport, f, ensure_ascii=False, indent=2)
        return

    with open(chemin, "w", encoding="utf-8") as f:
        yaml.dump(rapport, f, allow_unicode=True, sort_keys=False)


def exporter_json(rapport, chemin):
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
