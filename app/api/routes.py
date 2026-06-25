import uuid
import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import Job, JobSummary
from app.worker.tasks import process_csv_task

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Ensure the upload directory exists
UPLOAD_DIR = "app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_transactions_csv(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # 1. Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    # 2. Save the file temporarily to disk
    job_id = uuid.uuid4()
    file_extension = file.filename.split(".")[-1]
    safe_filename = f"{job_id}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 3. Create the Database Record
    new_job = Job(
        id=job_id,
        filename=file.filename,
        status="pending"
    )
    db.add(new_job)
    db.commit()
    
    # 4. Offload the heavy work to Celery via Redis
    process_csv_task.delay(str(job_id), file_path)
    
    # 5. Return immediately!
    return {
        "message": "File uploaded successfully. Processing started in the background.",
        "job_id": str(job_id),
        "status": "pending"
    }

@router.get("")
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status (pending, processing, completed, failed)"),
    db: Session = Depends(get_db)
):
    """List all jobs with optional status filtering."""
    query = db.query(Job)
    
    if status:
        query = query.filter(Job.status == status)
        
    jobs = query.all()
    
    return [
        {
            "job_id": str(job.id),
            "status": job.status,
            "filename": job.filename,
            "row_count": job.row_count_raw, 
            "created_at": job.created_at
        }
        for job in jobs
    ]

@router.get("/{job_id}/status")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """A quick endpoint to let the user check on their background job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {"job_id": str(job.id), "status": job.status, "error": job.error_message}

@router.get("/{job_id}/summary")
def get_job_summary(job_id: str, db: Session = Depends(get_db)):
    """Fetches the final AI-generated financial narrative."""
    # 1. Ensure the job actually exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # 2. Check if the AI is still thinking
    if job.status != "completed":
        return {"message": f"Job is currently {job.status}. Summary not ready yet."}
        
    # 3. Fetch the summary
    summary = db.query(JobSummary).filter(JobSummary.job_id == job_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found. The LLM might have failed.")
        
    return {
        "job_id": str(job.id),
        "total_spend_inr": summary.total_spend_inr,
        "total_spend_usd": summary.total_spend_usd,
        "anomaly_count": summary.anomaly_count,
        "risk_level": summary.risk_level,
        "top_merchants": summary.top_merchants,
        "ai_narrative": summary.narrative
    }