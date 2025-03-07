import os
import json
import requests
from dotenv import load_dotenv
from config_loader import get_config  # Si vous utilisez déjà ce module pour charger d'autres configs

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Charger la configuration via votre module (vous pouvez aussi directement utiliser os.getenv)
ft_config = get_config()
IDENTIFIANT_CLIENT = ft_config["france_travail"]["ID"]
CLE_SECRETE = ft_config["france_travail"]["KEY"]
SCOPES_OFFRES = ft_config["france_travail"]["SCOPE"]

# Endpoints de l'API France Travail
TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
TOKEN_PARAMS = {"realm": "/partenaire"}
OFFRES_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"


def get_bearer_token(client_id, client_secret, scope):
    """
    Récupère un Bearer Token via le flux client_credentials.
    Envoie une requête POST avec Content-Type 'application/x-www-form-urlencoded'
    et transmet les identifiants dans le corps.
    """
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }
    response = requests.post(TOKEN_URL, headers = headers, params = TOKEN_PARAMS, data = data)
    response.raise_for_status()
    token_data = response.json()
    return token_data.get("access_token")


def get_offres(token, code):
    """
    Récupère les offres d'emploi correspondant à une appellation donnée.
    Filtre sur "appellation" (le code métier) et "paysContinent": "01" pour la France.
    Gère la pagination par tranche de 150 offres, dans la limite de 3150 offres.
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    filter_params = {
        "appellation": code,
        "paysContinent": "01"
    }

    response = requests.get(OFFRES_URL, headers = headers, params = filter_params)
    response.raise_for_status()

    content_range = response.headers.get("Content-Range")
    total_offres = int(content_range.split("/")[-1]) if content_range else 0

    offres = []
    if response.status_code == 200:
        offres = response.json().get("resultats", [])
    elif response.status_code == 206:
        offres.extend(response.json().get("resultats", []))
        range_start = 150
        while range_start < total_offres and range_start < 3150:
            range_end = range_start + 149
            filter_params["range"] = f"{range_start}-{range_end}"
            pag_response = requests.get(OFFRES_URL, headers = headers, params = filter_params)
            pag_response.raise_for_status()
            offres.extend(pag_response.json().get("resultats", []))
            range_start += 150
    return offres


def load_appellations(appellations_file):
    """
    Charge le fichier JSON contenant les appellations.
    Le fichier doit contenir un tableau d'objets ayant au moins les clés "code" et "libelle".
    """
    with open(appellations_file, "r", encoding = "utf-8") as f:
        appellations = json.load(f)
    return appellations


def main():
    # Récupération du token
    token = get_bearer_token(IDENTIFIANT_CLIENT, CLE_SECRETE, SCOPES_OFFRES)
    print("Token obtenu :", token)

    # Chemin du fichier des appellations
    appellations_file = "/Users/dani/Git-Repo/Job_Market/data/data_appellations.json"
    appellations = load_appellations(appellations_file)

    all_offres = []
    # Itérer sur chaque appellation
    for item in appellations:
        code = item.get("code")
        libelle = item.get("libelle", "")
        print(f"Récupération des offres pour l'appellation {code} ({libelle})...")
        offres = get_offres(token, code)
        print(f"Nombre d'offres récupérées pour {code} : {len(offres)}")
        all_offres.extend(offres)

    # Déduplication des offres sur la base de leur identifiant ("id")
    unique_offres = {offre.get("id"): offre for offre in all_offres if offre.get("id")}.values()
    unique_offres_list = list(unique_offres)
    print(f"Nombre total d'offres après déduplication : {len(unique_offres_list)}")

    # Sauvegarde dans le répertoire de sortie souhaité
    output_directory = "/Users/dani/Git-Repo/Job_Market/data/france_travail/output"
    os.makedirs(output_directory, exist_ok = True)
    output_file = os.path.join(output_directory, "merged_offres_data.json")

    with open(output_file, "w", encoding = "utf-8") as f:
        json.dump(unique_offres_list, f, ensure_ascii = False, indent = 2)
    print(f"Les offres merged ont été sauvegardées dans {output_file}")


if __name__ == "__main__":
    main()
