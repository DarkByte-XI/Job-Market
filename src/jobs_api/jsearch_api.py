import requests
from config.logger import *
from config.config_loader import get_config

# Configuration des logs
logging.basicConfig(level = logging.INFO, format = "%(asctime)s - %(levelname)s - %(message)s")

# Charger les credentials API
jsearch_config = get_config()
JSEARCH_BASE_URL = jsearch_config["jsearch"]["BASE_URL"]
JSEARCH_HOST = jsearch_config["jsearch"]["HOST"]
JSEARCH_KEY = jsearch_config["jsearch"]["APP_KEY"]


def fetch_jobs_from_jsearch(query, country="fr", pages=1):
    """
    Récupère les offres d'emploi depuis l'API JSearch avec pagination.

    :param query: Titre du job recherché.
    :param country: Code pays (ex: 'fr' pour France).
    :param pages: Nombre de pages à récupérer.
    :return: Liste des offres d'emploi brutes.
    """
    url = f"{JSEARCH_BASE_URL}"
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": JSEARCH_HOST,
        "x-rapidapi-key": JSEARCH_KEY,
    }

    all_jobs = []

    for page in range(1, pages + 1):
        params = {
            "query": f"{query} in {country}",
            "country": country,
            "page": page,
            "num_pages": pages,
            "date_posted": "all"
        }

        try:
            response = requests.get(url, headers = headers, params = params)
            response.raise_for_status()
            data = response.json()

            jobs = data.get("data", [])
            info(f"Page {page}/{pages} - {len(jobs)} offres récupérées pour '{query}'.")
            all_jobs.extend(jobs)

            # Si aucune offre retournée sur une page, on arrête la pagination
            if not jobs:
                break

        except requests.exceptions.RequestException as e:
            error(f"Erreur API JSearch : {e}")
            break

    return all_jobs
