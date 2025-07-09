from fastapi import APIRouter, Query
from typing import List
from recommender.recommender import (
    build_recommendation_engine_from_folder,
    recommend_offers
)
from API.schemas.job import JobOfferResponse
import os

router = APIRouter()

ROOT = os.environ.get("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
PROCESSED_OFFERS_DIR = os.path.join(ROOT, "data/processed_data")

offers = []
vectorizer = None
offer_vectors = None
texts = []

def load_recommendation_data() -> None:
    global offers, vectorizer, offer_vectors, texts
    offers, vectorizer, offer_vectors, texts = build_recommendation_engine_from_folder(PROCESSED_OFFERS_DIR)
    print(f"✅ Données rechargées depuis {PROCESSED_OFFERS_DIR}")

# Chargement initial
load_recommendation_data()


@router.get("/search", response_model = List[JobOfferResponse])
def search_offers(query: str = Query(..., description = "Mot-clé recherché")):
    """
    Endpoint permettant de récupérer les offres d'emploi recommandées.
    Les résultats sont triés par pertinence (TF-IDF + cosinus).
    """
    try:
        recos = recommend_offers(
            user_input = query,
            offers_vectorizer = vectorizer,
            processed_offer_vectors = offer_vectors,
            processed_offers = offers,
            top_n = 20,
        )
        results: List[JobOfferResponse] = []
        for o in recos:
            # Coerce pour éviter les None auprès de Pydantic
            description = o.get("description") or ""
            company = o.get("company") or ""
            location = o.get("location") or ""
            code_postal = o.get("code_postal") or ""

            salary_min = (
                float(o["salary_min"])
                if o.get("salary_min") not in ("", None)
                else None
            )
            salary_max = (
                float(o["salary_max"])
                if o.get("salary_max") not in ("", None)
                else None
            )

            results.append(JobOfferResponse(
                external_id = o["external_id"],
                title = o["title"],
                company = company,
                description = description,
                location = location,
                code_postal = code_postal,
                salary_min = salary_min,
                salary_max = salary_max,
                url = o["apply_url"]
            ))

        return results

    except Exception as e:
        print(f"Erreur dans /search : {e}")
        raise


@router.post("/reload", status_code=200)
def reload_offers():
    try:
        load_recommendation_data()
        return {"message": "Données rechargées avec succès"}
    except Exception as e:
        return {"error": str(e)}