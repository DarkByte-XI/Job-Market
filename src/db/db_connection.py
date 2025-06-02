import psycopg2
from db.config import DB_CONFIG
from src.config.logger import info, error


def connect_db() -> psycopg2.extensions.connection | None:
    """
    Etablit une connexion à une base de données PostgreSQL en utilisant la configuration fournie.

    Cette fonction tente de se connecter à une base de données PostgreSQL à l'aide de détails de
    prédéfinis. Si la connexion réussit, elle renvoie l'objet de connexion.
    Si une erreur survient au cours du processus de connexion, elle est enregistrée et la fonction
    renvoie None.

    :return : Un objet de connexion psycopg2 si la connexion est réussie, None dans le cas contraire.
    :rtype : psycopg2.extensions.connection ou None
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        #info("Connexion réussie à AWS RDS PostgreSQL")
        return conn
    except Exception as e:
        error(f" Erreur de connexion : {e}")
        return None

if __name__ == "__main__":
    connect_db()
