"""
RAG Service models for KiwiQ system.

The RAG service is designed as a wrapper service that orchestrates existing components:
- WeaviateChunkClient for vector database operations
- CustomerDataService for MongoDB document access  
- DocumentIngestionPipeline for document processing

As such, it does not require its own database models. All data persistence
is handled by the underlying services it wraps.

For API request/response models, see schemas.py
For service exceptions, see exceptions.py
For service dependencies, see dependencies.py
For service logic, see services.py
For API endpoints, see routers.py
"""

# No database models needed for RAG service
# This service operates as a coordination layer over existing services
