from pydantic import BaseModel
from typing import Optional

class JobOfferResponse(BaseModel):
    job_id: int
    salary_min: Optional[int]
    salary_max: Optional[int]
    status: Optional[str]
    company_name: Optional[str]
    location: Optional[str]

    class Config:
        orm_mode = True