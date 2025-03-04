import os
import requests
from config_loader import get_config
from utils import save_to_json


def fetch_job_from_linkedin(params: dict):
    """
    Récupère les offres d'emploi depuis l'API LinkedIn via Rapid API en gérant la pagination par offset.
    L'API récupère les offres d'emploi publiées les sept derniers jours.
    Il est possible de récupérer des offres plus récentes, jusqu'à 1h de publication, mais nous ne limitons
    à cet endpoint au pour des raisons de limitations de requêtes.

    Les appels sont effectués avec offset = 0, puis 100 et 200 (si nécessaire).
    Si un appel retourne moins de 100 résultats, la pagination s'arrête.

    @param params: Dictionnaire contenant au minimum les filtres pour la requête, par exemple :
                   {
                     "title_filter": "Data Engineer in France",
                     "location_filter": "fr"
                   }
    """
    # Charger l'environnement et les credentials
    linkedin_config = get_config()
    linkedin_base_url = linkedin_config['linkedin']["BASE_URL"]
    linkedin_host = linkedin_config['linkedin']['HOST']
    linkedin_key = linkedin_config['linkedin']['APP_KEY']

    # Définir l'URL complète de l'API
    url = f"{linkedin_base_url}"

    # Définir les fichiers et répertoire de sortie
    OUTPUT_DIR = "/Users/dani/Git-Repo/Job_Market/data/linkedin/output"
    OUTPUT_FILE = "linkedin_jobs.json"

    headers = {
        'Content-Type': 'application/json',
        'x-rapidapi-host': linkedin_host,
        'x-rapidapi-key': linkedin_key,
    }

    all_jobs = []
    limit = 100  # L'API retourne 100 résultats par appel

    # Boucle sur les offsets 0, 100 et 200
    for offset in [0, 100, 200]:
        # Préparer les paramètres pour la requête
        linkedin_query_params = {
            "query": params.get("advanced_title_filter", ""),
            "country": params.get("location_filter", ""),
            "offset": offset,
            "limit": limit
        }
        print(f"Envoi de la requête avec offset = {offset}...")
        response = requests.get(url = url, headers = headers, params = linkedin_query_params)

        if response.status_code == 200:
            data = response.json()
            # Si la réponse est directement une liste, on l'utilise telle quelle ;
            # sinon, on tente de récupérer une liste depuis une clé "results"
            if isinstance(data, list):
                jobs = data
            elif isinstance(data, dict):
                jobs = data.get("results", [])
            else:
                jobs = []

            all_jobs.extend(jobs)
            print(f"Offset {offset} : {len(jobs)} offres récupérées.")

            # Si moins de 100 résultats sont retournés, il n'y a plus de pages
            if len(jobs) < limit:
                break
        else:
            print(f"Erreur: {response.status_code} - {response.text}")
            break

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
    # Exemple d'appel : on utilise "title_filter" et "location_filter" conformément à la fonction
    fetch_job_from_linkedin({
        "title": "'Data Engineer'",
        "country": "France"
    })
