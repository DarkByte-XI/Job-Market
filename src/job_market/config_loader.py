import yaml
import json


def load_credentials(file_path):
    """
    Charge les identifiants d'accès à l'API depuis un fichier YAML.
    Plus d'infos sur https://developer.adzuna.com/
    """
    with open(file_path, "r") as file:
        return yaml.safe_load(file)



def load_queries(file_path):
    """
    Charge les requêtes spécifiques depuis un fichier JSON.
    La fonction retourne les valeurs dans la clé title qui correspond aux requêtes,
    ainsi que le format adapté aux exclusions pris en charge par l'API (séparateur espace).
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Retourne la liste des jobs titles et les exclusions
    # dans le format adapté à l'API
    return {
        "title": data.get("title", []),
        "what_exclude" : " ".join(data.get("what_exclude", []))
    }

