from jobs_api.adzuna_api import *
from config_loader import *

# Définir les répertoires et fichiers de sortie
OUTPUT_DIRECTORY = "/Users/dani/Git-Repo/Job_Market/data/Adzuna/output"
NO_RESULTS_FILENAME = "no_results_queries.json"
CONSOLIDATED_FILENAME = "all_jobs.json"


def main():
    # Charger les queries
    queries = load_queries("../../data/job_keywords.json").get("title", [])
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
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    main()