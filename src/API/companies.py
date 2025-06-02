from fastapi import APIRouter
from typing import List
from src.pipelines.transform import PROCESSED_DATA_DIR
from src.API.schemas.company import CompanyResponse
import os
import json
import glob
import hashlib

router = APIRouter()

@router.get("/companies", response_model=List[CompanyResponse])
def list_companies():
    # On charge le dernier fichier processed contenant les offres
    # Même logique que dans recommender.py pour trouver le dernier fichier
    pattern = os.path.join(PROCESSED_DATA_DIR, "transformed_*.json")
    files = [f for f in glob.glob(pattern)]

    if not files:
        return []
    latest_file = max(files, key=os.path.getmtime)
    with open(latest_file, "r", encoding="utf-8") as f:
        offers = json.load(f)

    # Extraire entreprises distinctes
    companies_seen = set()
    companies = []

    for o in offers:
        company_name = o.get("company", "")
        if company_name and company_name not in companies_seen:
            company_id = hashlib.md5(company_name.encode()).hexdigest()
            companies.append(CompanyResponse(id = company_id, name = company_name))
            companies_seen.add(company_name)
    return companies