from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.models import domain 
from app.api.routes import router as jobs_router
#this creates table at startup if not exists but does not look for any modifications
#so in production we use Alembic for database versions
Base.metadata.create_all(bind=engine)
#translates domain.py into raw sql and send commands through engine to postgres db

# initialize the API
app = FastAPI(title=settings.PROJECT_NAME)
#attach job processing endpoints
app.include_router(jobs_router)

@app.get("/")
def health_check():
    """A simple endpoint to verify the server is running?"""
    return {"status": "ok", "project": settings.PROJECT_NAME, "environment": settings.ENVIRONMENT}