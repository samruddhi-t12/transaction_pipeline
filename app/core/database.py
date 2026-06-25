from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 1. Create the Engine
engine = create_engine(settings.DATABASE_URL)

# 2. Create the Session Factory
# Note the lowercase 'autoflush' here
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Create the Base Class
Base = declarative_base()

# 4. Dependency Injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()