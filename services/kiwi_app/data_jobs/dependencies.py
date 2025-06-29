"""
Data Jobs dependencies for KiwiQ system.

This module defines dependency injection functions for data jobs services and DAOs,
following KiwiQ's established patterns for dependency management.
Simplified for system-level jobs.
"""

import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_async_db_dependency
from kiwi_app.utils import get_kiwi_logger
from kiwi_app.auth.dependencies import get_organization_dao
from kiwi_app.data_jobs import crud, services, models
from kiwi_app.auth.dependencies import (
    get_current_active_superuser
)
from kiwi_app.auth.models import User

data_jobs_logger = get_kiwi_logger(name="kiwi_app.data_jobs.dependencies")

# --- DAO Dependency Factories --- #

def get_data_job_dao() -> crud.DataJobDAO:
    """Get DataJobDAO instance."""
    return crud.DataJobDAO()

# --- Service Dependency Factory --- #

def get_data_jobs_service_no_dependencies() -> services.DataJobService:
    """Get DataJobService instance without dependencies."""
    return services.DataJobService(
        data_job_dao=get_data_job_dao(),
    )

def get_data_jobs_service(
    data_job_dao: crud.DataJobDAO = Depends(get_data_job_dao),
) -> services.DataJobService:
    """
    Dependency function to instantiate DataJobService with its DAO dependencies.
    
    This follows KiwiQ's established pattern for service dependency injection,
    ensuring all required DAOs are properly injected into the service.
    """
    return services.DataJobService(
        data_job_dao=data_job_dao,
    )

# --- Resource Fetching Dependencies --- #

async def get_data_job_by_id(
    job_id: uuid.UUID = Path(..., description="Data job ID"),
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_async_db_dependency),
    data_job_dao: crud.DataJobDAO = Depends(get_data_job_dao)
) -> models.DataJob:
    """
    Dependency to fetch a data job by ID (admin only).
    
    This dependency validates that:
    1. The job exists
    2. The user is a superuser (since these are system jobs)
    
    Args:
        job_id: The data job ID to fetch
        current_user: Current authenticated superuser
        db: Database session
        data_job_dao: Data job DAO instance
        
    Returns:
        DataJob model instance
        
    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        # Fetch the job
        job = await data_job_dao.get(db, job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Data job {job_id} not found"
            )
        
        data_jobs_logger.info(f"Superuser {current_user.id} accessed data job {job_id}")
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        data_jobs_logger.error(f"Error fetching data job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch data job"
        ) 