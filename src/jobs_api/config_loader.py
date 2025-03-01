import json
import os
from dotenv import load_dotenv, find_dotenv


def get_config():
    """
    @return: dictionnaire contenant les configs des différentes API
    """

    # Charger les variables d'environnement
    load_dotenv(find_dotenv())

    config = {
        "adzuna": {
            "HOST": os.getenv("ADZUNA_BASE_URL"),
            "APP_ID": os.getenv("ADZUNA_APP_ID"),
            "APP_KEY": os.getenv("ADZUNA_APP_KEY"),
        },
        "rapid_api": {
            "HOST": os.getenv("RAPID_API_HOST"),
            "APP_KEY": os.getenv("RAPID_API_KEY"),
        }
    }

    for api, creds in config.items():
        missing = [key for key, value in creds.items() if not value]
        if missing:
            raise ValueError(f"Pour l'API {api}, les variables manquantes : {', '.join(missing)}")

    return config


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

