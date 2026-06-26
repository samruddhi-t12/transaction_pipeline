from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# establishes connection pool
engine = create_engine(settings.DATABASE_URL)

# create the Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# create the Base Class
Base = declarative_base()

def get_db():
    db = SessionLocal()#creates new session
    try:
        yield db #hands seesion obj to api route and suspends function
    finally:
        db.close()#close connection even it crashes