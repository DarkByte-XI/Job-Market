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

    # Définir les fichiers et répertoire de sortie
    OUTPUT_DIR = "/Users/dani/Git-Repo/Job_Market/data/jsearch/output"
    OUTPUT_FILE = "jsearch_jobs.json"

    headers = {
        'Content-Type': 'application/json',
        'x-rapidapi-host': f"{jsearch_host}",
        'x-rapidapi-key': f"{jsearch_key}",
    }

    all_jobs = []


    # Préparer les paramètres pour la requête
    jsearch_query_params = {
        "query": params.get("query", ""),
        "country": params.get("country", ""),
        "page": params.get("page", ""),
        "num_pages": params.get("num_pages", "")
    }
    # Exécuter la requête
    response = requests.get(url = url, headers = headers, params = jsearch_query_params)
    if response.status_code == 200:
        data = response.json()
        jobs = data.get("data", [])
        all_jobs.extend(jobs)
        print(f"Nombre d'offres récupérées : {len(all_jobs)}")
    else:
        print(f"Erreur: {response.status_code} - {response.text}")
    # Sauvegarder les résultats si récupérés
    try:
        if all_jobs:
            save_to_json(all_jobs, filename = OUTPUT_FILE, directory = OUTPUT_DIR)
            print(f"Fichier sauvegardé dans {OUTPUT_DIR}")
        else:
            print("Aucune offre n'a été récupérée.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans le fichier JSON : {e}")


if __name__ == "__main__":
    fetch_job_from_jsearch({"query":"Data Engineer in France",
                            "page":"1",
                            "num_pages":"20",
                            "country":"fr",
                            "date_posted":"all"})


