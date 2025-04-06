import json
import os
import datetime
from db.db_connection import connect_db
from config.logger import info, warning, error, critical  # Import des fonctions de log
from pipelines.transform import PROCESSED_DATA_DIR



def get_latest_file(directory):
    """
    Récupère le fichier JSON le plus récent dans le répertoire spécifié.
    """
    try:
        files = [f for f in os.listdir(directory) if f.endswith(".json")]
        if not files:
            warning("Aucun fichier trouvé dans le dossier de transformation.")
            return None

        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
        return os.path.join(directory, latest_file)

    except Exception as e:
        error("Erreur lors de la recherche du fichier : {}".format(e))
        return None



def insert_source(cur, source_name):
    """Insère une source et retourne son ID.
    Si le nom est manquant ou vide, l'offre sera ignorée (retourne None)."""
    if not source_name or source_name.strip() == "":
        warning("Nom de la source manquant, offre ignorée.")
        return None

    cur.execute(
        "INSERT INTO sources (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING source_id;",
        (source_name.strip(),)
    )
    return cur.fetchone()[0]



def insert_company(cur, company_name):
    """
    Insère une entreprise et retourne son ID.
    Si le nom est manquant ou vide, on utilise None (l'insertion est autorisée avec un nom nul).
    """
    company_name = company_name.strip() if company_name and company_name.strip() != "" else None

    cur.execute(
        "INSERT INTO companies (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING company_id;",
        (company_name,)
    )
    return cur.fetchone()[0]



def insert_location(cur, location, code_postal, longitude, latitude, country):
    """
    Insère une localisation et retourne son ID.
    La table locations inclut désormais la colonne country.
    Si à la fois location et country sont absents, l'offre est ignorée.
    """
    # Vérifier si les deux sont absents
    if (not location or location.strip() == "") and (not country or country.strip() == ""):
        warning("Localisation et pays manquants, offre ignorée.")
        return None

    location = location.strip() if location and location.strip() != "" else None
    code_postal = code_postal.strip() if code_postal and code_postal.strip() != "" else None
    longitude = longitude if longitude != "" else None
    latitude = latitude if latitude != "" else None
    country = country.strip() if country and country.strip() != "" else None

    # Comparaison avec IS NOT DISTINCT FROM pour gérer les NULL
    cur.execute(
            "SELECT location_id FROM locations WHERE location IS NOT DISTINCT FROM %s AND code_postal IS NOT DISTINCT FROM %s AND country IS NOT DISTINCT FROM %s;",
        (location, code_postal, country)
    )
    existing = cur.fetchone()
    if existing:
        return existing[0]

    cur.execute(
        "INSERT INTO locations (location, code_postal, longitude, latitude, country) VALUES (%s, %s, %s, %s, %s) RETURNING location_id;",
        (location, code_postal, longitude, latitude, country)
    )
    return cur.fetchone()[0]



def insert_job_offer(cur, job):
    """
    Prépare une offre d'emploi pour l'insertion.
    - Si le champ 'title' est manquant, l'offre est ignorée.
    - Si 'created_at' n'est pas fourni, la date et l'heure actuelles sont utilisées.
    - La source est obligatoire.
    - L'offre sera ignorée si à la fois la localisation et le pays sont absents.
    - La colonne country est gérée dans la table locations.
    """
    if not job.get("title") or job.get("title").strip() == "":
        warning("Offre {} ignorée car le titre est manquant.".format(job.get("external_id", "N/A")))
        return None

    if not job.get("created_at"):
        job["created_at"] = datetime.datetime.now()

    source_id = insert_source(cur, job.get("source"))
    if source_id is None:
        warning("Offre {} ignorée en raison d'une source manquante.".format(job.get("external_id", "N/A")))
        return None

    location_value = job.get("location", "")
    country_value = job.get("country", "")

    # Si aucune info de localisation n'est fournie (ni location ni country), on ignore l'offre.
    if (not location_value or location_value.strip() == "") and (not country_value or country_value.strip() == ""):
        warning("Offre {} ignorée car localisation et pays sont absents.".format(job.get("external_id", "N/A")))
        return None

    company_id = insert_company(cur, job.get("company"))

    # Appel à insert_location avec la valeur de country.
    location_id = insert_location(cur, location_value, job.get("code_postal"), job.get("longitude"), job.get("latitude"), country_value)

    return (
        source_id,
        job["external_id"],
        company_id,
        location_id,
        job.get("salary_min"),
        job.get("salary_max"),
        job["created_at"]
    )



def upsert_specific_source_table(cur, job_id, job):
    """Insère ou met à jour les données spécifiques à chaque source dans la table correspondante."""
    source_table_map = {
        "Adzuna": "adzuna_offers",
        "France Travail": "france_travail_offers",
        "JSearch": "jsearch_offers"
    }
    table_name = source_table_map.get(job.get("source"))
    if not table_name:
        return
    cur.execute(f"""
        INSERT INTO {table_name} (job_id, title, contract_type, sector, description)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (job_id) DO UPDATE SET
            title = EXCLUDED.title,
            contract_type = EXCLUDED.contract_type,
            sector = EXCLUDED.sector,
            description = EXCLUDED.description;
    """, (job_id, job.get("title"), job.get("contract_type"), job.get("sector"), job.get("description")))



def process_job(job):
    """
    Traite une offre d'emploi : insertion ou mise à jour dans job_offers et dans la table spécifique si applicable.
    Retourne un tuple (succès: bool, external_id: str).
    """
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                job_data = insert_job_offer(cur, job)
                if job_data is None:
                    warning("Offre {} ignorée (données insuffisantes).".format(job.get("external_id", "N/A")))
                    return False, job.get("external_id", "N/A")

                # Upsert dans job_offers
                cur.execute("""
                    INSERT INTO job_offers (source_id, external_id, company_id, location_id, salary_min, salary_max, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (external_id, source_id)
                    DO UPDATE SET 
                        company_id = EXCLUDED.company_id,
                        location_id = EXCLUDED.location_id,
                        salary_min = EXCLUDED.salary_min,
                        salary_max = EXCLUDED.salary_max,
                        created_at = EXCLUDED.created_at
                    RETURNING job_id;
                """, job_data)
                job_id = cur.fetchone()[0]

                # Upsert dans la table spécifique en fonction de la source
                upsert_specific_source_table(cur, job_id, job)
            conn.commit()
        return True, job.get("external_id", "N/A")
    except Exception as e:
        critical("Erreur lors de l'insertion/mise à jour de l'offre {} : {}".format(job.get("external_id", "N/A"), e))
        return False, job.get("external_id", "N/A")



def load_jobs_multithreaded(jobs, max_threads):
    """
    Charge les offres en parallèle via multithreading.
    Traite chaque offre individuellement en ouvrant une connexion par thread.
    Avant de lancer le traitement, vérifie que la connexion à la base est fonctionnelle.
    Log le nombre total d'offres insérées et la liste des offres ignorées.
    """
    try:
        with connect_db():
            info("Connexion à la base de données vérifiée avec succès.")
    except Exception as e:
        critical("Impossible d'établir une connexion à la base de données : {}".format(e))
        return 0, []

    total_inserted = 0
    skipped_offers = []
    info("⚡ Insertion en parallèle avec {} threads...".format(max_threads))

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        results = list(executor.map(process_job, jobs))

    for success, external_id in results:
        if success:
            total_inserted += 1
        else:
            skipped_offers.append(external_id)

    info("{} offres insérées avec succès.".format(total_inserted))
    info("{} offres ignorées : {}".format(len(skipped_offers), ', '.join(skipped_offers)))
    return total_inserted, skipped_offers



def load_jobs_to_db():
    """Charge les offres du dernier fichier transformé et les insère en base de données en parallèle."""
    file_path = get_latest_file(PROCESSED_DATA_DIR)
    if not file_path:
        warning("Aucun fichier valide à charger.")
        return

    info("Chargement du fichier : {}".format(file_path))
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            jobs = json.load(file)

        if not jobs:
            warning("Le fichier JSON est vide.")
            return

        info("{} offres à insérer...".format(len(jobs)))
        load_jobs_multithreaded(jobs, max_threads=4)

    except (json.JSONDecodeError, FileNotFoundError) as e:
        critical("Erreur lors de la lecture du fichier JSON : {}".format(e))
    except Exception as e:
        critical("Erreur générale : {}".format(e))


if __name__ == "__main__":
    load_jobs_to_db()