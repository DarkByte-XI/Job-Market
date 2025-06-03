"""
Schemas Pydantic pour les réponses d'offres d'emploi de l'API Job Market.
"""

from pydantic import BaseModel
from typing import Optional

class JobOfferResponse(BaseModel):
    """
    Modèle de réponse pour une offre d'emploi retournée par l'API.

    Champs :
        external_id (str) : Identifiant unique de l'offre (source externe).
        title (str) : Intitulé du poste.
        company (str) : Nom de l'entreprise.
        location (str) : Ville où se situe le poste.
        code_postal (Optional[str]) : Code postal.
        salary_min (Optional[float]) : Salaire minimum proposé, si disponible.
        salary_max (Optional[float]) : Salaire maximum proposé, si disponible.
        url (str) : Lien direct vers l'offre sur la plateforme source.
    """
    external_id: str
    title: str
    company: str
    location: str
    code_postal: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    url: str
