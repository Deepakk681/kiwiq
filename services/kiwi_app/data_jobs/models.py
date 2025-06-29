"""
Data Jobs models for KiwiQ system.

This module defines the database models for tracking data jobs like ingestion pipelines,
cron jobs, and other background processing tasks. Simplified for system-level jobs only.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import String as SQLAlchemyString, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel, Column

from global_utils import datetime_now_utc
from kiwi_app.settings import settings

# Define table prefix following KiwiQ patterns
table_prefix = f"{settings.DB_TABLE_NAMESPACE_PREFIX}data_jobs_"

# --- Enums --- #

class DataJobStatus(str, Enum):
    """Status values for data jobs."""
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DataJobType(str, Enum):
    """Types of data jobs in the system."""
    INGESTION = "rag_ingestion"
    DOCUMENT_PROCESSING = "document_processing"
    CREDIT_EXPIRATION = "credit_expiration"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    CRON_JOB = "cron_job"
    ONE_TIME_JOB = "one_time_job"
    DATA_CLEANUP = "data_cleanup"
    ANALYTICS_PROCESSING = "analytics_processing"
    WORKFLOW_EXECUTION = "workflow_execution"
    OTHER = "other"

# --- Models --- #

class DataJob(SQLModel, table=True):
    """
    Data job tracking for system-level background tasks.
    
    This model tracks various data processing jobs like ingestion pipelines,
    cron jobs, and other background tasks. Simplified for system use only.
    """
    __tablename__ = f"{table_prefix}data_job"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    
    # Job identification
    job_name: Optional[str] = Field(
        default=None,
        sa_column=Column(SQLAlchemyString, nullable=True),
        description="Optional human-readable name for the job"
    )
    job_type: str = Field(
        sa_column=Column(SQLAlchemyString, index=True),
        description="Type of job being performed"
    )
    
    # Status and timestamps
    status: DataJobStatus = Field(
        sa_column=Column(sa.Enum(DataJobStatus, name=f"{table_prefix}status_enum"), index=True),
        default=DataJobStatus.PENDING
    )
    # These timestamps track data processing timeframes (set manually by cron jobs)
    # NOT job execution times - they represent the time range of data being processed
    processed_timestamp_start: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True, index=True),
        description="Start of data processing timeframe (set by cron jobs)"
    )
    processed_timestamp_end: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True, index=True),
        description="End of data processing timeframe (set by cron jobs)"
    )
    
    # Error information
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="Error message if job failed"
    )
    
    # Performance tracking
    records_processed: Optional[int] = Field(
        default=None,
        description="Number of records successfully processed"
    )
    records_failed: Optional[int] = Field(
        default=None,
        description="Number of records that failed processing"
    )
    processing_duration_seconds: Optional[float] = Field(
        default=None,
        description="Total processing time in seconds"
    )
    
    # Job metadata
    job_metadata: Optional[Dict[str, Any]] = Field(
        sa_column=Column(JSON),
        default=None,
        description="Additional job-specific metadata"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime_now_utc,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False, index=True)
    )
    updated_at: datetime = Field(
        default_factory=datetime_now_utc,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False, onupdate=datetime_now_utc, index=True)
    )
    
    # Database indexes for efficient querying
    __table_args__ = (
        Index(f"idx_{table_prefix}data_job_type_status", "job_type", "status"),
        Index(f"idx_{table_prefix}data_job_type_created", "job_type", "created_at"),
        Index(f"idx_{table_prefix}data_job_status_created", "status", "created_at"),
        # Index(f"idx_{table_prefix}data_job_start_time", "processed_timestamp_start"),
        # Index(f"idx_{table_prefix}data_job_end_time", "processed_timestamp_end"),
    )
    
    # Helper methods
    def calculate_processing_duration(self) -> Optional[float]:
        """Calculate processing duration if both timestamps are available."""
        if self.processed_timestamp_start and self.processed_timestamp_end:
            delta = self.processed_timestamp_end - self.processed_timestamp_start
            return delta.total_seconds()
        return None
    
    def is_completed(self) -> bool:
        """Check if the job has completed (successfully or failed)."""
        return self.status in [DataJobStatus.COMPLETED, DataJobStatus.FAILED, DataJobStatus.CANCELLED]
    
    def is_running(self) -> bool:
        """Check if the job is currently running."""
        return self.status == DataJobStatus.STARTED
    
    def get_job_type_enum(self) -> DataJobType:
        """Get the job type as an enum value."""
        try:
            return DataJobType(self.job_type)
        except ValueError:
            return DataJobType.OTHER

# Update forward references
DataJob.model_rebuild() 