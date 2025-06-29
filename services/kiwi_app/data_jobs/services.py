"""
Data Jobs services for KiwiQ system.

This module defines the service layer for data job operations.
Simplified for basic admin dashboard functionality.
"""

import uuid
from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from kiwi_app.auth.utils import datetime_now_utc
from kiwi_app.utils import get_kiwi_logger

from kiwi_app.data_jobs import crud, models, schemas
from kiwi_app.data_jobs.models import DataJobStatus
from kiwi_app.data_jobs.exceptions import DataJobException

# Get logger for data job operations
data_jobs_logger = get_kiwi_logger(name="kiwi_app.data_jobs")


class DataJobService:
    """Service layer for data job operations."""
    
    def __init__(
        self,
        data_job_dao: crud.DataJobDAO,
    ):
        """Initialize service with DAO instances."""
        self.data_job_dao = data_job_dao
    
    # --- Job Management --- #
    
    async def create_job(
        self,
        db: AsyncSession,
        job_data: schemas.DataJobCreate
    ) -> schemas.DataJobRead:
        """Create a new data job."""
        try:
            job = await self.data_job_dao.create_job(
                db=db,
                job_data=job_data,
                commit=True
            )
            
            job_read = schemas.DataJobRead.model_validate(job)
            data_jobs_logger.info(f"Created data job {job.id} of type {job.job_type}")
            return job_read
            
        except Exception as e:
            data_jobs_logger.error(f"Error creating data job: {e}", exc_info=True)
            raise DataJobException(
                status_code=500,
                detail=f"Failed to create data job: {str(e)}"
            )
    
    async def update_job_status(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
        status_update: schemas.DataJobStatusUpdate
    ) -> schemas.DataJobRead:
        """Update job status."""
        try:
            job = await self.data_job_dao.update_job_status(
                db=db,
                job_id=job_id,
                status_update=status_update,
                commit=True
            )
            
            job_read = schemas.DataJobRead.model_validate(job)
            data_jobs_logger.info(f"Updated job {job_id} status to {status_update.status.value}")
            return job_read
            
        except Exception as e:
            data_jobs_logger.error(f"Error updating job status: {e}", exc_info=True)
            raise
    
    async def start_job(
        self,
        db: AsyncSession,
        job_id: uuid.UUID
    ) -> schemas.DataJobRead:
        """Start a data job execution."""
        try:
            job = await self.data_job_dao.start_job(db=db, job_id=job_id, commit=True)
            job_read = schemas.DataJobRead.model_validate(job)
            data_jobs_logger.info(f"Started job {job_id}")
            return job_read
            
        except Exception as e:
            data_jobs_logger.error(f"Error starting job: {e}", exc_info=True)
            raise
    
    async def complete_job(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
        completion_data: schemas.DataJobCompletion
    ) -> schemas.DataJobRead:
        """Complete a data job execution."""
        try:
            job = await self.data_job_dao.complete_job(
                db=db,
                job_id=job_id,
                records_processed=completion_data.records_processed,
                records_failed=completion_data.records_failed,
                commit=True
            )
            
            # Update metadata if provided
            if completion_data.result_metadata:
                update_data = schemas.DataJobUpdate(
                    job_metadata={
                        **(job.job_metadata or {}),
                        "completion_result": completion_data.result_metadata
                    }
                )
                
                job = await self.data_job_dao.update(
                    db=db,
                    db_obj=job,
                    obj_in=update_data
                )
                await db.commit()
                await db.refresh(job)
            
            job_read = schemas.DataJobRead.model_validate(job)
            data_jobs_logger.info(f"Completed job {job_id}")
            return job_read
            
        except Exception as e:
            data_jobs_logger.error(f"Error completing job: {e}", exc_info=True)
            raise
    
    async def fail_job(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
        failure_data: schemas.DataJobFailure
    ) -> schemas.DataJobRead:
        """Mark a data job as failed."""
        try:
            job = await self.data_job_dao.fail_job(
                db=db,
                job_id=job_id,
                error_message=failure_data.error_message,
                records_processed=failure_data.records_processed,
                records_failed=failure_data.records_failed,
                commit=True
            )
            
            # Update metadata if provided
            if failure_data.failure_metadata:
                update_data = schemas.DataJobUpdate(
                    job_metadata={
                        **(job.job_metadata or {}),
                        "failure_details": failure_data.failure_metadata
                    }
                )
                
                job = await self.data_job_dao.update(
                    db=db,
                    db_obj=job,
                    obj_in=update_data
                )
                await db.commit()
                await db.refresh(job)
            
            job_read = schemas.DataJobRead.model_validate(job)
            data_jobs_logger.error(f"Failed job {job_id}: {failure_data.error_message}")
            return job_read
            
        except Exception as e:
            data_jobs_logger.error(f"Error failing job: {e}", exc_info=True)
            raise
    
    # --- Job Querying --- #
    
    async def query_jobs(
        self,
        db: AsyncSession,
        query_params: schemas.DataJobQuery
    ) -> schemas.PaginatedDataJobs:
        """Query data jobs with filtering and pagination."""
        try:
            result = await self.data_job_dao.query_jobs(db=db, query_params=query_params)
            data_jobs_logger.info(f"Queried data jobs: {len(result.items)} results")
            return result
            
        except Exception as e:
            data_jobs_logger.error(f"Error querying data jobs: {e}", exc_info=True)
            raise
    
    async def get_job_statistics(
        self,
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> schemas.DataJobStats:
        """Get statistics about data jobs."""
        try:
            # Default to last 30 days if no date range provided
            if not date_from:
                date_from = datetime_now_utc() - timedelta(days=30)
            if not date_to:
                date_to = datetime_now_utc()
            
            stats = await self.data_job_dao.get_job_statistics(
                db=db,
                date_from=date_from,
                date_to=date_to
            )
            
            data_jobs_logger.info(f"Generated job statistics from {date_from} to {date_to}")
            return stats
            
        except Exception as e:
            data_jobs_logger.error(f"Error getting job statistics: {e}", exc_info=True)
            raise
    
    async def get_dashboard_data(
        self,
        db: AsyncSession
    ) -> schemas.DataJobDashboard:
        """Get dashboard data for data jobs."""
        try:
            # Get recent statistics
            recent_cutoff = datetime_now_utc() - timedelta(hours=24)
            stats = await self.get_job_statistics(
                db=db,
                date_from=recent_cutoff
            )
            
            # Get running jobs
            running_jobs = await self.data_job_dao.get_running_jobs(db)
            running_jobs_read = [schemas.DataJobRead.model_validate(job) for job in running_jobs]
            
            # Get recent failed jobs
            failed_jobs = await self.data_job_dao.get_failed_jobs(db=db, hours_back=24)
            failed_jobs_read = [schemas.DataJobRead.model_validate(job) for job in failed_jobs]
            
            dashboard = schemas.DataJobDashboard(
                statistics=stats,
                running_jobs=running_jobs_read,
                recent_failed_jobs=failed_jobs_read,
                last_updated=datetime_now_utc()
            )
            
            data_jobs_logger.info("Generated dashboard data")
            return dashboard
            
        except Exception as e:
            data_jobs_logger.error(f"Error getting dashboard data: {e}", exc_info=True)
            raise
    
    # --- Helper Methods --- #
    
    async def get_latest_successful_job(
        self,
        db: AsyncSession,
        job_type: str
    ) -> Optional[schemas.DataJobRead]:
        """Get the latest successful job of a specific type."""
        try:
            job = await self.data_job_dao.get_latest_successful_job(db, job_type)
            if job:
                return schemas.DataJobRead.model_validate(job)
            return None
            
        except Exception as e:
            data_jobs_logger.error(f"Error getting latest successful job: {e}", exc_info=True)
            raise
    
    async def get_successful_jobs_in_range(
        self,
        db: AsyncSession,
        job_type: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[schemas.DataJobRead]:
        """Get successful jobs of a specific type within a time range."""
        try:
            jobs = await self.data_job_dao.get_successful_jobs_in_range(
                db, job_type, start_time, end_time
            )
            return [schemas.DataJobRead.model_validate(job) for job in jobs]
            
        except Exception as e:
            data_jobs_logger.error(f"Error getting successful jobs in range: {e}", exc_info=True)
            raise
    
    # --- Bulk Operations --- #
    
    async def bulk_update_status(
        self,
        db: AsyncSession,
        job_ids: List[uuid.UUID],
        status: DataJobStatus,
        error_message: Optional[str] = None
    ) -> schemas.DataJobBulkStatusResult:
        """Bulk update status for multiple jobs."""
        try:
            result = await self.data_job_dao.bulk_update_status(
                db=db,
                job_ids=job_ids,
                status=status,
                error_message=error_message,
                commit=True
            )
            
            data_jobs_logger.info(f"Bulk updated {result.updated_count} jobs to {status.value}")
            return result
            
        except Exception as e:
            data_jobs_logger.error(f"Error in bulk status update: {e}", exc_info=True)
            raise
    
    async def cleanup_old_jobs(
        self,
        db: AsyncSession,
        older_than_days: int = 90
    ) -> schemas.DataJobCleanupResult:
        """Clean up old data jobs."""
        try:
            # Exclude running jobs from cleanup
            exclude_statuses = [DataJobStatus.STARTED, DataJobStatus.PENDING]
            
            deleted_count = await self.data_job_dao.delete_old_jobs(
                db=db,
                older_than_days=older_than_days,
                exclude_statuses=exclude_statuses,
                commit=True
            )
            
            cleanup_result = schemas.DataJobCleanupResult(
                success=True,
                deleted_count=deleted_count,
                older_than_days=older_than_days,
                excluded_statuses=[status.value for status in exclude_statuses],
                message=f"Successfully cleaned up {deleted_count} old jobs"
            )
            
            data_jobs_logger.info(f"Cleaned up {deleted_count} old jobs")
            return cleanup_result
            
        except Exception as e:
            data_jobs_logger.error(f"Error cleaning up old jobs: {e}", exc_info=True)
            raise
    
    # --- Deletion Operations --- #
    
    async def delete_job_by_id(
        self,
        db: AsyncSession,
        job_id: uuid.UUID
    ) -> schemas.DataJobDeleteResult:
        """Delete a specific job by ID."""
        try:
            deleted = await self.data_job_dao.delete_job_by_id(
                db=db,
                job_id=job_id,
                commit=True
            )
            
            if deleted:
                result = schemas.DataJobDeleteResult(
                    success=True,
                    deleted_count=1,
                    message=f"Successfully deleted job {job_id}"
                )
            else:
                result = schemas.DataJobDeleteResult(
                    success=False,
                    deleted_count=0,
                    message=f"Job {job_id} not found"
                )
            
            data_jobs_logger.info(f"Delete job by ID result: {result.message}")
            return result
            
        except Exception as e:
            data_jobs_logger.error(f"Error deleting job by ID: {e}", exc_info=True)
            raise
    
    async def delete_jobs_by_filter(
        self,
        db: AsyncSession,
        filter_criteria: schemas.DataJobDeleteFilter
    ) -> schemas.DataJobDeleteResult:
        """Delete jobs based on filter criteria."""
        try:
            # Exclude running/pending jobs for safety
            exclude_statuses = [DataJobStatus.STARTED, DataJobStatus.PENDING]
            
            deleted_count = await self.data_job_dao.delete_jobs_by_filter(
                db=db,
                job_types=filter_criteria.job_types,
                statuses=filter_criteria.statuses,
                created_before=filter_criteria.created_before,
                created_after=filter_criteria.created_after,
                exclude_statuses=exclude_statuses,
                commit=True
            )
            
            result = schemas.DataJobDeleteResult(
                success=True,
                deleted_count=deleted_count,
                message=f"Successfully deleted {deleted_count} jobs using filter criteria"
            )
            
            data_jobs_logger.info(f"Deleted {deleted_count} jobs by filter")
            return result
            
        except Exception as e:
            data_jobs_logger.error(f"Error deleting jobs by filter: {e}", exc_info=True)
            raise
    
    async def delete_all_jobs(
        self,
        db: AsyncSession,
        force: bool = False
    ) -> schemas.DataJobDeleteResult:
        """Delete all jobs with safety checks."""
        try:
            # Exclude running/pending jobs unless forced
            exclude_statuses = [] if force else [DataJobStatus.STARTED, DataJobStatus.PENDING]
            
            deleted_count = await self.data_job_dao.delete_all_jobs(
                db=db,
                exclude_statuses=exclude_statuses if exclude_statuses else None,
                commit=True
            )
            
            safety_note = "" if force else " (excluded running/pending jobs)"
            result = schemas.DataJobDeleteResult(
                success=True,
                deleted_count=deleted_count,
                message=f"Successfully deleted all {deleted_count} jobs{safety_note}"
            )
            
            data_jobs_logger.warning(f"Deleted ALL {deleted_count} jobs (force={force})")
            return result
            
        except Exception as e:
            data_jobs_logger.error(f"Error deleting all jobs: {e}", exc_info=True)
            raise
    
    # --- Flow Trigger Operations --- #
    
    async def trigger_rag_ingestion(
        self,
        trigger_params: schemas.RAGIngestionTrigger
    ) -> schemas.RAGIngestionTriggerResult:
        """Trigger RAG data ingestion flow."""
        try:
            # Import here to avoid circular imports
            from workflow_service.services.cron_flows import trigger_rag_ingestion_deployment
            
            # Trigger the deployment
            flow_run = await trigger_rag_ingestion_deployment(
                start_timestamp=trigger_params.start_timestamp,
                end_timestamp=trigger_params.end_timestamp,
                batch_size=trigger_params.batch_size,
                max_batches=trigger_params.max_batches,
                generate_vectors=trigger_params.generate_vectors
            )
            
            # Prepare result parameters
            parameters_used = {
                "start_timestamp": trigger_params.start_timestamp.isoformat() if trigger_params.start_timestamp else None,
                "end_timestamp": trigger_params.end_timestamp.isoformat() if trigger_params.end_timestamp else "now",
                "batch_size": trigger_params.batch_size,
                "max_batches": trigger_params.max_batches,
                "generate_vectors": trigger_params.generate_vectors
            }
            
            result = schemas.RAGIngestionTriggerResult(
                success=True,
                flow_run_id=str(flow_run.id),
                message=f"Successfully triggered RAG ingestion flow (Run ID: {flow_run.id})",
                parameters_used=parameters_used
            )
            
            data_jobs_logger.info(f"Triggered RAG ingestion flow: {flow_run.id}")
            return result
            
        except Exception as e:
            data_jobs_logger.error(f"Error triggering RAG ingestion: {e}", exc_info=True)
            result = schemas.RAGIngestionTriggerResult(
                success=False,
                flow_run_id="",
                message=f"Failed to trigger RAG ingestion: {str(e)}",
                parameters_used={}
            )
            return result 