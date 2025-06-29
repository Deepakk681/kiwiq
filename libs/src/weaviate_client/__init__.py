"""
Weaviate Client Module

This module provides async client functionality for Weaviate operations.
"""

from .weaviate_client import (
    ChunkSchema,
    WeaviateChunkClient,
)

__all__ = [
    "ChunkSchema",
    "WeaviateChunkClient",
]

# Version of the weaviate_client module
__version__ = "0.1.0"
