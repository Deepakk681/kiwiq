"""
RAG Service dependencies for KiwiQ system.

This module defines dependencies for RAG (Retrieval Augmented Generation) operations,
including permission checking, service instantiation, and resource management.
"""

import uuid
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_async_db_dependency
from kiwi_app.auth.models import User
from kiwi_app.auth.dependencies import (
    get_current_active_verified_user,
    get_current_active_superuser,
    PermissionChecker as AuthPermissionChecker
)
from kiwi_app.workflow_app.dependencies import (
    get_active_org_id,
    get_customer_data_service_dependency
)
from kiwi_app.workflow_app.constants import WorkflowPermissions
from kiwi_app.workflow_app.service_customer_data import CustomerDataService
from kiwi_app.utils import get_kiwi_logger

from kiwi_app.rag_service import services
from kiwi_app.rag_service.exceptions import (
    RAGConfigurationException,
    RAGPermissionException
)

from weaviate_client.weaviate_client import WeaviateChunkClient
from kiwi_app.data_jobs.ingestion.ingestion_pipeline import DocumentIngestionPipeline

# Get logger for RAG operations
rag_logger = get_kiwi_logger(name="kiwi_app.rag_service.dependencies")

# --- Permission Checkers --- #

# Reuse workflow permissions for organization data access
RequireRAGReadActiveOrg = AuthPermissionChecker([WorkflowPermissions.ORG_DATA_READ])
RequireRAGWriteActiveOrg = AuthPermissionChecker([WorkflowPermissions.ORG_DATA_WRITE])

# --- Weaviate Client Dependencies --- #

async def get_weaviate_client() -> AsyncGenerator[WeaviateChunkClient, None]:
    """Get Weaviate client dependency."""
    try:
        
        # Create and return Weaviate client
        client = WeaviateChunkClient()
        await client.connect()
        yield client
        # await client.close()
        
    except Exception as e:
        rag_logger.error(f"Failed to create Weaviate client: {e}", exc_info=True)
        raise RAGConfigurationException(
            component="weaviate",
            message=f"Failed to initialize Weaviate client: {str(e)}"
        )
    finally:
        try:
            await client.close()
        except Exception as e:
            rag_logger.error(f"Error closing Weaviate client: {e}", exc_info=True)
            pass

# --- Ingestion Pipeline Dependencies --- #

async def get_ingestion_pipeline(
        # weaviate_client: WeaviateChunkClient = Depends(get_weaviate_client), 
        request: Request,
        ):
    """Get document ingestion pipeline dependency."""
    try:
        # Import here to avoid circular imports
        
        weaviate_client = request.app.state.weaviate
        # Create and return ingestion pipeline
        pipeline = DocumentIngestionPipeline(weaviate_client=weaviate_client)
        return pipeline
        
    except Exception as e:
        rag_logger.error(f"Failed to create ingestion pipeline: {e}", exc_info=True)
        raise RAGConfigurationException(
            component="ingestion_pipeline",
            message=f"Failed to initialize ingestion pipeline: {str(e)}"
        )

# --- RAG Service Dependencies --- #

async def get_rag_service(
    # weaviate_client: WeaviateChunkClient = Depends(get_weaviate_client),
    request: Request,
    customer_data_service: CustomerDataService = Depends(get_customer_data_service_dependency),
    ingestion_pipeline = Depends(get_ingestion_pipeline)
) -> AsyncGenerator[services.RAGService, None]:
    """
    Dependency function to instantiate RAGService with its dependencies.
    
    This creates a fully configured RAG service with:
    - Weaviate client for vector operations
    - Customer data service for MongoDB document access
    - Ingestion pipeline for document processing
    """
    try:
        weaviate_client = request.app.state.weaviate
        rag_service = services.RAGService(
            weaviate_client=weaviate_client,
            customer_data_service=customer_data_service,
            ingestion_pipeline=ingestion_pipeline
        )
        
        rag_logger.info("RAG service instantiated successfully")
        yield rag_service
        
    except Exception as e:
        rag_logger.error(f"Failed to create RAG service: {e}", exc_info=True)
        raise RAGConfigurationException(
            component="rag_service",
            message=f"Failed to initialize RAG service: {str(e)}"
        )


# --- Resource Validation Dependencies --- #
# Removed extra validation methods - using existing permission checkers instead 