"""
Entrée principale de l’API Job Market (FastAPI).

- Monte les routes de recherche d’offres et de récupération des entreprises.
- Configure la documentation interactive.
"""

from fastapi import FastAPI
from src.API.recommend import router as recommend_router
from src.API.companies import router as companies_router

app = FastAPI(
    title="Job Market API",
    description="API interne de centralisation et de recommandation d’offres d’emploi multicanal.",
    version="1.0.0"
)

# On inclut les endpoints
app.include_router(recommend_router)
app.include_router(companies_router)
