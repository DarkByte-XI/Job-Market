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
        "france_travail":{
            "ID": os.getenv("FRANCE_TRAVAIL_ID"),
            "KEY": os.getenv("FRANCE_TRAVAIL_KEY"),
            "SCOPE": os.getenv("FRANCE_TRAVAIL_SCOPES")
        }

        #"upwork": {
        #    "BASE_URL": os.getenv("UPWORK_BASE_URL"),
        #    "HOST": os.getenv("UPWORK_HOST"),
        #    "APP_KEY": os.getenv("UPWORK_KEY")
        #}
    }

    for api, creds in config.items():
        missing = [key for key, value in creds.items() if not value]
        if missing:
            raise ValueError(f"Pour l'API {api}, les variables manquantes : {', '.join(missing)}")

    return config
