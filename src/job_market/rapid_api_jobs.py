import os
from dotenv import load_dotenv
import requests


def fetch_job_from_rapid(params):
    """
    Permet de récupérer les offres d'emploi à partir de l'API.
    Pour plus d'infos sur les paramètres, consulter https://rapidapi.com/Pat92/api/jobs-api14.
    L'API nécessite un abonnement moyennant des frais pour des limites étendues.

    @param params: Correspond aux paramètres de recherche. Les paramètres seront
    définis ci-dessus de manière dynamique afin qu'il soit récupérés des variables de l'environnement de travail.
    """
    # Charger l'environnement de travail et les credentials
    load_dotenv()
    api_base_url = os.getenv('RAPID_API_HOST')
    api_key = os.getenv('RAPID_API_KEY')

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-rapidapi-host': api_base_url,
        'x-rapidapi-key': api_key
    }

    params = {
        "query": params["query"],
        "location": params["location"],
        "remote_only": params["remote_only"] # false par défaut
    }

    response = requests.get(url=api_base_url, headers = headers, params=params)

    if response.status_code == 200:
        data = response.json()








