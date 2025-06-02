from pydantic import BaseModel
from typing import Optional

class JobOfferResponse(BaseModel):
    external_id: str
    title: str
    company: str
    description: str
    location: str
    code_postal: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    url: str