"""
Schemas Pydantic pour les réponses d'offres d'emploi de l'API Job Market.
"""

from pydantic import BaseModel
from typing import Optional

class JobOfferResponse(BaseModel):
    """
    Modèle de réponse pour une offre d'emploi retournée par l'API.
    """
    external_id: str
    title: str
    company: str
    description: str
    location: str
    code_postal: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    url: str
