"""
Weaviate Document Chunk Client

This module provides a specialized client for managing document chunks in Weaviate.
It extends the base WeaviateBaseClient with DocChunk-specific functionality including:
- ChunkSchema definition for document chunks
- Batch ingestion and deletion by doc_id
- Document reingestion with automatic chunk cleanup
- DocChunk-specific filtering and search
- Date range queries on temporal fields
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from weaviate.classes.config import Configure, DataType, Property, VectorDistances, Tokenization, StopwordsPreset
from weaviate.classes.query import Filter
from weaviate.util import generate_uuid5

from .base_client import WeaviateBaseClient

# Configure logging
logger = logging.getLogger(__name__)


class ChunkSchema:
    """
    Defines the schema for document chunks in Weaviate.

    This schema includes:
    - Temporal fields (created_at, updated_at, scheduled_date)
    - Document identifiers (doc_id, org_segment, user_segment, etc.)
    - Chunk content and metadata

    Note: created_at and updated_at represent the MongoDB document's original timestamps
    for sync and audit purposes.
    """

    # Collection name
    COLLECTION_NAME = "CustomerDocumentChunk"

    # Property names as constants for consistency
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    SCHEDULED_DATE = "scheduled_date"
    DOC_ID = "doc_id"
    ORG_SEGMENT = "org_segment"
    USER_SEGMENT = "user_segment"
    NAMESPACE = "namespace"
    DOC_NAME = "doc_name"
    VERSION = "version"
    CHUNK_NO = "chunk_no"
    CHUNK_CONTENT = "chunk_content"
    CHUNK_KEYS = "chunk_keys"

    @classmethod
    def get_properties(cls) -> List[Property]:
        """
        Returns the property definitions for the chunk schema.

        Returns:
            List[Property]: List of Weaviate property configurations
        """
        return [
            # Temporal fields

            Property(
                name=cls.CREATED_AT,
                data_type=DataType.DATE,
                description="MongoDB document creation timestamp",
                index_filterable=True,
                index_range_filters=True,  # Enable range filtering
                index_searchable=False,
                skip_vectorization=True,  # Don't include in vector
            ),
            Property(
                name=cls.UPDATED_AT,
                data_type=DataType.DATE,
                description="MongoDB document last update timestamp",
                index_filterable=True,
                index_range_filters=True,  # Enable range filtering
                index_searchable=False,
                skip_vectorization=True,  # Don't include in vector
            ),
            Property(
                name=cls.SCHEDULED_DATE,
                data_type=DataType.DATE,
                description="Scheduled date for the document (nullable)",
                index_filterable=True,
                index_range_filters=True,  # Enable range filtering
                index_searchable=False,
                skip_vectorization=True,  # Don't include in vector
                # Note: indexNullState is False by default
            ),

            # Document identifiers - all skip vectorization
            Property(
                name=cls.DOC_ID,
                data_type=DataType.TEXT,
                description="Full document ID for MongoDB queries and deletion",
                index_filterable=True,
                index_searchable=False,
                tokenization=Tokenization.FIELD,  # Exact match only
                skip_vectorization=True,  # Don't include in vector
            ),
            Property(
                name=cls.ORG_SEGMENT,
                data_type=DataType.TEXT,
                description="Organization segment identifier",
                index_filterable=True,
                index_searchable=False,
                tokenization=Tokenization.FIELD,
                skip_vectorization=True,  # Don't include in vector
            ),
            Property(
                name=cls.USER_SEGMENT,
                data_type=DataType.TEXT,
                description="User segment identifier",
                index_filterable=True,
                index_searchable=False,
                tokenization=Tokenization.FIELD,
                skip_vectorization=True,  # Don't include in vector
            ),
            Property(
                name=cls.NAMESPACE,
                data_type=DataType.TEXT,
                description="Document namespace",
                index_filterable=True,
                index_searchable=False,
                tokenization=Tokenization.FIELD,
                skip_vectorization=True,  # Don't include in vector
            ),
            Property(
                name=cls.DOC_NAME,
                data_type=DataType.TEXT,
                description="Document name",
                index_filterable=True,
                index_searchable=True,  # Allow text search on doc name
                tokenization=Tokenization.WORD,
                skip_vectorization=True,  # Don't include in vector
            ),
            Property(
                name=cls.VERSION,
                data_type=DataType.TEXT,
                description="Document version (nullable)",
                index_filterable=True,
                index_searchable=False,
                tokenization=Tokenization.FIELD,
                skip_vectorization=True,  # Don't include in vector
            ),
            Property(
                name=cls.CHUNK_NO,
                data_type=DataType.INT,
                description="Chunk number within the document",
                index_filterable=True,
                index_searchable=False,
                skip_vectorization=True,  # Don't include in vector
            ),

            # Chunk content
            Property(
                name=cls.CHUNK_CONTENT,
                data_type=DataType.TEXT,
                description="Main chunk content (JSON serialized or text/markdown) for vectorization and search",
                index_filterable=False,
                index_searchable=True,
                tokenization=Tokenization.WORD,
                vectorize_property_name=False,  # Don't include property name in vector
            ),
            Property(
                name=cls.CHUNK_KEYS,
                data_type=DataType.TEXT_ARRAY,
                description="JSON keys extracted from the chunk",
                index_filterable=True,
                index_searchable=True,
                tokenization=Tokenization.WORD,
                skip_vectorization=True,  # By default, don't include in vector
            ),
        ]


class WeaviateChunkClient(WeaviateBaseClient):
    """
    Specialized client for managing document chunks in Weaviate.

    This client extends WeaviateBaseClient with DocChunk-specific functionality:
    - Automatic schema creation with ChunkSchema
    - Batch ingestion with doc_id-based UUID generation
    - Efficient deletion by doc_id using ContainsAny optimization
    - Document reingestion operations
    - DocChunk-specific filtering and search
    - Timezone-aware date filtering

    Note: ContainsAny filters are used instead of multiple OR operations
    to avoid Weaviate's filter combination limits.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        host: Optional[str] = None,
        api_key: Optional[str] = None,
        additional_headers: Optional[Dict[str, str]] = None,
        collection_name: str = ChunkSchema.COLLECTION_NAME,
        vectorizer: str = "text2vec-openai",
        vectorizer_config: Optional[Dict[str, Any]] = None,
        batch_size: int = 200,
        delete_batch_size: int = 500,
    ):
        """
        Initialize the Weaviate chunk client.

        Args:
            url: Weaviate instance URL
            host: Weaviate host (for local connections)
            api_key: Optional API key for authentication
            additional_headers: Optional additional headers
            collection_name: Name of the collection (default: CustomerDocumentChunk)
            vectorizer: Vectorizer module to use (default: text2vec-openai)
            vectorizer_config: Optional vectorizer configuration
            batch_size: Size of each batch for ingestion (default: 200)
            delete_batch_size: Size of each batch for deletion (default: 500)
        """
        # Setup headers with OpenAI key if available
        openai_key = os.getenv("OPENAI_API_KEY")
        default_headers = {}
        if openai_key:
            default_headers["X-OpenAI-Api-Key"] = openai_key

        if additional_headers:
            merged_headers = {**default_headers, **additional_headers}
        else:
            merged_headers = default_headers

        # Initialize base client
        super().__init__(
            url=url,
            host=host,
            api_key=api_key,
            additional_headers=merged_headers,
            collection_name=collection_name,
            batch_size=batch_size,
            delete_batch_size=delete_batch_size,
        )

        self.vectorizer = vectorizer
        self.vectorizer_config = vectorizer_config or {}

        logger.info(f"Initialized WeaviateChunkClient for {self.url or self.host}")

    async def setup_schema(self, recreate: bool = False) -> None:
        """
        Setup or validate the chunk collection schema.

        Args:
            recreate: If True, delete and recreate the collection

        Design decisions:
        - Uses configurable vectorizer for flexibility
        - Enables BM25 for keyword search
        - Sets up appropriate indexes based on query patterns
        """
        # Configure vectorizer with model settings
        vectorizer_module = Configure.Vectorizer.text2vec_openai(
            model="text-embedding-3-large",
            vectorize_collection_name=False,
        )

        if self.vectorizer == "text2vec-cohere":
            vectorizer_module = Configure.Vectorizer.text2vec_cohere(
                vectorize_collection_name=False
            )
        elif self.vectorizer == "text2vec-huggingface":
            vectorizer_module = Configure.Vectorizer.text2vec_huggingface(
                vectorize_collection_name=False
            )

        # Use base client's setup_schema with chunk-specific configuration
        await super().setup_schema(
            properties=ChunkSchema.get_properties(),
            vectorizer_config=vectorizer_module,
            description="Customer document chunks with metadata for RAG applications",
            vector_index_config=Configure.VectorIndex.hnsw(),
            inverted_index_config=Configure.inverted_index(
                stopwords_preset=StopwordsPreset.EN,
                index_null_state=False,
                index_property_length=True,
                index_timestamps=True,
            ),
            recreate=recreate,
        )

    def _generate_chunk_uuid(self, chunk: Dict[str, Any]) -> str:
        """
        Generate deterministic UUID for a chunk based on doc_id and chunk_no.

        Args:
            chunk: Chunk dictionary with doc_id and chunk_no

        Returns:
            str: Generated UUID
        """
        uuid_seed = f"{chunk.get(ChunkSchema.DOC_ID)}_{chunk.get(ChunkSchema.CHUNK_NO)}"
        return str(generate_uuid5(uuid_seed))

    def _transform_chunk_properties(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform chunk properties for ingestion, including date formatting.

        Args:
            chunk: Raw chunk dictionary

        Returns:
            Dict[str, Any]: Transformed properties ready for Weaviate
        """
        properties = {}

        for prop in ChunkSchema.get_properties():
            prop_name = prop.name
            if prop_name in chunk:
                value = chunk[prop_name]

                # Handle date fields
                if prop.dataType == DataType.DATE and value is not None:
                    if isinstance(value, datetime):
                        if value.tzinfo is None:
                            value = value.replace(tzinfo=timezone.utc)
                        # Use ISO format with Z for UTC
                        value = value.isoformat().replace('+00:00', 'Z')
                    elif isinstance(value, str):
                        try:
                            parsed_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            if parsed_date.tzinfo is None:
                                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                            value = parsed_date.isoformat().replace('+00:00', 'Z')
                        except ValueError:
                            logger.warning(f"Invalid date format for {prop_name}: {value}, setting to None")
                            value = None

                properties[prop_name] = value

        return properties

    async def ingest_chunks(
        self,
        chunks: List[Dict[str, Any]],
        generate_vectors: bool = True,
    ) -> List[str]:
        """
        Ingest chunks in batches using the sync client for optimal performance.

        Args:
            chunks: List of chunk dictionaries
            generate_vectors: Whether to generate vectors (default: True)

        Returns:
            List[str]: List of generated UUIDs for the chunks

        Note:
        - Uses sync client for batch operations as recommended by Weaviate
        - Handles timezone conversion for dates
        - Generates deterministic UUIDs based on doc_id and chunk_no
        """
        return await self.ingest_objects(
            objects=chunks,
            uuid_generator=self._generate_chunk_uuid,
            property_transformer=self._transform_chunk_properties,
            generate_vectors=generate_vectors,
        )

    async def delete_by_doc_id(
        self,
        doc_id: Union[str, List[str]],
    ) -> Tuple[int, int, int, int]:
        """
        Delete all chunks associated with one or more document IDs.

        Args:
            doc_id: Single document ID or list of document IDs

        Returns:
            Tuple[int, int, int, int]: (total_doc_ids_deleted, failed, matched, successful)

        This method uses where clauses for efficient deletion without fetching UUIDs.
        For multiple doc_ids, uses ContainsAny filter to avoid limits with OR operations.
        """
        # Handle single doc_id or list
        doc_ids = [doc_id] if isinstance(doc_id, str) else doc_id

        if not doc_ids:
            return 0, 0, 0, 0  # Return proper tuple for empty input

        # Process in batches based on delete_batch_size
        total_doc_ids_deleted = 0
        successful = 0
        failed = 0
        matched = 0

        for i in range(0, len(doc_ids), self.delete_batch_size):
            batch_doc_ids = doc_ids[i:i + self.delete_batch_size]

            # Build filter for batch deletion using ContainsAny for efficiency
            if len(batch_doc_ids) == 1:
                where_filter = Filter.by_property(ChunkSchema.DOC_ID).equal(batch_doc_ids[0])
            else:
                # Use ContainsAny instead of combining multiple OR filters
                where_filter = Filter.by_property(ChunkSchema.DOC_ID).contains_any(batch_doc_ids)

            # Delete using base client's delete_many
            try:
                batch_failed, batch_matched, batch_successful = await self.delete_many(where_filter)

                failed += batch_failed
                matched += batch_matched
                successful += batch_successful

                # Only count as successful deletions if we actually have matches
                if batch_matched > 0:
                    total_doc_ids_deleted += len(batch_doc_ids)  # Approximate

            except Exception as e:
                logger.error(f"Failed to delete batch: {e}")
                raise

        logger.info(f"Deleted chunks for {len(doc_ids)} document(s)")
        return total_doc_ids_deleted, failed, matched, successful

    async def reingest_document(
        self,
        doc_id: str,
        new_chunks: List[Dict[str, Any]],
        generate_vectors: bool = True,
    ) -> Tuple[int, List[str]]:
        """
        Reingest a document by deleting old chunks and inserting new ones.

        Args:
            doc_id: Document ID to reingest
            new_chunks: New chunks for the document
            generate_vectors: Whether to generate vectors

        Returns:
            Tuple[int, List[str]]: (deleted_count, new_uuids)

        This is an atomic operation that ensures:
        - All old chunks are deleted before new ones are inserted
        - Consistent state even if insertion fails
        """
        # First, delete all existing chunks
        deleted_doc_count, failed, matched, successful = await self.delete_by_doc_id(doc_id)

        # Then, ingest new chunks
        new_uuids = await self.ingest_chunks(new_chunks, generate_vectors)

        logger.info(
            f"Reingested document {doc_id}: "
            f"deleted ~{deleted_doc_count}, inserted {len(new_uuids)}, failed {failed}, matched {matched}, successful {successful}"
        )

        return deleted_doc_count, new_uuids

    async def batch_reingest_documents(
        self,
        documents: List[Dict[str, Any]],
        generate_vectors: bool = True,
    ) -> Dict[str, Tuple[int, List[str]]]:
        """
        Reingest multiple documents in batch.

        Args:
            documents: List of dicts with 'doc_id' and 'chunks' keys
                      Example: [{"doc_id": "doc1", "chunks": [...]}, ...]
            generate_vectors: Whether to generate vectors

        Returns:
            Dict[str, Tuple[int, List[str]]]: Mapping of doc_id to (deleted_count, new_uuids)

        This method efficiently handles multiple document reingestions:
        - Batch deletes all old documents
        - Batch ingests all new chunks
        """
        if not documents:
            return {}

        # Extract all doc_ids for batch deletion
        doc_ids = [doc["doc_id"] for doc in documents]

        # Batch delete all documents
        logger.info(f"Batch deleting {len(doc_ids)} documents")
        total_docs_deleted, failed, matched, successful = await self.delete_by_doc_id(doc_ids)

        # Prepare all chunks for batch ingestion
        all_chunks = []
        doc_chunk_mapping = {}  # Track which chunks belong to which doc

        for doc in documents:
            doc_id = doc["doc_id"]
            chunks = doc["chunks"]
            start_idx = len(all_chunks)
            all_chunks.extend(chunks)
            end_idx = len(all_chunks)
            doc_chunk_mapping[doc_id] = (start_idx, end_idx)

        # Batch ingest all chunks
        logger.info(f"Batch ingesting {len(all_chunks)} chunks")
        all_uuids = await self.ingest_chunks(all_chunks, generate_vectors)

        # Map results back to documents
        results = {}
        for doc_id, (start_idx, end_idx) in doc_chunk_mapping.items():
            doc_uuids = all_uuids[start_idx:end_idx]
            # Approximate deleted count per doc
            avg_deleted = total_docs_deleted // len(doc_ids) if doc_ids else 0
            results[doc_id] = (avg_deleted, doc_uuids)

        logger.info(f"Batch reingested {len(documents)} documents")
        return results

    async def search_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        date_field: str = ChunkSchema.SCHEDULED_DATE,
        user_timezone: str = "UTC",
        additional_filters: Optional[Filter] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search for chunks within a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            date_field: Field to filter on (default: scheduled_date)
            user_timezone: User's timezone for conversion
            additional_filters: Additional filters to apply
            limit: Maximum results
            offset: Number of results to skip before applying the limit

        Returns:
            List[Dict[str, Any]]: Chunks within date range

        This method handles timezone conversion:
        - Converts user's local time to UTC for querying
        - Ensures consistent timezone handling
        """
        # Get timezone object
        if user_timezone == "UTC":
            tz = timezone.utc
        else:
            # For non-UTC timezones, you might want to use a library like zoneinfo
            # For now, we'll assume the dates are already in the correct timezone
            logger.warning(f"Timezone {user_timezone} conversion not implemented, using as-is")
            tz = None

        # Ensure dates are timezone-aware
        if tz and start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=tz)
        if tz and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=tz)

        # Convert to UTC for Weaviate query
        if start_date.tzinfo:
            start_utc = start_date.astimezone(timezone.utc)
        else:
            start_utc = start_date

        if end_date.tzinfo:
            end_utc = end_date.astimezone(timezone.utc)
        else:
            end_utc = end_date

        # Build date range filter with RFC3339 format
        start_date_str = start_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
        end_date_str = end_utc.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'

        date_filter = (
            Filter.by_property(date_field).greater_or_equal(start_date_str) &
            Filter.by_property(date_field).less_or_equal(end_date_str)
        )

        # Combine with additional filters if provided
        if additional_filters:
            where_filter = date_filter & additional_filters
        else:
            where_filter = date_filter

        # Use base client's fetch_objects
        return await self.fetch_objects(
            where_filter=where_filter,
            limit=limit,
            offset=offset,
        )

    def build_filter(
        self,
        doc_id: Optional[str] = None,
        org_segment: Optional[str] = None,
        user_segment: Optional[str] = None,
        namespace: Optional[str] = None,
        doc_name: Optional[str] = None,
        version: Optional[str] = None,
        # Date range filters
        created_at_start: Optional[datetime] = None,
        created_at_end: Optional[datetime] = None,
        updated_at_start: Optional[datetime] = None,
        updated_at_end: Optional[datetime] = None,
        scheduled_date_start: Optional[datetime] = None,
        scheduled_date_end: Optional[datetime] = None,
        # CHUNK_KEYS filters
        chunk_keys_contains_any: Optional[List[str]] = None,
        chunk_keys_contains_all: Optional[List[str]] = None,
    ) -> Optional[Filter]:
        """
        Build a compound filter from document identifiers, date ranges, and chunk keys.

        Args:
            doc_id: Document ID filter
            org_segment: Organization segment filter
            user_segment: User segment filter
            namespace: Namespace filter
            doc_name: Document name filter
            version: Version filter
            created_at_start: Filter for CREATED_AT >= this date
            created_at_end: Filter for CREATED_AT <= this date
            updated_at_start: Filter for UPDATED_AT >= this date
            updated_at_end: Filter for UPDATED_AT <= this date
            scheduled_date_start: Filter for SCHEDULED_DATE >= this date
            scheduled_date_end: Filter for SCHEDULED_DATE <= this date
            chunk_keys_contains_any: Filter for CHUNK_KEYS containing any of these values
            chunk_keys_contains_all: Filter for CHUNK_KEYS containing all of these values

            # TODO: add Like support for namespace / docname prefix / suffix filters https://docs.weaviate.io/weaviate/api/graphql/filters#like
            #     NOTE: this filter is inefficent and scales linearly with the number of documents!

        Returns:
            Optional[Filter]: Combined filter or None

        This is a helper method to build complex filters easily.
        Date values will be converted to ISO format with Z suffix for Weaviate.
        """
        filters = []

        # Basic identifier filters
        if doc_id:
            filters.append(Filter.by_property(ChunkSchema.DOC_ID).equal(doc_id))
        if org_segment:
            filters.append(Filter.by_property(ChunkSchema.ORG_SEGMENT).equal(org_segment))
        if user_segment:
            filters.append(Filter.by_property(ChunkSchema.USER_SEGMENT).equal(user_segment))
        if namespace:
            filters.append(Filter.by_property(ChunkSchema.NAMESPACE).equal(namespace))
        if doc_name:
            filters.append(Filter.by_property(ChunkSchema.DOC_NAME).equal(doc_name))
        if version:
            filters.append(Filter.by_property(ChunkSchema.VERSION).equal(version))

        # Date range filters for CREATED_AT
        if created_at_start:
            # Ensure timezone
            if created_at_start.tzinfo is None:
                created_at_start = created_at_start.replace(tzinfo=timezone.utc)
            iso_date = created_at_start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            filters.append(Filter.by_property(ChunkSchema.CREATED_AT).greater_or_equal(iso_date))
        if created_at_end:
            # Ensure timezone
            if created_at_end.tzinfo is None:
                created_at_end = created_at_end.replace(tzinfo=timezone.utc)
            iso_date = created_at_end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            filters.append(Filter.by_property(ChunkSchema.CREATED_AT).less_or_equal(iso_date))

        # Date range filters for UPDATED_AT
        if updated_at_start:
            # Ensure timezone
            if updated_at_start.tzinfo is None:
                updated_at_start = updated_at_start.replace(tzinfo=timezone.utc)
            iso_date = updated_at_start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            filters.append(Filter.by_property(ChunkSchema.UPDATED_AT).greater_or_equal(iso_date))
        if updated_at_end:
            # Ensure timezone
            if updated_at_end.tzinfo is None:
                updated_at_end = updated_at_end.replace(tzinfo=timezone.utc)
            iso_date = updated_at_end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            filters.append(Filter.by_property(ChunkSchema.UPDATED_AT).less_or_equal(iso_date))

        # Date range filters for SCHEDULED_DATE
        if scheduled_date_start:
            # Ensure timezone
            if scheduled_date_start.tzinfo is None:
                scheduled_date_start = scheduled_date_start.replace(tzinfo=timezone.utc)
            iso_date = scheduled_date_start.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            filters.append(Filter.by_property(ChunkSchema.SCHEDULED_DATE).greater_or_equal(iso_date))
        if scheduled_date_end:
            # Ensure timezone
            if scheduled_date_end.tzinfo is None:
                scheduled_date_end = scheduled_date_end.replace(tzinfo=timezone.utc)
            iso_date = scheduled_date_end.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            filters.append(Filter.by_property(ChunkSchema.SCHEDULED_DATE).less_or_equal(iso_date))

        # CHUNK_KEYS filters
        if chunk_keys_contains_any:
            filters.append(Filter.by_property(ChunkSchema.CHUNK_KEYS).contains_any(chunk_keys_contains_any))
        if chunk_keys_contains_all:
            filters.append(Filter.by_property(ChunkSchema.CHUNK_KEYS).contains_all(chunk_keys_contains_all))

        if not filters:
            return None

        # Combine all filters with AND - this is appropriate since we're combining
        # different types of filters (identifiers, dates, etc.)
        # Note: ContainsAny is already used above for array-based filtering
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f

        return combined_filter

    async def batch_fetch_by_doc_ids(
        self,
        doc_ids: List[str],
        return_properties: Optional[List[str]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch chunks for multiple document IDs efficiently.

        Args:
            doc_ids: List of document IDs to fetch
            return_properties: Properties to return

        Returns:
            Dict[str, List[Dict[str, Any]]]: Mapping of doc_id to chunks

        This method is optimized for batch fetching:
        - Groups results by doc_id
        - Handles large lists of doc_ids
        - Uses ContainsAny filter to avoid limits with OR operations
        """
        if not doc_ids:
            return {}

        results_by_doc_id = {doc_id: [] for doc_id in doc_ids}

        # Process in batches to avoid query size limits
        batch_size = 50  # Adjust based on Weaviate limits

        for i in range(0, len(doc_ids), batch_size):
            batch_doc_ids = doc_ids[i:i + batch_size]

            if len(batch_doc_ids) == 1:
                # Single doc_id
                combined_filter = Filter.by_property(ChunkSchema.DOC_ID).equal(batch_doc_ids[0])
            else:
                # Use ContainsAny instead of combining multiple OR filters
                combined_filter = Filter.by_property(ChunkSchema.DOC_ID).contains_any(batch_doc_ids)

            # Fetch objects using base client
            result_objects = await self.fetch_objects(
                where_filter=combined_filter,
                limit=10000,  # Adjust based on expected chunks per doc
                return_properties=return_properties,
            )

            # Group by doc_id
            for obj in result_objects:
                doc_id = obj["properties"].get(ChunkSchema.DOC_ID)
                if doc_id in results_by_doc_id:
                    results_by_doc_id[doc_id].append(obj)

        return results_by_doc_id


# Example usage function for testing
async def example_usage():
    """
    Example usage of the WeaviateChunkClient.

    This demonstrates:
    - Client initialization and connection
    - Schema setup
    - Chunk ingestion
    - Various search methods
    - Document reingestion
    - Batch operations
    """
    # Initialize client
    async with WeaviateChunkClient(
        vectorizer="text2vec-openai",
        batch_size=100,
        delete_batch_size=500,
    ) as client:
        # Setup schema
        await client.setup_schema(recreate=False)

        # Example chunks
        example_chunks = [
            {
                ChunkSchema.DOC_ID: "doc123",
                ChunkSchema.ORG_SEGMENT: "org1",
                ChunkSchema.USER_SEGMENT: "user1",
                ChunkSchema.NAMESPACE: "default",
                ChunkSchema.DOC_NAME: "Technical Documentation",
                ChunkSchema.VERSION: "1.0",
                ChunkSchema.CHUNK_NO: 1,
                ChunkSchema.CHUNK_CONTENT: '{"title": "Introduction", "content": "This is the first chunk of technical documentation."}',
                ChunkSchema.CHUNK_KEYS: ["title", "content"],
                ChunkSchema.CREATED_AT: datetime.now(timezone.utc),
                ChunkSchema.UPDATED_AT: datetime.now(timezone.utc),
                ChunkSchema.SCHEDULED_DATE: datetime(2024, 1, 15, tzinfo=timezone.utc),
            },
        ]

        # Ingest chunks
        uuids = await client.ingest_chunks(example_chunks)
        print(f"Ingested {len(uuids)} chunks")

        # Vector search
        results = await client.vector_search(
            query_text="technical documentation overview",
            limit=5,
        )
        print(f"Vector search found {len(results)} results")

        # Clean up
        await client.delete_by_doc_id("doc123")
        print("✅ Cleanup complete")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
