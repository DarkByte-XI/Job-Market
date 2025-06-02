from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, TIMESTAMP
from sqlalchemy.orm import relationship
from API.orm_connexion import Base

class Company(Base):
    __tablename__ = "companies"

    company_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)

    job_offers = relationship("JobOffer", back_populates="company")


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, index=True)
    location = Column(String(255))
    code_postal = Column(String(10))
    longitude = Column(Float)
    latitude = Column(Float)
    country = Column(String(255))

    job_offers = relationship("JobOffer", back_populates="location")


class JobOffer(Base):
    __tablename__ = "job_offers"

    job_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.company_id"))
    location_id = Column(Integer, ForeignKey("locations.location_id"))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    created_at = Column(TIMESTAMP)
    status = Column(Text)

    company = relationship("Company", back_populates="job_offers")
    location = relationship("Location", back_populates="job_offers")
