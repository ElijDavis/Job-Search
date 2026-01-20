# Data models for the backend application
# Handles data representation and database interactions

from sqlalchemy import Column, Integer, String, DateTime, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    company_name = Column(String)
    job_title = Column(String)
    job_url = Column(String, unique=True)
    match_score = Column(Integer)
    status = Column(String, default='Found')
    ats_type = Column(String)
    pay_range = Column(String)
    last_email_date = Column(DateTime)

# To use SQLite locally: 
# engine = create_engine('sqlite:///jobs.db')
# Base.metadata.create_all(engine)