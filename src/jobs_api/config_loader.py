import os
import logging
from dotenv import load_dotenv

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_config():
    """
    Charge les configurations des différentes APIs à partir des variables d'environnement.
    :return: Dictionnaire contenant les configs des APIs
    """

    # Charger les variables d'environnement depuis le fichier .env
    load_dotenv()

    config = {
        "adzuna": {
            "BASE_URL": os.getenv("ADZUNA_BASE_URL"),
            "APP_ID": os.getenv("ADZUNA_APP_ID"),
            "APP_KEY": os.getenv("ADZUNA_APP_KEY")
        },
        "rapid_api": {
            "HOST": os.getenv("RAPID_API_HOST"),
            "BASE_URL": os.getenv("RAPID_BASE_URL"),
            "APP_KEY": os.getenv("RAPID_API_KEY")
        },
        "jsearch": {
            "HOST": os.getenv("JSEARCH_HOST"),
            "BASE_URL": os.getenv("JSEARCH_BASE_URL"),
            "APP_KEY": os.getenv("JSEARCH_KEY")
        },
        "linkedin": {
            "HOST": os.getenv("LINKEDIN_HOST"),
            "BASE_URL": os.getenv("LINKEDIN_BASE_URL"),
            "APP_KEY": os.getenv("LINKEDIN_KEY")
        },
        "france_travail": {
            "ID": os.getenv("FRANCE_TRAVAIL_ID"),
            "KEY": os.getenv("FRANCE_TRAVAIL_KEY"),
            "SCOPE": os.getenv("FRANCE_TRAVAIL_SCOPES")
        }
    }

    # Vérifier les variables manquantes
    for api, creds in config.items():
        missing_keys = [key for key, value in creds.items() if not value]
        if missing_keys:
            logging.warning(f"API {api}: Variables manquantes - {', '.join(missing_keys)}")
        else:
            logging.info(f"API {api}: Toutes les variables sont chargées.")

    return config
