import requests
from config_loader import get_config
from utils import save_to_json


def fetch_job_from_jsearch(params):
    # Charger l'environnement de travail et les credentials
    jsearch_config = get_config()

    jsearch_base_url = jsearch_config['jsearch']["BASE_URL"]
    jsearch_host = jsearch_config['jsearch']['HOST']
    jsearch_key = jsearch_config['jsearch']['APP_KEY']

    # Définir l'URL complète de l'API
    url = f"{jsearch_base_url}"

    headers = {
        'Content-Type': 'application/json',
        'x-rapidapi-host': f"{jsearch_host}",
        'x-rapidapi-key': f"{jsearch_key}",
    }

    # Préparer les paramètres pour la requête
    jsearch_query_params = {
        "query": params.get("query", ""),
        "country": params.get("country", ""),
        "page": params.get("page", ""),
        "num_pages": params.get("num_pages", ""),
        "date_posted": params.get("date_posted", "")
    }
    # Exécuter la requête
    response = requests.get(url = url, headers = headers, params = jsearch_query_params)
    if response.status_code == 200:
        data = response.json()
        # On récupère les offres directement dans "data".
        jobs = data.get("data", [])
        print(f"Nombre d'offres récupérées pour la requête '{params.get('query', '')}': {len(jobs)}")
        return jobs
    else:
        print(f"Erreur: {response.status_code} - {response.text}")
        return []


if __name__ == "__main__":
    OUTPUT_DIR = "/Users/dani/Git-Repo/Job_Market/data/jsearch/output"
    OUTPUT_FILE = "jsearch_jobs.json"
    all_jobs = []
    queries = ["Data Engineer", "Data Analyst", "Big Data"]

    # Pour chaque requête, on récupère les offres et on les ajoute à la liste globale
    for query in queries:
        print(f"Récupération d'offres pour : {query}")
        params = {
            "query": f"{query} in France",
            "page": "10",
            "num_pages": "10",
            "country": "fr",
            "date_posted": "all"
        }
        jobs = fetch_job_from_jsearch(params)
        all_jobs.extend(jobs)

    print(f"Nombre total d'offres combinées: {len(all_jobs)}")

    # Sauvegarder les résultats combinés
    try:
        if all_jobs:
            save_to_json(all_jobs, filename = OUTPUT_FILE, directory = OUTPUT_DIR)
            print(f"Fichier sauvegardé dans {OUTPUT_DIR}")
        else:
            print("Aucune offre n'a été récupérée.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans le fichier JSON : {e}")
