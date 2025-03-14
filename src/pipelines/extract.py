import os
from config.logger import *
from jobs_api.utils import load_json_safely, save_to_json
from jobs_api.adzuna_api import fetch_jobs_from_adzuna
from jobs_api.france_travail_api import get_bearer_token, fetch_jobs_from_france_travail
from jobs_api.jsearch_api import fetch_jobs_from_jsearch


# Déterminer le chemin racine du projet (Job_Market)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

# Chemins vers les fichiers de ressources
RESSOURCES_DIR = os.path.join(BASE_DIR, "ressources")
JOB_KEYWORDS_FILE = os.path.join(RESSOURCES_DIR, "job_keywords.json")
APPELLATIONS_FILE = os.path.join(RESSOURCES_DIR, "data_appellations.json")

# Chemin vers le répértoire de sauvegarde
RAW_DATA_DIR = os.path.join(BASE_DIR, "data/raw_data")
ADZUNA_OUTPUT_DIR = os.path.join(RAW_DATA_DIR, "adzuna/output")
FT_OUTPUT_DIR = os.path.join(RAW_DATA_DIR, "france_travail/output")
JS_OUTPUT_DIR = os.path.join(RAW_DATA_DIR, "jsearch/output")


def extract_all_jobs():
    """Orchestration : récupère les offres d'emploi de toutes les APIs et les unifie."""
    info("Début de l'extraction des offres d'emploi...")

    # Charger les requêtes pour Adzuna
    job_keywords = load_json_safely(JOB_KEYWORDS_FILE)
    job_queries = job_keywords.get("title", []) if job_keywords else []

    # Charger les appellations pour France Travail
    appellations = load_json_safely(APPELLATIONS_FILE)
    job_appellations = [app["code"] for app in appellations] if appellations else []

    all_jobs = []

    # Extraction depuis Adzuna avec plusieurs mots-clés
    adzuna_jobs = []
    for query in job_queries:
        criteria = {"query": query, "results_per_page": 50}
        jobs, _ = fetch_jobs_from_adzuna(criteria)
        adzuna_jobs.extend(jobs)

    save_to_json(adzuna_jobs, ADZUNA_OUTPUT_DIR, "adzuna")  # Sauvegarde brute
    all_jobs.extend(adzuna_jobs)

    # Extraction depuis France Travail avec les appellations sélectionnées.
    france_travail_jobs = []
    token = get_bearer_token()
    if token:
        for code in job_appellations:
            jobs = fetch_jobs_from_france_travail(token, code)
            france_travail_jobs.extend(jobs)

    save_to_json(france_travail_jobs, FT_OUTPUT_DIR, "france_travail")  # Sauvegarde brute
    all_jobs.extend(france_travail_jobs)

    # Extraction depuis JSearch
    jsearch_jobs = fetch_jobs_from_jsearch("Data Engineer", pages = 10)
    save_to_json(jsearch_jobs, JS_OUTPUT_DIR, "jsearch")  # Sauvegarde brute
    all_jobs.extend(jsearch_jobs)

    return all_jobs  # Retourne les données brutes, sans modification

if __name__ == "__main__":
    extract_all_jobs()