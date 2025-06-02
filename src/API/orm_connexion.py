from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from db.config import DB_CONFIG


SQLALCHEMY_DATABASE_URL = "postgresql://{user}:{password}@{host}:{port}/{dbname}".format(**DB_CONFIG)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Fournit un générateur de session de base de données afin d'assurer une gestion correcte
    du cycle de vie de l'objet session.
    La session est créée lorsque le générateur est appelé et fermé après son utilisation.

    :yield : Un objet session pour interagir avec la base de données.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


