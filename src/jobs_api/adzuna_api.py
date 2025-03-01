import requests
import json
import os
import re
from config_loader import get_config

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
        url = f"{adzuna_config["adzuna"]["HOST"]}/{pays}/search/{page}"
        params = {
            "app_id": adzuna_config["adzuna"]["APP_ID"],
            "app_key": adzuna_config["adzuna"]["APP_KEY"],
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



def sanitize_filename(filename) :
    """
    Nettoie un nom de fichier en supprimant ou remplaçant les caractères invalides afin
    d'avoir un format lisible et compatible.

    :param filename: Le nom de fichier à nettoyer.
    :return: Un nom de fichier valide.
    """

    # Nettoie et supprime les caractères invalides
    filename = re.sub(r'\s*/\s*', '_', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = re.sub(r'[\\:*?"<>|]', '', filename)

    return filename



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



def save_to_json(data, filename, directory="."):
    """
    Sauvegarde les données dans un fichier JSON formaté dans un répertoire donné.

    :param data: Les données à écrire dans le fichier JSON.
    :param filename: Le nom du fichier de sortie.
    :param directory: Le répertoire où enregistrer le fichier.
    """
    try:
        # S'assurer que le répertoire existe
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Construire le chemin complet du fichier
        filepath = os.path.join(directory, filename)

        # Écrire les données dans le fichier JSON
        with open(filepath, mode="w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        print(f"Les données ont été sauvegardées dans le fichier '{filepath}'.\n")
        print("-" * 50)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans le fichier JSON : {e}")
        print("-" * 50)