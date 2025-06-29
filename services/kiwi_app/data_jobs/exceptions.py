"""
Data jobs exceptions for KiwiQ system.

This module defines custom exceptions for data job operations,
providing structured error handling and appropriate HTTP status codes.
"""

from typing import Optional
from fastapi import HTTPException, status


class DataJobException(HTTPException):
    """Base exception for data job operations."""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Data job operation failed",
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.status_code = status_code
        self.detail = detail


class DataJobNotFoundException(DataJobException):
    """Exception raised when a data job is not found."""
    
    def __init__(self, job_id: Optional[str] = None):
        detail = f"Data job not found"
        if job_id:
            detail = f"Data job with ID {job_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class DataJobInvalidStatusException(DataJobException):
    """Exception raised when attempting invalid status transitions."""
    
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {current_status} to {target_status}"
        )


class DataJobAlreadyStartedException(DataJobException):
    """Exception raised when attempting to start an already started job."""
    
    def __init__(self, job_id: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Data job {job_id} is already started"
        )


class DataJobNotRetryableException(DataJobException):
    """Exception raised when attempting to retry a non-retryable job."""
    
    def __init__(self, job_id: str, reason: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data job {job_id} cannot be retried: {reason}"
        )


class DataJobValidationException(DataJobException):
    """Exception raised when data job validation fails."""
    
    def __init__(self, validation_errors: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data job validation failed: {validation_errors}"
        )


class DataJobExecutionException(DataJobException):
    """Exception raised when data job execution fails."""
    
    def __init__(self, job_id: str, error_message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data job {job_id} execution failed: {error_message}"
        )


class DataJobTimeoutException(DataJobException):
    """Exception raised when data job execution times out."""
    
    def __init__(self, job_id: str, timeout_seconds: int):
        super().__init__(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Data job {job_id} timed out after {timeout_seconds} seconds"
        )


class DataJobConfigurationException(DataJobException):
    """Exception raised when data job configuration is invalid."""
    
    def __init__(self, config_issue: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data job configuration error: {config_issue}"
        ) 