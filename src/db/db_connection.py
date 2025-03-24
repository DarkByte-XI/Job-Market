import psycopg2
from db.config import DB_CONFIG
from src.config.logger import info, error

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        #info("Connexion réussie à AWS RDS PostgreSQL")
        return conn
    except Exception as e:
        error(f" Erreur de connexion : {e}")
        return None

if __name__ == "__main__":
    connect_db()
