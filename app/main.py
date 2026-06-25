from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
# We must import the models here so SQLAlchemy knows they exist before creating tables
from app.models import domain 
from app.api.routes import router as jobs_router
# The Sanity Check: Force SQLAlchemy to create the tables in PostgreSQL
# (Note: In a real enterprise app, we use a migration tool like Alembic for this, 
# but for this assignment, this is perfectly fine).
Base.metadata.create_all(bind=engine)

# Initialize the API
app = FastAPI(title=settings.PROJECT_NAME)
app.include_router(jobs_router)

@app.get("/")
def health_check():
    """A simple endpoint to verify the server is breathing."""
    return {"status": "ok", "project": settings.PROJECT_NAME, "environment": settings.ENVIRONMENT}