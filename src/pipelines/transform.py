import os
import re
import unicodedata
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from jobs_api.utils import save_to_json, load_json_safely
from config.logger import warning, info, error

# Définition des chemins
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data/raw_data")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data/processed_data")
RESSOURCES_DIR = os.path.join(BASE_DIR, "ressources")
INSEE_FILE = os.path.join(RESSOURCES_DIR, "communes_cp.csv")

def normalize_text(text):
    """Normalise le texte en supprimant les accents, en mettant en majuscules et en gérant certaines transformations spécifiques."""
    if not text or not isinstance(text, str):  # Vérification pour éviter les erreurs
        return None

    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[-']", " ", text)  # Remplace les tirets et apostrophes par des espaces
    text = re.sub(r"\s+", " ", text).strip()  # Supprime les espaces multiples

    # Transformer "SAINT" en "ST"
    text = re.sub(r"\bSAINT\b", "ST", text)

    # Inversion des arrondissements (ex: "9ème Arrondissement, Paris" → "PARIS 9")
    match = re.search(r"(\d+)[eè]m[eè]?\s*Arrondissement,?\s*(\w+)", text, re.IGNORECASE)
    if match:
        arrondissement = match.group(1)
        ville = match.group(2)
        text = f"{ville} {arrondissement}"

    return text.upper()


communes_dict = {}  # Dictionnaire pour correspondance `Code_postal` → `Libellé_d_acheminement`
communes_nom_dict = {}  # Dictionnaire `Nom_de_la_commune` → `Code_postal`

if not os.path.exists(INSEE_FILE):
    error(f"Fichier INSEE introuvable : {INSEE_FILE}")
else:
    try:
        info(f"Chargement du fichier INSEE : {INSEE_FILE}")
        communes_df = pd.read_csv(INSEE_FILE, sep=";", dtype=str, encoding="ISO-8859-1")

        # Vérification des colonnes requises
        required_columns = {"Nom_de_la_commune", "Code_postal", "Libellé_d_acheminement"}
        if not required_columns.issubset(communes_df.columns):
            raise ValueError(f"Colonnes manquantes dans le fichier INSEE : {required_columns - set(communes_df.columns)}")

        # Stocker les correspondances
        for _, row in communes_df.iterrows():
            commune_norm = normalize_text(row["Nom_de_la_commune"])
            libelle_norm = normalize_text(row["Libellé_d_acheminement"])
            code_postal = row["Code_postal"]

            # Associer `Code_postal` à `Libellé_d_acheminement`
            communes_dict.setdefault(code_postal, libelle_norm)

            # Associer `Nom_de_la_commune` à `Code_postal`
            communes_nom_dict.setdefault(commune_norm, code_postal)

        info(f"{len(communes_dict)} codes postaux chargés avec libellé d'acheminement.")
        info(f"{len(communes_nom_dict)} communes chargées avec code postal.")
    except Exception as e:
        error(f"Erreur lors du chargement du fichier INSEE : {e}")
        communes_dict = {}  # Dictionnaire vide en cas d'erreur
        communes_nom_dict = {}


def match_commune_insee(commune, use_nom_commune=False):
    """
    Recherche le code postal à partir de `Libellé_d_acheminement` ou `Nom_de_la_commune` dans le fichier INSEE.
    - Si `use_nom_commune=True`, on cherche dans `Nom_de_la_commune` (cas des arrondissements).
    - Sinon, on cherche dans `Libellé_d_acheminement`.
    - Si un arrondissement est détecté, la recherche se fait sur `Nom_de_la_commune`.
    """
    if not commune or not isinstance(commune, str) or commune.strip() == "":
        return None  # Assure que la fonction retourne toujours une valeur

    commune_normalize = normalize_text(commune)

    # Vérifier si l'entrée contient un arrondissement (ex: "PARIS 9", "LYON 3", etc.)
    match_arrondissement = re.search(r"(\d+)[eè]m[eè]?\s*Arrondissement,?\s*(\w+)", commune, re.IGNORECASE)

    if match_arrondissement:
        arrondissement = match_arrondissement.group(1)  # Ex: "9"
        ville = match_arrondissement.group(2)  # Ex: "Paris"
        full_key = f"{ville} {arrondissement}".upper()  # Ex: "PARIS 9"

        # 1️⃣ Recherche d'abord avec `Nom_de_la_commune`
        matched_cp = communes_nom_dict.get(full_key)
        if matched_cp:
            return matched_cp

    # 2️⃣ Recherche alternative avec `Libellé_d_acheminement`
    matched_cp = next((cp for cp, lib in communes_dict.items() if lib == commune_normalize), None)
    if matched_cp:
        return matched_cp

    # 3️⃣ Dernier recours : essayer `Nom_de_la_commune` directement (sans arrondissement)
    return communes_nom_dict.get(commune_normalize, None)



def clean_description(text):
    """Nettoie la description en supprimant les balises HTML et les espaces inutiles."""
    if not text:
        return None
    text = re.sub(r"<[^>]+>", " ", text).replace("\n", " ").replace("\r", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def extract_salary_france_travail(salary_text):
    """Extrait `salary_min` et `salary_max` depuis la chaîne de salaire de France Travail."""
    if not salary_text or "Non renseigné" in salary_text or "Salaire à négocier" in salary_text:
        return None, None

    match = re.findall(r"(\d+(?:[.,]\d+)?)\s*Euros", salary_text)
    if not match:
        return None, None

    salary_values = [float(value.replace(",", ".")) for value in match]
    salary_min, salary_max = min(salary_values), max(salary_values)

    if "Mensuel" in salary_text:
        return round(salary_min * 12), round(salary_max * 12)
    elif "Horaire" in salary_text:
        return round(salary_min * 151.67), round(salary_max * 151.67)
    return round(salary_min), round(salary_max)


def extract_location_france_travail(location_data):
    """
    Extrait la localisation et le code postal pour France Travail :
    - Si `codePostal` est présent, on récupère `Libellé_d_acheminement` depuis INSEE.
    - Si `codePostal` est absent, on nettoie et cherche un match.
    - Si un arrondissement est détecté, on cherche dans `Nom_de_la_commune`.
    - Sinon, on cherche dans `Libellé_d_acheminement`.
    """
    if not location_data:
        return None, None

    libelle = location_data.get("libelle", "")
    code_post = location_data.get("codePostal")

    # 1️⃣ Si le code postal est présent, récupérer `Libellé_d_acheminement`
    if code_post:
        matched_location = communes_dict.get(code_post)
        return matched_location if matched_location else libelle, code_post

    # 2️⃣ Nettoyage initial de la localisation
    location_cleaned = normalize_text(libelle)

    # Suppression des numéros isolés au début (ex: "44 - ST NAZAIRE" → "ST NAZAIRE")
    location_cleaned = re.sub(r"^\d+\s*-?\s*", "", location_cleaned).strip()

    # Correction des noms composés (ex: "HAUTS DE SEINE", "ILE DE FRANCE")
    location_cleaned = re.sub(r"\b(DE|DU|DES|LA|LE|LES|AUX)\b\s+", "", location_cleaned)

    # Suppression des valeurs entre parenthèses
    location_cleaned = re.sub(r"\(.*?\)", "", location_cleaned).strip()

    # Suppression des chiffres isolés sauf arrondissements (ex: "92" mais pas "8ème")
    location_cleaned = re.sub(r"\b\d+\b(?!\s*(e|er|ème|ÈME|ER)\b)", "", location_cleaned).strip()

    # 3️⃣ Vérification si la localisation contenait un arrondissement avant nettoyage
    match_arrondissement = re.search(r"(\d+)[eè]m[eè]?\s*Arrondissement", libelle, re.IGNORECASE)

    if match_arrondissement:
        # Match avec `Nom_de_la_commune`
        matched_cp = match_commune_insee(location_cleaned, use_nom_commune=True)
    else:
        # Match avec `Libellé_d_acheminement`
        matched_cp = match_commune_insee(location_cleaned, use_nom_commune=False)

    # 4️⃣ Si aucun match trouvé, garder l'original
    return location_cleaned, matched_cp if matched_cp else None



def extract_location_adzuna(location_data):
    """
    Extrait la localisation et le code postal pour Adzuna :
    - Si `location_area` contient 5 valeurs ou plus, teste d'abord la 5ᵉ (index 4), puis la 4ᵉ (index 3) en fallback.
    - Si `location_area` contient exactement 4 valeurs, teste directement la 4ᵉ (index 3).
    - Si aucun match, applique une normalisation et un traitement des arrondissements sur `display_name`.
    - Si toujours aucun match, tente de matcher sur la première partie du `display_name` (ex: "PARIS, ILE DE FRANCE" → "PARIS").
    - Si aucun match final, retourne la localisation normalisée.
    """
    if not location_data:
        return None, None

    display_name = location_data.get("display_name", "")
    area_list = location_data.get("area", [])

    # Vérification dans `location_area`
    if len(area_list) >= 5:
        location_candidate = normalize_text(area_list[4])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            return location_candidate, matched_cp

        location_candidate = normalize_text(area_list[3])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            return location_candidate, matched_cp

    elif len(area_list) == 4:
        location_candidate = normalize_text(area_list[3])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            return location_candidate, matched_cp

    # Normalisation de `display_name`
    location_cleaned = normalize_text(display_name)

    # Vérifier si un arrondissement est présent (ex: "9ème Arrondissement, Lyon")
    match_arrondissement = re.search(r"(\d+)[eè]m[eè]?\s*Arrondissement,?\s*(\w+)", display_name, re.IGNORECASE)

    if match_arrondissement:
        matched_cp = match_commune_insee(location_cleaned, use_nom_commune=True)
    else:
        matched_cp = match_commune_insee(location_cleaned, use_nom_commune=False)

    # Si aucun match, essayer d'extraire la première partie du `display_name`
    first_part = normalize_text(location_cleaned.split(",")[0])
    if not matched_cp and "," in location_cleaned:
        matched_cp = match_commune_insee(first_part, use_nom_commune=False)

    # Si toujours aucun match, retourner la localisation normalisée
    return first_part, matched_cp if matched_cp else location_cleaned


def extract_location_jsearch(location_name):
    """
    Recherche le code postal pour une localisation JSearch :
    - Normalisation de la ville.
    - Recherche du code postal en base INSEE.
    """
    if not location_name:
        return None, None  # Évite les erreurs si `location_name` est vide

    commune = normalize_text(location_name)
    matched_cp = match_commune_insee(commune)

    return commune, matched_cp if matched_cp is not None else None  # Suppression du warning PyCharm


TRANSFORMATION_FUNCTIONS = {
    "adzuna": lambda job: {
        "source": "Adzuna",
        "external_id": job.get("id"),
        "title": job.get("title"),
        "company": job.get("company", {}).get("display_name"),
        "location": extract_location_adzuna(job.get("location"))[0],
        "code_postal": extract_location_adzuna(job.get("location"))[1],
        "longitude": job.get("longitude"),
        "latitude": job.get("latitude"),
        "contract_type": job.get("contract_type"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "sector": job.get("category", {}).get("label"),
        "description": None,
        "created_at": job.get("created")
    },
    "france_travail": lambda job: {
        "source": "France Travail",
        "external_id": job.get("id"),
        "title": job.get("intitule"),
        "company": job.get("entreprise", {}).get("nom"),
        "location": extract_location_france_travail(job.get("lieuTravail"))[0],
        "code_postal": extract_location_france_travail(job.get("lieuTravail"))[1],
        "longitude": job.get("lieuTravail", {}).get("longitude"),
        "latitude": job.get("lieuTravail", {}).get("latitude"),
        "contract_type": job.get("typeContrat"),
        "salary_min": extract_salary_france_travail(job.get("salaire", {}).get("libelle"))[0],
        "salary_max": extract_salary_france_travail(job.get("salaire", {}).get("libelle"))[1],
        "sector": job.get("secteurActiviteLibelle"),
        "description": clean_description(job.get("description")),
        "created_at": job.get("dateCreation")
    },
    "jsearch": lambda job: {
        "source": "JSearch",
        "external_id": job.get("job_id"),
        "title": job.get("job_title"),
        "company": job.get("employer_name"),
        "location": extract_location_jsearch(job.get("job_location"))[0],
        "code_postal": extract_location_jsearch(job.get("job_location"))[1],
        "longitude": None,
        "latitude": None,
        "contract_type": job.get("job_employment_type"),
        "salary_min": job.get("job_min_salary"),
        "salary_max": job.get("job_max_salary"),
        "sector": None,
        "description": clean_description(job.get("job_description")),
        "created_at": job.get("job_posted_at")
    }
}


def process_source_files(source, source_dir):
    """Charge et transforme les fichiers JSON d'une source en parallèle."""
    if not os.path.exists(source_dir):
        warning(f"Dossier source introuvable pour {source}")
        return []

    file_paths = [os.path.join(source_dir, f) for f in os.listdir(source_dir)]


    def process_file(file_path):
        data = load_json_safely(file_path)
        return [TRANSFORMATION_FUNCTIONS[source](job) for job in data] if data else []

    with ThreadPoolExecutor() as executor:
        results = executor.map(process_file, file_paths)

    transformed_jobs = [job for sublist in results for job in sublist]
    info(f"{len(transformed_jobs)} offres transformées pour {source}")
    return transformed_jobs


def deduplicate_jobs(jobs):
    """
    Supprime les doublons dans une liste de jobs en se basant sur `external_id` et 'source'.
    """
    unique_jobs = {}
    for job in jobs:
        key = (job["external_id"], job["source"])  # Unicité basée sur l'ID et la source
        if key not in unique_jobs:
            unique_jobs[key] = job
    return list(unique_jobs.values())


def deduplicate_after_merge(jobs):
    """
    Supprime les doublons après fusion des sources, en se basant sur `title` et 'company'.
    """
    unique_jobs = {}
    for job in jobs:
        key = (job["title"].lower(), job["company"].lower() if job["company"] else None)
        if key not in unique_jobs:
            unique_jobs[key] = job
    return list(unique_jobs.values())



def transform_jobs():
    """Orchestration du traitement des offres d'emploi avec optimisation et logs détaillés."""
    all_transformed_jobs = []

    # Vérifier si le dictionnaire INSEE est bien chargé
    if not communes_dict:
        warning("Attention : Le fichier INSEE est absent ou mal chargé. Les correspondances de code postal peuvent être incomplètes.")

    for source in TRANSFORMATION_FUNCTIONS:
        source_dir = os.path.join(RAW_DATA_DIR, source, "output")

        # Chargement et transformation des fichiers en parallèle
        transformed_jobs = process_source_files(source, source_dir)

        # Déduplication intra-source
        unique_jobs = deduplicate_jobs(transformed_jobs)
        info(f"Déduplication intra-source terminée pour {source}, {len(unique_jobs)} offres uniques.")

        all_transformed_jobs.extend(unique_jobs)

    # Déduplication inter-sources après fusion
    final_jobs = deduplicate_after_merge(all_transformed_jobs)
    info(f"Déduplication inter-sources appliquée, {len(final_jobs)} offres finales.")

    # Sauvegarde des offres transformées
    save_to_json(final_jobs, directory = PROCESSED_DATA_DIR,
                 source = "transformed")
    info(f"Transformation terminée : {len(final_jobs)} offres sauvegardées.")



if __name__ == "__main__":
    transform_jobs()
