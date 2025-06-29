"""
RAG Service exceptions for KiwiQ system.

This module defines custom exceptions for RAG (Retrieval Augmented Generation) operations.
These exceptions provide specific error handling for various RAG service scenarios.
"""

from typing import Any, Dict, Optional
from fastapi import status
# from fastapi import HTTPException

class RAGServiceException(Exception):
    """Base exception for RAG service operations."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class RAGPermissionException(RAGServiceException):
    """Exception raised when user lacks required permissions for RAG operations."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions for RAG operation",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class RAGDocumentNotFoundException(RAGServiceException):
    """Exception raised when a document is not found in the vector database."""
    
    def __init__(
        self,
        doc_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Document '{doc_id}' not found in vector database"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={**(details or {}), "doc_id": doc_id}
        )


class RAGDocumentAccessException(RAGServiceException):
    """Exception raised when user cannot access a specific document."""
    
    def __init__(
        self,
        doc_id: str,
        user_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"User {user_id} cannot access document '{doc_id}'"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details={**(details or {}), "doc_id": doc_id, "user_id": user_id}
        )


class RAGSearchException(RAGServiceException):
    """Exception raised during document search operations."""
    
    def __init__(
        self,
        query: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Search failed for query: '{query[:100]}...'"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**(details or {}), "query": query}
        )


class RAGIngestionException(RAGServiceException):
    """Exception raised during document ingestion operations."""
    
    def __init__(
        self,
        doc_ids: list,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Ingestion failed for {len(doc_ids)} document(s)"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**(details or {}), "doc_ids": doc_ids, "doc_count": len(doc_ids)}
        )


class RAGWeaviateException(RAGServiceException):
    """Exception raised during Weaviate database operations."""
    
    def __init__(
        self,
        operation: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Weaviate operation '{operation}' failed"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={**(details or {}), "operation": operation}
        )


class RAGValidationException(RAGServiceException):
    """Exception raised when request validation fails."""
    
    def __init__(
        self,
        field: str,
        value: Any,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Invalid value for field '{field}': {value}"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={**(details or {}), "field": field, "value": str(value)}
        )


class RAGConfigurationException(RAGServiceException):
    """Exception raised when RAG service configuration is invalid."""
    
    def __init__(
        self,
        component: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"RAG service configuration error in component: {component}"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={**(details or {}), "component": component}
        )


class RAGResourceLimitException(RAGServiceException):
    """Exception raised when resource limits are exceeded."""
    
    def __init__(
        self,
        resource: str,
        limit: int,
        requested: int,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Resource limit exceeded for {resource}: requested {requested}, limit {limit}"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={
                **(details or {}),
                "resource": resource,
                "limit": limit,
                "requested": requested
            }
        )


class RAGMongoDBException(RAGServiceException):
    """Exception raised during MongoDB operations."""
    
    def __init__(
        self,
        operation: str,
        doc_id: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"MongoDB operation '{operation}' failed"
            if doc_id:
                message += f" for document '{doc_id}'"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={
                **(details or {}),
                "operation": operation,
                **({"doc_id": doc_id} if doc_id else {})
            }
        )


class RAGBulkOperationException(RAGServiceException):
    """Exception raised during bulk operations."""
    
    def __init__(
        self,
        operation: str,
        total_items: int,
        failed_items: int,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if message is None:
            message = f"Bulk {operation} partially failed: {failed_items}/{total_items} items failed"
        
        super().__init__(
            message=message,
            status_code=status.HTTP_207_MULTI_STATUS,
            details={
                **(details or {}),
                "operation": operation,
                "total_items": total_items,
                "failed_items": failed_items,
                "success_rate": (total_items - failed_items) / total_items if total_items > 0 else 0
            }
        ) 