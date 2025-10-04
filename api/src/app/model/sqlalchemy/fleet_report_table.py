from sqlalchemy import Column, String, JSON, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class FleetReport(Base):
    __tablename__ = 'fleet_report'
    __table_args__ = {'schema': None}

    Device = Column(String, primary_key=True)
    Network = Column(String, primary_key=True)
    Status = Column(String)
    Attributes = Column(JSON)
    Onboarding_Date = Column(TIMESTAMP)
    Last_Updated_Date = Column(TIMESTAMP)