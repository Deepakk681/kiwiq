import asyncio
import logging
from uuid import UUID
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from kiwi_client.customer_data_client import CustomerDataTestClient
from kiwi_client.auth_client import AuthenticatedClient
from kiwi_client.schemas.workflow_api_schemas import CustomerDataVersionedUpsert, CustomerDataVersionedUpsertResponse

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class JSONSerializableCustomerDataVersionedUpsert(CustomerDataVersionedUpsert):
    """Custom wrapper that ensures model_dump always uses mode='json' for UUID serialization"""
    
    def model_dump(self, **kwargs):
        kwargs['mode'] = 'json'
        return super().model_dump(**kwargs)


class FilenameConfig(BaseModel):
    """Configuration structure matching the workflow pattern"""
    static_namespace: str = Field(..., description="The namespace for the document")
    static_docname: str = Field(..., description="The document name")
    
    
class DocumentStorageConfig(BaseModel):
    """Extended configuration for document storage"""
    filename_config: FilenameConfig
    output_field_name: Optional[str] = Field(None, description="Field name for the output")
    is_shared: bool = Field(False, description="Whether the document is shared")
    is_system_entity: bool = Field(False, description="Whether this is a system entity")
    version: str = Field("v1", description="Document version")
    schema_template_name: Optional[str] = Field(None, description="Schema template name")
    schema_template_version: Optional[str] = Field(None, description="Schema template version")


class ConfigBasedUploader:
    """Data uploader that works with configuration objects similar to workflow patterns"""
    
    def __init__(self):
        self.client: Optional[CustomerDataTestClient] = None

    async def authenticate(self) -> None:
        """Authenticate with the service"""
        try:
            auth_client = await AuthenticatedClient().__aenter__()
            logger.info("Authenticated successfully.")
            self.client = CustomerDataTestClient(auth_client)
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    async def store_with_config(
        self,
        config: DocumentStorageConfig,
        data: Any,
        user_id: Optional[UUID] = None,
        entity_username: Optional[str] = None
    ) -> Optional[CustomerDataVersionedUpsertResponse]:
        """
        Store data using DocumentStorageConfig
        
        Args:
            config: DocumentStorageConfig object
            data: The data to store
            user_id: Optional user ID
            entity_username: Optional entity username
            
        Returns:
            Response from upsert operation or None if failed
        """
        if not self.client:
            await self.authenticate()

        try:
            # Prepare payload data
            payload_data = {
                "version": config.version,
                "is_shared": config.is_shared,
                "data": data,
                "is_system_entity": config.is_system_entity,
                "schema_template_name": config.schema_template_name,
                "schema_template_version": config.schema_template_version,
                "set_active_version": True
            }
            
            # Add user ID only for non-system entities
            if not config.is_system_entity and user_id:
                payload_data["on_behalf_of_user_id"] = user_id

            # Create payload with JSON serialization
            payload = JSONSerializableCustomerDataVersionedUpsert(**payload_data)
            
            # Perform the upsert
            response = await self.client.upsert_versioned_document(
                namespace=config.filename_config.static_namespace,
                docname=config.filename_config.static_docname,
                data=payload
            )
            
            if response:
                logger.info(f"Successfully stored data for {config.filename_config.static_docname}")
                logger.debug(f"Response: {response.model_dump_json(indent=2)}")
            else:
                logger.error(f"Failed to store data for {config.filename_config.static_docname}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error storing data for {config.filename_config.static_docname}: {e}")
            return None

    async def store_batch_with_configs(
        self,
        config_data_pairs: List[tuple[DocumentStorageConfig, Any]],
        user_id: Optional[UUID] = None,
        entity_username: Optional[str] = None
    ) -> List[Optional[CustomerDataVersionedUpsertResponse]]:
        """
        Store multiple documents with their configurations
        
        Args:
            config_data_pairs: List of (DocumentStorageConfig, data) tuples
            user_id: Optional user ID
            entity_username: Optional entity username
            
        Returns:
            List of responses from upsert operations
        """
        results = []
        for config, data in config_data_pairs:
            result = await self.store_with_config(config, data, user_id, entity_username)
            results.append(result)
        return results

    async def store_from_dict_config(
        self,
        config_dict: Dict[str, Any],
        data: Any,
        user_id: Optional[UUID] = None,
        entity_username: Optional[str] = None
    ) -> Optional[CustomerDataVersionedUpsertResponse]:
        """
        Store data using a dictionary configuration (convenient for JSON configs)
        
        Args:
            config_dict: Dictionary containing configuration keys
            data: The data to store
            user_id: Optional user ID
            entity_username: Optional entity username
            
        Returns:
            Response from upsert operation or None if failed
        """
        try:
            # Convert dict to DocumentStorageConfig
            config = DocumentStorageConfig(**config_dict)
            return await self.store_with_config(config, data, user_id, entity_username)
        except Exception as e:
            logger.error(f"Error creating config from dictionary: {e}")
            return None


# Utility function to create configs easily
def create_user_doc_config(
    namespace: str,
    docname: str,
    output_field_name: Optional[str] = None,
    version: str = "v1"
) -> DocumentStorageConfig:
    """Create a user document configuration"""
    return DocumentStorageConfig(
        filename_config=FilenameConfig(
            static_namespace=namespace,
            static_docname=docname
        ),
        output_field_name=output_field_name,
        is_shared=False,
        is_system_entity=False,
        version=version
    )


def create_system_doc_config(
    namespace: str,
    docname: str,
    output_field_name: Optional[str] = None,
    is_shared: bool = True,
    version: str = "v1"
) -> DocumentStorageConfig:
    """Create a system document configuration"""
    return DocumentStorageConfig(
        filename_config=FilenameConfig(
            static_namespace=namespace,
            static_docname=docname
        ),
        output_field_name=output_field_name,
        is_shared=is_shared,
        is_system_entity=True,
        version=version
    )


# Example usage
async def example_config_based_usage():
    """Example of using the config-based approach"""
    uploader = ConfigBasedUploader()
    
    # Example 1: Using the configuration structure similar to workflow pattern
    blog_seo_config = DocumentStorageConfig(
        filename_config=FilenameConfig(
            static_namespace="system_strategy_docs_namespace",
            static_docname="blog_seo_best_practices"
        ),
        output_field_name="seo_best_practices",
        is_shared=True,
        is_system_entity=True,
        version="v2.0"
    )
    
    seo_data = {
        "title_guidelines": [
            "Keep titles under 60 characters",
            "Include primary keyword in title",
            "Make titles compelling and clickable"
        ],
        "meta_description_rules": [
            "Keep under 160 characters",
            "Include call-to-action",
            "Use active voice"
        ],
        "content_structure": {
            "introduction": "Hook readers in first paragraph",
            "body": "Use H2 and H3 tags for structure",
            "conclusion": "Summarize and provide next steps"
        }
    }
    
    response = await uploader.store_with_config(
        config=blog_seo_config,
        data=seo_data
    )
    
    # Example 2: Using dictionary config (convenient for JSON)
    user_config_dict = {
        "filename_config": {
            "static_namespace": "user_strategy_johndoe",
            "static_docname": "content_preferences"
        },
        "output_field_name": "preferences",
        "is_shared": False,
        "is_system_entity": False,
        "version": "v1.5"
    }
    
    preferences_data = {
        "topics": ["technology", "AI", "productivity"],
        "tone": "professional yet approachable",
        "length": "medium (500-1000 words)",
        "format": "listicles and how-to guides"
    }
    
    user_id = UUID("3fa85f64-5717-4562-b3fc-2c963f66afa1")
    
    response2 = await uploader.store_from_dict_config(
        config_dict=user_config_dict,
        data=preferences_data,
        user_id=user_id,
        entity_username="johndoe"
    )
    
    # Example 3: Using utility functions
    methodology_config = create_system_doc_config(
        namespace="system_strategy_docs_namespace",
        docname="content_methodology_v3",
        output_field_name="methodology",
        version="v3.0"
    )
    
    methodology_data = {
        "research_phase": {
            "steps": ["keyword research", "competitor analysis", "audience research"],
            "tools": ["SEMrush", "Ahrefs", "Google Analytics"]
        },
        "creation_phase": {
            "steps": ["outline creation", "first draft", "editing", "optimization"],
            "review_checkpoints": ["fact-check", "tone review", "SEO optimization"]
        },
        "distribution_phase": {
            "channels": ["blog", "social media", "newsletter"],
            "timing": "optimal posting times based on audience data"
        }
    }
    
    response3 = await uploader.store_with_config(
        config=methodology_config,
        data=methodology_data
    )
    
    print(f"Stored {len([r for r in [response, response2, response3] if r])} documents successfully")


if __name__ == "__main__":
    print("Running config-based uploader example...")
    asyncio.run(example_config_based_usage()) 