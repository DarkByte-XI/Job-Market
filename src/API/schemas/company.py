from pydantic import BaseModel

class CompanyResponse(BaseModel):
    company_id: int
    name: str

    class Config:
        orm_mode = True
