import requests
import json
from config_loader import get_config
from utils import sanitize_filename, save_to_json


def fetch_jobs_from_adzuna(criteria):
    """
    Envoie une requête à l'API Adzuna pour récupérer plusieurs pages d'offres d'emploi
    et retourne les résultats avec le nombre total d'annonces disponibles.

    La fonction permet de récupérer les clés et les objets contenus dans les tableaux
    afin d'avoir uniquement les valeurs dont on a besoin.
    Les valeurs sont définies dans une variable ci-dessous

    :param criteria : permet de définir les critères de recherche
    """
    # Charger les variables d'environnements et récupérer les credentials
    adzuna_config = get_config()

    adzuna_base_url = adzuna_config["adzuna"]["BASE_URL"]
    adzuna_app_id = adzuna_config["adzuna"]["APP_ID"]
    adzuna_app_key = adzuna_config["adzuna"]["APP_KEY"]


    # Définir la page de départ
    page = 1
    pays = "fr"
    total_count = 0

    # Clés spécifiques à extraire
    keys_to_extract = ["id", "title", "company", "location", "location_area",
                       "salary_min", "salary_max", "category", "redirect_url", "longitude", "latitude"]

    # Stocker la sortie dans une liste
    results = []

    while True:
        print(f"Récupération de la page {page}...\n")
        url = f"{adzuna_base_url}/{pays}/search/{page}"
        params = {
            "app_id": adzuna_app_id,
            "app_key": adzuna_app_key,
            "title_only": criteria["query"],
            # "what_exclude" : criteria["what_exclude"],
            "results_per_page": criteria["results_per_page"]
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()

            # Récupérer le nombre total d'annonces à la première requête
            if page == 1 :
                total_count = data.get("count", 0)
                print(f"Nombre total d'annonces disponibles : {total_count}\n")

            # Ajouter les résultats de la page courante
            page_results = []
            for job in data.get("results", []):
                filtered_jobs = {key: job.get(key) for key in keys_to_extract}

                # Extraire le nom de l'entreprise de la clé "display_name" dans l'objet "company"
                if "company" in job and "display_name" in job["company"]:
                    filtered_jobs["company"] = job["company"]["display_name"]

                # Extraire la localisation
                if "location" in job and "display_name" in job["location"]:
                    filtered_jobs["location"] = job["location"].get("display_name")
                    filtered_jobs["location_area"] = job["location"].get("area", [])

                # Extraire le domaine d'activité
                if "category" in job and "label" in job["category"]:
                    # Renommer 'category' en 'field'
                    filtered_jobs["field"] = job["category"]["label"]
                    del filtered_jobs["category"]

                page_results.append(filtered_jobs)
            results.extend(page_results)

            # Arrêt anticipé si moins de résultats
            if len(page_results) < criteria["results_per_page"]:
                print("\nFin de la pagination\n")
                break
        else:
            print(f"Erreur {response.status_code}: {response.text}")
            break

        print(f"Nombre d'annonces récupérées : {len(results)}\n")

        page += 1  # Passer à la page suivante

    return results, total_count


def load_adzuna_queries(file_path):
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


def remove_adzuna_duplicates(results):
    """
    Supprime les doublons des offres d'emploi dans le fichier consolidé
    en se basant sur l'identifiant unique (ID) de chaque offre.

    :param results: Dictionnaire contenant les résultats combinés des offres d'emploi.
                    Doit inclure une clé "jobs" avec une liste d'offres.
    :return: Dictionnaire filtré sans doublons.
    """
    unique_jobs = []
    seen_ids = set()  # Ensemble pour stocker les IDs déjà vus

    for job in results.get("jobs", []):
        job_id = job.get("id")
        if job_id not in seen_ids:
            unique_jobs.append(job)
            seen_ids.add(job_id)

    # Mise à jour du dictionnaire consolidé avec les jobs uniques
    filtered_results = {
        "total_count": len(unique_jobs),
        "jobs": unique_jobs
    }

    return filtered_results



def remove_no_results_terms(job_titles_path, no_results_queries):
    """
    Supprime les termes du fichier job_keywords.json qui n'ont retourné aucun résultat.

    :param job_titles_path: Chemin vers le fichier job_keywords.json.
    :param no_results_queries: Liste des termes sans résultat.
    """
    try:
        # Charger les données actuelles du fichier job_keywords.json
        with open(job_titles_path, "r", encoding="utf-8") as file:
            job_titles = json.load(file)

        # Supprimer les termes sans résultat
        job_titles["title"] = [term for term in job_titles.get("title", []) if term not in no_results_queries]

        # Écrire les données mises à jour dans le fichier job_keywords.json
        with open(job_titles_path, "w", encoding="utf-8") as file:
            json.dump(job_titles, file, indent=4, ensure_ascii=False)

    except Exception as e:
        print(f"Erreur lors de la mise à jour de {job_titles_path} : {e}")



OUTPUT_DIRECTORY = "/Users/dani/Git-Repo/Job_Market/data/Adzuna/output"
NO_RESULTS_FILENAME = "no_results_queries.json"
CONSOLIDATED_FILENAME = "all_jobs.json"


def main():
    # Charger les queries
    queries = load_adzuna_queries("../../data/job_keywords.json").get("title", [])
    # exclusions = load_queries("../job_keywords.json").get("what_exclude", [])

    print(f"Titres à rechercher : {queries}\n")
    all_results = {}  # Dictionnaire pour stocker tous les résultats combinés
    no_results_queries = []  # Liste pour stocker les queries sans résultat

    for query in queries :
        print(f"Recherche en cours pour : '{query}'...")
        params = {
            "query": query,
            # "what_exclude": exclusions,
            "results_per_page": 50,
        }

        # Récupérer les résultats pour la requête envoyée selon les critères définis
        # dans le dictionnaire search_criteria
        jobs, total_count = fetch_jobs_from_adzuna(params)

        # Si aucun résultat, ajouter le terme à la liste no_results_queries
        if total_count == 0:
            print(f"  -> Aucun résultat trouvé pour '{query}', passage à la requête suivante.\n")
            no_results_queries.append(query)
            continue

        print(f"  -> Nombre total d'annonces : {total_count}")
        print(f"  -> Nombre d'annonces récupérées : {len(jobs)}\n")

        # Sauvegarder les résultats et créer un fichier par requête sinon ignorer
        if jobs:
            filename = sanitize_filename(f"jobs_{query.lower()}.json")
            save_to_json({"total_count": total_count, "jobs": jobs}, filename=filename, directory=OUTPUT_DIRECTORY)

            # Mettre à jour le fichier combiné pour regrouper tous les résultats
            all_results["total_count"] = all_results.get("total_count", 0) + total_count
            all_results.setdefault("jobs", []).extend(jobs)

    # Sauvegarder un fichier combiné pour toutes les requêtes
    if all_results:
        unique_jobs = remove_adzuna_duplicates(all_results)
        save_to_json(unique_jobs, filename=CONSOLIDATED_FILENAME, directory=OUTPUT_DIRECTORY)

        print(f"Tous les résultats sont sauvegardés dans : {OUTPUT_DIRECTORY}/{CONSOLIDATED_FILENAME}")


    # Sauvegarder la liste des queries sans résultat
    if no_results_queries:
        # Supprime les termes du fichier job_keywords.json qui n'ont retourné aucun résultat
        remove_no_results_terms("../job_keywords.json", no_results_queries)
        save_to_json(no_results_queries, filename=NO_RESULTS_FILENAME, directory=OUTPUT_DIRECTORY)


if __name__ == "__main__":
    main()