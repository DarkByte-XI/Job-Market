import os
import json
import re
import unicodedata
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from jobs_api.utils import save_to_json, load_json_safely
from config.logger import warning, info, error
from pipelines.extract import BASE_DIR, RAW_DATA_DIR, RESSOURCES_DIR

# Définition des chemins
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data/processed_data")
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


def harmonize_company_name(company_name):
    """
    Normalise le nom de l'entreprise pour harmoniser les variations d'écriture.
    Par exemple, "SNCF Connect", "Sncf connect" et "SNCF connect" seront transformés en une même chaîne,
    ce qui permet de réduire les doublons lors de la déduplication.
    """
    if not company_name or not isinstance(company_name, str):
        return None
    # Normalisation de base : supprime les accents, met en majuscules, remplace les tirets et apostrophes par des espaces, etc.
    normalized = normalize_text(company_name)
    # On peut ajouter ici des règles supplémentaires, par exemple supprimer des suffixes ou mots redondants
    # Exemples (à adapter selon les besoins) :
    # normalized = re.sub(r"\b(INC|CORP|LIMITED|SARL|LLC)\b", "", normalized)
    # normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def match_commune_insee(commune):
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

        # Recherche d'abord avec `Nom_de_la_commune`
        matched_cp = communes_nom_dict.get(full_key)
        if matched_cp:
            return matched_cp

    # Recherche alternative avec `Libellé_d_acheminement`
    matched_cp = next((cp for cp, lib in communes_dict.items() if lib == commune_normalize), None)
    if matched_cp:
        return matched_cp

    # Dernier recours : essayer `Nom_de_la_commune` directement (sans arrondissement)
    return communes_nom_dict.get(commune_normalize, None)


def clean_description(text):
    """Nettoie la description en supprimant les balises HTML et les espaces inutiles."""
    if not text:
        return None
    text = re.sub(r"<[^>]+>", " ", text).replace("\n", " ").replace("\r", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def extract_salary_france_travail(salary_text):
    """
    Extrait le salaire minimum et maximum depuis une chaîne de caractère
    en tenant compte des différents formats et périodes (mensuel, horaire, annuel).

    Cas particulier :
    - Si on détecte "mensuel" ET une valeur au moins égale à 10 000 (ex. 38 000),
      on suppose que les chiffres donnés sont déjà annualisés (ou simplement un
      format erroné dans l'annonce). Dans ce cas, on NE multiplie pas par 12.
    - Sinon, si "mensuel" et < 10 000 (arbitraire), on multiplie par 12.
    - Si "horaire" ou "/h" => on multiplie par 151,67 * 12.
    - Si "annuel" => on ne multiplie pas.
    - Si on trouve "K" quelque part => les valeurs sont en milliers.
    - Si aucun mot-clé de périodicité => fallback :
         - s'il y a un "k" => on garde tel quel (annuel)
         - sinon on multiplie par 12.

    :param salary_text: Chaîne contenant l'information du salaire.
    :return: Tuple (salary_min, salary_max) ou (None, None) si aucune valeur trouvée.
    """

    if not salary_text or any(term in salary_text.lower() for term in ["négocier", "profil", "autre"]):
        return None, None

    # 1) Retirer "sur 12 mois" (ou variante sur 12.0 mois) pour ne garder que la partie avant
    #   Ex: "Mensuel de 38000 Euros à 42000 Euros sur 12 mois" => "Mensuel de 38000 Euros à 42000 Euros"
    #   Mais on conserve en mémoire si on a rencontré ce pattern (au cas où besoin d'une logique dédiée)
    pattern_sur_12 = re.compile(r"sur\s*\d+(?:[.,]\d+)?\s*mois", re.IGNORECASE)

    # On coupe la chaîne avant "sur 12 mois"
    salary_text = pattern_sur_12.split(salary_text)[0].strip()

    # 2) Recherche de toutes les valeurs numériques + unité
    matches = re.findall(r"(\d+(?:[.,]\d+)?)\s*(K|k|k€|Mille|€|Euros?)?", salary_text, flags=re.IGNORECASE)
    if not matches:
        return None, None

    raw_values = []
    for val, unit in matches:
        number = float(val.replace(",", "."))
        raw_values.append((number, unit))

    if not raw_values:
        return None, None

    # 3) Vérifier la présence de 'k' => toutes les valeurs sont en milliers
    text_lower = salary_text.lower()
    has_k = bool(re.search(r"[kK]", text_lower))

    # 4) Conversion en valeurs brutes
    salary_values = []
    for (number, unit) in raw_values:
        if has_k or (unit and unit.lower() in ["k", "k€", "mille"]):
            salary_values.append(number * 1000)
        else:
            salary_values.append(number)

    salary_min_raw, salary_max_raw = min(salary_values), max(salary_values)

    # 5) Détermination de la périodicité
    # Règle :
    #   - mensuel => *12, sauf si la valeur >= 10000 => on suppose déjà annualisée
    #   - horaire => * 151.67 * 12
    #   - annuel => on laisse tel quel
    #   - fallback => s'il y a k => annuel, sinon => *12

    if re.search(r"mensuel|mois", text_lower):
        # Valeurs signalées comme mensuelles
        if salary_min_raw >= 10000:
            # Cas particulier : si la valeur mensuelle est au-dessus d'un gros seuil (10k),
            # on suppose qu'il s'agit en réalité d'un salaire annuel mal labellisé.
            salary_min, salary_max = round(salary_min_raw), round(salary_max_raw)
        else:
            # On considère effectivement que c'est un salaire mensuel
            salary_min = round(salary_min_raw * 12)
            salary_max = round(salary_max_raw * 12)
    elif re.search(r"horaire|/h", text_lower):
        # Horaire => *151.67 => mensuel => *12 => annuel
        salary_min = round(salary_min_raw * 151.67 * 12)
        salary_max = round(salary_max_raw * 151.67 * 12)
    elif re.search(r"annuel|an", text_lower):
        # Annuel => on laisse
        salary_min = round(salary_min_raw)
        salary_max = round(salary_max_raw)
    else:
        # fallback => k => annuel, sinon => mensuel
        if has_k:
            salary_min = round(salary_min_raw)
            salary_max = round(salary_max_raw)
        else:
            salary_min = round(salary_min_raw * 12)
            salary_max = round(salary_max_raw * 12)

    return salary_min, salary_max


def extract_location_france_travail(location_data):
    """
    Extrait la localisation et le code postal pour France Travail :
    - Si `codePostal` est présent, on récupère `Libellé_d_acheminement` depuis INSEE.
    - Si `codePostal` est absent, on nettoie et cherche un match.
    - Si un arrondissement est détecté, on cherche dans `Nom_de_la_commune`.
    - Sinon, on cherche dans `Libellé_d_acheminement`.

    :return localisation normalisée avec le code postal correspondant sinon juste la localisation.
    """
    if not location_data:
        return None, None

    libelle = location_data.get("libelle", "")
    code_post = location_data.get("codePostal")

    # Si le code postal est présent, récupérer `Libellé_d_acheminement`
    if code_post:
        matched_location = communes_dict.get(code_post)
        return matched_location if matched_location else libelle, code_post

    # Nettoyage initial de la localisation
    location_cleaned = normalize_text(libelle)

    # Suppression des numéros isolés au début (ex: "44 - ST NAZAIRE" → "ST NAZAIRE")
    location_cleaned = re.sub(r"^\d+\s*-?\s*", "", location_cleaned).strip()

    # Correction des noms composés (ex: "HAUTS DE SEINE", "ILE DE FRANCE")
    location_cleaned = re.sub(r"\b(DE|DU|DES|LA|LE|LES|AUX)\b\s+", "", location_cleaned)

    # Suppression des valeurs entre parenthèses
    location_cleaned = re.sub(r"\(.*?\)", "", location_cleaned).strip()

    # Suppression des chiffres isolés sauf arrondissements (ex: "92" mais pas "8ème")
    location_cleaned = re.sub(r"\b\d+\b(?!\s*(e|er|ème|ÈME|ER)\b)", "", location_cleaned).strip()

    # Vérification si la localisation contenait un arrondissement avant nettoyage
    match_arrondissement = re.search(r"(\d+)[eè]m[eè]?\s*Arrondissement", libelle, re.IGNORECASE)

    if match_arrondissement:
        # Match avec `Nom_de_la_commune`
        matched_cp = match_commune_insee(location_cleaned)
    else:
        # Match avec `Libellé_d_acheminement`
        matched_cp = match_commune_insee(location_cleaned)

    # Si aucun match trouvé, garder l'original
    return location_cleaned, matched_cp if matched_cp else None


def extract_location_adzuna(location_data):
    """
    Extrait la localisation, le code postal, et le pays pour Adzuna :
      - Si `area` contient 5 valeurs ou plus, teste d'abord la 5ᵉ (index 4), puis la 4ᵉ (index 3) en fallback.
      - Si `area` contient exactement 4 valeurs, teste directement la 4ᵉ (index 3).
      - Si `area` contient exactement 1 valeur, on considère qu'il s'agit uniquement du pays et on retourne (None, None, pays normalisé).
      - Sinon, applique une normalisation et un traitement sur `display_name` pour en extraire la localisation et le code postal.

    :return: Tuple (localisation, code_postal, pays)
    """
    if not location_data:
        return None, None, None

    display_name = location_data.get("display_name", "")
    area_list = location_data.get("area", [])

    # Si la liste area contient exactement 1 élément, c'est uniquement le pays.
    if len(area_list) == 1:
        return None, None, normalize_text(area_list[0])

    # Pour les cas où area_list contient 5 valeurs ou plus, tester en priorité l'index 4 puis l'index 3
    if len(area_list) >= 5:
        location_candidate = normalize_text(area_list[4])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            country = normalize_text(area_list[0]) if len(area_list) > 0 else None
            return location_candidate, matched_cp, country

        location_candidate = normalize_text(area_list[3])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            country = normalize_text(area_list[0]) if len(area_list) > 0 else None
            return location_candidate, matched_cp, country

    # Si area_list contient exactement 4 valeurs, tester l'index 3 directement
    elif len(area_list) == 4:
        location_candidate = normalize_text(area_list[3])
        matched_cp = match_commune_insee(location_candidate)
        if matched_cp:
            country = normalize_text(area_list[0]) if len(area_list) > 0 else None
            return location_candidate, matched_cp, country

    # Sinon, utiliser display_name pour déterminer la localisation
    location_cleaned = normalize_text(display_name)

    # Vérifier la présence d'un arrondissement (exemple : "9ème Arrondissement, Lyon")
    match_arrondissement = re.search(r"(\d+)[eè]m[eè]?\s*Arrondissement,?\s*(\w+)", display_name, re.IGNORECASE)
    if match_arrondissement:
        matched_cp = match_commune_insee(location_cleaned)
    else:
        matched_cp = match_commune_insee(location_cleaned)

    first_part = normalize_text(location_cleaned.split(",")[0])
    if not matched_cp and "," in location_cleaned:
        matched_cp = match_commune_insee(first_part)

    # Définir le pays à partir du premier élément de area_list s'il existe
    country = normalize_text(area_list[0]) if area_list and len(area_list) > 0 else None

    return first_part, matched_cp if matched_cp else None, country


def extract_location_jsearch(location_name):
    """
    Recherche le code postal pour une localisation JSearch et récupère le nom du pays correspondant :
      - Si location_name correspond à un code de pays présent dans 'code_pays.json' (comparaison insensible à la casse),
        on considère que seule l'information pays est fournie et on retourne (None, None, nom_du_pays_normalisé).
      - Sinon, on normalise la ville via normalize_text,
        on recherche le code postal en base INSEE via match_commune_insee.

    :param location_name: Nom de la ville ou code de pays.
    :return: Tuple (commune, code_postal, pays)
             - commune: Nom de la ville normalisé, ou None si seule l'information pays est fournie.
             - code_postal: Code postal correspondant si trouvé, sinon None.
             - pays: Nom du pays normalisé (via normalize_text) si trouvé dans le mapping, sinon None.
    """
    if not location_name:
        return None, None, None

    # Charger le dictionnaire des codes pays depuis code_pays.json
    country_dict = {}
    try:
        with open(f'{RESSOURCES_DIR}/code_pays.json', 'r', encoding = 'utf-8') as f:
            country_dict = json.load(f)
    except Exception as _e:
        warning(f"Erreur lors de la lecture du fichier code_pays.json : {_e}")


    # Normaliser la valeur d'entrée et vérifier si elle correspond à un code pays
    code_input = location_name.strip().upper()
    country_codes = {code.strip().upper() for code in country_dict.keys()}
    if code_input in country_codes:
        # Si c'est un code de pays, retourner uniquement le pays normalisé
        # On suppose que country_dict[code] retourne le nom complet du pays
        return None, None, normalize_text(country_dict[code_input])

    # Sinon, traiter location_name comme le nom d'une ville
    commune = normalize_text(location_name)
    matched_cp = match_commune_insee(commune)

    return commune, matched_cp if matched_cp is not None else None, None


def convert_to_timestamp(date_str):
    """
    Convertit une date sous différents formats en un timestamp PostgreSQL-compatible.

    :param date_str: Chaîne de caractères représentant une date.
    :return: Chaîne de caractères au format 'YYYY-MM-DD HH:MI:SS' ou None si la conversion échoue.
    """
    if not date_str:
        return None

    # Liste des formats de dates possibles
    date_formats = [
        "%Y-%m-%dT%H:%M:%SZ",    # Format ISO 8601 (Adzuna, France Travail)
        "%Y-%m-%dT%H:%M:%S.%fZ", # Format ISO avec millisecondes
        "%d/%m/%Y %H:%M:%S",     # Format français avec heure
        "%Y-%m-%d %H:%M:%S",     # Format SQL classique
        "%d-%m-%Y",              # Format court (jour-mois-année)
        "%Y/%m/%d",              # Format alternatif (année/mois/jour)
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S")  # Format PostgreSQL
        except ValueError:
            continue

    # Si aucun format ne correspond, on retourne None
    return None


def convert_relative_time(relative_str):
    """
    Convertit une chaîne du format "il y a X jours" ou "il y a X heures"
    en un timestamp PostgreSQL-compatible ("%Y-%m-%d %H:%M:%S").
    """
    import re
    from datetime import datetime, timedelta

    if not relative_str or not isinstance(relative_str, str):
        return None

    # Mettre la chaîne en minuscules et supprimer les espaces superflus
    relative_str = relative_str.lower().strip()

    # Rechercher le pattern "il y a <nombre> <unité>"
    match = re.search(r"il y a (\d+)\s*(jours?|heures?)", relative_str)
    if match:
        number = int(match.group(1))
        unit = match.group(2)
        now = datetime.now()
        if "jour" in unit:
            delta = timedelta(days = number)
        elif "heure" in unit:
            delta = timedelta(hours = number)
        else:
            return None
        created_time = now - delta
        return created_time.strftime("%Y-%m-%d %H:%M:%S")

    return None


TRANSFORMATION_FUNCTIONS = {
    "adzuna": lambda job: {
        "source": "Adzuna",
        "external_id": job.get("id"),
        "title": job.get("title"),
        "company": harmonize_company_name(job.get("company", {}).get("display_name")),
        "location": extract_location_adzuna(job.get("location"))[0],
        "code_postal": extract_location_adzuna(job.get("location"))[1],
        "longitude": job.get("longitude"),
        "latitude": job.get("latitude"),
        "contract_type": job.get("contract_type"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "sector": job.get("category", {}).get("label"),
        "description": None,
        "country": extract_location_adzuna(job.get("location"))[2],
        "created_at": convert_to_timestamp(job.get("created")),
        "apply_url": job.get("redirect_url")
    },
    "france_travail": lambda job: {
        "source": "France Travail",
        "external_id": job.get("id"),
        "title": job.get("intitule"),
        "company": harmonize_company_name(job.get("entreprise", {}).get("nom")),
        "location": extract_location_france_travail(job.get("lieuTravail"))[0],
        "code_postal": extract_location_france_travail(job.get("lieuTravail"))[1],
        "longitude": job.get("lieuTravail", {}).get("longitude"),
        "latitude": job.get("lieuTravail", {}).get("latitude"),
        "contract_type": job.get("typeContrat"),
        "salary_min": extract_salary_france_travail(job.get("salaire", {}).get("libelle"))[0],
        "salary_max": extract_salary_france_travail(job.get("salaire", {}).get("libelle"))[1],
        "sector": job.get("secteurActiviteLibelle"),
        "description": clean_description(job.get("description")),
        "country": "FRANCE",
        "created_at": convert_to_timestamp(job.get("dateCreation")),
        "apply_url": job.get("origineOffre", {}).get("urlOrigine")
    },
    "jsearch": lambda job: {
        "source": "JSearch",
        "external_id": job.get("job_id"),
        "title": job.get("job_title"),
        "company": harmonize_company_name(job.get("employer_name")),
        "location": extract_location_jsearch(job.get("job_location"))[0],
        "code_postal": extract_location_jsearch(job.get("job_location"))[1],
        "longitude": job.get("job_longitude"),
        "latitude": job.get("job_latitude"),
        "contract_type": job.get("job_employment_type"),
        "salary_min": job.get("job_min_salary"),
        "salary_max": job.get("job_max_salary"),
        "sector": None,
        "description": clean_description(job.get("job_description")),
        "country": extract_location_jsearch(job.get("job_country"))[2],
        "created_at": convert_relative_time(job.get("job_posted_at")),
        "apply_url": job.get("job_apply_link")
    }
}


def process_source_files(source, source_dir):
    """Charge et transforme les fichiers JSON d'une source en parallèle."""
    if not os.path.exists(source_dir):
        warning(f"Dossier source introuvable pour {source}")
        return []

    file_paths = [
    os.path.join(source_dir, f)
    for f in os.listdir(source_dir)
    if f.lower().endswith('.json')
]


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
        # Normaliser le titre (on le met en minuscule pour la comparaison)
        title_key = job.get("title", "").strip().lower()
        # Harmoniser le nom de l'entreprise
        company_key = harmonize_company_name(job.get("company"))
        key = (title_key, company_key)
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
    try:
        if final_jobs:
            save_to_json(final_jobs, directory = PROCESSED_DATA_DIR,
                         source = "transformed")
            info(f"Transformation terminée : {len(final_jobs)} offres sauvegardées.")
    except Exception as exception:
        error(f"Le fichier transformé n'a pas été sauvegardé - {exception}")



if __name__ == "__main__":
    transform_jobs()
