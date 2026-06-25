import uuid
from sqlalchemy import Column, String, Numeric, Boolean, Integer, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    filename = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, index=True) 
    row_count_raw = Column(Integer, nullable=True)
    row_count_clean = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="check_job_status"),
    )

    # Relationships
    transactions = relationship("Transaction", back_populates="job", cascade="all, delete-orphan")
    summary = relationship("JobSummary", back_populates="job", uselist=False, cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    txn_id = Column(String(255), nullable=True)
    date = Column(DateTime, nullable=False)
    merchant = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    account_id = Column(String(255), nullable=True)
    is_anomaly = Column(Boolean, nullable=False, default=False)
    anomaly_reason = Column(String, nullable=True)
    llm_category = Column(String(50), nullable=True)
    llm_raw_response = Column(JSONB, nullable=True)
    llm_failed = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("currency IN ('INR', 'USD')", name="check_currency"),
        CheckConstraint("status IN ('SUCCESS', 'FAILED', 'PENDING')", name="check_txn_status"),
    )

    # Relationships
    job = relationship("Job", back_populates="transactions")

class JobSummary(Base):
    __tablename__ = "job_summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_spend_inr = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_spend_usd = Column(Numeric(15, 2), nullable=False, default=0.00)
    top_merchants = Column(JSONB, nullable=False)
    anomaly_count = Column(Integer, nullable=False, default=0)
    narrative = Column(String, nullable=False)
    risk_level = Column(String(10), nullable=False)

    __table_args__ = (
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name="check_risk_level"),
    )

    # Relationships
    job = relationship("Job", back_populates="summary")