import requests
from config.logger import *
from config.config_loader import get_config

# Configuration des logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Charger les credentials API
adzuna_config = get_config()
ADZUNA_BASE_URL = adzuna_config["adzuna"]["BASE_URL"]
ADZUNA_APP_ID = adzuna_config["adzuna"]["APP_ID"]
ADZUNA_APP_KEY = adzuna_config["adzuna"]["APP_KEY"]


def fetch_jobs_from_adzuna(criteria):
    """
    Récupère les offres d'emploi depuis l'API Adzuna en paginant.
    :param criteria: Dictionnaire contenant les critères de recherche (ex: {"query": "Data Engineer", "results_per_page": 50})
    :return: Liste des offres brutes (JSON)
    """
    page = 1
    country = "fr"
    total_count = 0
    results = []

    while True:
        info(f"Récupération de la page {page} pour '{criteria['query']}'...")

        url = f"{ADZUNA_BASE_URL}/{country}/search/{page}"
        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "what_phrase": criteria["query"],
            "results_per_page": criteria["results_per_page"]
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Stocker le nombre total d'annonces
            if page == 1:
                total_count = data.get("count", 0)
                info(f"Nombre total d'annonces disponibles : {total_count}")

            # Récupérer les résultats
            page_results = data.get("results", [])
            if not page_results:
                info("Fin de la pagination : plus d'offres disponibles.")
                break  # Arrêter si plus de résultats

            results.extend(page_results)
            page += 1  # Passer à la page suivante

            # Arrêt anticipé si le nombre récupéré est inférieur à `results_per_page`
            if len(page_results) < criteria["results_per_page"]:
                info("Fin de la pagination (moins de résultats que demandés).")
                break

        except requests.exceptions.RequestException as e:
            error(f"Erreur API Adzuna : {e}")
            break

    return results, total_count
