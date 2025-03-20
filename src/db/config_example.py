"""
Ce fichier est nécessaire pour établir une connexion avec la base de données nécessaire à
l'hébergement des offres d'emploi récupérées.

!!! Une base de données PostgresSQL est strictement nécessaire !!!
La modélisation ainsi que la partie d'ingestion des données sont strictement propre à Postgres.
Tout changement peut rendre le script dysfonctionnel.

Le port est prérempli sur 5432 par défaut.
Se réferer à la documentation pour plus de détails.
"""

DB_CONFIG = {
    "dbname": "",
    "user": "",
    "password": "",
    "host": "",
    "port": "5432"
}