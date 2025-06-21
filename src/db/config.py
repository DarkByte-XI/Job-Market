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

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT")
}