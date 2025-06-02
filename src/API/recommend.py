from fastapi import APIRouter, Query
from typing import List
from src.recommender.recommender import (
    build_recommendation_engine_from_folder,
    recommend_offers
)
from src.pipelines.transform import PROCESSED_DATA_DIR
from src.API.schemas.job import JobOfferResponse

router = APIRouter()

offers, vectorizer, offer_vectors, texts, offers_normalized = build_recommendation_engine_from_folder(PROCESSED_DATA_DIR)

@router.get("/search", response_model=List[JobOfferResponse])
def search_offers(query: str = Query(..., description="Mot-clé recherché")):
    try:
        recos = recommend_offers(user_input=query,
                                 offers_vectorizer=vectorizer,
                                 processed_offer_vectors=offer_vectors,
                                 processed_offers=offers,
                                 top_n=10,
                                 score_threshold=0.3)
        results = []
        for o in recos:
            description = o.get("description") or ""
            salary_min = float(o["salary_min"]) if o.get("salary_min") not in ("", None) else None
            salary_max = float(o["salary_max"]) if o.get("salary_max") not in ("", None) else None
            location = o.get("location") or ""
            code_postal = o.get("code_postal") or None

            results.append(JobOfferResponse(
                external_id = o["external_id"],
                title = o["title"],
                company = o["company"],
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