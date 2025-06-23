"""
Ce fichier est nécessaire pour établir une connexion avec la base de données.

!!! Une base de données **PostgresSQL** est strictement nécessaire !!!
La modélisation ainsi que la partie d'ingestion des données sont strictement propre à Postgres.

Les variables d'environnement sont définies dans le fichier .env.
Adapter les variables d'environnement pour votre environnement.
Se référer à la documentation pour plus de détails.
"""

import os
from dotenv import load_dotenv

DOTENV_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(DOTENV_BASE_DIR, "../../.env")
load_dotenv(dotenv_path = dotenv_path)


DB_CONFIG = {
    "dbname": os.getenv("JOBS_POSTGRES_DB"),
    "user": os.getenv("JOBS_POSTGRES_USER"),
    "password": os.getenv("JOBS_POSTGRES_PASSWORD"),
    "host": os.getenv("JOBS_POSTGRES_HOST"),
    "port": os.getenv("JOBS_POSTGRES_PORT")
}