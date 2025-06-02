# src/API/main.py

from fastapi import FastAPI
from src.API.recommend import router as recommend_router
from src.API.companies import router as companies_router

app = FastAPI(
    title="Job Recommendation API",
    description="API de recherche et recommandation d'offres d'emploi",
    version="1.0.0"
)

# On inclut les endpoints
app.include_router(recommend_router)
app.include_router(companies_router)
