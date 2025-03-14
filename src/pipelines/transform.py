import os
import json
from config.logger import *
from jobs_api.utils import save_to_json

# Définition des chemins
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data/raw_data")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data/processed_data")

# Liste des sources à traiter
SOURCES = ["adzuna", "france_travail", "jsearch"]

def load_json_files(directory):
    """Charge tous les fichiers JSON d'un répertoire et retourne une liste de données."""
    all_data = []
    if not os.path.exists(directory):
        warning(f"Dossier non trouvé : {directory}")
        return []

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                all_data.extend(data if isinstance(data, list) else [data])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            error(f"Erreur lors de la lecture {file_path} : {e}")

    return all_data

def deduplicate_jobs(jobs):
    """Supprime les doublons dans une liste d'offres en se basant sur l'ID externe."""
    seen_ids = set()
    unique_jobs = []

    for job in jobs:
        job_id = job.get("external_id")
        if job_id and job_id not in seen_ids:
            seen_ids.add(job_id)
            unique_jobs.append(job)

    return unique_jobs

def deduplicate_after_merge(jobs):
    """Déduplique après fusion en vérifiant entreprise + intitulé."""
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = (job["company"], job["title"])  # Clé unique : même entreprise + même titre
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs

# Harmonisation des structures pour chaque source
def harmonize_adzuna(job):
    """Transforme une offre Adzuna pour l'harmoniser avec les autres sources."""
    return {
        "source": "Adzuna",
        "external_id": job.get("id"),
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name"),
        "location": job.get("location", {}).get("display_name"),
        "contract_type": job.get("contract_type"),
        "description": None, # Description scindée pour adzuna
        "created_at": job.get("created")
    }

def harmonize_france_travail(job):
    """Transforme une offre France Travail pour l'harmoniser avec les autres sources."""
    return {
        "source": "France Travail",
        "external_id": job.get("id"),
        "title": job.get("intitule"),
        "company": job.get("entreprise", {}).get("nom"),
        "location": job.get("lieuTravail", {}).get("libelle"),
        "contract_type": job.get("typeContrat"),
        "description": job.get("description"),
        "created_at": job.get("dateCreation")
    }

def harmonize_jsearch(job):
    """Transforme une offre JSearch pour l'harmoniser avec les autres sources."""
    return {
        "source": "JSearch",
        "external_id": job.get("job_id"),
        "title": job.get("job_title"),
        "company": job.get("employer_name"),
        "location": job.get("job_location"),
        "contract_type": job.get("job_employment_type"),
        "description": job.get("job_description"),
        "created_at": job.get("job_posted_at")
    }

def transform_jobs():
    """Charge, nettoie, fusionne et sauvegarde les offres transformées."""
    all_transformed_jobs = []

    # Charger et transformer les données source par source
    for source in SOURCES:
        source_dir = os.path.join(RAW_DATA_DIR, source, "output")
        raw_jobs = load_json_files(source_dir)

        if source == "adzuna":
            structured_jobs = [harmonize_adzuna(job) for job in raw_jobs]
        elif source == "france_travail":
            structured_jobs = [harmonize_france_travail(job) for job in raw_jobs]
        elif source == "jsearch":
            structured_jobs = [harmonize_jsearch(job) for job in raw_jobs]
        else:
            continue  # Ignore une source inconnue

        # Déduplication interne
        unique_jobs = deduplicate_jobs(structured_jobs)
        all_transformed_jobs.extend(unique_jobs)

    # Déduplication après fusion
    final_jobs = deduplicate_after_merge(all_transformed_jobs)

    # Sauvegarde des offres transformées
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    save_to_json(final_jobs, "processed_data", "transformed_jobs.json")

    info(f"Transformation terminée : {len(final_jobs)} offres sauvegardées.")

if __name__ == "__main__":
    transform_jobs()
